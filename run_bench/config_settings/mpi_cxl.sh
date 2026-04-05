#!/bin/bash
PINNING=""

export CXL_SHIM_WIN=1
export CXL_DAX_RESET=1  # Reset allocation counter on first process
# export CXL_SHIM_VERBOSE=1
# CXL_SHIM_VERBOSE: unset when disabled (C lib sees as disabled), export=1 when enabled
if [ "${CXL_SHIM_VERBOSE:-0}" = "1" ]; then
    export CXL_SHIM_VERBOSE=1
else
    unset CXL_SHIM_VERBOSE
fi
export CXL_SHIM_ALLOC=1
export CXL_SHIM_COPY_SEND=1
export CXL_SHIM_COPY_RECV=1
export CXL_DAX_PATH="/dev/dax0.0"
export GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX512F,-AVX512DQ,-AVX512BW,-AVX512VL

MPIRUN="/usr/local/bin/mpirun"
# RUN_ENV1="FI_PROVIDER=tcp FI_TCP_IFACE=ens3f0"
MPIARGS="--allow-run-as-root --mca osc ^ucx -np ${NUM_PROCESS} --map-by ppr:${PPN}:node -hostfile ${HOSTFILE_DIR}/hostfile${NUM_NODES} -x CXL_SHIM_ALLOC=${CXL_SHIM_ALLOC} -x CXL_SHIM_COPY_SEND=${CXL_SHIM_COPY_SEND} -x CXL_SHIM_COPY_RECV=${CXL_SHIM_COPY_RECV} -x CXL_DAX_PATH=${CXL_DAX_PATH} -x CXL_DAX_RESET=${CXL_DAX_RESET} -x GLIBC_TUNABLES=${GLIBC_TUNABLES} -x LD_PRELOAD=${MPI_SHIM_LIB}"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_DIR}"

