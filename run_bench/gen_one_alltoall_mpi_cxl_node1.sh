#!/bin/bash
set -euo pipefail

# Generate a single run_#{use_case}.sh containing all one-sided latency benchmark commands
# (all NUM_PROCESS combinations) by calling gen_eval.sh with a spec file.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCH_NAME="osu_alltoall"
USE_CASE_BASE="osu_alltoall_mpi_cxl_node1_20260302"
NET_CONFIG="mpi_cxl"
NUM_NODES="1"
PROCESS_LIST="2 4"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"
CC_TYPE="nocc"

OUT_FILE="${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"
rm -f "${OUT_FILE}"

for p in ${PROCESS_LIST}; do
  "${SCRIPT_DIR}/scripts/gen_eval.sh" \
    -B "${BENCH_NAME}" \
    -T "${CC_TYPE}" \
    -P "${p}" \
    -C "${USE_CASE_BASE}" \
    -V "${NET_CONFIG}" \
    -N "${NUM_NODES}" \
    -o "${OUT_DIR}" \
    --append
done

echo "Done. Script: ${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"

