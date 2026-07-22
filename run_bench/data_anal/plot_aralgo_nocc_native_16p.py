#!/usr/bin/env python3
"""
Allreduce algorithm comparison for the paper (fig:allreduce-algo), redesigned
2026-07-21: flat vs tree vs Rabenseifner on the qemuless CXL path under the
nocc build, plus plain Open MPI (no shim) as the host-library reference.
Single panel at 16 processes, MPI_FLOAT, gate 256KB (CXL path covers the
sweep; verified by shim counters in every log).

Pairing rationale: plain Open MPI issues no cache flushes, so the nocc shim is
the matched-cache-control-work comparison, parallel to cfo+cfo <-> cMPI in
fig:collective-cmpi.

MEMU data: median of 3 runs from
  osu_allreduce/mpi_cxl_qemuless/nocc/16/aralgo_{flat,tree,rab}_qemuless_node1_20260720/*/output.log
Native data: single run (OSU internal averages) from
  results_collective_qemuless_vs_openmpi_vs_cmpi_20260620_raw/osu_allreduce/openmpi_native/**/16/**/output.log
  (2026-07-19 MPI_FLOAT re-run; same datatype as the MEMU series).

Output: data_anal/allreduce_algo_compare.png / .pdf (overwrites the old
cfo+cfo two-panel figure; that one stays reproducible via plot_aralgo.py).
"""
import glob
import os
import re
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.abspath(os.path.join(HERE, "..", ".."))
ARALGO = os.path.join(EXP, "osu_allreduce", "mpi_cxl_qemuless", "nocc", "16")
RAW = os.path.join(HERE, "..",
                   "results_collective_qemuless_vs_openmpi_vs_cmpi_20260620_raw")
NP = 16


def parse_output_log(path):
    out = {}
    with open(path, errors="ignore") as f:
        for line in f:
            clean = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
            m = re.match(r"^(\d+)\s+([\d.]+)\s*$", clean)
            if m and 0 < int(m.group(1)) <= (1 << 30):
                out.setdefault(int(m.group(1)), float(m.group(2)))
    return out


def memu_median(algo):
    runs = [parse_output_log(p) for p in sorted(glob.glob(os.path.join(
        ARALGO, f"aralgo_{algo}_qemuless_node1_20260720", "*", "output.log")))]
    assert runs, f"no runs for {algo}"
    sizes = set.intersection(*[set(r) for r in runs])
    return {s: statistics.median([r[s] for r in runs]) for s in sizes}


def native():
    logs = sorted(glob.glob(os.path.join(
        RAW, "osu_allreduce", "openmpi_native", "**", str(NP), "**",
        "output.log"), recursive=True))
    assert logs, "no native log"
    return parse_output_log(logs[-1])


def human_bytes(x, _pos=None):
    if x < 1:
        return ""
    if x < 1024:
        return f"{int(x)}"
    if x < 1024 ** 2:
        v = x / 1024
        return f"{int(v)}K" if v == int(v) else f"{v:g}K"
    v = x / (1024 ** 2)
    return f"{int(v)}M" if v == int(v) else f"{v:g}M"


def main():
    series = [
        ("flat (all-read + 2 barriers)", memu_median("flat"), "#2a78d6", "o", "-"),
        ("binomial tree", memu_median("tree"), "#008300", "s", "-"),
        ("Rabenseifner", memu_median("rab"), "#e87ba4", "^", "-"),
        ("Open MPI (no shim)", native(), "#444444", "d", "--"),
    ]
    xmax = max(memu_median("flat"))  # 256 KiB: aralgo sweep end

    fig, ax = plt.subplots(figsize=(11.5, 3.0))
    for label, d, color, mk, ls in series:
        sizes = sorted(s for s in d if s <= xmax)
        ax.plot(sizes, [d[s] for s in sizes], color=color, marker=mk,
                linestyle=ls, ms=5.5, lw=1.8, alpha=0.95, label=label)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(human_bytes))
    ax.set_xlabel("Message Size (Bytes)", fontsize=17)
    ax.set_ylabel(f"Median Latency (us),\n{NP} procs", fontsize=15)
    ax.grid(True, which="both", ls=":", alpha=0.35)
    ax.tick_params(labelsize=15)
    ax.legend(fontsize=14.5, ncol=4, frameon=True, edgecolor="gray",
              loc="upper left")
    fig.tight_layout()

    for ext in ("png", "pdf"):
        out = os.path.join(HERE, f"allreduce_algo_compare.{ext}")
        fig.savefig(out, dpi=200, bbox_inches="tight")
        print(f"wrote {out}")

    # numbers for the paper text
    flat, tree, rab, nat = [dict(s[1]) for s in series]
    best = {s: min(flat[s], tree[s], rab[s]) for s in flat}
    lo = [s for s in sorted(flat) if s <= 2048]
    hi = [s for s in sorted(flat) if 4096 <= s <= xmax]
    print("tree wins <=2K, over flat: %.1f-%.1f x"
          % (min(flat[s] / tree[s] for s in lo), max(flat[s] / tree[s] for s in lo)))
    print("rab wins >=4K, over tree: %.2f-%.2f x; over flat %.1f-%.1f x"
          % (min(tree[s] / rab[s] for s in hi), max(tree[s] / rab[s] for s in hi),
             min(flat[s] / rab[s] for s in hi), max(flat[s] / rab[s] for s in hi)))
    common = [s for s in sorted(best) if s in nat]
    print("native/bestMEMU: %.2f-%.2f x"
          % (min(nat[s] / best[s] for s in common),
             max(nat[s] / best[s] for s in common)))
    print("native/flat (flat loses everywhere?): %.2f-%.2f"
          % (min(nat[s] / flat[s] for s in common),
             max(nat[s] / flat[s] for s in common)))
    print("winner flip: 64K tree/rab=%.2f  4K tree/rab=%.2f  2K tree/rab=%.2f"
          % (tree[65536] / rab[65536], tree[4096] / rab[4096],
             tree[2048] / rab[2048]))


if __name__ == "__main__":
    main()
