WORKLOAD_DIR=/home/sherry/CXLMemSim/workloads


# CXL MPI Library
cd /root/gromacs/
./build.sh

# Stencil
cd ${WORKLOAD_DIR}/stencil
make

