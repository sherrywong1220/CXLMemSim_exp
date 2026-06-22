#!/bin/bash
# One-shot runner: execute the three collective comparison eval scripts back to
# back, methodology-consistent with the historical cMPI / qemuless runs
# (i.e. run the self-contained eval scripts DIRECTLY -- no run_bench.sh, so no
# drop_caches / HT-disable / freq pinning; the scripts' own per-case `sleep 10`
# is the only spacing).
#
# Order: mpi_cxl_qemuless -> openmpi_native -> cmpi (cMPI runs LAST).
#
# Run from a login shell with full Mems_allowed (dax0.0 lives on NUMA node 2);
# qemuless + cmpi touch /dev/dax0.0.
#
# IMPORTANT: cMPI's cxl_shm_init() keys off the `initialized` flag at the start
# of /dev/dax0.0 -- if it is non-zero garbage (qemuless ran first and wrote the
# dax region) rank 0 SKIPS its clean init and the run hangs on a corrupt heap.
# So we zero the dax region with clear_dax immediately before the cMPI stage.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TAG="node1_20260620"

# Ordered: cMPI last.
SCRIPTS=(
  "run_collective_mpi_cxl_qemuless_${TAG}.sh"
  "run_collective_openmpi_native_${TAG}.sh"
  "run_collective_cmpi_${TAG}.sh"
)

rc_overall=0
for s in "${SCRIPTS[@]}"; do
  path="${SCRIPT_DIR}/${s}"
  echo
  echo "==================================================================="
  echo ">>> START ${s}"
  echo "==================================================================="
  if [[ ! -f "${path}" ]]; then
    echo "!!! MISSING: ${path} -- skipped"
    rc_overall=1
    continue
  fi
  # cMPI needs a zeroed dax region (see header) -- wipe it right before cMPI runs.
  if [[ "${s}" == *cmpi* ]]; then
    echo "--- clear_dax before cMPI (reset /dev/dax0.0 init flag) ---"
    if [[ -x "${RUN_DIR}/clear_dax" ]]; then
      "${RUN_DIR}/clear_dax" || { echo "!!! clear_dax failed -- cMPI will likely hang"; rc_overall=1; }
    else
      echo "!!! ${RUN_DIR}/clear_dax not found/executable -- build it (gcc clear_dax.c -o clear_dax)"
      rc_overall=1
    fi
  fi
  bash "${path}"
  rc=$?
  if [[ ${rc} -ne 0 ]]; then
    echo "!!! ${s} exited with code ${rc} (continuing with remaining stacks)"
    rc_overall=1
  else
    echo "<<< DONE  ${s}"
  fi
done

echo
echo "==================================================================="
echo "All three stacks finished. overall rc=${rc_overall}"
echo "Results under: \$DIR/results/<bench>/<net_config>/nocc/<np>/<usecase>/<ts>/"
echo "==================================================================="
exit ${rc_overall}
