#!/bin/bash
PINNING=""
MPIRUN="/opt/intel/oneapi/mpi/2021.17/bin/mpirun"
RUN_ENV1="FI_PROVIDER=tcp  FI_TCP_IFACE=ens3f0"
MPIARGS="-np ${NUM_PROCESS} -ppn ${PPN} -hostfile ${DIR}/mpi_hostfile"
