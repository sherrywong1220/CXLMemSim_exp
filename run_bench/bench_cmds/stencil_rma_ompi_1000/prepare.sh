#!/bin/bash
# 2D Jacobi stencil with derived-datatype halo exchange over MPI one-sided RMA
# (MPI_Win_allocate + MPI_Win_fence), Open MPI build for the qemuless CC-policy
# experiments. Same source and flags as the Intel MPI stencil used in the
# paper's Q1 sweep (CXLMemSim_clflush/workloads/stencil, -std=c99).
# Real-application RMA workload: every halo Put/Get pays the flush policy.
GRID_SIZE=1000
ENERGY=100
NITERS=800

BIN="/mnt/nvme01/sherry/workloads/stencil-openmpi/bin/stencil_mpi_ddt_rma"
APP_RUN="${BIN} ${GRID_SIZE} ${ENERGY} ${NITERS}"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"
