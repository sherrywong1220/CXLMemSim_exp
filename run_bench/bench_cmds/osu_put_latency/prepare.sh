#!/bin/bash

APP_RUN="/root/osu-micro-benchmarks-7.4-ext/libexec/osu-micro-benchmarks/mpi/one-sided/osu_put_latency -m :16384 -i 200"
BENCH_RUN="${MPIRUN} ${MPIARGS} ${APP_RUN}"
