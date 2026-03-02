#!/bin/bash
PINNING=""
MPIRUN="/opt/intel/oneapi/mpi/2021.17/bin/mpirun"
RUN_ENV1="UCX_LOG_LEVEL=info"
MPIARGS="-np ${NUM_PROCESS} -ppn ${PPN} -hostfile ${DIR}/mpi_hostfile"

