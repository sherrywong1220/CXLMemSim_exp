#!/bin/bash
# CC_TYPE: nocc - no cache control shim
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="nocc"
export MPI_SHIM_LIB="${CXL_SHM_LIB_DIR}/libmpi_cxl_shim_nocc.so"
