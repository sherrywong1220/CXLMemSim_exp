#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
BENCH_RUN="${BIN_DIR}/bc -f ${BIN_DIR}/benchmark/graphs/urand.sg -i4 -n1"

# Mem size: 23.7GB