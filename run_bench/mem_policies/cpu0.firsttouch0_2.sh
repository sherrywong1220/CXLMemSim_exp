#!/bin/bash

if [[ "x${TIERING_VER}" == "xnobalance" || "x${TIERING_VER}" == "xnobalance_thp" ]]; then
    PINNING="numactl -N 0 --"
else
    PINNING="numactl -b -N 0 --"
fi