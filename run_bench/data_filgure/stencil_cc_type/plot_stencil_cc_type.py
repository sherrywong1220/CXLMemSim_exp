#!/usr/bin/env python3
"""
Plot stencil_mpi_ddt_rma performance across different cc_types.
2x2 grid: one subplot per grid size (1000, 2000, 4000, 8000).
Each subplot: grouped bar chart with x-axis = process count, bars = cc_type.
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os
import re
import glob

matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

RESULTS_BASE = os.path.join(os.path.dirname(__file__), "../../results_optane")
OUTPUT_DIR = os.path.dirname(__file__)

SIZES = [1000, 2000, 4000, 8000]
PROCESS_COUNTS = [4, 9, 16, 25, 36]
CC_TYPES = [
    "nocc",
    "cc_clflush_clflush",
    "cc_clflush_clflushopt",
    "cc_clflushopt_clflush",
    "cc_clflushopt_clflushopt",
    "cc_clwb_clflush",
    "cc_clwb_clflushopt",
]
CC_LABELS = [
    "No CC",
    "clflush+\nclflush",
    "clflush+\nclflushopt",
    "clflushopt+\nclflush",
    "clflushopt+\nclflushopt",
    "clwb+\nclflush",
    "clwb+\nclflushopt",
]
CC_COLORS = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3"]
HATCHES = ["", "//", "\\\\", "xx", "..", "++", "oo"]


def parse_time_from_log(filepath):
    """Extract execution time from stencil output.log."""
    try:
        with open(filepath, "r") as f:
            content = f.read()
        # Strip ANSI escape codes
        clean = re.sub(r"\x1b\[[0-9;]*m", "", content)
        match = re.search(r"\[0\] last heat:.*?time:\s+([\d.]+)", clean)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None


def collect_data():
    """Collect timing data as the median over all repeat runs: {size: {cc_type: {nprocs: time}}}."""
    data = {}
    for size in SIZES:
        data[size] = {}
        for cc in CC_TYPES:
            data[size][cc] = {}
            for nprocs in PROCESS_COUNTS:
                pattern = os.path.join(
                    RESULTS_BASE,
                    f"stencil_mpi_ddt_rma_{size}",
                    "mpi_cxl", cc, str(nprocs),
                    "*", "*", "output.log",
                )
                logs = sorted(glob.glob(pattern))
                # Median across all repeat runs (robust to single-run outliers)
                times = [t for t in (parse_time_from_log(log) for log in logs) if t is not None]
                if times:
                    data[size][cc][nprocs] = float(np.median(times))
    return data


def plot_grouped_bars(data):
    """Create 2x2 grouped bar chart."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 11.5))
    axes = axes.flatten()

    n_cc = len(CC_TYPES)
    n_proc = len(PROCESS_COUNTS)
    bar_width = 0.11
    group_width = n_cc * bar_width

    for idx, size in enumerate(SIZES):
        ax = axes[idx]
        x_base = np.arange(n_proc)

        # Get nocc baseline for normalization
        nocc_values = {}
        for nprocs in PROCESS_COUNTS:
            t = data[size].get("nocc", {}).get(nprocs, None)
            if t and t > 0:
                nocc_values[nprocs] = t

        for cc_idx, cc in enumerate(CC_TYPES):
            values = []
            for nprocs in PROCESS_COUNTS:
                t = data[size].get(cc, {}).get(nprocs, 0)
                baseline = nocc_values.get(nprocs, 1)
                values.append(t / baseline if baseline > 0 else 0)

            offset = (cc_idx - n_cc / 2 + 0.5) * bar_width
            bars = ax.bar(
                x_base + offset, values, bar_width,
                color=CC_COLORS[cc_idx],
                hatch=HATCHES[cc_idx],
                edgecolor="black", linewidth=0.5,
                label=CC_LABELS[cc_idx] if idx == 0 else None,
                zorder=3,
            )

        # Draw baseline=1.0 reference line
        ax.axhline(y=1.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5, zorder=2)

        ax.set_xticks(x_base)
        ax.set_xticklabels([str(p) for p in PROCESS_COUNTS], fontsize=32)
        ax.set_xlabel("Number of Processes", fontsize=36)
        ax.set_title(f"Grid Size {size}x{size}", fontsize=36, fontweight="bold")
        ax.tick_params(labelsize=32)
        ax.grid(True, axis="y", alpha=0.3, zorder=0)
        ax.set_axisbelow(True)
        ax.set_ylim(bottom=0.9)

    # Single legend at top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles, labels,
        loc="upper center",
        ncol=7,
        fontsize=18,
        bbox_to_anchor=(0.58, 1.02),
        frameon=True,
        edgecolor="gray",
        columnspacing=0.5,
        handletextpad=0.3,
        handlelength=1.0,
    )

    fig.supylabel("Normalized Execution Time\n(relative to No CC)",
                  fontsize=28, x=0.085, y=0.40)
    fig.tight_layout(rect=[0.10, 0, 1, 0.93], w_pad=3.0, h_pad=1.5)

    out_png = os.path.join(OUTPUT_DIR, "stencil_cc_type_comparison.png")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_png}")

    out_pdf = os.path.join(OUTPUT_DIR, "stencil_cc_type_comparison.pdf")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    data = collect_data()

    # Print summary (normalized to nocc)
    for size in SIZES:
        print(f"\n=== Grid Size {size} ===")
        for nprocs in PROCESS_COUNTS:
            nocc_t = data[size].get("nocc", {}).get(nprocs, None)
            print(f"  {nprocs} procs:", end="")
            for cc in CC_TYPES:
                t = data[size].get(cc, {}).get(nprocs, None)
                if t is not None and nocc_t:
                    print(f"  {cc.replace('cc_','')}: {t/nocc_t:.3f}x", end="")
            print()

    plot_grouped_bars(data)
