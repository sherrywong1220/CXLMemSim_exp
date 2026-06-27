#!/usr/bin/env python3
"""
Parse OSU collective (allreduce / allgather / alltoall) latency results and emit
tidy + wide comparison CSVs across MPI "series".

A *series* is a (net_config, cc_type) pair with a short label -- this lets the
same net_config appear more than once under different cache-control shims (e.g.
qemuless with nocc vs qemuless with CLFLUSHOPT, which mirrors cMPI's flush path).

Result tree (produced by gen_eval.sh eval scripts):
  results/<bench>/<net_config>/<cc_type>/<num_process>/<usecase>/<timestamp>/output.log

The OSU output embeds a latency table:
  # Size       Avg Latency(us)
  1                       2.90
  ...
  1048576               846.32

Config via env vars:
  DATA_ANAL_BENCHMARKS  space-separated; default "osu_allreduce osu_allgather osu_alltoall"
  DATA_ANAL_SERIES      space-separated "net_config:cc_type[:label]" entries.
                        Default is the four-way study below.

Outputs (under data_anal/):
  osu_collective_long.csv     -> series,net_config,cc_type,benchmark,num_process,msg_size,avg_latency_us
  osu_collective_compare.csv  -> per (benchmark,num_process,msg_size): one column per
                                 series + ratios vs the first (baseline) series.
"""
import os
import re
import csv
import glob

REPO_RESULTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"
)

BENCHMARKS = os.getenv(
    "DATA_ANAL_BENCHMARKS", "osu_allreduce osu_allgather osu_alltoall"
).split()

# Default series for this study. First entry is the comparison baseline.
DEFAULT_SERIES = [
    ("mpi_cxl_qemuless", "nocc", "qemuless_nocc"),
    ("mpi_cxl_qemuless", "cc_clflushopt_clflushopt", "qemuless_clflushopt"),
    ("openmpi_native", "nocc", "openmpi_native"),
    ("cmpi", "nocc", "cmpi"),
]


def load_series():
    env = os.getenv("DATA_ANAL_SERIES")
    if not env:
        return DEFAULT_SERIES
    series = []
    for tok in env.split():
        parts = tok.split(":")
        net, cc = parts[0], parts[1]
        label = parts[2] if len(parts) > 2 else f"{net}__{cc}"
        series.append((net, cc, label))
    return series


SERIES = load_series()

# A data row in the OSU latency table: "<size>   <latency>"
ROW_RE = re.compile(r"^\s*(\d+)\s+(\d+\.?\d*)\s*$")
HEADER_RE = re.compile(r"^#\s*Size\s+Avg Latency", re.IGNORECASE)


def parse_latency_table(output_log_path):
    """Return list of (msg_size:int, avg_latency_us:float). [] if no table found."""
    rows = []
    in_table = False
    try:
        with open(output_log_path, "r", errors="replace") as fh:
            for line in fh:
                if HEADER_RE.search(line):
                    in_table = True
                    rows = []  # keep the LAST table in the file
                    continue
                if in_table:
                    m = ROW_RE.match(line)
                    if m:
                        rows.append((int(m.group(1)), float(m.group(2))))
                    elif line.strip() and not line.startswith("#"):
                        # a non-comment, non-data line ends the table
                        in_table = False
    except OSError as e:
        print(f"  ! cannot read {output_log_path}: {e}")
    return rows


def newest_run_dir(bench, net, cc):
    """Newest timestamp dir per num_process under bench/net/cc/<np>/<usecase>/<ts>."""
    base = os.path.join(REPO_RESULTS, bench, net, cc)
    found = {}  # np(int) -> output.log path (newest ts)
    if not os.path.isdir(base):
        return found
    for np_dir in os.listdir(base):
        np_path = os.path.join(base, np_dir)
        if not (np_dir.isdigit() and os.path.isdir(np_path)):
            continue
        logs = glob.glob(os.path.join(np_path, "*", "*", "output.log"))
        if not logs:
            continue
        newest = max(logs, key=lambda p: os.path.getmtime(p))
        found[int(np_dir)] = newest
    return found


def main():
    print(f"results root : {REPO_RESULTS}")
    print(f"benchmarks   : {BENCHMARKS}")
    print("series       :")
    for net, cc, label in SERIES:
        print(f"               {label:22s} = {net} / {cc}")

    # table[(bench, np, size)][label] = latency
    table = {}
    long_rows = []
    seen = []  # series labels that actually produced data (preserve order)

    for bench in BENCHMARKS:
        for net, cc, label in SERIES:
            runs = newest_run_dir(bench, net, cc)
            if not runs:
                print(f"  - {bench:14s} {label:22s}: no results")
                continue
            n_pts = 0
            for np_, log in sorted(runs.items()):
                pts = parse_latency_table(log)
                if not pts:
                    print(f"  ! {bench} {label} np={np_}: no latency table "
                          f"(crashed/empty) -> {log}")
                    continue
                if label not in seen:
                    seen.append(label)
                for size, lat in pts:
                    long_rows.append([label, net, cc, bench, np_, size, lat])
                    table.setdefault((bench, np_, size), {})[label] = lat
                    n_pts += 1
            print(f"  + {bench:14s} {label:22s}: {len(runs)} np x sizes "
                  f"= {n_pts} points")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    long_path = os.path.join(out_dir, "osu_collective_long.csv")
    with open(long_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["series", "net_config", "cc_type", "benchmark",
                    "num_process", "msg_size", "avg_latency_us"])
        w.writerows(long_rows)
    print(f"\nWrote {long_path} ({len(long_rows)} rows)")

    # Wide comparison: one column per series + ratio vs baseline (first seen series).
    base = seen[0] if seen else None
    wide_path = os.path.join(out_dir, "osu_collective_compare.csv")
    header = ["benchmark", "num_process", "msg_size"] + seen
    for label in seen:
        if label != base:
            header.append(f"{label}/{base}")
    with open(wide_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for (bench, np_, size) in sorted(table.keys()):
            cells = table[(bench, np_, size)]
            row = [bench, np_, size] + [
                (f"{cells[label]:.2f}" if label in cells else "") for label in seen
            ]
            base_val = cells.get(base)
            for label in seen:
                if label == base:
                    continue
                v = cells.get(label)
                row.append(f"{v / base_val:.3f}" if v and base_val else "")
            w.writerow(row)
    print(f"Wrote {wide_path} (baseline series = {base})")


if __name__ == "__main__":
    main()
