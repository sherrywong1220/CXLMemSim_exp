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



#  install libmpi_cxl_shim
```
cd gromacs

make CC=/home/sherry/openmpi-install/bin/mpicc MPICC=/home/sherry/openmpi-install/bin/mpicc
```

# cMPI install
```bash
./configure \
    --prefix=/home/sherry/mpich_cxl-install \
    --with-shared-memory=cxl \
    --disable-fortran \
    CC=/home/sherry/gcc-12.3.0/bin/gcc \
    CXX=/home/sherry/gcc-12.3.0/bin/g++ \
    MPICHLIB_CFLAGS="-march=native -mclflushopt" \
    LDFLAGS="-L/home/sherry/gcc-12.3.0/lib64 -Wl,-rpath,/home/sherry/gcc-12.3.0/lib64"

make -j16 && make install
```

# openmpi install
```bash
  ./configure \
      --prefix=/home/sherry/openmpi-install \
      CC=/home/sherry/gcc-12.3.0-install/bin/gcc \
      CXX=/home/sherry/gcc-12.3.0-install/bin/g++ \
      --enable-mpi-fortran=no \
      LDFLAGS="-L/home/sherry/gcc-12.3.0-install/lib64 -Wl,-rpath,/home/sherry/gcc-12.3.0-install/lib64"

make -j16 && make install
```