#!/bin/bash

# Enable hyper threading
if [ "$(cat /sys/devices/system/cpu/smt/control)" == "off" ]; then
    sudo bash -c "echo on > /sys/devices/system/cpu/smt/control"
    echo "Hyper threading enabled"
fi
