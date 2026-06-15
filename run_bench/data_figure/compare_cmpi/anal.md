# OSU MPI_Get Multiple Bandwidth: MPI+CXL Shim vs CMPI Analysis

## Benchmark Configuration

- **Benchmark**: OSU MPI_Get Multiple Bandwidth Test v7.4
- **Window creation**: MPI_Win_allocate
- **Synchronization**: MPI_Win_flush
- **Message size range**: 1 B ~ 1 MB
- **Iterations**: 200
- **Process counts**: 2, 4, 8, 16, 32
- **Node**: optane03 (single node)
- **Cache coherence**: disabled (nocc)

## Overall Observations

### MPI+CXL Shim (Qemuless) — Left Subfigure

- Bandwidth exhibits a clear **bell-shaped curve**: rises sharply from small messages, peaks at medium sizes (~32 KB–64 KB), then declines at large sizes.
- **Scalability with process count is excellent**: increasing processes yields proportionally higher aggregate bandwidth.
  - 2 procs peak: ~2,800 MB/s
  - 4 procs peak: ~5,500 MB/s
  - 8 procs peak: ~10,000 MB/s
  - 16 procs peak: ~20,000 MB/s
  - 32 procs peak: ~38,000 MB/s
- Peak bandwidth scales roughly linearly with process count, indicating low contention and efficient use of CXL DAX device bandwidth.
- At large message sizes (>256 KB), bandwidth drops significantly due to memory subsystem saturation and TLB pressure.

### CMPI (MPICH CXL) — Right Subfigure

- Bandwidth is **substantially lower** across all message sizes and process counts.
- Peak bandwidth ranges from ~1,100 MB/s (2 procs) to ~2,700 MB/s (32 procs).
- The bandwidth curve is flatter — it rises gradually and plateaus around 16 KB–64 KB, without the sharp peak seen in MPI+CXL Shim.
- Scalability with process count is **limited**: doubling processes does not proportionally increase bandwidth, suggesting contention or serialization bottlenecks in CMPI's shared memory implementation.
- At large message sizes (>128 KB), bandwidth degrades similarly to MPI+CXL Shim but from a much lower baseline.

## Quantitative Comparison

| Metric | MPI+CXL Shim | CMPI | Ratio (Shim/CMPI) |
|--------|-------------|------|-------------------|
| Peak BW (2 procs) | ~2,800 MB/s | ~1,100 MB/s | ~2.5x |
| Peak BW (32 procs) | ~38,000 MB/s | ~2,700 MB/s | ~14x |
| BW scalability (2→32 procs) | ~13.6x | ~2.5x | — |
| Optimal message size | 32–64 KB | 16–64 KB | — |

## Key Takeaways

1. **MPI+CXL Shim delivers significantly higher bandwidth** than CMPI, especially at higher process counts. The gap widens from ~2.5x (2 procs) to ~14x (32 procs).

2. **MPI+CXL Shim scales near-linearly** with process count, while CMPI exhibits poor scalability — likely due to contention in MPICH's internal shared memory path.

3. **CXL DAX direct access** (used by MPI+CXL Shim via `LD_PRELOAD` shim with remotable pointers and per-rank message queues) is far more efficient for RMA (one-sided) operations than CMPI's approach.

4. **Both implementations** show bandwidth degradation at large message sizes (>256 KB), which is expected due to memory hierarchy effects (cache capacity, TLB misses, NUMA/CXL latency).

5. The **small message performance** (<64 B) is low for both, which is typical for MPI_Get — the overhead of window management and synchronization dominates at small transfer sizes.
