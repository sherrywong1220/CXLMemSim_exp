#!/usr/bin/env python3
"""
Analyze the allreduce algorithm x cc-policy matrix (aralgo_cc_long.csv).

Per (algo, np, size-band):
  - geomean latency ratio of each cc policy to the band's best policy
  - best / worst policy and the misconfiguration penalty (worst/best)
  - cross-algorithm misconfiguration: cost of running algo B with algo A's
    best policy
Also compares policy *sensitivity* across algorithms (hypothesis: tree/rab
cut per-rank flush counts O(N)->O(log N), so sensitivity shrinks).

Outputs:
  aralgo_cc_pref.csv                  tidy per-(algo,np,band,cc) ratios
  aralgo_cc_heatmap.{png,pdf}         policy-preference heatmap
  stdout: summary tables for the paper
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, "aralgo_cc_long.csv"))
# The paper reports 16 processes only; drop other process counts.
df = df[df["num_process"] == 16]

BANDS = [("small<=1K", 0, 1024), ("mid2-32K", 2048, 32768),
         ("large64-256K", 65536, 262144)]
ALGOS = ["flat", "tree", "rab"]
CCS = ["nocc", "cc_clwb_clflush", "cc_clwb_clflushopt", "cc_clflush_clflush",
       "cc_clflush_clflushopt", "cc_clflushopt_clflush",
       "cc_clflushopt_clflushopt"]
CC_SHORT = {"nocc": "nocc", "cc_clwb_clflush": "clwb+cf",
            "cc_clwb_clflushopt": "clwb+cfo", "cc_clflush_clflush": "cf+cf",
            "cc_clflush_clflushopt": "cf+cfo",
            "cc_clflushopt_clflush": "cfo+cf",
            "cc_clflushopt_clflushopt": "cfo+cfo"}


def geomean(x):
    x = np.asarray(x, dtype=float)
    return float(np.exp(np.log(x).mean())) if len(x) else float("nan")


def band_of(size):
    for name, lo, hi in BANDS:
        if lo <= size <= hi:
            return name
    return None


df["band"] = df["msg_size"].map(band_of)
df = df[df["band"].notna()]

rows = []
for (algo, np_, band), g in df.groupby(["algo", "num_process", "band"]):
    piv = g.pivot_table(index="msg_size", columns="cc",
                        values="median_latency_us")
    piv = piv.dropna(axis=1)
    per_size_best = piv.min(axis=1)
    for cc in piv.columns:
        rows.append({"algo": algo, "num_process": np_, "band": band,
                     "cc": cc,
                     "geomean_ratio_to_best":
                         round(geomean(piv[cc] / per_size_best), 3),
                     "geomean_latency_us": round(geomean(piv[cc]), 1)})
pref = pd.DataFrame(rows)
pref.to_csv(os.path.join(HERE, "aralgo_cc_pref.csv"), index=False)

band_order = [b[0] for b in BANDS]
print("=" * 78)
print("Policy preference per (algo, np, band): best cc, worst-vs-best "
      "penalty,\nand flush-policy sensitivity excluding nocc "
      "(worst_cc/best_cc among the 6 CC types)")
print("=" * 78)
summary = []
for np_ in sorted(pref["num_process"].unique()):
    for band in band_order:
        for algo in ALGOS:
            g = pref[(pref.algo == algo) & (pref.num_process == np_) &
                     (pref.band == band)].set_index("cc")
            if g.empty:
                continue
            cc_only = g.drop(index="nocc", errors="ignore")
            best = cc_only["geomean_ratio_to_best"].idxmin()
            worst = cc_only["geomean_ratio_to_best"].idxmax()
            pen = cc_only.loc[worst, "geomean_ratio_to_best"] / \
                cc_only.loc[best, "geomean_ratio_to_best"]
            nocc_ratio = (g.loc["nocc", "geomean_ratio_to_best"]
                          if "nocc" in g.index else float("nan"))
            summary.append({"np": np_, "band": band, "algo": algo,
                            "best_cc": CC_SHORT[best],
                            "worst_cc": CC_SHORT[worst],
                            "penalty": round(pen, 2),
                            "nocc_ratio": nocc_ratio})
s = pd.DataFrame(summary)
print(s.to_string(index=False))

print()
print("=" * 78)
print("Cross-algorithm misconfiguration: latency ratio when algo runs with")
print("another algo's best policy (per np, geomean over ALL sizes, CC only)")
print("=" * 78)
for np_ in sorted(df["num_process"].unique()):
    sub = df[(df.num_process == np_) & (df.cc != "nocc")]
    piv = sub.pivot_table(index="msg_size", columns=["algo", "cc"],
                          values="median_latency_us")
    best_cc = {}
    for algo in ALGOS:
        ratios = {cc: geomean(piv[algo][cc] / piv[algo].min(axis=1))
                  for cc in piv[algo].columns}
        best_cc[algo] = min(ratios, key=ratios.get)
    mat = pd.DataFrame(index=ALGOS, columns=ALGOS, dtype=float)
    for run_algo in ALGOS:
        base = piv[run_algo][best_cc[run_algo]]
        for pol_algo in ALGOS:
            mat.loc[run_algo, pol_algo] = round(
                geomean(piv[run_algo][best_cc[pol_algo]] / base), 3)
    print(f"\nnp={np_}  (row = algo being run, col = whose best policy; "
          f"best: " +
          ", ".join(f"{a}={CC_SHORT[best_cc[a]]}" for a in ALGOS) + ")")
    print(mat.to_string())

# ---- heatmap: rows = cc, cols = algo x band, one panel per np -------------
# Ratio base = best among the 6 CC policies (nocc excluded); the nocc row
# then reads as the coherence tax (values < 1).
BAND_SHORT = {"small<=1K": "S", "mid2-32K": "M", "large64-256K": "L"}
nps = sorted(pref["num_process"].unique())
fig, axes = plt.subplots(1, len(nps), figsize=(7.2 * len(nps), 4.6))
if len(nps) == 1:
    axes = [axes]
cols = [(a, b) for b in band_order for a in ALGOS]
last_im = None
for ax, np_ in zip(axes, nps):
    m = np.full((len(CCS), len(cols)), np.nan)
    for j, (algo, band) in enumerate(cols):
        g = pref[(pref.algo == algo) & (pref.num_process == np_) &
                 (pref.band == band)].set_index("cc")
        cc_best = g.drop(index="nocc",
                         errors="ignore")["geomean_ratio_to_best"].min()
        for i, cc in enumerate(CCS):
            if cc in g.index:
                m[i, j] = g.loc[cc, "geomean_ratio_to_best"] / cc_best
    cc_rows = m[1:, :]
    vmax = float(np.nanpercentile(cc_rows, 97))
    im = ax.imshow(m, cmap="Blues", vmin=0.0, vmax=vmax, aspect="auto")
    last_im = im
    for i in range(len(CCS)):
        for j in range(len(cols)):
            if not np.isnan(m[i, j]):
                dark = m[i, j] > vmax * 0.72
                ax.text(j, i, f"{m[i, j]:.2f}", ha="center", va="center",
                        fontsize=7.5, color="white" if dark else "#1a1a19")
    ax.axhline(0.5, color="0.4", lw=0.8)  # separate nocc reference row
    for k in (1, 2):                      # separate the three size bands
        ax.axvline(k * len(ALGOS) - 0.5, color="0.4", lw=0.8)
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{a}\n{BAND_SHORT[b]}" for a, b in cols],
                       fontsize=8)
    ax.set_yticks(range(len(CCS)))
    ax.set_yticklabels([CC_SHORT[c] for c in CCS], fontsize=8.5)
    ax.set_title(f"np = {np_}", fontsize=11)
fig.suptitle("Allreduce: latency ratio to the best CC policy per "
             "(algorithm, size band)\n(geomean; S ≤ 1KB, M 2-32KB, "
             "L 64-256KB; nocc row = no-coherence floor)",
             fontsize=11.5, y=1.06)
fig.colorbar(last_im, ax=axes, shrink=0.8, label="ratio to best CC policy")
for ext in ("png", "pdf"):
    out = os.path.join(HERE, f"aralgo_cc_heatmap.{ext}")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nwrote {out}")
