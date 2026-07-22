#!/usr/bin/env python3
"""
Cross-application CC-policy preference analysis.

Consumes app_cc_pref_median.csv (from parse_app_cc_pref.py) and reduces each
benchmark to one or more *application operating points*. Each point fixes ONE
message size (size_lo == size_hi; a band would average away the winner flips
this figure exists to show), so the scalar per cc_type is simply the cross-rep
median at that size. Sizes are chosen where the per-size winner analysis shows
a policy-sensitive spread, and jointly so that every coherent policy wins
somewhere:

  put_lat_128B    osu_put_latency  2p  latency at 128 B      lower  clwb+cf
  put_lat_16K     osu_put_latency  2p  latency at 16 KiB     lower  cfo+cfo
  put_bw_32K      osu_put_bw       2p  bandwidth at 32 KiB   higher cfo+cfo
  put_bw_1M       osu_put_bw       2p  bandwidth at 1 MiB    higher clwb+cf
  get_lat_2K      osu_get_latency  2p  latency at 2 KiB      lower  clwb+cfo
  get_lat_1M      osu_get_latency  2p  latency at 1 MiB      lower  cfo+cfo
  get_bw_256K     osu_get_bw       2p  bandwidth at 256 KiB  higher clwb+cfo
  allgather_256B  osu_allgather   16p  latency at 256 B      lower  cf+cf
  allgather_512B  osu_allgather   16p  latency at 512 B      lower  cfo+cf
  allgather_4K    osu_allgather   16p  latency at 4 KiB      lower  cfo+cfo
  alltoall_4K     osu_alltoall    16p  latency at 4 KiB      lower  cf+cfo
  allreduce_ctrl  osu_allreduce   16p  latency at 2 KiB      lower
                                       (hidden from the paper heatmap)
  lulesh_fom      lulesh_baseline  8p  FOM                   higher

For every operating point it reports each cc_type's value, the slowdown vs the
best *coherent* policy (nocc excluded: it is only correct single-node), the
best coherent policy, and the worst-case penalty of picking another point's
best policy here (the "misconfiguration cost" that justifies per-app tuning).

Outputs:
  app_cc_pref_points.csv   tidy per-point per-cc values + normalized
  app_cc_pref_matrix.csv   rows = operating points, cols = cc types,
                           cells = value normalized to best coherent (1.00 = best)
  stdout: human-readable preference table + cross-application penalty matrix
"""
import csv
import math
import os
import statistics
from collections import defaultdict

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MED_CSV = os.path.join(OUT_DIR, "app_cc_pref_median.csv")
LONG_CSV = os.path.join(OUT_DIR, "app_cc_pref_long.csv")

COHERENT = [
    "cc_clwb_clflush",
    "cc_clwb_clflushopt",
    "cc_clflush_clflush",
    "cc_clflush_clflushopt",
    "cc_clflushopt_clflush",
    "cc_clflushopt_clflushopt",
]
ALL_CC = ["nocc"] + COHERENT

SHORT = {
    "nocc": "nocc",
    "cc_clwb_clflush": "clwb+cf",
    "cc_clwb_clflushopt": "clwb+cfo",
    "cc_clflush_clflush": "cf+cf",
    "cc_clflush_clflushopt": "cf+cfo",
    "cc_clflushopt_clflush": "cfo+cf",
    "cc_clflushopt_clflushopt": "cfo+cfo",
}

# (point, benchmark, np, size_lo, size_hi, direction)
POINTS = [
    ("put_lat_128B", "osu_put_latency", "2", 128, 128, "lower"),
    ("put_lat_16K", "osu_put_latency", "2", 16384, 16384, "lower"),
    ("put_bw_32K", "osu_put_bw", "2", 32768, 32768, "higher"),
    ("put_bw_1M", "osu_put_bw", "2", 1048576, 1048576, "higher"),
    ("get_lat_2K", "osu_get_latency", "2", 2048, 2048, "lower"),
    ("get_lat_1M", "osu_get_latency", "2", 1048576, 1048576, "lower"),
    ("get_bw_256K", "osu_get_bw", "2", 262144, 262144, "higher"),
    ("allgather_256B", "osu_allgather", "16", 256, 256, "lower"),
    ("allgather_512B", "osu_allgather", "16", 512, 512, "lower"),
    ("allgather_4K", "osu_allgather", "16", 4096, 4096, "lower"),
    ("alltoall_4K", "osu_alltoall", "16", 4096, 4096, "lower"),
    ("allreduce_ctrl", "osu_allreduce", "16", 2048, 2048, "lower"),
    ("lulesh_fom", "lulesh_baseline", "8", 0, 0, "higher"),
    ("lulesh27_fom", "lulesh_baseline", "27", 0, 0, "higher"),
    ("npb_is", "npb_is_d", "16", 0, 0, "lower"),
    ("graph500_bfs", "graph500_simple_s20", "16", 0, 0, "lower"),
    ("stencil_9p", "stencil_rma_ompi_1000", "9", 0, 0, "lower"),
    ("stencil_16p", "stencil_rma_ompi_1000", "16", 0, 0, "lower"),
    ("stencil_25p", "stencil_rma_ompi_1000", "25", 0, 0, "lower"),
    ("stencil_36p", "stencil_rma_ompi_1000", "36", 0, 0, "lower"),
]


def geomean(vals):
    return math.exp(sum(math.log(v) for v in vals) / len(vals))


def main():
    data = defaultdict(list)  # (bench, cc, np) -> [(size, value)]
    with open(MED_CSV) as fh:
        for r in csv.DictReader(fh):
            data[(r["benchmark"], r["cc_type"], r["num_process"])].append(
                (int(r["msg_size"]), float(r["value"])))

    point_vals = {}  # (point, cc) -> scalar
    for point, bench, np_, lo, hi, direction in POINTS:
        for cc in ALL_CC:
            rows = [v for s, v in data.get((bench, cc, np_), []) if lo <= s <= hi]
            if rows:
                point_vals[(point, cc)] = geomean(rows)

    # Noise floor per point: per-rep operating-point scalars (geomean within a
    # timestamp), then across-rep relative half-spread, median over cc types.
    rep_vals = defaultdict(lambda: defaultdict(list))  # (bench,cc,np) -> ts -> [v]
    with open(LONG_CSV) as fh:
        for r in csv.DictReader(fh):
            rep_vals[(r["benchmark"], r["cc_type"], r["num_process"])][
                r["timestamp"]].append((int(r["msg_size"]), float(r["value"])))
    noise = {}  # point -> median over cc of (max-min)/(2*median) across reps
    for point, bench, np_, lo, hi, direction in POINTS:
        spreads = []
        for cc in ALL_CC:
            scalars = []
            for ts, rows in rep_vals.get((bench, cc, np_), {}).items():
                vals = [v for s, v in rows if lo <= s <= hi]
                if vals:
                    scalars.append(geomean(vals))
            if len(scalars) >= 2:
                med = statistics.median(scalars)
                if med > 0:
                    spreads.append((max(scalars) - min(scalars)) / (2 * med))
        if spreads:
            noise[point] = statistics.median(spreads)

    tidy = []
    matrix_rows = []
    print()
    print(f"{'operating point':16s} " +
          " ".join(f"{SHORT[c]:>9s}" for c in ALL_CC) +
          "   best-coh  spread  noise  sensitive?")
    for point, bench, np_, lo, hi, direction in POINTS:
        vals = {c: point_vals.get((point, c)) for c in ALL_CC}
        coh = {c: v for c, v in vals.items() if c in COHERENT and v is not None}
        if not coh:
            print(f"{point:16s}  (no data yet)")
            continue
        if direction == "lower":
            best_cc = min(coh, key=coh.get)
            worst_cc = max(coh, key=coh.get)
            norm = {c: (v / coh[best_cc] if v is not None else None)
                    for c, v in vals.items()}
        else:
            best_cc = max(coh, key=coh.get)
            worst_cc = min(coh, key=coh.get)
            norm = {c: (coh[best_cc] / v if v is not None else None)
                    for c, v in vals.items()}
        spread = norm[worst_cc]
        cells = " ".join(
            f"{norm[c]:9.3f}" if norm[c] is not None else f"{'--':>9s}"
            for c in ALL_CC)
        nz = noise.get(point)
        nz_s = f"{nz*100:4.1f}%" if nz is not None else "  --"
        sens = "yes" if (nz is not None and (spread - 1) > 3 * nz) else "no"
        print(f"{point:16s} {cells}   {SHORT[best_cc]:>8s}  {spread:5.2f}x  {nz_s}  {sens}")
        for c in ALL_CC:
            if vals[c] is not None:
                tidy.append(dict(point=point, benchmark=bench, num_process=np_,
                                 cc_type=c, cc_short=SHORT[c], value=vals[c],
                                 norm_vs_best_coherent=norm[c],
                                 direction=direction,
                                 best_coherent=SHORT[best_cc]))
        matrix_rows.append([point] + [
            f"{norm[c]:.4f}" if norm[c] is not None else "" for c in ALL_CC] +
            [SHORT[best_cc], f"{spread:.4f}",
             f"{nz:.4f}" if nz is not None else "", sens])

    with open(os.path.join(OUT_DIR, "app_cc_pref_points.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "point", "benchmark", "num_process", "cc_type", "cc_short",
            "value", "norm_vs_best_coherent", "direction", "best_coherent"])
        w.writeheader()
        w.writerows(tidy)
    with open(os.path.join(OUT_DIR, "app_cc_pref_matrix.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["point"] + [SHORT[c] for c in ALL_CC] +
                   ["best_coherent", "spread", "noise", "sensitive"])
        w.writerows(matrix_rows)

    # Cross-application penalty: apply point A's best coherent policy to point B
    bestof = {row[0]: row[1 + len(ALL_CC)] for row in matrix_rows}
    inv_short = {v: k for k, v in SHORT.items()}
    pts = [r[0] for r in matrix_rows]
    print("\nMisconfiguration penalty (% slower than B's best) when running B")
    print("under the best coherent policy of A:")
    print(f"{'A \\ B':16s} " + " ".join(f"{p[:9]:>10s}" for p in pts))
    norm_lookup = {(t["point"], t["cc_type"]): t["norm_vs_best_coherent"]
                   for t in tidy}
    for a in pts:
        cc_a = inv_short[bestof[a]]
        cells = []
        for b in pts:
            n = norm_lookup.get((b, cc_a))
            cells.append(f"{(n - 1) * 100:10.1f}" if n is not None else f"{'--':>10s}")
        print(f"{a:16s} " + " ".join(cells))

    print("\nWrote app_cc_pref_points.csv and app_cc_pref_matrix.csv")


if __name__ == "__main__":
    main()
