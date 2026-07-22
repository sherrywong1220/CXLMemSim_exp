#!/usr/bin/env python3
"""
Paper figure for the cross-application CC-policy preference study.

Heatmap: rows = application operating points, columns = the 7 flush policies
(nocc separated as the no-coherence reference), cell value = performance
normalized to the best coherent policy for that row (1.00 = row best; larger
= slower). The best coherent policy per row is marked with a star.

Input:  ../../data_anal/app_cc_pref_matrix.csv  (from analyze_app_cc_pref.py)
Output: app_cc_pref_heatmap.pdf
"""
import csv
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams["pdf.fonttype"] = 42
matplotlib.rcParams["ps.fonttype"] = 42

HERE = os.path.dirname(os.path.abspath(__file__))
MATRIX_CSV = os.path.join(HERE, "../../data_anal/app_cc_pref_matrix.csv")
OUT_PDF = os.path.join(HERE, "app_cc_pref_heatmap.pdf")

CC_ORDER = ["nocc", "clwb+cf", "clwb+cfo", "cf+cf", "cf+cfo", "cfo+cf", "cfo+cfo"]
CC_TEX = ["nocc", "clwb+\nclflush", "clwb+\nclflushopt", "clflush+\nclflush",
          "clflush+\nclflushopt", "clflushopt+\nclflush", "clflushopt+\nclflushopt"]

ROW_LABELS = {
    "put_lat_128B": "RMA Put lat. (128 B)",
    "put_lat_16K": "RMA Put lat. (16 KiB)",
    "put_bw_32K": "RMA Put bw. (32 KiB)",
    "put_bw_1M": "RMA Put bw. (1 MiB)",
    "get_lat_2K": "RMA Get lat. (2 KiB)",
    "get_lat_1M": "RMA Get lat. (1 MiB)",
    "get_bw_256K": "RMA Get bw. (256 KiB)",
    "allgather_256B": "Allgather (256 B, 16p)",
    "allgather_512B": "Allgather (512 B, 16p)",
    "allgather_4K": "Allgather (4 KiB, 16p)",
    "alltoall_4K": "Alltoall (4 KiB, 16p)",
    # "allreduce_ctrl": "Allreduce",  # hidden for now
    "stencil_9p": "Stencil RMA (9p)",
    "stencil_16p": "Stencil RMA (16p)",
    "stencil_25p": "Stencil RMA (25p)",
    "graph500_bfs": "Graph500 BFS (16p)",
    "npb_is": "NPB IS.D (16p)",
    "lulesh_fom": "LULESH (8p)",
    "lulesh27_fom": "LULESH (27p)",
}
ROW_ORDER = list(ROW_LABELS)


def main():
    rows = {}
    with open(MATRIX_CSV) as fh:
        for r in csv.DictReader(fh):
            rows[r["point"]] = r

    present = [p for p in ROW_ORDER if p in rows]
    data = np.full((len(present), len(CC_ORDER)), np.nan)
    best, sensitive = [], []
    for i, p in enumerate(present):
        for j, cc in enumerate(CC_ORDER):
            v = rows[p].get(cc, "")
            if v:
                data[i, j] = float(v)
        best.append(rows[p]["best_coherent"])
        sensitive.append(rows[p].get("sensitive", "yes") == "yes")

    fig, ax = plt.subplots(figsize=(7.0, 0.42 * len(present) + 1.6))
    # color scale over coherent columns only; cap for readability
    disp = np.array(data)
    vmax = min(np.nanmax(disp[:, 1:]), 3.5)
    im = ax.imshow(disp[:, 1:], cmap="YlOrRd", vmin=1.0, vmax=vmax, aspect="auto")

    # nocc column drawn as text-only reference on the left of the heatmap
    for i, p in enumerate(present):
        v = data[i, 0]
        ax.text(-0.62, i, f"{v:.2f}" if np.isfinite(v) else "--",
                ha="center", va="center", fontsize=8, color="#555555")

    for i, p in enumerate(present):
        for j, cc in enumerate(CC_ORDER[1:], start=1):
            v = data[i, j]
            if not np.isfinite(v):
                continue
            star = "★" if (cc == best[i] and sensitive[i]) else ""
            frac = (min(v, vmax) - 1.0) / (vmax - 1.0) if vmax > 1 else 0
            color = "white" if frac > 0.6 else "black"
            ax.text(j - 1, i, f"{star}{v:.2f}", ha="center", va="center",
                    fontsize=8, color=color,
                    fontweight="bold" if star else "normal")

    ax.set_xticks(range(len(CC_ORDER) - 1))
    ax.set_xticklabels(CC_TEX[1:], fontsize=8)
    ax.set_yticks(range(len(present)))
    ylabels = [ROW_LABELS[p] + ("" if s else " $^\\dagger$")
               for p, s in zip(present, sensitive)]
    ax.set_yticklabels(ylabels, fontsize=9)
    ax.text(-0.62, -0.9, "nocc\n(ref)", ha="center", va="center", fontsize=8,
            transform=ax.transData)
    ax.set_xlim(-1.1, len(CC_ORDER) - 1.5)

    cbar = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    cbar.set_label("Slowdown vs. best coherent policy", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.tight_layout()
    fig.savefig(OUT_PDF, bbox_inches="tight")
    print(f"Wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
