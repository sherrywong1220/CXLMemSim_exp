#!/bin/bash

export OMP_NUM_THREADS=8
BIN_DIR=/mnt/nvme01/sherry/workloads/gapbs
BENCH_RUN="${BIN_DIR}/bfs -f ${BIN_DIR}/benchmark/graphs/web.sg -n128"

# Mem size: 17.7GB