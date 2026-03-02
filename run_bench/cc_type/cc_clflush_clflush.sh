#!/bin/bash
# CC_TYPE: cc_clflush_clflush - CLFLUSH + CLFLUSH
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clflush_clflush"
SHIM_LIB="${WORKLOAD_DIR}/gromacs/libmpi_cxl_shim_cc_clflush_clflush.so"
export LD_PRELOAD="${SHIM_LIB}"
