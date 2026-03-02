#!/bin/bash

# Memory traffic analysis script runner with environment variable configuration

# Set environment variables for PCM memory traffic data analysis
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering_thp"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="full_dram_mo_intel_mlc"

echo "Starting PCM memory traffic data analysis..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_NET_CONFIGS: $DATA_ANAL_NET_CONFIGS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

# Run PCM memory traffic analysis
echo "Running PCM memory traffic analysis..."
../../venv/bin/python3 parse_mem_traffic.py

if [ $? -eq 0 ]; then
    echo ""
    echo "PCM memory traffic analysis completed!"
    echo "Generated plots saved in memory_traffic_plots/ directory"
    
    # List generated files
    if [ -d "memory_traffic_plots" ]; then
        echo ""
        echo "Generated files:"
        ls -la memory_traffic_plots/*.png 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
    fi
    
    echo ""
    echo "Analysis summary:"
    echo "  - Memory Read (MB/s) trends"
    echo "  - Memory Write (MB/s) trends" 
    echo "  - PMM Read (MB/s) trends"
    echo "  - PMM Write (MB/s) trends"
    echo "  - Comparison across different tiering versions"
else
    echo ""
    echo "PCM memory traffic analysis failed!"
    exit 1
fi
