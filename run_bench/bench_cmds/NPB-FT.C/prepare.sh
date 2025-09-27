#!/bin/bash
export OMP_NUM_THREADS=8
BIN=${WORKLOAD_DIR}/NPB3.4.2/NPB3.4-OMP/bin
BENCH_RUN="${BIN}/ft.C.x"

# Mem size: 40.1GB