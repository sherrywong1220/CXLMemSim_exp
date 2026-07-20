#!/usr/bin/env python3
"""
Plot osu_get_mbw from results_qemu (mpi_cxl, nocc).
One subfigure per node count, lines per process count.
Uses only the latest timestamp for each config.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.lines import Line2D
import numpy as np
import os
import re
import glob
from collections import defaultdict


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

RESULTS_BASE = os.path.join(os.path.dirname(__file__), "../../results_qemu/osu_get_mbw/mpi_cxl/nocc")
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


def discover_data():
    """Discover all (node_count, nprocs) combos, pick latest timestamp."""
    # data[node_count][nprocs] = (sizes, bws)
    data = defaultdict(dict)
    pattern = os.path.join(RESULTS_BASE, "*", "osu_get_mbw_mpi_cxl_node*", "*", "output.log")
    all_files = sorted(glob.glob(pattern))

    # Group by (node_count, nprocs), keep latest
    latest = {}  # (node, nprocs) -> filepath
    for f in all_files:
        parts = f.split(os.sep)
        # .../nocc/{nprocs}/osu_get_mbw_mpi_cxl_node{N}_.../{timestamp}/output.log
        nprocs = None
        node = None
        for i, p in enumerate(parts):
            if p == "nocc" and i + 1 < len(parts):
                nprocs = int(parts[i + 1])
            m = re.search(r"node(\d+)", p)
            if m and "osu_get_mbw" in p:
                node = int(m.group(1))
        if node and nprocs:
            key = (node, nprocs)
            latest[key] = f  # sorted, so last wins = latest timestamp

    for (node, nprocs), filepath in sorted(latest.items()):
        sizes, bws = parse_output_log(filepath)
        if sizes:
            data[node][nprocs] = (sizes, bws)

    return dict(data)


def plot_multi_node(data):
    """Create subfigures per node count."""
    nodes = sorted(data.keys())
    n_nodes = len(nodes)

    fig, axes = plt.subplots(1, n_nodes, figsize=(5 * n_nodes, 2.8), sharey=True)
    if n_nodes == 1:
        axes = [axes]

    markers = ["o", "s", "^", "D", "v", "p", "h", "*"]

    # Global proc -> color/marker map so one shared legend is consistent across
    # panels even though each node runs a different set of process counts.
    all_procs = sorted({p for node in nodes for p in data[node].keys()})
    proc_color = {p: f'C{i}' for i, p in enumerate(all_procs)}
    proc_marker = {p: markers[i % len(markers)] for i, p in enumerate(all_procs)}

    for ax, node in zip(axes, nodes):
        procs_sorted = sorted(data[node].keys())
        for np_ in procs_sorted:
            sizes, bws = data[node][np_]
            ax.plot(
                sizes, bws,
                marker=proc_marker[np_], color=proc_color[np_],
                linewidth=1.2, markersize=7, alpha=0.85,
                label=f"{np_} procs",
            )
        ax.set_xscale("log", base=2)
        ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
        ax.set_xlabel("Message Size (Bytes)", fontsize=25)
        ax.set_title(f"Node {node}", fontsize=28)
        ax.grid(True, alpha=0.3, which="both")
        ax.tick_params(labelsize=22)

    axes[0].set_ylabel("Bandwidth (MB/s)", fontsize=20)

    # Single shared legend, one horizontal row centered at the top
    handles = [Line2D([0], [0], color=proc_color[p], marker=proc_marker[p],
                      linewidth=1.2, markersize=9, label=f"{p} procs")
               for p in all_procs]
    fig.legend(handles=handles, loc="upper center", ncol=len(all_procs),
               fontsize=22, frameon=True, edgecolor="gray", bbox_to_anchor=(0.5, 1.22))

    fig.tight_layout()

    out_png = os.path.join(OUTPUT_DIR, "get_mbw_multi_node.png")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    print(f"Saved: {out_png}")

    out_pdf = os.path.join(OUTPUT_DIR, "get_mbw_multi_node.pdf")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    data = discover_data()
    for node in sorted(data.keys()):
        procs = sorted(data[node].keys())
        print(f"Node {node}: procs={procs}")
    plot_multi_node(data)
