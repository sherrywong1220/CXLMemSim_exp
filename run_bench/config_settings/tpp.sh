#!/bin/bash
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

echo "inherit" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-2048kB/enabled
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-64kB/enabled
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-512kB/enabled

echo 2 | sudo tee /proc/sys/kernel/numa_balancing
echo 1 | sudo tee /sys/kernel/mm/numa/demotion_enabled