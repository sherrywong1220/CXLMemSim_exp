#!/bin/bash

APP1="${WORKLOAD_DIR}/NPB3.4.2/NPB3.4-OMP/bin/ft.C.x"
APP2="${WORKLOAD_DIR}/NPB3.4.2/NPB3.4-OMP/bin/cg.D.x"

echo "Starting App2..."
numactl -N 0 --  "$APP2" > ${LOG_DIR}/app2.log 2>&1 &

sleep 20 

echo "Starting App1..."
numactl -N 0 --  "$APP1" > ${LOG_DIR}/app1.log 2>&1 &

wait

echo "All applications finished."
