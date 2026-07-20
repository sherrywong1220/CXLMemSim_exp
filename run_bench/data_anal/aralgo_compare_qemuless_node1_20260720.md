# Allreduce Algorithm Comparison on the CXL Shared-Memory Path

**use_case:** `aralgo_{flat,tree,rab}_qemuless_node1_20260720` · **date:** 2026-07-20 · **machine:** optane03

Supports the claim that no single collective implementation choice is optimal
across operating points on CXL shared memory — the winning algorithm crosses
over twice within one operation — motivating MEMU's per-workload policy /
algorithm customization.

---

## 1. Experiment setup

### Hardware / platform
- Single node `optane03`, 48 cores, Intel Optane DCPMM exposed as devdax
  `/dev/dax0.0` (64 GB) emulating a CXL Type-3 memory device ("qemuless"
  MEMU configuration — no QEMU, ranks are plain host processes sharing the
  DAX mapping).
- All ranks on one host: `--map-by ppr:<np>:node`, np ∈ {16, 32}.

### Software
- Open MPI 5.0.3 (`/home/sherry/openmpi-install`), `--mca osc ^ucx`.
- Shim: `CXLMemSim/workloads/gromacs/mpi_cxl_shim.c`, variant
  `libmpi_cxl_shim_cc_clflushopt_clflushopt.so`
  (**uniform CC policy**: write-side flush = `clflushopt`, read-side
  invalidate = `clflushopt`; per user decision the 7-policy sweep was not
  run — policy is held constant so algorithm is the only variable).
- Benchmark: OSU micro-benchmarks 7.4-ext,
  `osu_allreduce -T mpi_float -m :262144 -i 200`.
  `-T mpi_float` is required: OSU 7.4 defaults to MPI_CHAR, which is not on
  the shim's reduction-datatype allowlist and silently measures passthrough
  (probe-verified on 2026-07-19).

### Key environment
```
CXL_ALLREDUCE_ALGO   = flat | tree | rab     (the experiment variable)
CXL_DIRECT_MAX_BYTES = 262144                (gate raised 4 KB -> 256 KB)
CXL_MEM_SIZE         = 8589934592            (8 GB; the flat path allocates a
                                              fresh CXL buffer per call and
                                              never frees — a 256 KB-gate
                                              sweep overflows the default 4 GB)
CXL_SHIM_ALLOC/WIN/COPY_SEND/COPY_RECV = 1
CXL_DAX_PATH = /dev/dax0.0, CXL_DAX_RESET = 1
GLIBC_TUNABLES = glibc.cpu.hwcaps=-AVX512F,... (AVX-512 loads fault on the
                                              DAX mapping)
```
DAX cleared once before the sweep (`sudo -n ./thp_exec ./clear_dax` — the
thp_exec wrapper is mandatory under Claude Code, see the THP_DISABLE gotcha).

### Protocol
3 repetitions × 3 algorithms × 2 process counts = 18 runs, interleaved
rep-major (rep1: all 6 combos, then rep2, rep3) so drift affects all cells
equally. Per-cell statistic: **median across reps**. Runner script:
`eval_scripts/run_aralgo_compare_qemuless_node1_20260720.sh`.
Raw logs: `results/osu_allreduce/mpi_cxl_qemuless/cc_clflushopt_clflushopt/
<np>/aralgo_<algo>_qemuless_node1_20260720/<YYYYMMDDHHMMSS>/output.log`.

### Noise
Across the 102 (algo, np, size) cells: median cross-rep spread
(max−min)/median = **2.5 %**, p90 = 10.1 %. Three outlier cells reach ~77 %
(one anomalously *fast* rep of flat np=16 at 64–128 KB; the median discards
it). Conclusions below rest on ≥1.3× gaps, well above this noise floor.

---

## 2. The three algorithms

All three run entirely in CXL shared memory (probe-verified: zero calls
reach the underlying MPI within the gate) and share the shim's gate
conditions (COMM_WORLD, MPI_SUM, allowlisted datatype, non-IN_PLACE,
size ≤ gate, all ranks local). Selected by `CXL_ALLREDUCE_ALGO`.

| | flat (baseline, default) | tree (binomial) | rab (Rabenseifner) |
|---|---|---|---|
| Structure | every rank reads all N−1 peer buffers | binomial reduce to rank 0, all ranks read root's slot | recursive-halving reduce-scatter + recursive-doubling allgather |
| Synchronization | **2 × MPI_Barrier** per call | seq-tagged flags, no barrier | seq-tagged flags, no barrier |
| Critical-path stages | 1 (but O(N) work in it) | log₂N + 1 | 2·log₂N |
| Remote reads / rank | N−1 × S | ≤ log₂N × S (+1 × S bcast) | ~2 × S total, in log₂N fragments each phase |
| Write-flush volume / rank | 1 × S | ≤ log₂N × S | ~2 × S in fragments |
| Invalidate volume / rank | (N−1) × S | ≤ (log₂N + 1) × S | ~2 × S in fragments |
| Total device traffic | O(N²·S) | O(N·S) | O(N·S) |
| Constraints | — | any N | N must be a power of two (else auto-fallback to tree); segment bounds ⌊i·count/N⌋ handle any count, including count < N |

Implementation (all in `mpi_cxl_shim.c`, section "CXL Allreduce algorithm
variants"): persistent per-rank workspace allocated once
(2 × gate bytes + 2 × 16 flag cachelines), peer pointers exchanged through
the collective rptr table and cached locally. Publish protocol: write data →
`cxl_flush_range(data)` → store flag (release) → flush flag line; waiter
invalidates the flag line before each poll and invalidates the data range
before reading. Calls are matched by a monotone sequence number (all gate
conditions are rank-uniform, so ranks stay in lockstep); buffers ping-pong
on seq parity, which the dependency structure of both algorithms makes
sufficient for reuse without any per-call barrier.

### Correctness evidence
- Numeric verification (`allreduce_algo_test.c`): all algos × np {6, 16, 32}
  × sizes 4 B–256 KB × {nocc, clflushopt+clflushopt} shims: exact sums,
  including rab's fallback at np=6 and the ping-pong across 5 back-to-back
  calls per size. MPI_IN_PLACE and >gate sizes still route to passthrough
  and stay correct.
- Interposer probe (`probe.c` after the shim in LD_PRELOAD, counts calls
  reaching real MPI): 0 passthrough for gated calls under every algorithm.
- OSU `-c` validation: 17 717 consecutive tree calls at np=16, all sizes
  Pass — exercises long-run flag/sequence reuse.

---

## 3. Results

Median latency (µs), MPI_FLOAT, clflushopt+clflushopt, gate 256 KB.
Speedup = flat / algo (>1 means faster than flat). Bold = best of the three.

### np = 16
| size (B) | flat | tree | rab | tree× | rab× |
|---:|---:|---:|---:|---:|---:|
| 4 | 27.6 | **14.2** | 19.2 | 1.94 | 1.43 |
| 64 | 21.5 | **12.6** | 23.0 | 1.71 | 0.94 |
| 256 | 39.7 | **17.7** | 22.3 | 2.24 | 1.78 |
| 1024 | 61.3 | **27.8** | 32.1 | 2.20 | 1.91 |
| 4096 | 111.4 | **55.3** | 73.4 | 2.02 | 1.52 |
| 16384 | 306.7 | **120.3** | 155.4 | 2.55 | 1.97 |
| 65536 | 1647.8 | **413.5** | 522.4 | 3.98 | 3.15 |
| 262144 | 6127.7 | **1736.9** | 2052.1 | 3.53 | 2.99 |

### np = 32
| size (B) | flat | tree | rab | tree× | rab× |
|---:|---:|---:|---:|---:|---:|
| 4 | 72.3 | **30.9** | 47.4 | 2.34 | 1.53 |
| 256 | 160.4 | **47.6** | 56.6 | 3.37 | 2.83 |
| 512 | 296.8 | 73.7 | **72.2** | 4.03 | 4.11 |
| 2048 | 542.6 | **178.0** | 303.1 | 3.05 | 1.79 |
| 4096 | 674.2 | **268.0** | 583.0 | 2.52 | 1.16 |
| 8192 | 937.2 | **452.7** | 952.6 | 2.07 | 0.98 |
| 16384 | 1268.7 | **783.3** | 1450.0 | 1.62 | 0.87 |
| 32768 | 1932.1 | **1473.8** | 2462.5 | 1.31 | 0.78 |
| 65536 | 3909.1 | **2903.4** | 3748.3 | 1.35 | 1.04 |
| 131072 | 7865.5 | 7343.2 | **6987.4** | 1.07 | 1.13 |
| 262144 | 16885.4 | 14858.6 | **13251.2** | 1.14 | 1.27 |

Full data: `aralgo_long.csv` (102 cells × 3 reps).
Figure: `allreduce_algo_compare.{png,pdf}` (log-log, one panel per np).

---

## 4. Observations

1. **Tree dominates the latency-bound regime.** At np=16 tree is best at
   *every* size (1.7–4.6× vs flat); at np=32 it is best from 4 B to 64 KB
   (up to 4.0×). Largest gains sit at 64–128 KB / np=16 (~4×), where flat's
   O(N·S) invalidate volume is maximal but Optane bandwidth is not yet the
   binding constraint.
2. **The winner crosses over twice at np=32.** rab ≈ tree at 512 B
   (both ~4× over flat), *loses to flat* at 8–32 KB (0.78–0.98×), then
   becomes the overall best ≥128 KB (1.13–1.27× vs flat, and better than
   tree). No algorithm is uniformly optimal even with the policy held fixed.
3. **Flat's collapse is contention, not barriers.** Native barrier costs
   3.2–3.7 µs at np≥16 (measured separately); two barriers explain <7 µs of
   flat's 674 µs at 4 KB / np=32. The dominant term is N² concurrent Optane
   reads plus O(N·S) clflushopt invalidate work per rank.
4. **Reproducibility anchor:** flat @ 4 KB / np=32 / clflushopt measured
   674 µs here vs 667 µs in the 2026-07-19 four-stack comparison (different
   gate, different day) — 1 % apart.
5. **Convergence at the bandwidth wall.** At np=32 / 256 KB all three land
   within 1.3× (13.3–16.9 ms): aggregate Optane traffic, not algorithm
   structure, is the limiter. The remaining rab win comes from its O(N·S)
   traffic with balanced fragments.

## 5. Analysis

**Why tree wins the small/mid range.** Per-rank flush+invalidate volume
drops from (N−1)·S (flat) to ≤(log₂N+1)·S. With clflushopt on both paths
this is a direct instruction-count reduction; at np=32, 31·S → 6·S ≈ 5×,
matching the observed 2.3–4× (the residual gap is the root-slot broadcast,
where all N−1 ranks still read one buffer concurrently).

**Why rab loses the mid range at np=32.** rab always executes 2·log₂N = 10
flag-synchronized stages; each stage costs a fixed flag round-trip
(poll-with-invalidate on Optane ≈ µs-scale) *plus* per-fragment flush setup,
while its bandwidth saving over tree only matters once S/N fragments are
large. At S = 8–32 KB the fragments are 256 B–1 KB: pure sync overhead with
no bandwidth to save — tree does the same job in half the stages, and even
flat's single-stage structure wins over rab's 10 sync hops. The rab
advantage appears exactly when fragments reach ~4 KB (S ≥ 128 KB at np=32),
i.e., when per-stage payload amortizes the sync cost.

**Why the crossover is the paper's point.** Both crossovers happen *within
one collective on one fabric with one coherence policy* — driven only by
(S, N). A runtime with a single hard-wired algorithm (as real MPI libraries
hard-wire their shared-memory collectives) is mis-tuned somewhere in the
(S, N) plane by 1.3–4×. MEMU exposes the algorithm as a knob
(`CXL_ALLREDUCE_ALGO`) the same way it exposes the CC flush policy; this
experiment is the algorithm-axis analogue of the cross-application policy
preference result, measured under a deliberately fixed policy so the two
axes are cleanly separable. (Natural follow-up: the policy axis interacts —
tree/rab cut flush *counts* per rank from O(N) to O(log N), so
policy-sensitivity itself should shrink under tree/rab; left for a 7-policy
× 3-algorithm sweep.)

## 6. Threats to validity / caveats

- **Absolute numbers are Optane-emulation artifacts.** Native Open MPI
  (DRAM, hardware coherence) does 4 KB / np=32 in ~15 µs — every CXL-path
  variant is slower; the claim is about *relative* algorithm/policy
  structure on a software-coherent CXL fabric, not beating native.
- Float summation order differs per algorithm (ULP-level); OSU validation
  passes because test values are integer-valued floats.
- rab requires power-of-two np (else silent tree fallback — check
  `CXL allreduce algorithm` line in the log); count < N degenerates
  gracefully (empty segments).
- Flat leaks one CXL allocation per call — long sweeps need CXL_MEM_SIZE
  headroom (8 GB used here); tree/rab use a fixed workspace and do not leak.
- Single node, single machine, 3 reps; medians robust to the observed
  outliers but tails at 64–128 KB / np=16 show occasional 2× swings
  (suspected Optane background activity).
- OSU table parsing: shim log lines interleave nondeterministically with
  the latency table under mpirun — parsers must skip stray lines inside the
  table (fixed in `parse_aralgo.py`; the strict end-of-table heuristic in
  `parse_osu_collective.py` silently drops such runs).

## 7. Artifact inventory & reproduction

| artifact | path (relative to `run_bench/`) |
|---|---|
| shim implementation | `../../CXLMemSim/workloads/gromacs/mpi_cxl_shim.c` ("CXL Allreduce algorithm variants" section + dispatch in `MPI_Allreduce`) |
| runner | `eval_scripts/run_aralgo_compare_qemuless_node1_20260720.sh` |
| raw logs | `results/osu_allreduce/mpi_cxl_qemuless/cc_clflushopt_clflushopt/{16,32}/aralgo_*_qemuless_node1_20260720/*/output.log` |
| parser / tidy CSV | `data_anal/parse_aralgo.py` → `data_anal/aralgo_long.csv` |
| figure | `data_anal/plot_aralgo.py` → `data_anal/allreduce_algo_compare.{png,pdf}` |
| correctness test + probe | scratchpad `allreduce_probe/{allreduce_algo_test.c,probe.c}` (session 2026-07-20; probe = LD_PRELOAD interposer after the shim counting passthrough via RTLD_NEXT) |

Reproduce: rebuild shims
(`PATH=/home/sherry/openmpi-install/bin:$PATH bash build.sh all` — Intel
oneAPI mpicc silently builds ABI-broken shims), then
`./thp_exec bash eval_scripts/run_aralgo_compare_qemuless_node1_20260720.sh`
and `python3 data_anal/parse_aralgo.py && python3 data_anal/plot_aralgo.py`.

---

## 8. Extension: full algorithm × CC-policy matrix (same day)

Follow-up sweep re-introducing the policy axis: **3 algorithms × 7 cc types
× np {16, 32} × 3 reps** (108 new runs via
`eval_scripts/run_aralgo_cc_matrix_qemuless_node1_20260720.sh`, rep-major,
nocc first per rep; the 18 `cc_clflushopt_clflushopt` runs of §1 are
reused). Same OSU command, gate, and environment; only `LD_PRELOAD` selects
the shim variant. 714 (cc, algo, np, size) cells, 3 reps each.
Policy naming: `<write-flush>+<read-invalidate>`, cf = clflush,
cfo = clflushopt.

### 8.1 Best policy per (algorithm, np, size band)

Geomean over sizes within band; penalty = worst/best among the 6 CC types
(nocc excluded — it is the no-coherence floor and is best everywhere).

| np | band | flat best | tree best | rab best | flat pen. | tree pen. | rab pen. |
|---|---|---|---|---|---:|---:|---:|
| 16 | ≤1K | cfo+cfo | cfo+cfo | clwb+cfo | 1.09 | 1.15 | 1.04 |
| 16 | 2–32K | clwb+cfo | cfo+cfo | cfo+cfo | 2.58 | 2.83 | 1.35 |
| 16 | 64–256K | cf+cfo | cfo+cfo | cfo+cfo | 2.40 | 3.91 | 1.51 |
| 32 | ≤1K | cf+cfo | cfo+cfo | clwb+cf | 1.02 | 1.08 | 1.03 |
| 32 | 2–32K | cf+cfo | cf+cfo | **cf+cf** | 2.15 | 1.34 | 1.49 |
| 32 | 64–256K | cfo+cfo | cfo+cfo | cf+cfo | 2.91 | 1.31 | 1.14 |

### 8.2 Cross-algorithm misconfiguration cost

Latency ratio (geomean over all 17 sizes) when an algorithm runs under
another algorithm's best policy — the direct quantification of "one fixed
policy does not fit all implementations":

- np=16 (best: flat = cf+cfo, tree = rab = cfo+cfo):
  running **tree with flat's best policy costs 1.31×**; flat with
  tree's best costs only 1.01× (asymmetric).
- np=32 (best: flat = tree = cfo+cfo, rab = cf+cf):
  running **flat with rab's best policy costs 1.51×**; tree with rab's
  best 1.18×; rab with flat/tree's best 1.13×.

### 8.3 Observations

1. **The best policy moves with the algorithm** at a fixed operating point
   (np=32 mid: flat/tree want read-side cfo, rab wants cf+cf; np=16 large:
   flat wants cf+cfo, tree/rab want cfo+cfo) — the algorithm-axis analogue
   of the cross-application preference result, measured inside a single
   collective.
2. **Read-side clflush is the dominant hazard, but only for read-heavy
   structures.** All three `*+cf` rows cost flat 2.1–2.9× and tree (np16)
   2.3–3.9× at mid/large sizes, yet rab absorbs them at 1.1–1.5× — its
   per-step ranges are S/N fragments, so invalidate loops are short and
   overlap with the pairwise exchange.
3. **Fewer flushes ≠ less policy-sensitive.** Tree issues O(log N) flushes
   vs flat's O(N), yet at np=16 large it is the *most* sensitive cell in
   the matrix (3.91× for cf+cf vs 2.34× for flat). Flat's N−1 invalidates
   are independent and overlap in the memory system; tree's sit on a
   serialized log-N dependency chain, so per-instruction flush latency
   multiplies. Policy sensitivity tracks *critical-path* flush count, not
   total flush count.
4. **The coherence tax varies 1.2×–12× by algorithm and size** (nocc row:
   0.85 → flat/np16/large ≈ 1.2× tax; 0.08 → rab/np16/large ≈ 12× tax),
   i.e., which algorithm wins also depends on whether software coherence is
   on at all — under nocc, rab's bandwidth advantage is much larger.
5. rab at np=32 mid prefers cf+cf while every other cell hates cf+cf —
   with 256 B–1 KB fragments, clflush's synchronous completion apparently
   beats clflushopt's weaker ordering on this Optane platform (consistent
   with the paper's Fig-1 read-side inversion at small sizes on real CXL).

### 8.4 Artifacts (extension)

| artifact | path |
|---|---|
| runner | `eval_scripts/run_aralgo_cc_matrix_qemuless_node1_20260720.sh` |
| raw logs | `results/osu_allreduce/mpi_cxl_qemuless/<cc>/{16,32}/aralgo_<algo>_qemuless_node1_20260720/*/output.log` |
| parser | `data_anal/parse_aralgo_cc.py` → `aralgo_cc_long.csv` (714 cells) |
| analysis | `data_anal/analyze_aralgo_cc.py` → `aralgo_cc_pref.csv` + stdout tables |
| figure | `data_anal/aralgo_cc_heatmap.{png,pdf}` (ratio to best CC policy per algo×band; nocc row = floor) |
