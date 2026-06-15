#!/bin/bash
set -euo pipefail

# Generate run script for LULESH CXL s=80 on 1 node qemuless.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCH_NAME="lulesh_cxl_s80"
USE_CASE_BASE="lulesh_cxl_s80_mpi_cxl_qemuless_node1_20260407"
# lulesh2.0_cxl manages CXL memory itself via cxl_rapid.h; do NOT LD_PRELOAD
# the shim (which would dual-send-leak the pool under halo exchange).
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
