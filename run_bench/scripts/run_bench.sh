#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${DIR}/../env.sh"

function func_cache_flush() {
    echo 3 | sudo tee /proc/sys/vm/drop_caches
    free
    sleep 5
    return
}

function func_prepare() {
    echo "Preparing benchmark start..."

	ulimit -m unlimited
	ulimit -v unlimited
	ulimit -d unlimited
	ulimit -s unlimited

    echo 0 | sudo tee /proc/sys/kernel/numa_balancing
	sudo sysctl kernel.perf_event_max_sample_rate=100000
	${DIR}/scripts/disable_hyper_threading.sh
	${DIR}/scripts/disable_cpu_freq_scaling.sh
	${DIR}/scripts/set_uncore_freq.sh on
	${DIR}/scripts/enable_pmu_modules.sh
	# echo 1 > /sys/kernel/debug/tracing/events/migrate/mm_migrate_pages/enable
	
	sudo killall bpftrace 2>/dev/null || true
	sudo killall perf 2>/dev/null || true
	sudo killall AMDuProfPcm 2>/dev/null || true
	sudo killall pcm-memory 2>/dev/null || true
	
	DATE=$(date +%Y%m%d%H%M)

    export PPN=$((NUM_PROCESS / NUM_NODES))

    if [[ -e ${DIR}/cc_type/${CC_TYPE}.sh ]]; then
	    source ${DIR}/cc_type/${CC_TYPE}.sh
	else
	    echo "ERROR: ${CC_TYPE}.sh does not exist."
	    exit -1
	fi

    if [[ -e ${DIR}/config_settings/${NET_CONFIG}.sh ]]; then
	    source ${DIR}/config_settings/${NET_CONFIG}.sh
	else
	    echo "ERROR: ${NET_CONFIG}.sh does not exist."
	    exit -1
	fi

	if [[ ! -e ${DIR}/bench_cmds/${BENCH_NAME}/prepare.sh ]]; then
	    echo "ERROR: ${BENCH_NAME}/prepare.sh does not exist."
	    exit -1
	fi

	if [[ ! -e ${DIR}/bench_cmds/${BENCH_NAME}/post.sh ]]; then
	    echo "ERROR: ${BENCH_NAME}/post.sh does not exist."
	    exit -1
	fi
	sleep 5
}

function func_usage() {
    echo
    echo -e "Usage: $0 [-B benchmark] [-V version] [-C usecase] [-T cctype] [-P process] [-N nodes]..."
    echo
    echo "  -B,   --benchmark   [arg]    benchmark name to run. e.g., Graph500, XSBench, etc"
    echo "  -V,   --version     [arg]    version to run. e.g., autonuma, TPP, etc"
	echo "  -C,   --usecase     [arg]    use case to run. e.g., cxl_232G, soft_cxl_20G, etc"
	echo "  -T,   --cctype      [arg]    CC_TYPE for CXL shim. e.g., nocc, cc_clwb_clflush, cc_clwb_clflushopt, etc"
	echo "  -P,   --process     [arg]    the number of processes to run."
	echo "  -N,   --nodes       [arg]    the number of nodes to run. e.g., 1, 2, 4, 8, etc"
	echo "  -MO,  --monitor         	monitor mode"
    echo "  -?,   --help"
    echo "        --usage"
    echo
}

# get options:
while (( "$#" )); do
    case "$1" in
	-B|--benchmark)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		BENCH_NAME=( "$2" )
        export BENCH_NAME
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-V|--version)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		NET_CONFIG=( "$2" )
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-C|--usecase)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		USE_CASE=( "$2" )
		export USE_CASE
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-T|--cctype)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		CC_TYPE=( "$2" )
		export CC_TYPE
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-P|--process)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		NUM_PROCESS=( "$2" )
        export NUM_PROCESS
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-N|--nodes)
	    if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
		NUM_NODES=( "$2" )
		export NUM_NODES
		shift 2
	    else
		echo "Error: Argument for $1 is missing" >&2
		func_usage
		exit -1
	    fi
	    ;;
	-MO|--monitor)
	    CONFIG_MONITOR=on
	    shift 1
	    ;;
	-H|-?|-h|--help|--usage)
	    func_usage
	    exit
	    ;;
	*)
	    echo "Error: Invalid option $1"
	    func_usage
	    exit -1
	    ;;
    esac
done

function func_main() {
    TIMESTAMP=$(date +%Y%m%d%H%M)
    export LOG_DIR=${DIR}/results/${BENCH_NAME}/${NET_CONFIG}/${CC_TYPE}/${NUM_PROCESS}/${USE_CASE}/${TIMESTAMP}
    mkdir -p ${LOG_DIR}

	numastat -m > ${LOG_DIR}/before_numastat.log
	cat /proc/vmstat > ${LOG_DIR}/before_vmstat.log
    func_cache_flush
	
	if [[ "x${CONFIG_MONITOR}" == "xon" ]]; then
		echo "CONFIG_MONITOR is on"
		# ${DIR}/monitor/numa_migrate.sh ${LOG_DIR} &
		# ${DIR}/monitor/numa_page.sh ${LOG_DIR} &
		# ${DIR}/monitor/perf_tlb.sh ${LOG_DIR} &
		# ${DIR}/monitor/perf_ibs_op.sh ${LOG_DIR} &
		# ${DIR}/monitor/numa_chain_wrapper.sh ${LOG_DIR} &
		CPU_VENDOR=$(lscpu | grep "Vendor ID" | awk '{print $3}')
		if [[ "${CPU_VENDOR}" == "AuthenticAMD" ]]; then
			echo "Detected AMD CPU, starting amduprof monitoring"
			${DIR}/monitor/amduprof_cxl.sh ${LOG_DIR} &
		elif [[ "${CPU_VENDOR}" == "GenuineIntel" ]]; then
			echo "Detected Intel CPU, starting intel_pcm monitoring"
			${DIR}/monitor/intel_pcm.sh ${LOG_DIR} &
		else
			echo "Unknown CPU type: ${CPU_VENDOR}, skipping hardware monitoring"
		fi
	fi

	source ${DIR}/bench_cmds/${BENCH_NAME}/prepare.sh
	export APP_RUN BENCH_RUN
	CMD="${BENCH_RUN} 2>&1 | tee -a ${LOG_DIR}/output.log"
	echo "${CMD}" | tee ${LOG_DIR}/output.log
	
	eval "${CMD} &"
	WRAPPER_PID=$!
	echo "WRAPPER_PID: ${WRAPPER_PID}"
	wait ${WRAPPER_PID}

	source ${DIR}/bench_cmds/${BENCH_NAME}/post.sh

	if [[ "x${CONFIG_MONITOR}" == "xon" ]]; then
		echo "CONFIG_MONITOR is on"
		sleep 2
		sudo pkill -f numa_chain.sh
		sudo killall bpftrace 2>/dev/null || true
		sudo killall perf 2>/dev/null || true
		sudo killall AMDuProfPcm 2>/dev/null || true
		sudo killall pcm-memory 2>/dev/null || true
	fi
	cat /proc/vmstat > ${LOG_DIR}/after_vmstat.log
    sleep 2

    sudo dmesg -c > ${LOG_DIR}/dmesg.txt
	${DIR}/scripts/set_uncore_freq.sh off
}

func_prepare
func_main
