#!/bin/bash
# CC_TYPE: cc_clflush_clflush - CLFLUSH + CLFLUSH
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clflush_clflush"
export MPI_SHIM_LIB="${CXL_SHM_LIB_DIR}/libmpi_cxl_shim_cc_clflush_clflush.so"

