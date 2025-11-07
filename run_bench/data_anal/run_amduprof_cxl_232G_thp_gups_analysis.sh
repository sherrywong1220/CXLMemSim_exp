#!/bin/bash

# AMDuProf CXL result parsing script runner with environment variable configuration

# Set environment variables for AMDuProf CXL data analysis
# export DATA_ANAL_BENCHMARKS="thp_gups_20_40 thp_gups"
export DATA_ANAL_BENCHMARKS="thp_gups_20_40_op"
export DATA_ANAL_TIERING_VERS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo_amduprof_cxl"

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
else
    echo ""
    echo "AMDuProf CXL analysis failed!"
    exit 1
fi
