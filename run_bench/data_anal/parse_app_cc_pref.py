#!/usr/bin/env python3
"""
Parse the cross-application CC-policy preference experiment (app_cc_pref) and
emit tidy + summary CSVs.

Result tree (produced by gen_app_cc_pref_qemuless_node1.sh + gen_eval.sh):
  results/<bench>/mpi_cxl_qemuless/<cc_type>/<np>/<usecase>/<timestamp>/output.log

Benchmarks and their metrics:
  osu_put_latency, osu_get_latency          "# Size  Latency (us)"      lower better
  osu_put_bw, osu_get_bw                    "# Size  Bandwidth (MB/s)"  higher better
  osu_allgather, osu_alltoall, osu_allreduce"# Size  Avg Latency(us)"   lower better
  lulesh_baseline                           "FOM = X (z/s)"             higher better

Repetitions = timestamp dirs; the summary takes the median across reps
(per benchmark x cc_type x msg_size).

Outputs (under data_anal/):
  app_cc_pref_long.csv    -> benchmark,cc_type,num_process,timestamp,msg_size,value,metric
  app_cc_pref_median.csv  -> benchmark,cc_type,num_process,msg_size,value,metric,n_reps

Operating-point summary (the per-"application" preference table) is produced by
analyze_app_cc_pref.py, which consumes app_cc_pref_median.csv.

Env overrides:
  APP_CC_PREF_USECASE  (default app_cc_pref_qemuless_node1_20260718)
"""
import csv
import glob
import os
import re
import statistics

RUN_BENCH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(RUN_BENCH, "results")
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

USECASES = os.getenv(
    "APP_CC_PREF_USECASE",
    "app_cc_pref_qemuless_node1_20260718 app_cc_pref_apps_qemuless_node1_20260718"
    " app_cc_pref_apps_qemuless_node1_20260718_backfill"
    " app_cc_pref_qemuless_node1_20260718_extra",
).split()
NET_CONFIG = "mpi_cxl_qemuless"

BENCH_METRIC = {
    "osu_put_latency": ("latency_us", "lower"),
    "osu_get_latency": ("latency_us", "lower"),
    "osu_put_bw": ("bandwidth_MBps", "higher"),
    "osu_get_bw": ("bandwidth_MBps", "higher"),
    "osu_allgather": ("latency_us", "lower"),
    "osu_alltoall": ("latency_us", "lower"),
    "osu_allreduce": ("latency_us", "lower"),
    "lulesh_baseline": ("fom_zps", "higher"),
    "npb_is_c": ("time_s", "lower"),
    "npb_is_d": ("time_s", "lower"),
    "graph500_simple_s20": ("bfs_median_s", "lower"),
    "stencil_rma_ompi_1000": ("time_s", "lower"),
}

CC_TYPES = [
    "nocc",
    "cc_clwb_clflush",
    "cc_clwb_clflushopt",
    "cc_clflush_clflush",
    "cc_clflush_clflushopt",
    "cc_clflushopt_clflush",
    "cc_clflushopt_clflushopt",
]

ROW_RE = re.compile(r"^\s*(\d+)\s+(\d+\.?\d*(?:[eE][+-]?\d+)?)\s*$")
HEADER_RE = re.compile(r"^#\s*Size\s+(Latency|Bandwidth|Avg Latency)", re.IGNORECASE)
FOM_RE = re.compile(r"FOM\s*=\s*(\d+\.?\d*)")
NPB_TIME_RE = re.compile(r"Time in seconds\s*=\s*(\d+\.?\d*)")
G500_MEDIAN_RE = re.compile(r"median_time:\s*(\d+\.?\d*(?:[eE][+-]?\d+)?)")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

STENCIL_TIME_RE = re.compile(r"last heat:\s*\S+\s+time:\s*(\d+\.?\d*)")

SCALAR_RE = {  # benchmarks whose result is one scalar (reported as msg_size=0)
    "lulesh_baseline": FOM_RE,
    "npb_is_c": NPB_TIME_RE,
    "npb_is_d": NPB_TIME_RE,
    "graph500_simple_s20": G500_MEDIAN_RE,
    "stencil_rma_ompi_1000": STENCIL_TIME_RE,
}


def parse_output_log(path, bench):
    """Return list of (msg_size, value). LULESH uses msg_size=0.

    Shim INFO lines (colored, may interleave with the OSU table) are stripped
    of ANSI codes and skipped; the table runs from its header to EOF or the
    shim statistics banner. Duplicate sizes keep the first occurrence.
    """
    rows, in_table, seen = [], False, set()
    try:
        fh = open(path, "r", errors="replace")
    except OSError:
        return []
    with fh:
        for raw in fh:
            line = ANSI_RE.sub("", raw)
            if bench in SCALAR_RE:
                m = SCALAR_RE[bench].search(line)
                if m:
                    rows = [(0, float(m.group(1)))]
                continue
            if HEADER_RE.search(line):
                in_table = True
                rows, seen = [], set()  # keep the LAST table in the file
                continue
            if in_table:
                if "Statistics Summary" in line:
                    in_table = False
                    continue
                m = ROW_RE.match(line)
                if m:
                    size = int(m.group(1))
                    if size not in seen:
                        seen.add(size)
                        rows.append((size, float(m.group(2))))
    return rows


def main():
    long_rows = []
    for bench, (metric, _) in BENCH_METRIC.items():
        for cc in CC_TYPES:
            logs = []
            for usecase in USECASES:
                pattern = os.path.join(
                    RESULTS, bench, NET_CONFIG, cc, "*", usecase, "*", "output.log"
                )
                logs.extend(glob.glob(pattern))
            for log in sorted(logs):
                parts = log.split(os.sep)
                ts = parts[-2]
                np_ = parts[-4]
                rows = parse_output_log(log, bench)
                if not rows:
                    print(f"WARN: no data in {log}")
                    continue
                for size, val in rows:
                    long_rows.append(
                        dict(benchmark=bench, cc_type=cc, num_process=np_,
                             timestamp=ts, msg_size=size, value=val, metric=metric)
                    )

    long_csv = os.path.join(OUT_DIR, "app_cc_pref_long.csv")
    with open(long_csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "benchmark", "cc_type", "num_process", "timestamp",
            "msg_size", "value", "metric"])
        w.writeheader()
        w.writerows(long_rows)
    print(f"Wrote {long_csv} ({len(long_rows)} rows)")

    # median across reps
    keyed = {}
    for r in long_rows:
        k = (r["benchmark"], r["cc_type"], r["num_process"], r["msg_size"], r["metric"])
        keyed.setdefault(k, []).append(r["value"])
    med_csv = os.path.join(OUT_DIR, "app_cc_pref_median.csv")
    with open(med_csv, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["benchmark", "cc_type", "num_process", "msg_size",
                    "value", "metric", "n_reps"])
        for (bench, cc, np_, size, metric), vals in sorted(keyed.items()):
            w.writerow([bench, cc, np_, size,
                        statistics.median(vals), metric, len(vals)])
    print(f"Wrote {med_csv} ({len(keyed)} rows)")


if __name__ == "__main__":
    main()
