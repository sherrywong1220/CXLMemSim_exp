#!/bin/bash
# Per-rank window size (4 procs, 2x2 grid) and where it sits:
#   n=1000  →  3.8MB  (L3, partly spills)     63K  cachelines/fence
#   n=2000  → 15.3MB  (DRAM, beyond LLC)      251K  cachelines/fence
#   n=4000  → 61.2MB  (DRAM/PMEM)           1,002K  cachelines/fence
#   n=8000  → 245MB   (deep PMEM)           4,008K  cachelines/fence
GRID_SIZE=4000
ENERGY=100
NITERS=200

BIN="${WORKLOAD_DIR}/stencil/bin/stencil_mpi_ddt_rma"
APP_RUN="${BIN} ${GRID_SIZE} ${ENERGY} ${NITERS}"
BENCH_RUN="env ${RUN_ENV1} ${MPIRUN} ${MPIARGS} ${APP_RUN}"
