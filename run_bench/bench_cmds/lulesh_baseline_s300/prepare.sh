#!/bin/bash
# LULESH 2.0 baseline, large domain (s=300) to push halo into DRAM-bandwidth regime.
# halo face ~= 5.7 MB; total halo ~34 MB/rank — well outside L3.
# Iteration count reduced so total runtime stays manageable.

LULESH_DIR="/mnt/nvme01/sherry/CXLMemSim/workloads/lulesh"
BIN="${LULESH_DIR}/lulesh2.0"
# Pin to 1 OMP thread per rank to avoid oversubscription on single-node runs.
APP_RUN="${BIN} -s 300 -i 10"
BENCH_RUN="${MPIRUN} ${MPIARGS} -x OMP_NUM_THREADS=1 ${APP_RUN}"
