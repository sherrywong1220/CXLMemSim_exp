#!/bin/bash
# mpi_cxl_qemuless: single-node qemuless mode — all ranks share the same
# CXL DAX device (or shared-memory fallback), so all_ranks_local=true and
# CXL mailbox / RMA / collectives are fully enabled.

PINNING=""

export CXL_SHIM_WIN=1
export CXL_DAX_RESET=1
if [ "${CXL_SHIM_VERBOSE:-0}" = "1" ]; then
    export CXL_SHIM_VERBOSE=1
else
    unset CXL_SHIM_VERBOSE
fi
export CXL_SHIM_ALLOC=1
export CXL_SHIM_COPY_SEND=1
export CXL_SHIM_COPY_RECV=1

# Qemuless: use PMEM DAX device to simulate CXL memory
export CXL_DAX_PATH="/dev/dax0.0"

# Disable AVX-512 to avoid SIGILL on CXL memory paths
export GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX512F,-AVX512DQ,-AVX512BW,-AVX512VL

MPIRUN="/home/sherry/openmpi-install/bin/mpirun"

# Single-node: no hostfile, all processes mapped locally
MPIARGS="--allow-run-as-root --mca osc ^ucx -np ${NUM_PROCESS} --map-by ppr:${PPN}:node -x CXL_SHIM_ALLOC=${CXL_SHIM_ALLOC} -x CXL_SHIM_WIN=${CXL_SHIM_WIN} -x CXL_SHIM_COPY_SEND=${CXL_SHIM_COPY_SEND} -x CXL_SHIM_COPY_RECV=${CXL_SHIM_COPY_RECV} -x CXL_DAX_PATH=${CXL_DAX_PATH} -x CXL_DAX_RESET=${CXL_DAX_RESET} -x GLIBC_TUNABLES=${GLIBC_TUNABLES} -x LD_PRELOAD=${MPI_SHIM_LIB}"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_OPENMPI_DIR}"

