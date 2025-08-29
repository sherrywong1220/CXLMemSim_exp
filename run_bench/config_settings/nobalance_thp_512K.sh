#!/bin/bash

echo "always" | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
echo "always" | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-2048kB/enabled
echo "never" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-64kB/enabled
echo "inherit" | sudo tee /sys/kernel/mm/transparent_hugepage/hugepages-512kB/enabled


echo 0 | sudo tee /proc/sys/kernel/numa_balancing
echo 0 | sudo tee /sys/kernel/mm/numa/demotion_enabled