#!/bin/bash
# Run OSU eval scripts in order: put_bw (node2), get_mbw (nodes 1–4), get_multi_lat (nodes 1–4).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SCRIPTS=(
    run_osu_get_mbw_cmpi_node1_20260302.sh
    run_osu_get_multi_lat_cmpi_node1_20260302.sh
    run_osu_get_mbw_mpi_cxl_qemuless_node1_20260302.sh
    run_osu_get_multi_lat_mpi_cxl_qemuless_node1_20260302.sh
)

for s in "${SCRIPTS[@]}"; do
  echo "========== $(date -Iseconds)  Running: ${s} =========="
  bash "${SCRIPT_DIR}/${s}"
done

echo "========== $(date -Iseconds)  All ${#SCRIPTS[@]} scripts finished =========="
