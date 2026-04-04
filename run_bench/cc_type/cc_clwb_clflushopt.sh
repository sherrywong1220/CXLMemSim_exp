#!/bin/bash
# CC_TYPE: cc_clwb_clflushopt - CLWB + CLFLUSHOPT
# CXL_SHIM_* etc. are set in config_settings/mpi_cxl.sh

export CC_TYPE="cc_clwb_clflushopt"
export MPI_SHIM_LIB="/root/gromacs/libmpi_cxl_shim_cc_clwb_clflushopt.so"

