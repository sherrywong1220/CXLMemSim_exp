#!/bin/bash
set -euo pipefail

# Generate a qemuless collective run with CC_TYPE=cc_clflushopt_clflushopt, so the
# CXL shim flushes message buffers with CLFLUSHOPT -- matching cMPI, whose
# cxl_shm.c data path uses _mm_clflushopt. This makes the qemuless-vs-cMPI
# comparison apples-to-apples on cacheline write-back behaviour (the existing
# nocc qemuless group does NO cache control).
#
# Same net_config (mpi_cxl_qemuless), benchmarks and np list as the nocc group.
# Results land under a separate cc_type dir, so they don't collide:
#   results/<bench>/mpi_cxl_qemuless/cc_clflushopt_clflushopt/<np>/<usecase>/<ts>/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCHMARKS="osu_allgather osu_allreduce osu_alltoall"
NET_CONFIG="mpi_cxl_qemuless"
CC_TYPE="cc_clflushopt_clflushopt"
PROCESS_LIST="2 4 8 16 32"
NUM_NODES="1"
USE_CASE_BASE="collective_mpi_cxl_qemuless_clflushopt_node1_20260620"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"

OUT_FILE="${OUT_DIR%/}/run_${USE_CASE_BASE}.sh"
rm -f "${OUT_FILE}"

for BENCH_NAME in ${BENCHMARKS}; do
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
done

echo "Done. Script: ${OUT_FILE}"
