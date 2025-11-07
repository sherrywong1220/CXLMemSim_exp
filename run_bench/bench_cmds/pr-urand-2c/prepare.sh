#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
APP_RUN="${BIN_DIR}/pr -f ${BIN_DIR}/benchmark/graphs/urand.sg -i1000 -t1e-4 -n4"
BENCH_RUN="${DIR}/bench_cmds/run_2_copies.sh"

# Mem size: 36GB
