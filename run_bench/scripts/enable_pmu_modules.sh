#!/bin/bash

sudo modprobe msr
sudo modprobe amd_uncore
sudo modprobe cxl_pci
sudo modprobe cxl_mem
sudo modprobe cxl_pmu