#!/bin/bash
# CC_TYPE: cc_clflushopt_clflush - CLFLUSHOPT + CLFLUSH
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clflushopt_clflush"
export MPI_SHIM_LIB="${CXL_SHM_LIB_DIR}/libmpi_cxl_shim_cc_clflushopt_clflush.so"

