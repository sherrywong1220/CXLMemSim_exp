#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=/mnt/nvme01/sherry/workloads/gapbs
BENCH_RUN="${BIN_DIR}/pr -f ${BIN_DIR}/benchmark/graphs/web.sg -i1000 -t1e-4 -n16"

# Mem size: 16.3GB