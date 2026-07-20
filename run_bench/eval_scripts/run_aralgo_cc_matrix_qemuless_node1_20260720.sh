#!/bin/bash
# Algorithm x CC-policy matrix for CXL allreduce: 3 algos x 6 cc types
# (cc_clflushopt_clflushopt reused from run_aralgo_compare_*) x np {16,32}
# x 3 reps. Rep-major so drift spreads across all cells. nocc first per rep
# (fast, noise reference). Same use_case as the algo compare so the cc axis
# lives in the results path: results/osu_allreduce/mpi_cxl_qemuless/<cc>/...
# Run via: ./thp_exec bash eval_scripts/run_aralgo_cc_matrix_qemuless_node1_20260720.sh

set -u
export DIR="/mnt/nvme01/sherry/CXLMemSim_exp/run_bench"
export CXL_MEM_SIZE="8589934592"

SHIM_DIR=/mnt/nvme01/sherry/CXLMemSim/workloads/gromacs
OSU=/mnt/nvme01/sherry/workloads/osu-micro-benchmarks-7.4-ext-openmpi/c/mpi/collective/blocking/osu_allreduce
MPIRUN=/home/sherry/openmpi-install/bin/mpirun
CC_TYPES="nocc cc_clwb_clflush cc_clwb_clflushopt cc_clflush_clflush cc_clflush_clflushopt cc_clflushopt_clflush"

sudo -n "${DIR}/thp_exec" "${DIR}/clear_dax"

for rep in 1 2 3; do
  for cc in ${CC_TYPES}; do
    if [ "${cc}" = "nocc" ]; then
      SHIM="${SHIM_DIR}/libmpi_cxl_shim_nocc.so"
    else
      SHIM="${SHIM_DIR}/libmpi_cxl_shim_${cc}.so"
    fi
    for algo in flat tree rab; do
      for np in 16 32; do
        LOG_DIR="${DIR}/results/osu_allreduce/mpi_cxl_qemuless/${cc}/${np}/aralgo_${algo}_qemuless_node1_20260720/$(date +%Y%m%d%H%M%S)"
        mkdir -p "${LOG_DIR}"
        sleep 5
        echo "=== rep=${rep} cc=${cc} algo=${algo} np=${np}" | tee "${LOG_DIR}/output.log"
        ${MPIRUN} --allow-run-as-root --mca osc ^ucx -np ${np} --map-by ppr:${np}:node \
          -x CXL_SHIM_ALLOC=1 -x CXL_SHIM_WIN=1 -x CXL_SHIM_COPY_SEND=1 -x CXL_SHIM_COPY_RECV=1 \
          -x CXL_DAX_PATH=/dev/dax0.0 -x CXL_DAX_RESET=1 \
          -x CXL_DIRECT_MAX_BYTES=262144 -x CXL_ALLREDUCE_ALGO=${algo} \
          -x GLIBC_TUNABLES=glibc.cpu.hwcaps=-AVX512F,-AVX512DQ,-AVX512BW,-AVX512VL \
          -x LD_PRELOAD=${SHIM} \
          ${OSU} -T mpi_float -m :262144 -i 200 2>&1 | tee -a "${LOG_DIR}/output.log"
      done
    done
  done
done
echo "aralgo cc matrix done"
