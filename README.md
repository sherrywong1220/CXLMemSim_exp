# eBPF_mem_tiering

```
git clone https://github.com/sherrywong1220/eBPF_mem_tiering.git
cd eBPF_mem_tiering
```

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

## Build other moduels

To build  `memeater`, edit `LOCAL_NUMA` to the NUMA node number of the default tier, and `FARMEM_NUMA` to the NUMA node number of the alternate tier in `run_bench/memeater/memeater.c`

```
cd run_bench
cd memeater
sudo make
```

## Run Benchmarks

```
cd run_bench
bash run_tpp_mTHP_cxl_232G.sh
```