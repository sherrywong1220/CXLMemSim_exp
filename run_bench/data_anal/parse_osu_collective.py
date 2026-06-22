#!/usr/bin/env python3
"""
Parse OSU collective (allreduce / allgather / alltoall) latency results and emit
tidy + wide comparison CSVs across MPI stacks (net_configs).

Result tree (produced by gen_eval.sh eval scripts):
  results/<bench>/<net_config>/<cc_type>/<num_process>/<usecase>/<timestamp>/output.log

The OSU output embeds a latency table:
  # Size       Avg Latency(us)
  1                       2.90
  ...
  1048576               846.32

Config via env vars (space-separated), with sensible defaults for this study:
  DATA_ANAL_BENCHMARKS   default: "osu_allreduce osu_allgather osu_alltoall"
  DATA_ANAL_NET_CONFIGS  default: "mpi_cxl_qemuless openmpi_native cmpi"
  DATA_ANAL_CC_TYPE      default: "nocc"

Outputs (under data_anal/):
  osu_collective_long.csv     -> benchmark,net_config,num_process,msg_size,avg_latency_us
  osu_collective_compare.csv  -> per (benchmark,num_process,msg_size): one column per
                                 net_config + ratios vs the first net_config present.
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
NET_CONFIGS = os.getenv(
    "DATA_ANAL_NET_CONFIGS", "mpi_cxl_qemuless openmpi_native cmpi"
).split()
CC_TYPE = os.getenv("DATA_ANAL_CC_TYPE", "nocc")

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


def newest_run_dir(bench, net):
    """Newest timestamp dir per num_process under bench/net/CC_TYPE/<np>/<usecase>/<ts>."""
    base = os.path.join(REPO_RESULTS, bench, net, CC_TYPE)
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
    print(f"net_configs  : {NET_CONFIGS}")
    print(f"cc_type      : {CC_TYPE}")

    # long_rows[(bench, np, size)][net] = latency
    table = {}
    long_rows = []
    seen_nets = []  # preserve order, only nets that produced data

    for bench in BENCHMARKS:
        for net in NET_CONFIGS:
            runs = newest_run_dir(bench, net)
            if not runs:
                print(f"  - {bench:14s} {net:18s}: no results")
                continue
            n_pts = 0
            for np_, log in sorted(runs.items()):
                pts = parse_latency_table(log)
                if not pts:
                    print(f"  ! {bench} {net} np={np_}: no latency table "
                          f"(crashed/empty) -> {log}")
                    continue
                if net not in seen_nets:
                    seen_nets.append(net)
                for size, lat in pts:
                    long_rows.append([bench, net, np_, size, lat])
                    table.setdefault((bench, np_, size), {})[net] = lat
                    n_pts += 1
            print(f"  + {bench:14s} {net:18s}: {len(runs)} np x sizes "
                  f"= {n_pts} points")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    long_path = os.path.join(out_dir, "osu_collective_long.csv")
    with open(long_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["benchmark", "net_config", "num_process",
                    "msg_size", "avg_latency_us"])
        w.writerows(long_rows)
    print(f"\nWrote {long_path} ({len(long_rows)} rows)")

    # Wide comparison: one column per net_config + ratio vs baseline (first seen net).
    base_net = seen_nets[0] if seen_nets else None
    wide_path = os.path.join(out_dir, "osu_collective_compare.csv")
    header = ["benchmark", "num_process", "msg_size"] + seen_nets
    for net in seen_nets:
        if net != base_net:
            header.append(f"{net}/{base_net}")
    with open(wide_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for (bench, np_, size) in sorted(table.keys()):
            cells = table[(bench, np_, size)]
            row = [bench, np_, size] + [
                (f"{cells[net]:.2f}" if net in cells else "") for net in seen_nets
            ]
            base_val = cells.get(base_net)
            for net in seen_nets:
                if net == base_net:
                    continue
                v = cells.get(net)
                row.append(f"{v / base_val:.3f}" if v and base_val else "")
            w.writerow(row)
    print(f"Wrote {wide_path} (baseline net_config = {base_net})")


if __name__ == "__main__":
    main()
