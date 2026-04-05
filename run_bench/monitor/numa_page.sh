#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../env.sh"
DIR=${DIR:-"$(cd "${SCRIPT_DIR}/.." && pwd)"}

LOG_DIR=${1:-"/tmp/numa_page_logs"}

mkdir -p ${LOG_DIR}

rm -f ${LOG_DIR}/numa_page.log

sudo bpftrace ${DIR}/monitor/numa_page.bt >> ${LOG_DIR}/numa_page.log