#!/bin/bash

# Data parsing script runner with environment variable configuration

# Set environment variables for data analysis
export DATA_ANAL_BENCHMARKS="pr-twitter-3c bc-twitter-3c bfs-twitter-3c cc-twitter-3c bc-urand-2c bfs-urand-2c cc-urand-2c pr-urand-2c bc-web-2c bfs-web-2c cc-web-2c pr-web-2c NPB-FT.C NPB-MG.D NPB-CG.D-2c silo_ycsb"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="stress1G_t2r82_soft_cxl_20G_ht250"
export CSV_FILE="perf_results_autonuma_stress1G_t2r82_soft_cxl_20G_ht250_wi.csv"

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