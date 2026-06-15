#!/bin/bash
# LULESH 2.0 CXL-enabled, mid-size domain (s=80).
# halo face ~= 315 KB; total halo ~2 MB/rank — still exceeds L2, fits in L3.
# Size chosen to be safe under mpi_cxl_shim's dual-send leak (unlike s=300).

LULESH_DIR="/mnt/nvme01/sherry/CXLMemSim/workloads/lulesh"
BIN="${LULESH_DIR}/lulesh2.0_cxl"
# Pin to 1 OMP thread per rank to avoid oversubscription on single-node runs.
APP_RUN="${BIN} -s 80 -i 100"
BENCH_RUN="${MPIRUN} ${MPIARGS} -x OMP_NUM_THREADS=1 ${APP_RUN}"
