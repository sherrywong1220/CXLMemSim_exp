#!/bin/bash
# openmpi_native: single-node NATIVE OpenMPI baseline (no CXL shim).
#
# Same OpenMPI 5.0.3 build as mpi_cxl_qemuless, but WITHOUT the CXL
# interposition layer:
#   - No LD_PRELOAD of libmpi_cxl_shim*.so  -> MPI uses OpenMPI's native
#     shared-memory BTL (vader/sm) on regular DRAM.
#   - No CXL_SHIM_* / CXL_DAX_PATH env      -> nothing touches /dev/dax0.0.
#   - No GLIBC_TUNABLES AVX-512 disable     -> not needed off the CXL path.
#
# This is the DRAM reference point for comparing against mpi_cxl_qemuless
# (OpenMPI + CXL shim) and cmpi (MPICH + CXL shared memory).

PINNING=""

# No CXL shim: make sure nothing is preloaded.
unset LD_PRELOAD
export LD_PRELOAD

MPIRUN="/home/sherry/openmpi-install/bin/mpirun"

# Single-node: no hostfile, all processes mapped locally.
MPIARGS="--allow-run-as-root -np ${NUM_PROCESS} --map-by ppr:${PPN}:node"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_OPENMPI_DIR}"
