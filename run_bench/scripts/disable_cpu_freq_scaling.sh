#!/bin/bash

if [ ! -e "/sys/devices/system/cpu/intel_pstate" ] ||
   [ "$(cat /sys/devices/system/cpu/intel_pstate/status)" == "off" ]; then
    printf "Intel pstate is not the CPU frequency scaling driver. Please disable CPU frequency scaling manually.\n"
    exit 1
fi

# Silent pushd and popd
pushd () {
    command pushd "$@" > /dev/null
}
popd () {
    command popd "$@" > /dev/null
}

pushd /sys/devices/system/cpu
for CORE in cpu[0-9]*; do
    pushd $CORE

    if [ -e "online" ] && [ "$(cat online)" == "0" ]; then
        popd
        continue
    fi

    pushd cpufreq
    # default value: powersave
    sudo bash -c "echo \"performance\" > scaling_governor"
    sudo bash -c "echo $(cat cpuinfo_max_freq) > scaling_max_freq"
    sudo bash -c "echo $(cat cpuinfo_max_freq) > scaling_min_freq"
    popd

    popd
done
popd

pushd /sys/devices/system/cpu/intel_pstate
# default value: 0
sudo bash -c "echo 1 > no_turbo"
# default value: 100
sudo bash -c "echo 100 > max_perf_pct"
# default value: 27
sudo bash -c "echo 100 > min_perf_pct"
popd