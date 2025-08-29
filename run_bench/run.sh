#!/bin/bash

BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D faster_uniform_ycsb_a faster_uniform_ycsb_b faster_uniform_ycsb_c faster_uniform_ycsb_f faster_ycsb_a faster_ycsb_f tpch_9 tpch_20 tpch_21 silo_ycsb"
MEM_POLICYS="cpu0.weightedinterleave0_2"

export OMP_NUM_THREADS=8


# TIERING_VERS="autonuma"
# TIERING_VERS="tiering-0.8"
# TIERING_VERS="tpp"
# TIERING_VERS="memtis"
# TIERING_VERS="autonuma_tiering"
TIERING_VERS="nobalance nobalance_thp autonuma_tiering_thp autonuma_tiering"

LOCAL_DRAM_SIZE="80G"

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
        echo "current_time ${CURRENT_TIME}"
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done
