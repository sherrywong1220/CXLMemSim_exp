#!/bin/bash

BENCHMARKS="MIX"
MEM_POLICYS="cpu0.weightedinterleave0_2"

export OMP_NUM_THREADS=8

TIERING_VERS="nobalance_thp"

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="cxl_10G_mo_amduprof_cxl_wi"
# LOCAL_DRAM_SIZE="111G"


mkdir -p log


local_numa=0
local_size=10240
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
        echo "current_time ${CURRENT_TIME}"
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} -MO >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done

sudo rmmod ./memeater/memeater.ko;