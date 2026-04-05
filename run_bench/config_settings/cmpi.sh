#!/bin/bash
PINNING=""

MPIRUN=/home/sherry/mpich_cxl-install/bin/mpirun

unset LD_PRELOAD
export LD_PRELOAD
# RUN_ENV1="FI_PROVIDER=tcp FI_TCP_IFACE=ens3f0"
MPIARGS="-np ${NUM_PROCESS} -ppn ${PPN}"

export OSU_BENCH_DIR="${OSU_BENCHMARKS_CMPI_DIR}"

