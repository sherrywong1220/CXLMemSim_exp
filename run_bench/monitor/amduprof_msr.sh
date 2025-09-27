#!/bin/bash

LOG_DIR=${1:-"/tmp/amduprof_msr_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/amduprof_msr.log

sudo AMDuProfPcm --msr -a -o ${LOG_DIR}/amduprof_msr.log 