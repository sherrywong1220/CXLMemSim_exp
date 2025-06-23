#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=/mnt/nvme01/sherry/workloads/gapbs
BENCH_RUN="${BIN_DIR}/bc -f ${BIN_DIR}/benchmark/graphs/web.sg -i4 -n16"