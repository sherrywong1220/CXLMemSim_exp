#!/usr/bin/env python3
"""
Plot the allreduce algorithm comparison: flat vs tree vs Rabenseifner on the
qemuless CXL path, uniform cc_clflushopt_clflushopt, MPI_FLOAT, gate 256KB.
Reads aralgo_long.csv (parse_aralgo.py). One panel per process count.

Output: data_anal/allreduce_algo_compare.png / .pdf
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "aralgo_long.csv"))

# algo -> (display, color, marker)   [categorical slots, CVD-validated]
ALGOS = {
    "flat": ("flat (all-read + 2 barriers)", "#2a78d6", "o"),
    "tree": ("binomial tree",                "#008300", "s"),
    "rab":  ("Rabenseifner",                 "#e87ba4", "^"),
}

nps = sorted(df["num_process"].unique())
fig, axes = plt.subplots(1, len(nps), figsize=(5.2 * len(nps), 4.0),
                         sharey=True, sharex=True)
if len(nps) == 1:
    axes = [axes]

for ax, n in zip(axes, nps):
    sub = df[df["num_process"] == n]
    for key, (label, color, mk) in ALGOS.items():
        d = sub[sub["algo"] == key].sort_values("msg_size")
        if d.empty:
            continue
        ax.plot(d["msg_size"], d["median_latency_us"], color=color,
                marker=mk, ms=4.5, lw=1.7, alpha=0.95)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_title(f"np = {n}", fontsize=12)
    ax.set_xlabel("Message size (bytes)")
    ax.grid(True, which="both", ls=":", alpha=0.35)
axes[0].set_ylabel("Median latency (µs)")

handles = [mlines.Line2D([], [], color=c, marker=mk, ms=6, lw=1.8, label=lbl)
           for (lbl, c, mk) in ALGOS.values()]
fig.legend(handles=handles, loc="upper center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, 1.04))
fig.suptitle("CXL allreduce algorithms (qemuless, clflushopt+clflushopt, "
             "MPI_FLOAT, gate 256KB)", y=1.12, fontsize=13)
fig.tight_layout()

for ext in ("png", "pdf"):
    out = os.path.join(HERE, f"allreduce_algo_compare.{ext}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")

# quick speedup table vs flat
piv = df.pivot_table(index=["num_process", "msg_size"], columns="algo",
                     values="median_latency_us")
if {"flat", "tree", "rab"} <= set(piv.columns):
    piv["tree_speedup"] = (piv["flat"] / piv["tree"]).round(2)
    piv["rab_speedup"] = (piv["flat"] / piv["rab"]).round(2)
    print(piv[["flat", "tree", "rab", "tree_speedup",
               "rab_speedup"]].to_string())
