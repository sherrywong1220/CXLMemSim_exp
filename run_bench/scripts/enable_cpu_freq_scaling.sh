#!/bin/bash

# Enable CPU frequency scaling and restore default values
# This script reverses the changes made by disable_cpu_freq_scaling.sh

if [ ! -e "/sys/devices/system/cpu/intel_pstate" ] ||
   [ "$(cat /sys/devices/system/cpu/intel_pstate/status)" == "off" ]; then
    printf "Intel pstate is not the CPU frequency scaling driver. Please enable CPU frequency scaling manually.\n"
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
    # Restore default governor: powersave
    sudo bash -c "echo \"powersave\" > scaling_governor"
    
    # Restore default frequency limits
    default_max_freq=$(cat cpuinfo_max_freq)
    default_min_freq=$(cat cpuinfo_min_freq)
    
    sudo bash -c "echo ${default_max_freq} > scaling_max_freq"
    sudo bash -c "echo ${default_min_freq} > scaling_min_freq"
    
    echo "Core $CORE: restored powersave governor and default frequency limits"
    popd

    popd
done
popd

pushd /sys/devices/system/cpu/intel_pstate
sudo bash -c "echo 0 > no_turbo"
sudo bash -c "echo 100 > max_perf_pct"
sudo bash -c "echo 27 > min_perf_pct"
popd

echo "CPU frequency scaling restored to default settings"
echo "- CPU governor: powersave"
echo "- Turbo boost: enabled"
echo "- Performance limits: default" 