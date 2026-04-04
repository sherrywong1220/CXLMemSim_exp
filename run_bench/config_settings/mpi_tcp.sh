#!/bin/bash
PINNING=""
MPIRUN="/usr/local/bin/mpirun"
# RUN_ENV1="FI_PROVIDER=tcp FI_TCP_IFACE=ens3f0"
MPIARGS="--allow-run-as-root -np ${NUM_PROCESS} --map-by ppr:${PPN}:node -hostfile /root/hostfile${NUM_NODES} -x CXL_DAX_PATH -x CXL_DAX_RESET -x CXL_SHIM_VERBOSE -x LD_PRELOAD"
