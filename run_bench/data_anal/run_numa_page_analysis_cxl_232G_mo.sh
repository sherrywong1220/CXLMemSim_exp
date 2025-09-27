#!/bin/bash

# NUMA page result parsing script runner with environment variable configuration

# Set environment variables for NUMA page data analysis
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_TIERING_VERS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo"

echo "Starting NUMA page result data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_TIERING_VERS: $DATA_ANAL_TIERING_VERS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

# Run NUMA page result parsing
echo "Running NUMA page result analysis..."
../../venv/bin/python3 parse_numa_page_results.py

if [ $? -eq 0 ]; then
    echo ""
    echo "NUMA page result analysis completed!"
    echo "Generated tables saved in numa_page_tables/ directory"
    
    # List generated files
    if [ -d "numa_page_tables" ]; then
        echo ""
        echo "Generated files:"
        ls -la numa_page_tables/*.{csv,html} 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
    fi
    
    echo ""
    echo "Analysis summary:"
    echo "  - do_numa_page call counts and latencies"
    echo "  - do_huge_pmd_numa_page call counts and latencies" 
    echo "  - Comparison across different tiering versions"
    echo "  - CSV and HTML formatted tables"
else
    echo ""
    echo "NUMA page result analysis failed!"
    exit 1
fi

