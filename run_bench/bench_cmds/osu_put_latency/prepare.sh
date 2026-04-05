#!/bin/bash

APP_RUN="${OSU_BENCHMARKS_DIR}/mpi/one-sided/osu_put_latency -m :16384 -i 200"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"
