#!/usr/bin/env python3
"""
Plot Intel MPI osu_get_bw and osu_get_latency from intelmpi_log/.
One figure with two subfigures (bandwidth, latency), each with one line
per cache-coherency strategy.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
import os
import re

LOG_BASE = os.path.join(os.path.dirname(__file__), "../../intelmpi_log")
OUTPUT_DIR = os.path.dirname(__file__)

CC_TYPES = [
    ("nocc", "nocc"),
    ("cc_clflush_clflush", "clflush"),
    ("cc_clflushopt_clflushopt", "clflushopt"),
    ("cc_clwb_clflush", "clwb+clflush"),
]


def human_bytes(x, _pos=None):
    if x < 1:
        return ""
    if x < 1024:
        return f"{int(x)}"
    if x < 1024 ** 2:
        v = x / 1024
        return f"{int(v)}K" if v == int(v) else f"{v:g}K"
    if x < 1024 ** 3:
        v = x / (1024 ** 2)
        return f"{int(v)}M" if v == int(v) else f"{v:g}M"
    v = x / (1024 ** 3)
    return f"{int(v)}G" if v == int(v) else f"{v:g}G"


def parse_perf_log(filepath):
    sizes, vals = [], []
    in_data = False
    with open(filepath, "r") as f:
        for line in f:
            line = line.rstrip()
            if "Performance Data:" in line:
                in_data = True
                continue
            if not in_data:
                continue
            if line.startswith("=") or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 2:
                try:
                    s = int(parts[0])
                    v = float(parts[1])
                except ValueError:
                    if vals:
                        break
                    continue
                sizes.append(s)
                vals.append(v)
    return sizes, vals


def load(bench):
    out = {}
    for cc, label in CC_TYPES:
        path = os.path.join(LOG_BASE, bench, cc, "perf.log")
        if os.path.exists(path):
            sizes, vals = parse_perf_log(path)
            if sizes:
                out[label] = (sizes, vals)
    return out


def plot():
    bw_data = load("osu_get_bw")
    lat_data = load("osu_get_latency")

    fig, axes = plt.subplots(2, 1, figsize=(7, 6.5))
    markers = ["o", "s", "^", "D", "v", "p"]

    # Bandwidth
    ax = axes[0]
    for idx, (cc, label) in enumerate(CC_TYPES):
        if label not in bw_data:
            continue
        sizes, vals = bw_data[label]
        ax.plot(sizes, vals, marker=markers[idx % len(markers)],
                color=f"C{idx}", linewidth=1.3, markersize=6,
                alpha=0.85, label=label)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
    ax.set_xlabel("Message Size (Bytes)", fontsize=20)
    ax.set_ylabel("Bandwidth (MB/s)", fontsize=20)
    ax.set_title("(a) osu_get_bw", fontsize=22)
    ax.grid(True, alpha=0.3, which="both")
    ax.tick_params(labelsize=18)

    # Latency
    ax = axes[1]
    for idx, (cc, label) in enumerate(CC_TYPES):
        if label not in lat_data:
            continue
        sizes, vals = lat_data[label]
        # Drop size 0 for log x-axis
        sv = [(s, v) for s, v in zip(sizes, vals) if s > 0]
        sizes = [s for s, _ in sv]
        vals = [v for _, v in sv]
        ax.plot(sizes, vals, marker=markers[idx % len(markers)],
                color=f"C{idx}", linewidth=1.3, markersize=6,
                alpha=0.85, label=label)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
    ax.set_xlabel("Message Size (Bytes)", fontsize=20)
    ax.set_ylabel("Latency (us)", fontsize=20)
    ax.set_title("(b) osu_get_latency", fontsize=22)
    ax.grid(True, alpha=0.3, which="both")
    ax.tick_params(labelsize=18)

    # Single shared legend, one horizontal row centered at the top
    handles = [Line2D([0], [0], color=f"C{i}", marker=markers[i % len(markers)],
                      linewidth=1.3, markersize=8, label=label)
               for i, (cc, label) in enumerate(CC_TYPES)]
    fig.legend(handles=handles, loc="upper center", ncol=len(CC_TYPES),
               fontsize=18, frameon=True, edgecolor="gray", bbox_to_anchor=(0.5, 1.0))

    fig.tight_layout(rect=[0, 0, 1, 0.90], h_pad=3.0)

    out_png = os.path.join(OUTPUT_DIR, "intelmpi_get.png")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_png}")

    out_pdf = os.path.join(OUTPUT_DIR, "intelmpi_get.pdf")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    plot()
