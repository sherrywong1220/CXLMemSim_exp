#!/bin/bash
set -euo pipefail

# Real-application companion to gen_app_cc_pref_qemuless_node1.sh:
# same seven CC variants, but on real MPI applications rather than OSU
# microbenchmarks.
#   npb_is_d             16p  NPB 3.4.2 IS class D: bulk Alltoallv exchange;
#                             insensitivity control among real apps
#   graph500_simple_s20  16p  Graph500 MPI BFS: high-rate Isend/Irecv through
#                             the CXL mailbox path
#   lulesh_baseline      27p  LULESH 2.0 -s 30: halo Isend/Irecv + allreduce
#                             (8p variant runs in the main OSU spec)
#   stencil_rma_ompi_1000 16p/36p  2D Jacobi RMA halo exchange (real RMA app);
#                             16p balanced, 36p communication-bound
#
# Run each repetition through ./thp_exec (see thp_exec.c):
#   ./thp_exec bash eval_scripts/run_app_cc_pref_apps_qemuless_node1_20260718.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CC_TYPES="nocc cc_clwb_clflush cc_clwb_clflushopt cc_clflush_clflush cc_clflush_clflushopt cc_clflushopt_clflush cc_clflushopt_clflushopt"
NET_CONFIG="mpi_cxl_qemuless"
NUM_NODES="1"
USE_CASE_BASE="app_cc_pref_apps_qemuless_node1_20260718"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"
SPEC_FILE="${OUT_DIR}/spec_${USE_CASE_BASE}.txt"

mkdir -p "${OUT_DIR}"

BENCH_NP="npb_is_d:16 graph500_simple_s20:16 lulesh_baseline:27 stencil_rma_ompi_1000:9 stencil_rma_ompi_1000:16 stencil_rma_ompi_1000:25 stencil_rma_ompi_1000:36"

: > "${SPEC_FILE}"
for cc in ${CC_TYPES}; do
  for pair in ${BENCH_NP}; do
    bench="${pair%%:*}"
    np="${pair##*:}"
    echo "${bench} ${cc} ${np}" >> "${SPEC_FILE}"
  done
done

OUT_FILE="${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"
rm -f "${OUT_FILE}"

"${SCRIPT_DIR}/scripts/gen_eval.sh" \
  -C "${USE_CASE_BASE}" \
  -V "${NET_CONFIG}" \
  -N "${NUM_NODES}" \
  --spec-file "${SPEC_FILE}" \
  -o "${OUT_DIR}"

echo "Done. Script: ${OUT_FILE}"
echo "Run each repetition with: ./thp_exec bash ${OUT_FILE}"
