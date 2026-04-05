#!/bin/bash
PINNING=""
MPIRUN="/usr/local/bin/mpirun"
# RUN_ENV1="UCX_LOG_LEVEL=info"
MPIARGS="--allow-run-as-root -np ${NUM_PROCESS} --map-by ppr:${PPN}:node -hostfile ${HOSTFILE_DIR}/hostfile${NUM_NODES} -x CXL_DAX_PATH -x CXL_DAX_RESET -x CXL_SHIM_VERBOSE -x LD_PRELOAD"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_DIR}"

