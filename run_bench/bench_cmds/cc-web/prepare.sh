#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
BENCH_RUN="${BIN_DIR}/cc -f ${BIN_DIR}/benchmark/graphs/web.sg -n256"

# Mem size: 15.3GB