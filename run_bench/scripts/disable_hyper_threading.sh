#!/bin/bash

# Disable hyper threading
if [ "$(cat /sys/devices/system/cpu/smt/control)" == "on" ]; then
    sudo bash -c "echo off > /sys/devices/system/cpu/smt/control"
fi
