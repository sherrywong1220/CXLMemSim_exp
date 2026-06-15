#!/usr/bin/env python3
"""
Plot osu_get_mbw bandwidth comparison:
  Left:   mpi_cxl_qemuless (nocc)
  Middle: mpi_cxl_qemuless (clflushopt_clflushopt)
  Right:  cmpi (nocc)
Three subfigures, lines per process count.
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import re
import glob

RESULTS_BASE = os.path.join(os.path.dirname(__file__), "../../results_optane/osu_get_mbw")
PROCESS_COUNTS = [2, 4, 8, 16, 32]
OUTPUT_DIR = os.path.dirname(__file__)


def parse_output_log(filepath):
    """Parse an osu_get_mbw output.log, return (sizes, bandwidths)."""
    sizes = []
    bandwidths = []
    with open(filepath, "r") as f:
        for line in f:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            if not clean or clean.startswith("#") or clean.startswith("["):
                continue
            parts = clean.split()
            if len(parts) >= 2:
                try:
                    size = int(parts[0])
                    bw = float(parts[1])
                    sizes.append(size)
                    bandwidths.append(bw)
                except ValueError:
                    continue
    return sizes, bandwidths


def find_latest_log(impl, cc_type, nprocs):
    """Find the latest output.log for a given implementation, cc type, and process count."""
    if impl == "cmpi":
        pattern = os.path.join(
            RESULTS_BASE, impl, "nocc", str(nprocs),
            f"osu_get_mbw_{impl}_node1_*", "*", "output.log"
        )
    else:
        if cc_type == "nocc":
            pattern = os.path.join(
                RESULTS_BASE, impl, "nocc", str(nprocs),
                f"osu_get_mbw_{impl}_node1_*", "*", "output.log"
            )
        else:
            pattern = os.path.join(
                RESULTS_BASE, impl, f"cc_{cc_type}", str(nprocs),
                f"osu_get_mbw_{impl}_node1_cc_{cc_type}_*", "*", "output.log"
            )
    matches = sorted(glob.glob(pattern))
    if not matches:
        print(f"Warning: no data found for {impl}/{cc_type} nprocs={nprocs}")
        return None
    return matches[-1]


def load_all_data():
    """Load data for all three configurations."""
    configs = [
        ("mpi_cxl_qemuless", "nocc"),
        ("mpi_cxl_qemuless", "clflushopt_clflushopt"),
        ("cmpi", "nocc"),
    ]
    data = {}
    for impl, cc_type in configs:
        key = f"{impl}/{cc_type}"
        data[key] = {}
        for np_ in PROCESS_COUNTS:
            logfile = find_latest_log(impl, cc_type, np_)
            if logfile:
                sizes, bws = parse_output_log(logfile)
                if sizes:
                    data[key][np_] = (sizes, bws)
    return data


def plot_comparison(data):
    """Create three-subfigure comparison plot."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 2.8), sharey=True)

    panels = [
        ("mpi_cxl_qemuless/nocc", "MEMU (default)"),
        ("mpi_cxl_qemuless/clflushopt_clflushopt", "MEMU (clflushopt)"),
        ("cmpi/nocc", "CMPI (MPICH CXL)"),
    ]
    colors = [f'C{i}' for i in range(len(PROCESS_COUNTS))]
    markers = ["o", "s", "^", "D", "v"]

    for ax, (key, title) in zip(axes, panels):
        for idx, np_ in enumerate(PROCESS_COUNTS):
            if np_ in data.get(key, {}):
                sizes, bws = data[key][np_]
                ax.plot(
                    sizes, bws,
                    marker=markers[idx], color=colors[idx],
                    linewidth=1.2, markersize=7, alpha=0.85,
                    label=f"{np_} procs",
                )
        ax.set_xscale("log", base=2)
        ax.set_xlabel("Message Size (Bytes)", fontsize=11)
        ax.set_title(title, fontsize=12)
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3, which="both")
        ax.tick_params(labelsize=9)

    axes[0].set_ylabel("Bandwidth (MB/s)", fontsize=11)

    fig.tight_layout()

    out_path = os.path.join(OUTPUT_DIR, "get_mbw_compare_cmpi.png")
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_path}")

    out_pdf = os.path.join(OUTPUT_DIR, "get_mbw_compare_cmpi.pdf")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    data = load_all_data()
    plot_comparison(data)
