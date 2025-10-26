#!/bin/bash

LOG_DIR=${1:-"/tmp/perf_ibs_op_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/perf_ibs_op.log

# sudo perf record -e ibs_op// -a --data --phys-data -o ${LOG_DIR}/perf_ibs_op.log 
sudo perf record -e ibs_op/l3missonly/ -a --data --phys-data -o ${LOG_DIR}/perf_ibs_op.log 