#!/usr/bin/env python3
"""
Allreduce four-stack comparison (-T mpi_float rerun of 2026-07-19):
CXLMemSim qemuless nocc / qemuless clflushopt / cMPI (MPICH-CXL) / Open MPI native.

Reads osu_collective_long.csv (parse_osu_collective.py). One panel per process
count; x = message size (log2), y = avg latency us (log). The 4096B line marks
the shim's CXL_DIRECT_MAX_BYTES gate: below it the qemuless series use the CXL
collective path, above it they pass through to Open MPI.

Output: data_anal/allreduce_compare_4stack.png / .pdf
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "osu_collective_long.csv")

# label-in-CSV -> (display, color, linestyle, marker)
SERIES = {
    "qemuless_nocc":       ("qemuless nocc",       "#2a78d6", "-",  "o"),
    "qemuless_clflushopt": ("qemuless clflushopt", "#008300", "-",  "s"),
    "cmpi":                ("cMPI (MPICH-CXL)",    "#e87ba4", "--", "x"),
    "openmpi_native":      ("Open MPI native",     "#eda100", "--", "^"),
}
CXL_GATE = 4096

df = pd.read_csv(CSV)
df = df[(df["benchmark"] == "osu_allreduce") & (df["series"].isin(SERIES))]
if df.empty:
    raise SystemExit("no osu_allreduce rows for the four series — run parse first")

nps = sorted(df["num_process"].unique())
fig, axes = plt.subplots(1, len(nps), figsize=(3.2 * len(nps), 3.6),
                         sharey=True, sharex=True)
if len(nps) == 1:
    axes = [axes]

for ax, n in zip(axes, nps):
    sub = df[df["num_process"] == n]
    for key, (label, color, ls, mk) in SERIES.items():
        d = sub[sub["series"] == key].sort_values("msg_size")
        if d.empty:
            continue
        ax.plot(d["msg_size"], d["avg_latency_us"], color=color, ls=ls,
                marker=mk, ms=4, lw=1.6, alpha=0.95)
    ax.axvline(CXL_GATE, color="0.45", ls=":", lw=1)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_title(f"np = {n}", fontsize=11)
    ax.set_xlabel("Message size (bytes)")
    ax.grid(True, which="both", ls=":", alpha=0.35)
axes[0].set_ylabel("Avg latency (µs)")
# gate annotation on the first panel only
axes[0].annotate("CXL direct ≤ 4KB", xy=(CXL_GATE, axes[0].get_ylim()[1]),
                 xytext=(-4, -2), textcoords="offset points",
                 ha="right", va="top", fontsize=8, color="0.35", rotation=90)

handles = [mlines.Line2D([], [], color=c, ls=ls, marker=mk, ms=5, lw=1.8,
                         label=lbl)
           for (lbl, c, ls, mk) in SERIES.values()]
fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False,
           bbox_to_anchor=(0.5, 1.06))
fig.suptitle("OSU Allreduce latency (MPI_FLOAT), single node",
             y=1.14, fontsize=13)
fig.tight_layout()

for ext in ("png", "pdf"):
    out = os.path.join(HERE, f"allreduce_compare_4stack.{ext}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")
