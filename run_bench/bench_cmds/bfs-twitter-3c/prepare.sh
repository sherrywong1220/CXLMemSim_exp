#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
APP_RUN="${BIN_DIR}/bfs -f ${BIN_DIR}/benchmark/graphs/twitter.sg -n128"
BENCH_RUN="${DIR}/bench_cmds/run_3_copies.sh"

# Mem size: 36GB
