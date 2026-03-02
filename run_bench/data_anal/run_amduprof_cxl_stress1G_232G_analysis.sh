#!/bin/bash

# AMDuProf CXL result parsing script runner with environment variable configuration

# Set environment variables for AMDuProf CXL data analysis
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D silo_ycsb"
export DATA_ANAL_NET_CONFIGS="autonuma_tiering_thp autonuma_tiering_thp_512K autonuma_tiering_thp_64K autonuma_tiering"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2.14 cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="stress1G_cxl_232G"

echo "Starting AMDuProf CXL data parsing..."
echo "Environment variables set:"
echo "  DATA_ANAL_BENCHMARKS: $DATA_ANAL_BENCHMARKS"
echo "  DATA_ANAL_NET_CONFIGS: $DATA_ANAL_NET_CONFIGS"
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
