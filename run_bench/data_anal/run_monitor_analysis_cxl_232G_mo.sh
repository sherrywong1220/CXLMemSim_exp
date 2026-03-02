#!/bin/bash

# Monitor result parsing script runner with environment variable configuration

# Set environment variables for monitor data analysis
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo"

echo "Starting monitor result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_NET_CONFIGS: $DATA_ANAL_NET_CONFIGS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

# Run monitor result parsing
echo "Running monitor result analysis..."
../../venv/bin/python3 parse_monitor_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Monitor result analysis completed!"
    echo "Generated plots saved in monitoring_plots/ directory"
else
    echo ""
    echo "Monitor result analysis failed!"
    exit 1
fi
