#!/bin/bash

if [[ "${NET_CONFIG}" == "cmpi" || "${NET_CONFIG}" == "mpi_cxl_qemuless" ]]; then
  OSU_MSG_SIZE=":1048576"
else
  OSU_MSG_SIZE=":16384"
fi

APP_RUN="${OSU_BENCH_DIR}/mpi/pt2pt/osu_mbw_mr -m ${OSU_MSG_SIZE} -i 200"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"

