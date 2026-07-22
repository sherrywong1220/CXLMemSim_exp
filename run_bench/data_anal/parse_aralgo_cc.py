#!/usr/bin/env python3
"""
Parse the allreduce algorithm x cc-policy matrix
(use_case aralgo_<algo>_qemuless_node1_20260720, all cc types including the
reused cc_clflushopt_clflushopt runs from the algo-compare experiment).

Output: data_anal/aralgo_cc_long.csv
        columns: cc,algo,num_process,msg_size,reps,median_latency_us
"""
import csv
import glob
import os
import re
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
# Raw data lives at the CXLMemSim_exp root (two levels up from data_anal):
#   <root>/osu_allreduce/mpi_cxl_qemuless/<cc>/<np>/<usecase>/<ts>/output.log
RESULTS = os.path.join(os.path.dirname(os.path.dirname(HERE)),
                       "osu_allreduce", "mpi_cxl_qemuless")

ROW_RE = re.compile(r"^\s*(\d+)\s+(\d+\.?\d*)\s*$")
HEADER_RE = re.compile(r"^#\s*Size\s+Avg Latency", re.IGNORECASE)


def parse_table(path):
    """Rows after the last OSU table header; stray interleaved shim log
    lines inside the table region are ignored (see aralgo doc, section 6)."""
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


data = {}  # (cc, algo, np, size) -> [latencies]
for log in glob.glob(os.path.join(RESULTS, "*", "*",
                                  "aralgo_*_qemuless_node1_*", "*",
                                  "output.log")):
    parts = log.split(os.sep)
    cc, np_ = parts[-5], int(parts[-4])
    m = re.match(r"aralgo_(\w+?)_qemuless", parts[-3])
    if not m:
        continue
    algo = m.group(1)
    rows = parse_table(log)
    if not rows:
        print(f"  ! no table: {log}")
        continue
    for size, lat in rows:
        data.setdefault((cc, algo, np_, size), []).append(lat)

out = os.path.join(HERE, "aralgo_cc_long.csv")
with open(out, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["cc", "algo", "num_process", "msg_size", "reps",
                "median_latency_us"])
    for (cc, algo, np_, size), lats in sorted(data.items()):
        w.writerow([cc, algo, np_, size, len(lats),
                    round(statistics.median(lats), 2)])

ccs = sorted({k[0] for k in data})
print(f"wrote {out} ({len(data)} cells, cc types: {ccs})")
