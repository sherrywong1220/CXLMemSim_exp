#!/bin/bash

# AMDuProf CXL result parsing script runner with environment variable configuration

# Set environment variables for AMDuProf CXL data analysis
export DATA_ANAL_BENCHMARKS="MIX"
export DATA_ANAL_TIERING_VERS="nobalance_thp"
export DATA_ANAL_MEM_POLICYS="cpu0.firsttouch0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_10G_mo_amduprof_cxl_ft21"

echo "Starting AMDuProf CXL data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_TIERING_VERS: $DATA_ANAL_TIERING_VERS"
echo "  DATA_ANAL_MEM_POLICYS: $DATA_ANAL_MEM_POLICYS"
echo "  DATA_ANAL_LDRAM_SIZES: $DATA_ANAL_LDRAM_SIZES"
echo ""

# Check if virtual environment exists
if [ ! -d "../../venv" ]; then
    echo "Error: Virtual environment not found at ../../venv"
    echo "Please create a virtual environment first"
    exit 1
fi

# Run AMDuProf CXL result analysis
echo "Running AMDuProf CXL analysis..."
../../venv/bin/python3 parse_amduprof_cxl.py

if [ $? -eq 0 ]; then
    echo ""
    echo "AMDuProf CXL analysis completed!"
    echo "Generated plots saved in cxl_plots/ directory"
    
    # List generated files
    if [ -d "cxl_plots" ]; then
        echo ""
        echo "Generated files:"
        ls -la cxl_plots/*.png 2>/dev/null | awk '{print "  - " $9}' | sed 's|.*/||'
    fi
    
    echo ""
    echo "Analysis summary:"
    echo "  - CXL Read Memory BW trends for each workload and memory policy"
    echo "  - CXL Write Memory BW trends for each workload and memory policy" 
    echo "  - Comparison across different tiering versions"
    echo "  - Statistical summary of memory traffic patterns"
else
    echo ""
    echo "AMDuProf CXL analysis failed!"
    exit 1
fi
