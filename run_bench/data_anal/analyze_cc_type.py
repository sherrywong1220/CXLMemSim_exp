#!/usr/bin/env python3
"""
Analyze performance across different CC_TYPE for a given use_case.
Compares stencil (and compatible) benchmark results by cc_type, outputs CSV + TXT.
Ref: parse_results.py, analyze_perf_results.py
"""

import os
import re
import sys
import csv
import argparse
import numpy as np
from pathlib import Path

# Add parent so we can import timestamp_utils when run from data_anal/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
import timestamp_utils


def extract_stencil_time(output_log_path):
    """Extract stencil time from output.log: '[0] last heat: X.XX time: Y.YY'"""
    try:
        with open(output_log_path, 'r') as f:
            content = f.read()
        match = re.search(r'last heat:\s*[\d.e+-]+\s*time:\s*([\d.]+)', content)
        if match:
            return float(match.group(1))
        # Fallback: execution time from run_bench wrapper
        match = re.search(r'execution time (\d+\.?\d*)\s*\(s\)', content)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Warning: {output_log_path}: {e}", file=sys.stderr)
    return None


def extract_stencil_heat(output_log_path):
    """Extract last heat value if present."""
    try:
        with open(output_log_path, 'r') as f:
            content = f.read()
        match = re.search(r'last heat:\s*([\d.e+-]+)\s*time:', content)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None


def find_cc_type_results(results_base, use_case, bench_name=None, net_config=None, num_process=None):
    """
    Find all cc_type result dirs for the given use_case.
    Structure: results/{bench_name}/{net_config}/{cc_type}/{num_process}/{use_case}/{timestamp}/
    Returns list of (cc_type, num_process_str, output_log_path).
    """
    results_base = os.path.abspath(results_base)
    if not os.path.isdir(results_base):
        print(f"Error: results base not found: {results_base}", file=sys.stderr)
        return []

    found = []
    for bname in os.listdir(results_base):
        if bench_name is not None and bname != bench_name:
            continue
        bench_path = os.path.join(results_base, bname)
        if not os.path.isdir(bench_path):
            continue
        for ncfg in os.listdir(bench_path):
            if net_config is not None and ncfg != net_config:
                continue
            config_path = os.path.join(bench_path, ncfg)
            if not os.path.isdir(config_path):
                continue
            for cctype in os.listdir(config_path):
                cc_path = os.path.join(config_path, cctype)
                if not os.path.isdir(cc_path):
                    continue
                for nproc in os.listdir(cc_path):
                    if num_process is not None and nproc != str(num_process):
                        continue
                    use_case_path = os.path.join(cc_path, nproc, use_case)
                    if not os.path.isdir(use_case_path):
                        continue
                    for ts_dir in timestamp_utils.get_all_timestamp_dirs(use_case_path):
                        out_log = os.path.join(ts_dir, "output.log")
                        if os.path.isfile(out_log):
                            found.append((bname, cctype, nproc, out_log))
    return found


def extract_grid_size(bench_name):
    """Extract grid size from bench name, e.g. stencil_mpi_ddt_rma_1000 -> 1000."""
    m = re.search(r'_(\d+)$', bench_name)
    return m.group(1) if m else bench_name


def aggregate_by_cc_type(rows):
    """Aggregate (cc_type, time, heat) rows: mean, std, num_runs per cc_type."""
    from collections import defaultdict
    by_cc = defaultdict(lambda: {'times': [], 'heats': []})
    for cc, t, h in rows:
        if t is not None:
            by_cc[cc]['times'].append(t)
        if h is not None:
            by_cc[cc]['heats'].append(h)

    result = []
    for cc in sorted(by_cc.keys()):
        times = by_cc[cc]['times']
        heats = by_cc[cc]['heats']
        row = {
            'cc_type': cc,
            'num_runs': len(times),
            'execution_time': float(np.mean(times)) if times else None,
            'execution_time_std': float(np.std(times)) if len(times) > 1 else (0.0 if times else None),
            'heat': float(np.mean(heats)) if heats else None,
            'heat_std': float(np.std(heats)) if len(heats) > 1 else None,
        }
        result.append(row)
    return result


def run_analysis(results_base, use_case, bench_name=None, net_config=None, num_process=None,
                 out_csv=None, out_txt=None):
    """Scan results, aggregate by (num_process, grid_size, cc_type); TXT: per num_process table with rows=grid_size, cols=cc_type, cell=performance (vs nocc %)."""
    if not os.path.isabs(results_base):
        results_base = os.path.normpath(os.path.join(SCRIPT_DIR, results_base))
    rows_raw = find_cc_type_results(results_base, use_case, bench_name, net_config, num_process)
    if not rows_raw:
        print(f"No results found for use_case={use_case}", file=sys.stderr)
        return None

    from collections import defaultdict
    # (nproc -> (grid_size, cc_type) -> list of (t, h))
    by_nproc_gs_cc = defaultdict(lambda: defaultdict(list))
    for bname, cc, nproc, out_log in rows_raw:
        grid_size = extract_grid_size(bname)
        t = extract_stencil_time(out_log)
        h = extract_stencil_heat(out_log)
        by_nproc_gs_cc[nproc][(grid_size, cc)].append((t, h))

    # Build per-nproc: grid_sizes (sorted), cc_types (sorted), and (grid_size, cc_type) -> mean_time
    tables = []  # list of (nproc, grid_sizes, cc_types, cell_map, nocc_map)
    all_cc = set()
    for nproc in sorted(by_nproc_gs_cc.keys(), key=lambda x: int(x)):
        gs_cc_lists = by_nproc_gs_cc[nproc]
        grid_sizes = sorted(set(gs for gs, _ in gs_cc_lists), key=lambda x: int(x))
        cc_types = sorted(set(cc for _, cc in gs_cc_lists))
        all_cc.update(cc_types)
        cell_map = {}  # (grid_size, cc_type) -> { execution_time, num_runs, ... }
        for (gs, cc), pairs in gs_cc_lists.items():
            times = [p[0] for p in pairs if p[0] is not None]
            heats = [p[1] for p in pairs if p[1] is not None]
            cell_map[(gs, cc)] = {
                'execution_time': float(np.mean(times)) if times else None,
                'execution_time_std': float(np.std(times)) if len(times) > 1 else (0.0 if times else None),
                'num_runs': len(times),
                'heat': float(np.mean(heats)) if heats else None,
            }
        nocc_map = {}  # grid_size -> nocc time (baseline)
        for gs in grid_sizes:
            t = cell_map.get((gs, 'nocc'), {}).get('execution_time')
            if t is not None:
                nocc_map[gs] = t
            else:
                # fallback: first cc_type for this grid_size
                for c in cc_types:
                    t = cell_map.get((gs, c), {}).get('execution_time')
                    if t is not None:
                        nocc_map[gs] = t
                        break
        if grid_sizes and cc_types:
            tables.append((nproc, grid_sizes, cc_types, cell_map, nocc_map))

    if not tables:
        return None

    os.makedirs(os.path.join(SCRIPT_DIR, "perf_results"), exist_ok=True)
    if out_csv is None:
        out_csv = os.path.join(SCRIPT_DIR, "perf_results", f"cc_type_{use_case}.csv")
    elif not os.path.isabs(out_csv):
        out_csv = os.path.normpath(os.path.join(SCRIPT_DIR, out_csv))
    if out_txt is None:
        out_txt = os.path.join(SCRIPT_DIR, "perf_results", f"cc_type_{use_case}.txt")
    elif not os.path.isabs(out_txt):
        out_txt = os.path.normpath(os.path.join(SCRIPT_DIR, out_txt))

    # CSV: one row per (num_process, grid_size, cc_type)
    csv_rows = []
    for nproc, grid_sizes, cc_types, cell_map, _ in tables:
        for gs in grid_sizes:
            for cc in cc_types:
                c = cell_map.get((gs, cc), {})
                csv_rows.append({
                    'num_process': int(nproc), 'grid_size': gs, 'cc_type': cc,
                    'num_runs': c.get('num_runs', 0),
                    'execution_time': c.get('execution_time'),
                    'execution_time_std': c.get('execution_time_std'),
                    'heat': c.get('heat'),
                })
    fieldnames = ['num_process', 'grid_size', 'cc_type', 'num_runs', 'execution_time', 'execution_time_std', 'heat']
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(csv_rows)
    print(f"CSV written: {out_csv}")

    # TXT: one table per num_process; row header = grid_size, column header = cc_type; cell = "time (vs nocc %)"
    lines = []
    lines.append("=" * 90)
    lines.append("CC_TYPE PERFORMANCE COMPARISON (BY NUM_PROCESS, ROWS=CC_TYPE COLS=GRID_SIZE)")
    lines.append("=" * 90)
    lines.append(f"use_case:    {use_case}")
    lines.append(f"bench_name:  {bench_name or 'all'}")
    lines.append(f"net_config:  {net_config or 'all'}")
    lines.append("(lower time is better; value in parentheses = vs nocc %, negative = faster)")
    lines.append("")

    for nproc, grid_sizes, cc_types, cell_map, nocc_map in tables:
        lines.append("-" * 90)
        lines.append(f"num_process = {nproc}")
        lines.append("-" * 90)
        # Rows = cc_type, Columns = grid_size (swapped from original)
        cell_width = 22
        header = f"{'cc_type':<28}"
        for gs in grid_sizes:
            header += f" {str(gs):<{cell_width}}"
        lines.append(header)
        sep_len = 28 + (cell_width + 1) * len(grid_sizes)
        lines.append("-" * min(sep_len, 120))
        for cc in cc_types:
            row_str = f"{cc:<28}"
            for gs in grid_sizes:
                nocc_time = nocc_map.get(gs)
                c = cell_map.get((gs, cc), {})
                t = c.get('execution_time')
                if t is not None and nocc_time and nocc_time > 0:
                    pct = (t - nocc_time) / nocc_time * 100
                    cell = f"{t:.4f} ({pct:+.2f}%)"
                elif t is not None:
                    cell = f"{t:.4f} (N/A)"
                else:
                    cell = "N/A"
                row_str += f" {cell:<{cell_width}}"
            lines.append(row_str)
        lines.append("")

    lines.append("=" * 90)
    lines.append("END CC_TYPE ANALYSIS")
    lines.append("=" * 90)

    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print(f"TXT written: {out_txt}")

    return csv_rows


def main():
    parser = argparse.ArgumentParser(description="Compare performance across cc_type for a use_case")
    parser.add_argument("use_case", help="Use case name (e.g. stencil_cc_20260228)")
    parser.add_argument("-r", "--results", default="../results",
                        help="Results base directory (default: ../results)")
    parser.add_argument("-B", "--bench", default=None, help="Benchmark name (e.g. stencil_mpi_ddt_rma_1000)")
    parser.add_argument("-V", "--version", default=None, help="Net config (e.g. mpi_cxl)")
    parser.add_argument("-P", "--process", type=int, default=None, help="Number of processes (e.g. 4)")
    parser.add_argument("-o", "--csv", default=None, help="Output CSV path")
    parser.add_argument("-t", "--txt", default=None, help="Output TXT path")
    args = parser.parse_args()

    run_analysis(
        args.results,
        args.use_case,
        bench_name=args.bench,
        net_config=args.version,
        num_process=args.process,
        out_csv=args.csv,
        out_txt=args.txt,
    )


if __name__ == "__main__":
    main()
