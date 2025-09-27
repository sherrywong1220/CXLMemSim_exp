# MemEater

The `memeater` kernel module is designed to consume memory on a specific NUMA node for memory tiering benchmarks. 

## Build memeater module

To build  `memeater`, edit `LOCAL_NUMA` to the NUMA node number of the default tier, and `FARMEM_NUMA` to the NUMA node number of the alternate tier in `run_bench/memeater/memeater.c`

```
sudo make
```

## Note

If you change the kernel, you need to rebuild the module again.

```  
make clean  
sudo make
```  

## Usage
### Basic Usage

```bash
# Load module with required sizeMiB parameter (Amount of memory to consume in megabytes)
sudo insmod memeater.ko sizeMiB=1024

# Check whether the module is live
cat /proc/modules | grep memeater

# Unload module (releases all allocated memory)
sudo rmmod memeater
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sizeMiB` | int | 0 (required) | Amount of memory to consume in megabytes |
| `PGSIZE` | int | 4096 | Page size in bytes (4096 = 4KB, 2097152 = 2MB) |
| `PGORDER` | int | 0 | Page allocation order (2^PGORDER consecutive pages) |

### Examples

```bash
# Consume 1GB using standard 4KB pages
sudo insmod memeater.ko sizeMiB=1024

# Consume 2GB using 2MB huge pages
sudo insmod memeater.ko sizeMiB=2048 PGSIZE=2097152 PGORDER=9

# Dynamic sizing based on available memory using standard 4KB pages
sudo insmod memeater.ko sizeMiB=$(numastat -m | grep MemFree | awk '{print int($2-4096)}')

# Check memory consumption
numastat -m

# Unload when done
sudo rmmod memeater

```

### Acknowledgement
The source code of MemEater is from the marvalous work in this [publication(SOSP24-colloid)](https://dl.acm.org/doi/10.1145/3694715.3695968).

