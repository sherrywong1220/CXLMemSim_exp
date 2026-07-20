#!/usr/bin/env python3
"""
Parse the allreduce algorithm-comparison runs (flat/tree/rab, qemuless,
cc_clflushopt_clflushopt, use_case aralgo_<algo>_qemuless_node1_20260720)
into a tidy CSV with the median across repetitions.

Output: data_anal/aralgo_long.csv
        columns: algo,num_process,msg_size,reps,median_latency_us
"""
import csv
import glob
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), "results", "osu_allreduce",
                       "mpi_cxl_qemuless", "cc_clflushopt_clflushopt")

ROW_RE = re.compile(r"^\s*(\d+)\s+(\d+\.?\d*)\s*$")
HEADER_RE = re.compile(r"^#\s*Size\s+Avg Latency", re.IGNORECASE)


def parse_table(path):
    """Collect data rows after the last '# Size  Avg Latency' header.
    Shim log lines interleave nondeterministically with the OSU table under
    mpirun, so stray lines inside the table region are ignored rather than
    treated as end-of-table."""
    rows, in_table = [], False
    with open(path, errors="replace") as fh:
        for line in fh:
            if HEADER_RE.search(line):
                in_table, rows = True, []
                continue
            if in_table:
                m = ROW_RE.match(line)
                if m:
                    rows.append((int(m.group(1)), float(m.group(2))))
    return rows


data = {}  # (algo, np, size) -> [latencies]
for log in glob.glob(os.path.join(RESULTS, "*", "aralgo_*_qemuless_node1_*",
                                  "*", "output.log")):
    parts = log.split(os.sep)
    np_ = int(parts[-4])
    m = re.match(r"aralgo_(\w+?)_qemuless", parts[-3])
    if not m:
        continue
    algo = m.group(1)
    rows = parse_table(log)
    if not rows:
        print(f"  ! empty table: {log}")
        continue
    for size, lat in rows:
        data.setdefault((algo, np_, size), []).append(lat)

out = os.path.join(HERE, "aralgo_long.csv")
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["algo", "num_process", "msg_size", "reps",
                "median_latency_us"])
    for (algo, np_, size), lats in sorted(data.items()):
        w.writerow([algo, np_, size, len(lats),
                    round(statistics.median(lats), 2)])
print(f"wrote {out} ({len(data)} cells)")
