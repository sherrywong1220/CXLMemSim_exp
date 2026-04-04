# CXLMemSim_EXP


## Linux Kernel Configuration Check

```
cd run_bench
bash check.sh
```

## Install Workloads

```
cd run_bench/workload_install
bash workload_install.sh
```

## Generate Benchmarks Execution Script

```
cd run_bench
bash gen_one_allgather_mpi_cxl_node1.sh

# scp generated scripts in eval_scripts to QEMU VM
scp /home/sherry/CXLMemSim_exp/run_bench/eval_scripts/run_osu_alltoall_mpi_cxl_node1_20260302.sh root@192.168.100.20:/root/cxlmemsim_eval/
```