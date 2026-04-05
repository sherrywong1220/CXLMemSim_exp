#!/bin/bash
# CC_TYPE: cc_clflush_clflushopt - CLFLUSH + CLFLUSHOPT
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clflush_clflushopt"
export MPI_SHIM_LIB="${CXL_SHM_LIB_DIR}/libmpi_cxl_shim_cc_clflush_clflushopt.so"

