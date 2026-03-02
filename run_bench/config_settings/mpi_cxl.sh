#!/bin/bash
PINNING=""
MPIRUN="/opt/intel/oneapi/mpi/2021.17/bin/mpirun"
RUN_ENV1="FI_PROVIDER=tcp  FI_TCP_IFACE=ens3f0"
MPIARGS="-np ${NUM_PROCESS} -ppn ${PPN} -hostfile ${DIR}/mpi_hostfile"

# CXL shim env (ref: test_osu_cxl_qemuless.sh, test_stencil_cxl_qemuless.sh)
export CXL_SHIM_WIN=1
export CXL_DAX_RESET=1  # Reset allocation counter on first process
export CXL_SHIM_VERBOSE=1
# CXL_SHIM_VERBOSE: unset when disabled (C lib sees as disabled), export=1 when enabled
if [ "${CXL_SHIM_VERBOSE:-0}" = "1" ]; then
    export CXL_SHIM_VERBOSE=1
else
    unset CXL_SHIM_VERBOSE
fi
export CXL_SHIM_ALLOC=1
export CXL_SHIM_COPY_SEND=1
export CXL_SHIM_COPY_RECV=1
# DAX device or shared memory fallback (default 4GB)
CXL_MEM_SIZE=${CXL_MEM_SIZE:-$((4*1024*1024*1024))}
if [ -e "/dev/dax0.0" ] && [ -r "/dev/dax0.0" ] && [ -w "/dev/dax0.0" ]; then
    export CXL_DAX_PATH="/dev/dax0.0"
else
    export CXL_MEM_SIZE=$CXL_MEM_SIZE
fi