#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
BENCH_RUN="${BIN_DIR}/bfs -f ${BIN_DIR}/benchmark/graphs/urand.sg -n64"

# Mem size: 17.7GB