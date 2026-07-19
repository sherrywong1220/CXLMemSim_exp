#!/bin/bash
# NPB 3.4.2 IS (integer sort), class D, MPI version, 16 ranks.
# Communication profile: bulk MPI_Alltoallv key exchange per iteration plus a
# small MPI_Allreduce on bucket counts. Bulk exchange bypasses the shim's CXL
# collective path (Alltoallv is not interposed), so IS doubles as a
# policy-insensitivity control among real applications.
# Class D (~10x class C runtime) for better signal-to-noise.

BIN="/mnt/nvme01/sherry/workloads/NPB3.4.2/NPB3.4-MPI/bin/is.D.x"
APP_RUN="${BIN}"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"
