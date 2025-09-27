#!/bin/bash

# Set DIR to the run_bench directory
DIR=${DIR:-"/home/sherry/projects/eBPF_mem_tiering/run_bench"}

LOG_DIR=${1:-"/tmp/numa_page_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/numa_page.log

sudo bpftrace ${DIR}/monitor/numa_page.bt >> ${LOG_DIR}/numa_page.log