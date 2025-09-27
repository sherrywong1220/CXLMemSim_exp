#!/bin/bash

LOG_DIR=${1:-"/tmp/perf_tlb_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/perf_tlb.log

sudo perf stat -a -I 5000 -M tlb -o ${LOG_DIR}/perf_tlb.log