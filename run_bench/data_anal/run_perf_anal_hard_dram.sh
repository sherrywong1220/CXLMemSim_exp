#!/bin/bash

# Data parsing script runner with environment variable configuration

# Set environment variables for data analysis
export DATA_ANAL_BENCHMARKS="faster_ycsb_a faster_ycsb_f faster_uniform_ycsb_a faster_uniform_ycsb_f bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web"
export DATA_ANAL_TIERING_VERS="nobalance nobalance_thp nobalance_thp_512K nobalance_thp_64K autonuma_tiering autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K"
export DATA_ANAL_MEM_POLICYS="cpu0.firsttouch0_2"
export DATA_ANAL_LDRAM_SIZES="4G"
export CSV_FILE="perf_results_hard_dram.csv"

echo "Starting result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_TIERING_VERS: $DATA_ANAL_TIERING_VERS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo ""

../../venv/bin/python3 parse_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Data parsing completed!"
    echo "Generated CSV file: $CSV_FILE"
else
    echo ""
    echo "Data parsing failed!"
    exit 1
fi 

echo "Starting performance results analysis..."
../../venv/bin/python3 analyze_perf_results.py "$CSV_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "Performance analysis completed!"
    echo "Check the generated .txt file for detailed analysis results."
else
    echo ""
    echo "Performance analysis failed!"
    exit 1
fi 