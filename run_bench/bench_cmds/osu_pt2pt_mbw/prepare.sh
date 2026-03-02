#!/bin/bash

APP_RUN="osu-micro-benchmarks-7.4/c/mpi/pt2pt/osu_mbw_mr -m :8388608 -i 2000"
BENCH_RUN="env ${RUN_ENV1} ${MPIRUN} ${MPIARGS} ${APP_RUN}"

