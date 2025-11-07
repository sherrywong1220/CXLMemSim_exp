#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
BENCH_RUN="${BIN_DIR}/bc -f ${BIN_DIR}/benchmark/graphs/twitter.sg -i4 -n16"

# Mem size: 12GB
