#!/bin/bash

BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D"
MEM_POLICYS="cpu0.weightedinterleave0_2"

export OMP_NUM_THREADS=8

# sudo dmesg -c

# TIERING_VER="autonuma"
# TIERING_VER="tiering-0.8"
# TIERING_VER="tpp"
# TIERING_VER="memtis"
# TIERING_VER="autonuma_tiering"
TIERING_VER="nobalance"
export TIERING_VER

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="80G"

mkdir -p log

for BENCH in ${BENCHMARKS};
do
    for MP in ${MEM_POLICYS};
    do
	# ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log

    CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
    echo "current_time ${CURRENT_TIME}"
    ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE}
    sleep 15
    done
done
