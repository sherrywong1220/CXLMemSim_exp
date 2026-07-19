#!/bin/bash
# NPB 3.4.2 IS (integer sort), class C, MPI version.
# Communication profile: large MPI_Alltoallv exchange per iteration plus a
# 4KB MPI_Allreduce(MPI_INT, MPI_SUM) on bucket counts, which takes the
# shim's flat CXL collective path when <= CXL_DIRECT_MAX_BYTES.
# Built for a fixed process count; run with -P 16.

BIN="/mnt/nvme01/sherry/workloads/NPB3.4.2/NPB3.4-MPI/bin/is.C.x"
APP_RUN="${BIN}"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"
