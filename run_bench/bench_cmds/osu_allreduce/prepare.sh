#!/bin/bash

if [[ "${NET_CONFIG}" == "cmpi" || "${NET_CONFIG}" == "mpi_cxl_qemuless" || "${NET_CONFIG}" == "openmpi_native" ]]; then
  OSU_MSG_SIZE=":1048576"
else
  OSU_MSG_SIZE=":16384"
fi

# -T mpi_float: OSU 7.4 defaults to MPI_CHAR, which is not on the shim's
# allreduce datatype allowlist (reduction needs typed arithmetic) and thus
# always passes through to the underlying MPI. mpi_float exercises the CXL
# collective path for sizes <= CXL_DIRECT_MAX_BYTES (default 4096).
APP_RUN="${OSU_BENCH_DIR}/mpi/collective/blocking/osu_allreduce -T mpi_float -m ${OSU_MSG_SIZE} -i 200"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"

