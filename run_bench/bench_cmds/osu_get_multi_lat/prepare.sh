#!/bin/bash

APP_RUN="osu-micro-benchmarks-7.4/c/mpi/one-sided/osu_get_multi_lat -m :8388608 -i 2000 -s pscw"
BENCH_RUN="env ${RUN_ENV1} ${MPIRUN} ${MPIARGS} ${APP_RUN}"
