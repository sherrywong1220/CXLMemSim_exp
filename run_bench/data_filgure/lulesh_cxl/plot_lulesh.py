#!/usr/bin/env python3
"""
Plot LULESH baseline vs CXL on real Optane host (results_optane/).
One figure with two subfigures: (a) Elapsed time, (b) FOM (z/s).
X-axis: process count.
"""

import matplotlib.pyplot as plt
import os
import re
import glob
from collections import defaultdict

RESULTS_BASE = os.path.join(os.path.dirname(__file__), "../../results_optane")
OUTPUT_DIR = os.path.dirname(__file__)

VARIANTS = [
    ("lulesh_baseline", "Baseline"),
    ("lulesh_cxl", "MEMU-CXL"),
]


def parse_output(filepath):
    elapsed, fom = None, None
    with open(filepath, "r", errors="ignore") as f:
        for line in f:
            m = re.search(r"Elapsed time\s*=\s*([0-9.]+)", line)
            if m:
                elapsed = float(m.group(1))
            m = re.search(r"FOM\s*=\s*([0-9.]+)", line)
            if m:
                fom = float(m.group(1))
    return elapsed, fom


def discover():
    """Return {variant: {nprocs: (elapsed, fom)}}, latest timestamp wins."""
    data = defaultdict(dict)
    for variant, _ in VARIANTS:
        pattern = os.path.join(
            RESULTS_BASE, variant, "mpi_cxl_qemuless", "nocc",
            "*", "*", "*", "output.log",
        )
        latest = {}
        for f in sorted(glob.glob(pattern)):
            parts = f.split(os.sep)
            # .../nocc/{nprocs}/{run}/{ts}/output.log
            try:
                idx = parts.index("nocc")
                nprocs = int(parts[idx + 1])
            except (ValueError, IndexError):
                continue
            latest[nprocs] = f  # sorted -> latest wins
        for nprocs, f in latest.items():
            elapsed, fom = parse_output(f)
            if elapsed is not None and fom is not None:
                data[variant][nprocs] = (elapsed, fom)
    return data


def plot(data):
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4))

    markers = ["o", "s"]
    colors = ["C0", "C3"]

    # (a) Elapsed time
    ax = axes[0]
    for idx, (variant, label) in enumerate(VARIANTS):
        if variant not in data:
            continue
        procs = sorted(data[variant].keys())
        ys = [data[variant][p][0] for p in procs]
        ax.plot(procs, ys, marker=markers[idx], color=colors[idx],
                linewidth=1.5, markersize=8, label=label)
    ax.set_xlabel("MPI Processes", fontsize=11)
    ax.set_ylabel("Elapsed Time (s)", fontsize=11)
    ax.set_title("(a) Elapsed Time", fontsize=12)
    ax.set_xscale("log")
    ax.set_xticks([1, 8, 27])
    ax.set_xticklabels(["1", "8", "27"])
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)

    # (b) FOM
    ax = axes[1]
    for idx, (variant, label) in enumerate(VARIANTS):
        if variant not in data:
            continue
        procs = sorted(data[variant].keys())
        ys = [data[variant][p][1] for p in procs]
        ax.plot(procs, ys, marker=markers[idx], color=colors[idx],
                linewidth=1.5, markersize=8, label=label)
    ax.set_xlabel("MPI Processes", fontsize=11)
    ax.set_ylabel("FOM (z/s)", fontsize=11)
    ax.set_title("(b) Figure of Merit", fontsize=12)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xticks([1, 8, 27])
    ax.set_xticklabels(["1", "8", "27"])
    ax.grid(True, alpha=0.3, which="both")
    ax.legend(fontsize=9)
    ax.tick_params(labelsize=9)

    fig.tight_layout()

    out_png = os.path.join(OUTPUT_DIR, "lulesh_baseline_vs_cxl.png")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_png}")

    out_pdf = os.path.join(OUTPUT_DIR, "lulesh_baseline_vs_cxl.pdf")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    data = discover()
    for variant, _ in VARIANTS:
        for nprocs in sorted(data.get(variant, {}).keys()):
            elapsed, fom = data[variant][nprocs]
            print(f"{variant} np={nprocs}: elapsed={elapsed}s FOM={fom}")
    plot(data)
