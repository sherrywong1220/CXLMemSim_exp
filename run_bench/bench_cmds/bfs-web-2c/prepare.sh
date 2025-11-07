#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
APP_RUN="${BIN_DIR}/bfs -f ${BIN_DIR}/benchmark/graphs/web.sg -n128"
BENCH_RUN="${DIR}/bench_cmds/run_2_copies.sh"

# Mem size: 35GB
