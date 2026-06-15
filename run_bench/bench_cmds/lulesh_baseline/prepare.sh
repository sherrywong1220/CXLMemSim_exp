#!/bin/bash
# LULESH 2.0 baseline (standard MPI comm buffers in DRAM)
# -s 30: 30^3 elements per domain
# -i 100: 100 iterations

LULESH_DIR="/mnt/nvme01/sherry/CXLMemSim/workloads/lulesh"
BIN="${LULESH_DIR}/lulesh2.0"
# Pin to 1 OMP thread per rank to avoid oversubscription on single-node runs.
APP_RUN="${BIN} -s 30 -i 100"
BENCH_RUN="${MPIRUN} ${MPIARGS} -x OMP_NUM_THREADS=1 ${APP_RUN}"
