#!/bin/bash

# Data parsing script runner with environment variable configuration

# Set environment variables for data analysis
export DATA_ANAL_BENCHMARKS="faster_uniform_ycsb_a faster_uniform_ycsb_b faster_uniform_ycsb_c faster_uniform_ycsb_f faster_ycsb_a faster_ycsb_f"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering nobalance autonuma_tiering_thp nobalance_thp autonuma_tiering_thp_512K nobalance_thp_512K autonuma_tiering_thp_64K nobalance_thp_64K"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.13 cpu0.weightedinterleave0_2.12 cpu0.weightedinterleave0_2 cpu0.weightedinterleave0_2.43 cpu0.weightedinterleave0_2.21"
export DATA_ANAL_LDRAM_SIZES="4G"
export CSV_FILE="perf_results_ldram4G_wi.csv"

echo "Starting result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_NET_CONFIGS: $DATA_ANAL_NET_CONFIGS"
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