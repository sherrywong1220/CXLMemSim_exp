#!/bin/bash
export OMP_NUM_THREADS=8

BIN=/mnt/nvme01/sherry/workloads/silo/out-perf.masstree/benchmarks
BENCH_RUN="${BIN}/dbtest --verbose --bench ycsb --num-threads 8 --scale-factor 200000 --ops-per-worker=500000000"


# Mem size: 29.0G