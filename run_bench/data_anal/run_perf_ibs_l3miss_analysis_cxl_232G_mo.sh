#!/bin/bash

export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_TIERING_VERS="autonuma_tiering_thp"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo_hot"

echo "Starting Perf IBS result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_TIERING_VERS: $DATA_ANAL_TIERING_VERS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

echo "Running Perf IBS result analysis..."
../../venv/bin/python3 parse_perf_ibs_l3miss_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Perf IBS result analysis completed!"
    echo "Generated tables saved in perf_ibs_l3miss_tables// directory"
else
    echo ""
    echo "Perf IBS L3 miss result analysis failed!"
    exit 1
fi
