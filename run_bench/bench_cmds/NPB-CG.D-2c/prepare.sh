#!/bin/bash

export OMP_NUM_THREADS=8

BIN=${WORKLOAD_DIR}/NPB3.4.2/NPB3.4-OMP/bin
APP_RUN="${BIN}/cg.D.x"
BENCH_RUN="${DIR}/bench_cmds/run_2_copies.sh"

# Mem size: 32.6GB
