#!/bin/bash

BENCHMARKS="pr-twitter-3c bc-twitter-3c bfs-twitter-3c cc-twitter-3c bc-urand-2c bfs-urand-2c cc-urand-2c pr-urand-2c bc-web-2c bfs-web-2c cc-web-2c pr-web-2c NPB-FT.C NPB-MG.D NPB-CG.D-2c silo_ycsb"
MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
TIERING_VERS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"

export OMP_NUM_THREADS=8

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="stress1G_t2r82_soft_cxl_20G_ht250"
# LOCAL_DRAM_SIZE="111G"

mkdir -p log

killall memstress
sleep 10
echo 3 | sudo tee /proc/sys/vm/drop_caches
free
sleep 5
CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
MEMSTRESS_LOG="./log/memstress_${CURRENT_TIME}.log"
../tools/memstress/memstress -n 2 -b 1024 -t 2 -c 48 -r 8:2 >> "$MEMSTRESS_LOG" 2>&1 &
MEMSTRESS_PID=$!
echo "memstress PID: $MEMSTRESS_PID"
sleep 10

local_numa=0
local_size=20480
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

kill -TERM $MEMSTRESS_PID
echo "memstress PID: $MEMSTRESS_PID killed"