#!/bin/bash
# Run stencil CXL benchmarks: all CC_TYPE variants, multiple grid sizes




CC_TYPES="nocc cc_clwb_clflush cc_clwb_clflushopt cc_clflush_clflush cc_clflush_clflushopt cc_clflushopt_clflush cc_clflushopt_clflushopt"

GRID_SIZES="1000 2000 4000 8000"

USE_CASE="stencil_cc_20260228"

mkdir -p log

# 4 procs (2x2 grid)
for cc in $CC_TYPES; do
        n=1000
        CURRENT_TIME=$(date +%Y%m%d%H%M)
        echo "=== CC_TYPE=$cc GRID_SIZE=$n NUM_PROCS=4 ==="
        ./scripts/run_bench.sh -B "stencil_mpi_ddt_rma_${n}" -V mpi_cxl -C "${USE_CASE}" -T "$cc" -P 4 -N 1 >> ./log/${USE_CASE}_${CURRENT_TIME}.log 2>&1
        sleep 5
done


echo "All stencil CC_TYPE x GRID_SIZE runs completed."
