# OSU MPI_Get Multi Latency: MEMU vs CMPI Analysis

## Benchmark Configuration

- **Benchmark**: OSU MPI_Get Multi Latency Test v7.4
- **Window creation**: MPI_Win_allocate
- **Synchronization**: MPI_Win_flush
- **Message size range**: 1 B ~ 1 MB
- **Iterations**: 200
- **Process counts**: 2, 4, 8, 16, 32
- **Node**: optane03 (single node)

## Overall Observations

### MEMU (default) — Left Subfigure

- Achieves the **lowest small-message latency** across all configurations: ~0.5 us at 1 B (2 procs).
- Latency scales smoothly with message size, staying below 1 us up to ~256 B.
- Process count has minimal impact on latency for small/medium messages, indicating low contention in the nocc (no cache coherence) path.
- At 1 MB: latency ranges from ~117 us (2 procs) to ~261 us (16 procs), with an anomalous spike to ~3120 us at 32 procs.
- The 32-procs outlier at 1 MB likely reflects memory subsystem saturation or contention on the DAX device at high concurrency.

### MEMU (clflushopt) — Middle Subfigure

- Small-message latency is higher than nocc: ~0.9–1.7 us at small sizes, due to the overhead of explicit cache line flushing (clflushopt instructions).
- The clflushopt overhead is roughly **2–3x** compared to nocc for small messages (<1 KB).
- For medium messages (1 KB–64 KB), clflushopt latency converges with nocc, as the flush cost becomes a smaller fraction of total transfer time.
- At 1 MB: 2-procs latency is ~708 us (vs. 117 us for nocc), showing that clflushopt adds significant overhead at large sizes due to flushing entire cache lines.
- 2-procs data has fewer data points (6 vs. 14+ for other configs), starting from 32 B rather than 1 B.

### CMPI (MPICH CXL) — Right Subfigure

- **Highest small-message latency**: ~2 us (2 procs) to ~14.5 us (16 procs) at 1 B.
- Latency increases notably with process count even for small messages, suggesting serialization or lock contention in MPICH's shared memory layer.
- At 1 MB: latency ranges from ~500 us (2 procs) to ~790 us (16 procs).
- **32 procs failed** for CMPI — MPICH crashed with "unable to allocate shared memory" errors, indicating scalability limitations in CMPI's shared memory allocation.
- The latency curve is smoother and more predictable than MEMU, but from a higher baseline.

## Quantitative Comparison

| Metric | MEMU (default) | MEMU (clflushopt) | CMPI |
|--------|---------------|-------------------|------|
| Latency @ 1B, 2 procs | 0.53 us | ~0.94 us (@ 32B) | 2.04 us |
| Latency @ 1B, 16 procs | 0.68 us | 1.07 us | 14.55 us |
| Latency @ 1MB, 2 procs | 116.70 us | 707.96 us | 499.73 us |
| Latency @ 1MB, 16 procs | 261.46 us | 575.19 us | 790.12 us |
| 32-procs support | Yes | Yes | Failed |
| Scalability (2→16 procs @ 1B) | 1.3x | 1.1x | 7.1x |

## Key Takeaways

1. **MEMU (default) delivers the lowest latency** for small messages (~0.5 us), roughly 4x lower than CMPI (~2 us) and 2x lower than MEMU with clflushopt (~1 us).

2. **MEMU scales better with process count**: latency increase from 2→16 procs is only 1.3x for MEMU (default), vs. 7.1x for CMPI. This indicates MEMU's per-rank message queue design avoids the shared-memory contention seen in CMPI.

3. **clflushopt adds measurable overhead**: ~2x for small messages and ~6x for 1 MB messages (2 procs), reflecting the cost of explicit cache line flushing for coherence. This is the price of ensuring data consistency across CXL-attached memory.

4. **CMPI fails at 32 processes** due to shared memory allocation limits in MPICH, while MEMU handles 32 procs successfully (albeit with increased latency at 1 MB).

5. **For large messages (1 MB)**, CMPI (500 us) actually outperforms MEMU-clflushopt (708 us) at 2 procs, suggesting MPICH's bulk transfer path is efficient but the clflushopt overhead dominates. MEMU (default) remains fastest at 117 us.

6. **All implementations** show the expected near-linear latency growth with message size beyond ~16 KB, dominated by memory bandwidth limitations rather than software overhead.
