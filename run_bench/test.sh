#!/bin/bash

BENCHMARKS="pr-twitter"
MEM_POLICYS="cpu0.weightedinterleave0_2"

export OMP_NUM_THREADS=8

TIERING_VERS="autonuma_tiering_thp"

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="stress1G_t2r82_cxl_232G"
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

kill -TERM $MEMSTRESS_PID
echo "memstress PID: $MEMSTRESS_PID killed"