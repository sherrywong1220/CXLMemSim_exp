#!/bin/bash

BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-CG.D"
MEM_POLICYS="cpu0.firsttouch0_2 cpu0.weightedinterleave0_2.12 cpu0.weightedinterleave0_2 cpu0.weightedinterleave0_2.43 cpu0.weightedinterleave0_2.21 cpu0.weightedinterleave0_2.13"
export OMP_NUM_THREADS=8

TIERING_VERS="nobalance_thp_512K autonuma_tiering_thp_512K nobalance_thp_64K autonuma_tiering_thp_64K nobalance_thp autonuma_tiering_thp nobalance autonuma_tiering"

LOCAL_DRAM_SIZE="10G"

mkdir -p log

for TIERING_VER in ${TIERING_VERS};
do
    echo "TIERING_VER ${TIERING_VER}"
    export TIERING_VER
    for BENCH in ${BENCHMARKS};
    do
        for MP in ${MEM_POLICYS};
        do
    	# ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log

        CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
        echo "${TIERING_VER}_${CURRENT_TIME}"
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done
