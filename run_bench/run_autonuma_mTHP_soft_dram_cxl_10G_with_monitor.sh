#!/bin/bash

BENCHMARKS="NPB-MG.D bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-SP.D silo_ycsb"
MEM_POLICYS="cpu0.firsttouch0_2 cpu0.weightedinterleave0_2 cpu0.weightedinterleave0_2.14"

export OMP_NUM_THREADS=8

TIERING_VERS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="soft_cxl_10G_mo"
# LOCAL_DRAM_SIZE="111G"

mkdir -p log

echo 3 | sudo tee /proc/sys/vm/drop_caches
free
sleep 5

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
    	# ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log

        CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
        echo "current_time ${CURRENT_TIME}"
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} -MO >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done

sudo rmmod ./memeater/memeater.ko;
