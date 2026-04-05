#!/bin/bash

APP_RUN="${OSU_BENCHMARKS_DIR}/mpi/pt2pt/osu_mbw_mr -m :16384 -i 200"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"

