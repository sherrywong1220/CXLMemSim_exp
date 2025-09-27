#!/bin/bash

LOG_DIR=${1:-"/tmp/amduprof_cxl_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/amduprof_cxl.log

sudo AMDuProfPcm -m cxl -a -o ${LOG_DIR}/amduprof_cxl.log 