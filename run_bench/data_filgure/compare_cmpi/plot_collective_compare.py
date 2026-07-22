#!/usr/bin/env python3
"""
Collective-communication comparison: MEMU (OpenMPI + CXL shim) vs cMPI
(MPICH + in-library CXL_SHM).

One figure, three panels: Allgather, Allreduce, Alltoall.
Each panel plots Avg Latency (us, log) vs Message Size (bytes, log) at a
fixed process count (default 16 -- the largest count cMPI survives; it fails
to initialize at 32). Data are the raw OSU logs collected on optane03 in
run_bench/results_collective_qemuless_vs_openmpi_vs_cmpi_20260620_raw.
"""

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import re
import glob

RESULTS_BASE = os.path.join(
    os.path.dirname(__file__),
    "../../results_collective_qemuless_vs_openmpi_vs_cmpi_20260620_raw",
)
OUTPUT_DIR = os.path.dirname(__file__)

NP = 16  # process count shown in the figure
BENCHES = ["osu_allgather", "osu_allreduce", "osu_alltoall"]
PRETTY = {"osu_allgather": "Allgather", "osu_allreduce": "Allreduce",
          "osu_alltoall": "Alltoall"}

# (config dir, cc dir, label, color, marker, linestyle, z, linewidth)
# MEMU uses cc_clflushopt_clflushopt: the shim flushes with the same
# clflushopt instruction cMPI's cxl_shm.c data path uses, so the comparison
# is apples-to-apples on cache-control work (see gen_collective_qemuless_
# clflushopt_node1.sh).
SERIES = [
    ("cmpi",             "nocc", "cMPI (MPICH+CXL_SHM)", "#c1272d", "o", "-",  3, 1.8),
    ("mpi_cxl_qemuless", "cc_clflushopt_clflushopt", "MEMU (OpenMPI+shim)", "#0057b7", "s", "-",  4, 1.8),
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


def parse_output_log(filepath):
    """Parse an OSU collective output.log -> {size: latency_us} (first seen)."""
    out = {}
    with open(filepath, errors="ignore") as f:
        for line in f:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            m = re.match(r"^(\d+)\s+([\d.]+)\s*$", clean)
            if not m:
                continue
            size, lat = int(m.group(1)), float(m.group(2))
            if size <= 0 or size > (1 << 30):
                continue
            out.setdefault(size, lat)
    return out


def find_log(bench, config, cc, np_):
    pat = os.path.join(RESULTS_BASE, bench, config, cc, str(np_),
                       "*", "*", "output.log")
    matches = sorted(glob.glob(pat))
    return matches[-1] if matches else None


def load(bench, config, cc, np_):
    log = find_log(bench, config, cc, np_)
    if not log:
        return None
    d = parse_output_log(log)
    return d if d else None


def main():
    fig, axes = plt.subplots(1, 3, figsize=(15, 3.0), sharey=False)

    for ax, bench in zip(axes, BENCHES):
        for config, cc, label, color, marker, ls, z, lw in SERIES:
            d = load(bench, config, cc, NP)
            if not d:
                print(f"[warn] no data: {bench} {config}/{cc} np={NP}")
                continue
            sizes = sorted(d.keys())
            lats = [d[s] for s in sizes]
            ax.plot(sizes, lats, marker=marker, color=color, linestyle=ls,
                    linewidth=lw, markersize=5.5, alpha=0.9, zorder=z,
                    label=label)
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
        ax.set_xlabel("Message Size (Bytes)", fontsize=19)
        ax.set_title(PRETTY[bench], fontsize=21)
        ax.grid(True, alpha=0.3, which="both")
        ax.tick_params(labelsize=17)

    axes[0].set_ylabel(f"Avg Latency (us), {NP} procs", fontsize=19)
    # single shared legend across the top
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=19,
               frameon=True, edgecolor="gray", bbox_to_anchor=(0.5, 1.14))
    fig.tight_layout()

    stem = "collective_compare_cmpi"
    out_png = os.path.join(OUTPUT_DIR, f"{stem}.png")
    out_pdf = os.path.join(OUTPUT_DIR, f"{stem}.pdf")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    fig.savefig(out_pdf, bbox_inches="tight")
    print(f"Saved: {out_png}")
    print(f"Saved: {out_pdf}")


if __name__ == "__main__":
    main()
