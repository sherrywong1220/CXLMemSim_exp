#!/bin/bash

if [[ "${TIERING_VER}" == *"nobalance"* ]]; then
    PINNING="numactl -N 0 --"
else
    PINNING="numactl -b -N 0 --"
fi