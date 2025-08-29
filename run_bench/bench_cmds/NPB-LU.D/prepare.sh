#!/bin/bash

export OMP_NUM_THREADS=8

BIN=/mnt/nvme01/sherry/workloads/NPB3.4.2/NPB3.4-OMP/bin
BENCH_RUN="${BIN}/lu.D.x"

# Mem size: 57.5GB