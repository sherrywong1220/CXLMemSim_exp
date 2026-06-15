#!/bin/bash
set -euo pipefail

# Generate run script for LULESH baseline s=300 on 1 node qemuless.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCH_NAME="lulesh_baseline_s300"
USE_CASE_BASE="lulesh_baseline_s300_mpi_cxl_qemuless_node1_20260407"
# Match the cxl s300 config so the comparison is strictly "DRAM vs CXL DAX
# for domain arrays" — no shim in either arm.
NET_CONFIG="mpi_cxl_qemuless_noshim"
NUM_NODES="1"
PROCESS_LIST="1 8 27"
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
