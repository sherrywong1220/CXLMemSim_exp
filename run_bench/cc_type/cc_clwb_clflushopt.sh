#!/bin/bash
# CC_TYPE: cc_clwb_clflushopt - CLWB + CLFLUSHOPT
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clwb_clflushopt"
SHIM_LIB="${WORKLOAD_DIR}/gromacs/libmpi_cxl_shim_cc_clwb_clflushopt.so"
export LD_PRELOAD="${SHIM_LIB}"
