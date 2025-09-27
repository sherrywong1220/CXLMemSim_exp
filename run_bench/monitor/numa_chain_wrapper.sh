#!/bin/bash

# Set DIR to the run_bench directory
DIR=${DIR:-"/home/sherry/projects/eBPF_mem_tiering/run_bench"}

LOG_DIR=${1:-"/tmp/numa_chain_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/numa_chain.log

sudo ${DIR}/monitor/numa_chain.sh run  >> ${LOG_DIR}/numa_chain.log