#!/bin/bash

if [[ "x${TIERING_VER}" == "xnobalance" || "x${TIERING_VER}" == "xnobalance_thp" ]]; then
    PINNING="numactl -N 0 -w 0,2 --"
else
    PINNING="numactl -b -N 0 -w 0,2 --"
fi