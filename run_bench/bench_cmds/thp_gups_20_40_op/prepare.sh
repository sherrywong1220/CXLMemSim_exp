#!/bin/bash
BIN_DIR=${WORKLOAD_DIR}/THP_GUPS
BENCH_RUN="${BIN_DIR}/thp_gups --buffer_size=64G --hotspot_size=16G --base_hot_shift=2 --threads=48 --distribution=hotspot --hotspot_prob=40 --read_ratio=80 --iterations=1000000000"

# Mem size: 64.0GB