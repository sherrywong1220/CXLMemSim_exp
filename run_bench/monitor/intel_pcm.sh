#!/bin/bash

LOG_DIR=${1:-"/tmp/intel_pcm_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/pcm_memory.csv

sudo pcm-memory -i=1 -csv="$LOG_DIR/pcm_memory.csv"
