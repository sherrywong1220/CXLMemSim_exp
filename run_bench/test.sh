#!/bin/bash

BENCHMARKS="bc-web"
MEM_POLICYS="cpu0.weightedinterleave0_2"
export OMP_NUM_THREADS=8

TIERING_VERS="nobalance_thp"

LOCAL_DRAM_SIZE="123G"

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
