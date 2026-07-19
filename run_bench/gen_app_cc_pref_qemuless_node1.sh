#!/bin/bash
set -euo pipefail

# Generate the cross-application CC-policy preference experiment (qemuless).
#
# Goal: show that different MPI applications prefer different cache-coherency
# (flush) policy variants, extending the single-benchmark (stencil) evidence
# in the paper's Q1. Each benchmark stresses a different shim path:
#   osu_put_latency  2p  - RMA write path (flush target range per Put)
#   osu_get_latency  2p  - RMA read path (invalidate target range per Get)
#   osu_put_bw       2p  - bulk RMA writes, sender buffer reused every iter
#   osu_get_bw       2p  - bulk RMA reads, large invalidate ranges
#   osu_allgather   16p  - flat CXL collective: flush own slot + invalidate N-1
#   osu_alltoall    16p  - flat CXL collective, transpose reads
#   osu_allreduce   16p  - passthrough (datatype not on allowlist): negative control
#   lulesh_baseline  8p  - end-to-end app, mailbox Isend/Irecv path
#
# All seven CC variants run for every benchmark. nocc is the no-coherence
# reference only (single-node-correct; not a coherent candidate cross-host).
#
# NOTE: run the generated script through ./thp_exec, e.g.
#   ./thp_exec bash eval_scripts/run_<usecase>.sh
# if the launching shell has THP_enabled=0 (see thp_exec.c).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CC_TYPES="nocc cc_clwb_clflush cc_clwb_clflushopt cc_clflush_clflush cc_clflush_clflushopt cc_clflushopt_clflush cc_clflushopt_clflushopt"
NET_CONFIG="mpi_cxl_qemuless"
NUM_NODES="1"
USE_CASE_BASE="app_cc_pref_qemuless_node1_20260718"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"
SPEC_FILE="${OUT_DIR}/spec_${USE_CASE_BASE}.txt"

mkdir -p "${OUT_DIR}"

# "bench:np" pairs
BENCH_NP="osu_put_latency:2 osu_get_latency:2 osu_put_bw:2 osu_get_bw:2 osu_allgather:16 osu_alltoall:16 osu_allreduce:16 lulesh_baseline:8"

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
