#!/bin/bash

BENCHMARKS="faster_uniform_ycsb_a faster_uniform_ycsb_b faster_uniform_ycsb_c faster_uniform_ycsb_f faster_ycsb_a faster_ycsb_f"
MEM_POLICYS="cpu0.firsttouch0_2 cpu0.weightedinterleave0_2.12 cpu0.weightedinterleave0_2 cpu0.weightedinterleave0_2.43 cpu0.weightedinterleave0_2.21 cpu0.weightedinterleave0_2.13"

export OMP_NUM_THREADS=8

TIERING_VERS="nobalance_thp_512K tpp_thp_512K nobalance_thp_64K tpp_thp_64K nobalance_thp tpp_thp nobalance tpp"

LOCAL_DRAM_SIZE="soft_cxl_4G"

mkdir -p log

echo 3 | sudo tee /proc/sys/vm/drop_caches
free
sleep 5

local_numa=0
local_size=4096
sudo insmod ./memeater/memeater.ko sizeMiB=$(numastat -m | grep MemFree | awk -v nidx=$local_numa -v sz=$local_size '{print int($(2+nidx)-sz)}');

for TIERING_VER in ${TIERING_VERS};
do
    echo "TIERING_VER ${TIERING_VER}"
    export TIERING_VER
    for BENCH in ${BENCHMARKS};
    do
        for MP in ${MEM_POLICYS};
        do
        CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
        echo "${TIERING_VER}_${CURRENT_TIME}"
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done

sudo rmmod ./memeater/memeater.ko;