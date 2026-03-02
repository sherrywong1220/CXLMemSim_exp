# Data Parsing Script

This directory contains scripts for parsing experiment result data with configurable benchmarks and tiering versions through environment variables.


## Usage

Environment Variables Configuration in `run_anal.sh`:  

```bash
### DATA_ANAL_BENCHMARKS
export DATA_ANAL_BENCHMARKS="bc-urand bc-web bfs-urand bfs-web cc-urand cc-web pr-urand pr-web NPB-BT.D NPB-CG.D NPB-FT.C NPB-LU.D NPB-MG.D NPB-SP.D faster_uniform_ycsb_a faster_uniform_ycsb_b faster_uniform_ycsb_c faster_uniform_ycsb_f faster_ycsb_a faster_ycsb_f tpch_9 tpch_20 tpch_21"

### DATA_ANAL_NET_CONFIGS
export DATA_ANAL_NET_CONFIGS="nobalance nobalance_thp nobalance_thp_64K nobalance_thp_512K autonuma_tiering autonuma_tiering_thp  autonuma_tiering_thp_64K autonuma_tiering_thp_512K"

### DATA_ANAL_MEM_POLICYS
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2"

### DATA_ANAL_LDRAM_SIZES
export DATA_ANAL_LDRAM_SIZES="4G 80G"
```

Runs the analysis:  

```bash
cd data_anal
bash run_anal.sh
bash run_hard_dram.sh
```

## Output

The script generates a CSV file named `perf_results.csv` with the following columns:

- workload: Workload name
- tiering: Memory tiering version
- mem_policy: Memory policy configuration
- ldram_size: LDRAM size configuration
- execution_time: Execution time (seconds)
- throughput: Throughput metric (workload-specific)
- rss: RSS difference (GB)
- pgpromote_success: Number of successful page promotions
- numa_pte_updates: Number of NUMA page table updates
- numa_huge_pte_updates: Number of NUMA huge page table updates
- numa_hint_faults: Number of NUMA hint faults
- pgmigrate_success: Number of successful page migrations
- pgmigrate_fail: Number of failed page migrations
- numa_pages_migrated: Number of NUMA pages migrated
- thp_migration_success: Number of successful THP migrations
- thp_migration_success_2 through thp_migration_success_9: Additional THP migration success metrics
- thp_fault_alloc: Number of THP fault allocations
- thp_fault_alloc_2 through thp_fault_alloc_9: Additional THP fault allocation metrics
- thp_migration_split: Number of THP migration splits
- thp_migration_split_2 through thp_migration_split_9: Additional THP migration split metrics
- thp_migration_fail: Number of failed THP migrations
- thp_migration_fail_2 through thp_migration_fail_9: Additional THP migration failure metrics
- numa_local: Number of local NUMA accesses
- numa_other: Number of other NUMA accesses

## Directory Structure Requirements

Expected result directory structure:
```
run_bench/results/
├── bc-urand/
│   ├── autonuma_tiering/
│   ├── autonuma_tiering_thp/
│   ├── nobalance/
│   └── nobalance_thp/
├── bc-web/
│   ├── autonuma_tiering/
│   ├── autonuma_tiering_thp/
│   ├── nobalance/
│   └── nobalance_thp/
└── [other workloads]/
    └── [tiering versions]/
        └── [memory policies]/
            └── [memory sizes]/
                ├── output.log
                ├── rss.log
                ├── before_vmstat.log
                └── after_vmstat.log
```

Each result directory should contain:
```
cpu*.weightedinterleave*/80G/
├── output.log
├── rss.log
├── before_vmstat.log
└── after_vmstat.log
```

## Environment Variables

The script requires the following environment variables to be set:

- `DATA_ANAL_BENCHMARKS`: Space-separated list of workload names
- `DATA_ANAL_NET_CONFIGS`: Space-separated list of tiering versions
- `DATA_ANAL_MEM_POLICYS`: Space-separated list of memory policy configurations
- `DATA_ANAL_LDRAM_SIZES`: Space-separated list of LDRAM size configurations (e.g., "80G 120G 160G")
- `CSV_FILE`: Output CSV filename

## Notes

- The script automatically handles missing files and outputs warning messages to console
- If a metric cannot be parsed, the corresponding CSV cell will be empty
- The script supports processing multiple CPU configurations and memory size configurations
- Environment variables allow flexible configuration without modifying the script
- The script will show the configuration being used at startup
- LDRAM sizes are specified as strings in the environment variable and used directly as directory names 