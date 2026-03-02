#!/bin/bash

# Perf IBS result parsing script runner with environment variable configuration

# Set environment variables for Perf IBS data analysis
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering_thp"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo_hot"

echo "Starting Perf IBS result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_NET_CONFIGS: $DATA_ANAL_NET_CONFIGS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

# Run Perf IBS result parsing
echo "Running Perf IBS result analysis..."
../../venv/bin/python3 parse_perf_ibs_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "Perf IBS result analysis completed!"
    echo "Generated tables saved in perf_ibs_tables/ directory"
    
    # List generated files
    if [ -d "perf_ibs_tables" ]; then
        echo ""
        echo "Generated files:"
        ls -la perf_ibs_tables/*.csv 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
        ls -la perf_ibs_tables/*.txt 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
        if [ -d "perf_ibs_tables/histograms" ]; then
            ls -la perf_ibs_tables/histograms/*.png 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
        fi
    fi
    
    echo ""
    echo "Analysis summary:"
    echo "  - IBS hot pages analysis and statistics"
    echo "  - THP usage efficiency analysis"
    echo "  - Access pattern analysis and recommendations"
    echo "  - Base page and huge page access distribution histograms"
    echo "  - CSV formatted tables"
    echo "  - PNG histogram plots"
    echo "  - Detailed analysis reports in TXT format"
else
    echo ""
    echo "Perf IBS result analysis failed!"
    exit 1
fi
