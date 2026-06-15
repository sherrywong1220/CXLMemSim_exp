#!/bin/bash
# mpi_cxl_qemuless_noshim: single-node qemuless mode for apps that manage
# CXL memory themselves via cxl_rapid.h (e.g. lulesh2.0_cxl).
#
# Differences from mpi_cxl_qemuless.sh:
#   - No LD_PRELOAD of libmpi_cxl_shim*.so. The app attaches to /dev/dax0.0
#     directly via its own cxl_rapid_init path.
#   - None of the CXL_SHIM_COPY_SEND / COPY_RECV / ALLOC / WIN env vars,
#     which are dual-send-path features of the shim that leak the CXL pool
#     when the receiver never drains the mailbox.
#   - MPI messages go through OpenMPI's native shared-memory BTL (vader/CMA),
#     which is already optimal for ranks co-located on one node.
#
# Net effect: the app still places all its data in CXL DAX (via rapid_malloc),
# but MPI itself is not instrumented, so there is no mailbox queue-full spam
# and no dual-send leak. This is the correct config for lulesh_cxl.

PINNING=""

export CXL_DAX_RESET=1
if [ "${CXL_SHIM_VERBOSE:-0}" = "1" ]; then
    export CXL_SHIM_VERBOSE=1
else
    unset CXL_SHIM_VERBOSE
fi

# Qemuless: use PMEM DAX device as CXL pool
export CXL_DAX_PATH="/dev/dax0.0"

# Disable AVX-512 to avoid SIGILL on CXL memory paths
export GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX512F,-AVX512DQ,-AVX512BW,-AVX512VL

MPIRUN="/home/sherry/openmpi-install/bin/mpirun"

# Single-node: no hostfile, all processes mapped locally.
# NO -x LD_PRELOAD — app uses cxl_rapid.h directly.
MPIARGS="--allow-run-as-root --mca osc ^ucx -np ${NUM_PROCESS} --map-by ppr:${PPN}:node -x CXL_DAX_PATH=${CXL_DAX_PATH} -x CXL_DAX_RESET=${CXL_DAX_RESET} -x GLIBC_TUNABLES=${GLIBC_TUNABLES}"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_OPENMPI_DIR}"
