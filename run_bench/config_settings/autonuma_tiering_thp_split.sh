#!/bin/bash
echo "always" | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo "always" | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

echo 2 | sudo tee /proc/sys/kernel/numa_balancing
echo 1 | sudo tee /sys/kernel/mm/numa/demotion_enabled