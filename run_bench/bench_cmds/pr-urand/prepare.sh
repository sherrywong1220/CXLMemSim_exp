#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=${WORKLOAD_DIR}/gapbs
BENCH_RUN="${BIN_DIR}/pr -f ${BIN_DIR}/benchmark/graphs/urand.sg -i1000 -t1e-4 -n4"

# Mem size: 18.0GB