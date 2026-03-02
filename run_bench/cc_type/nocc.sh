#!/bin/bash
# CC_TYPE: nocc - no cache control shim
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="nocc"
SHIM_LIB="${WORKLOAD_DIR}/gromacs/libmpi_cxl_shim_nocc.so"
export LD_PRELOAD="${SHIM_LIB}"