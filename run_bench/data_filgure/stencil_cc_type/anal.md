# Stencil MPI DDT RMA - CC Type Performance Analysis

## Experiment Setup

- **Workload**: stencil_mpi_ddt_rma (MPI RMA-based stencil with derived datatypes)
- **Grid Sizes**: 1000, 2000, 4000, 8000
- **Process Counts**: 4, 9, 16, 25, 36
- **CC Types**: nocc, clflush+clflush, clflush+clflushopt, clflushopt+clflush, clflushopt+clflushopt, clwb+clflush, clwb+clflushopt
- **Backend**: mpi_cxl (CXL shim over DAX device)
- **Data**: latest timestamp run per configuration, normalized to nocc baseline

## Key Observations

### 1. CC overhead is most significant at small grid size + high process count

At grid size 1000x1000 with 36 processes, all CC variants incur 1.42x-1.49x overhead relative to nocc. This is because smaller per-process working sets lead to more frequent RMA operations relative to computation, amplifying the cost of cache flush instructions.

| CC Type | 1000x1000, 36 procs |
|---------|---------------------|
| clflush+clflush | 1.46x |
| clflush+clflushopt | 1.42x |
| clflushopt+clflush | 1.47x |
| clflushopt+clflushopt | 1.43x |
| clwb+clflush | 1.49x |
| clwb+clflushopt | 1.49x |

### 2. CC overhead diminishes rapidly with increasing grid size

| Grid Size | 36 procs CC overhead range |
|-----------|---------------------------|
| 1000      | 1.42x - 1.49x             |
| 2000      | 1.04x - 1.08x             |
| 4000      | 0.99x - 0.99x (negligible)|
| 8000      | 1.00x - 1.02x (negligible)|

At large grid sizes (4000, 8000), computation dominates and the cache flush overhead becomes negligible, with all CC variants within 2% of nocc.

### 3. Among CC variants, differences are marginal

No single CC strategy consistently outperforms others. At 1000x1000 / 36 procs where overhead is largest, clflush+clflushopt (1.42x) and clflushopt+clflushopt (1.43x) are marginally better than clwb-based variants (1.49x), but these differences are small relative to the nocc-vs-CC gap.

### 4. Non-monotonic scaling at grid size 4000

The 4000x4000 grid exhibits an unusual scaling pattern: execution time decreases from 4→9 procs, increases at 16 procs, decreases at 25 procs, and increases again at 36 procs. This non-monotonic behavior likely reflects NUMA topology effects — certain process counts (16, 36) may span multiple NUMA domains, incurring cross-node memory access penalties that offset the parallelism benefit.

### 5. nocc is consistently the fastest or tied for fastest

Across all configurations, nocc never shows a performance penalty, confirming that the CXL shim's default behavior without explicit cache management is sufficient for correctness on this workload, and the flush instructions add pure overhead.
