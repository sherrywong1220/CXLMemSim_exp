#!/usr/bin/env python3
"""
Plot osu_allgather and osu_allreduce latency from results_qemu (mpi_cxl, nocc).
One subfigure per node count, lines per total process count.
Uses only the latest timestamp for each config.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import re
import glob
from collections import defaultdict


def human_bytes(x, _pos=None):
    if x <= 0:
        return "0"
    if x >= 1024 * 1024:
        v = x / (1024 * 1024)
        return f"{v:g}M"
    if x >= 1024:
        v = x / 1024
        return f"{v:g}K"
    return f"{int(x)}"

BENCHES = ["osu_allgather", "osu_allreduce"]
RESULTS_BASE = os.path.join(os.path.dirname(__file__), "../../results_qemu")
OUTPUT_DIR = os.path.dirname(__file__)


def parse_output_log(filepath):
    """Parse OSU collective output.log -> (sizes, latencies_us)."""
    sizes, lats = [], []
    with open(filepath, "r") as f:
        for line in f:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            if not clean or clean.startswith("#") or clean.startswith("["):
                continue
            parts = clean.split()
            if len(parts) >= 2:
                try:
                    size = int(parts[0])
                    lat = float(parts[1])
                except ValueError:
                    continue
                # Sanity: OSU sizes are powers of two, drop obvious garbage
                if size <= 0 or size > (1 << 30):
                    continue
                sizes.append(size)
                lats.append(lat)
    # If duplicate sizes (interleaved logs), keep first occurrence
    seen = {}
    for s, l in zip(sizes, lats):
        if s not in seen:
            seen[s] = l
    out = sorted(seen.items())
    return [s for s, _ in out], [l for _, l in out]


def discover_data(bench):
    base = os.path.join(RESULTS_BASE, bench, "mpi_cxl", "nocc")
    pattern = os.path.join(base, "*", f"{bench}_mpi_cxl_node*", "*", "output.log")
    all_files = sorted(glob.glob(pattern))

    # data[node_count][nprocs] = (sizes, lats)
    data = defaultdict(dict)
    latest = {}  # (node, nprocs) -> filepath
    for f in all_files:
        parts = f.split(os.sep)
        nprocs = None
        node = None
        for i, p in enumerate(parts):
            if p == "nocc" and i + 1 < len(parts):
                try:
                    nprocs = int(parts[i + 1])
                except ValueError:
                    pass
            m = re.search(r"node(\d+)", p)
            if m and bench in p:
                node = int(m.group(1))
        if node and nprocs:
            latest[(node, nprocs)] = f  # sorted -> latest wins

    for (node, nprocs), filepath in sorted(latest.items()):
        sizes, lats = parse_output_log(filepath)
        if sizes:
            data[node][nprocs] = (sizes, lats)
    return dict(data)


def plot_bench(bench, data, pretty_name):
    nodes = sorted(data.keys())
    n_nodes = len(nodes)
    if n_nodes == 0:
        print(f"[{bench}] no data, skipping")
        return

    fig, axes = plt.subplots(1, n_nodes, figsize=(5 * n_nodes, 2.8), sharey=True)
    if n_nodes == 1:
        axes = [axes]

    markers = ["o", "s", "^", "D", "v", "p", "h", "*"]

    for ax, node in zip(axes, nodes):
        procs_sorted = sorted(data[node].keys())
        for idx, np_ in enumerate(procs_sorted):
            sizes, lats = data[node][np_]
            ax.plot(
                sizes, lats,
                marker=markers[idx % len(markers)], color=f"C{idx}",
                linewidth=1.2, markersize=7, alpha=0.85,
                label=f"{np_} procs",
            )
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
        ax.set_xlabel("Message Size (Bytes)", fontsize=11)
        ax.set_title(f"{node} Node{'s' if node > 1 else ''}", fontsize=12)
        ax.legend(fontsize=8, loc="upper left")
        ax.grid(True, alpha=0.3, which="both")
        ax.tick_params(labelsize=9)

    axes[0].set_ylabel("Latency (us)", fontsize=11)
    fig.tight_layout()

    stem = f"{bench}_multi_node"
    out_png = os.path.join(OUTPUT_DIR, f"{stem}.png")
    out_pdf = os.path.join(OUTPUT_DIR, f"{stem}.pdf")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out_png}")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    pretty = {"osu_allgather": "Allgather", "osu_allreduce": "Allreduce"}
    for bench in BENCHES:
        data = discover_data(bench)
        for node in sorted(data.keys()):
            procs = sorted(data[node].keys())
            print(f"[{bench}] Node {node}: procs={procs}")
        plot_bench(bench, data, pretty[bench])
