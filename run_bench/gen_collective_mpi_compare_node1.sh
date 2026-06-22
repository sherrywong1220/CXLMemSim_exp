#!/bin/bash
set -euo pipefail

# Generate run_<usecase>.sh scripts to compare collective (allreduce / allgather /
# alltoall) performance across three single-node MPI stacks:
#
#   mpi_cxl_qemuless  - OpenMPI 5.0.3 + CXL shim (LD_PRELOAD), data on /dev/dax0.0
#   openmpi_native    - native OpenMPI 5.0.3, no shim, DRAM baseline
#   cmpi              - MPICH 4.2.3 built --with-shared-memory=cxl
#
# One self-contained run script is produced per net config; each runs all three
# collectives across every NUM_PROCESS. Results land under
#   results/<bench>/<net_config>/nocc/<np>/<usecase>/<timestamp>/
# so the net_config dimension keeps the three stacks separated for analysis.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BENCHMARKS="osu_allreduce osu_allgather osu_alltoall"
NET_CONFIGS="mpi_cxl_qemuless openmpi_native cmpi"
PROCESS_LIST="2 4 8 16 32"
NUM_NODES="1"
CC_TYPE="nocc"
DATE_TAG="20260620"
OUT_DIR="${SCRIPT_DIR}/eval_scripts"

for NET_CONFIG in ${NET_CONFIGS}; do
  USE_CASE_BASE="collective_${NET_CONFIG}_node1_${DATE_TAG}"
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
done
