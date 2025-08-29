#!/bin/bash

echo 4 | sudo tee /sys/kernel/mm/mempolicy/weighted_interleave/node0
echo 1 | sudo tee /sys/kernel/mm/mempolicy/weighted_interleave/node1
echo 3 | sudo tee /sys/kernel/mm/mempolicy/weighted_interleave/node2
echo 1 | sudo tee /sys/kernel/mm/mempolicy/weighted_interleave/node3

if [[ "${TIERING_VER}" == *"nobalance"* ]]; then
    PINNING="numactl -N 0 -w 0,2 --"
else
    PINNING="numactl -b -N 0 -w 0,2 --"
fi