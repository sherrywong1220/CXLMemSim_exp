#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
APP_RUN="${BIN_DIR}/pr -f ${BIN_DIR}/benchmark/graphs/twitter.sg -i1000 -t1e-4 -n16"
BENCH_RUN="${DIR}/bench_cmds/run_3_copies.sh"

# Mem size: 36GB
