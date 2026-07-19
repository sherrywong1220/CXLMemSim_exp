#!/bin/bash
# Graph500 reference MPI BFS (bfs_simple), SCALE=20 (1M vertices), edgefactor 16.
# Communication profile: many aggregated MPI_Isend/MPI_Irecv exchanges per BFS
# level -> exercises the shim's CXL mailbox path (flush on send, invalidate on
# recv) far more intensively than LULESH. Validation skipped: the experiment
# measures BFS time under different flush policies, not correctness of BFS.
GRAPH500_SCALE=20
GRAPH500_EDGEFACTOR=16
export SKIP_VALIDATION=1

BIN="/mnt/nvme01/sherry/workloads/graph500/mpi/graph500_mpi_simple"
APP_RUN="${BIN} ${GRAPH500_SCALE} ${GRAPH500_EDGEFACTOR}"
BENCH_RUN="${MPIRUN} ${MPIARGS} -x SKIP_VALIDATION=1 -x OMP_NUM_THREADS=1 ${APP_RUN}"
