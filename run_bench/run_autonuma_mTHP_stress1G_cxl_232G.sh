#!/bin/bash

BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"

export OMP_NUM_THREADS=8

TIERING_VERS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"

# LOCAL_DRAM_SIZE="40G"
# LOCAL_DRAM_SIZE="65G"
#LOCAL_DRAM_SIZE="100G"
#LOCAL_DRAM_SIZE="120G"
LOCAL_DRAM_SIZE="stress1G_cxl_232G"
# LOCAL_DRAM_SIZE="111G"

mkdir -p log

killall memstress
sleep 10
echo 3 | sudo tee /proc/sys/vm/drop_caches
free
sleep 5
CURRENT_TIME=$(date "+%Y.%m.%d-%H.%M.%S")
MEMSTRESS_LOG="./log/memstress_${CURRENT_TIME}.log"
../tools/memstress -c 62-63 -n 2 -s 512 -b 1024 -w 5 >> "$MEMSTRESS_LOG" 2>&1 &
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
        ./scripts/run_bench.sh -B ${BENCH} -M ${MP} -V ${TIERING_VER} -LM ${LOCAL_DRAM_SIZE} >> ./log/${TIERING_VER}_${CURRENT_TIME}.log 2>&1
        sleep 15
        done
    done
done

kill -TERM $MEMSTRESS_PID
echo "memstress PID: $MEMSTRESS_PID killed"