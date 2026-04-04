#!/bin/bash
set -euo pipefail

# Generate a single run_#{use_case}.sh containing all stencil benchmark commands
# (all CC_TYPE x GRID_SIZE x PROCESS combinations) by calling gen_eval.sh with a spec file.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CC_TYPES="nocc cc_clwb_clflush cc_clwb_clflushopt cc_clflush_clflush cc_clflush_clflushopt cc_clflushopt_clflush cc_clflushopt_clflushopt"
GRID_SIZES="1000 2000 4000 8000"
USE_CASE_BASE="stencil_cc_$(date +%Y%m%d)"
NET_CONFIG="mpi_cxl"
NUM_NODES="1"
PROCESS_LIST="4 9 16 25 36"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"
OUT_FILE="${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"
rm -f "${OUT_FILE}"

for cc in ${CC_TYPES}; do
  for n in ${GRID_SIZES}; do
    BENCH_NAME="stencil_mpi_ddt_rma_${n}"
    "${SCRIPT_DIR}/scripts/gen_eval.sh" \
      -B "${BENCH_NAME}" \
      -T "${cc}" \
      -P "${PROCESS_LIST}" \
      -C "${USE_CASE_BASE}" \
      -V "${NET_CONFIG}" \
      -N "${NUM_NODES}" \
      -o "${OUT_DIR}" \
      --append
  done
done

echo "Done. Script: ${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"
