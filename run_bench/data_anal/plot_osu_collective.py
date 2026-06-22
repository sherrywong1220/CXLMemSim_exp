#!/usr/bin/env python3
"""
Plot OSU collective latency: mpi_cxl_qemuless vs cMPI for allgather / allreduce /
alltoall. Reads osu_collective_long.csv (produced by parse_osu_collective.py).

For a fair head-to-head, only the process counts present in BOTH stacks are
plotted (cMPI currently maxes at np=16). Latency vs message size, log-log, one
subplot per benchmark; colour = num_process, line style = MPI stack.

Output: data_anal/osu_collective_qemuless_vs_cmpi.png (+ .pdf)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(HERE, "osu_collective_long.csv")

NETS = {                      # net_config -> (label, linestyle, marker)
    "mpi_cxl_qemuless": ("CXLMemSim qemuless", "-",  "o"),
    "cmpi":             ("cMPI",               "--", "x"),
}
BENCHES = ["osu_allgather", "osu_allreduce", "osu_alltoall"]
TITLES = {"osu_allgather": "Allgather",
          "osu_allreduce": "Allreduce",
          "osu_alltoall": "Alltoall"}

df = pd.read_csv(CSV)
df = df[df["net_config"].isin(NETS)]

# Common process counts present for BOTH stacks (per benchmark intersection -> global).
common_np = None
for b in BENCHES:
    sub = df[df["benchmark"] == b]
    nps = None
    for net in NETS:
        s = set(sub[sub["net_config"] == net]["num_process"].unique())
        nps = s if nps is None else (nps & s)
    common_np = nps if common_np is None else (common_np & nps)
common_np = sorted(common_np or [])
print(f"plotting np = {common_np}")

cmap = plt.get_cmap("viridis")
np_color = {n: cmap(i / max(1, len(common_np) - 1))
            for i, n in enumerate(common_np)}

fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharex=True)
for ax, bench in zip(axes, BENCHES):
    sub = df[(df["benchmark"] == bench) & (df["num_process"].isin(common_np))]
    for net, (label, ls, mk) in NETS.items():
        for n in common_np:
            d = sub[(sub["net_config"] == net) & (sub["num_process"] == n)]
            d = d.sort_values("msg_size")
            if d.empty:
                continue
            ax.plot(d["msg_size"], d["avg_latency_us"],
                    ls=ls, marker=mk, ms=4, lw=1.5,
                    color=np_color[n], alpha=0.9)
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_title(TITLES[bench])
    ax.set_xlabel("Message size (bytes)")
    ax.grid(True, which="both", ls=":", alpha=0.4)
axes[0].set_ylabel("Avg latency (us)")

# Legend: colour = np, style = stack.
np_handles = [mlines.Line2D([], [], color=np_color[n], lw=2, label=f"np={n}")
              for n in common_np]
net_handles = [mlines.Line2D([], [], color="black", ls=ls, marker=mk, label=label)
               for (label, ls, mk) in NETS.values()]
leg1 = fig.legend(handles=np_handles, title="processes",
                  loc="upper center", bbox_to_anchor=(0.40, 1.02), ncol=len(common_np))
fig.legend(handles=net_handles, title="MPI stack",
           loc="upper center", bbox_to_anchor=(0.78, 1.02), ncol=2)
fig.add_artist(leg1)
fig.suptitle("OSU collective latency: CXLMemSim qemuless vs cMPI (single node, nocc)",
             y=1.08, fontsize=13)
fig.tight_layout()

for ext in ("png", "pdf"):
    out = os.path.join(HERE, f"osu_collective_qemuless_vs_cmpi.{ext}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"wrote {out}")
