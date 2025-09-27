#!/bin/bash

# Set DIR to the run_bench directory
DIR=${DIR:-"/home/sherry/projects/eBPF_mem_tiering/run_bench"}

LOG_DIR=${1:-"/tmp/numa_migrate_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/numa_migrate.log

sudo bpftrace ${DIR}/monitor/numa_migrate.bt >> ${LOG_DIR}/numa_migrate.log