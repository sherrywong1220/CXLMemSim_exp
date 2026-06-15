#!/bin/bash
set -euo pipefail

# Generate run script for LULESH baseline on 2 nodes (perfect cube process counts).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCH_NAME="lulesh_baseline"
USE_CASE_BASE="lulesh_baseline_mpi_cxl_node2_20260405"
NET_CONFIG="mpi_cxl"
NUM_NODES="2"
PROCESS_LIST="8"
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
