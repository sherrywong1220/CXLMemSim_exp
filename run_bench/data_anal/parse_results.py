#!/usr/bin/env python3
"""
Script to parse result data and generate CSV file
Parse execution time, RSS and vmstat data for workloads under different tiering versions
"""

import os
import re
import csv
import glob
import numpy as np
from pathlib import Path
import timestamp_utils

def extract_execution_time(output_log_path, workload=None):
    """Extract execution time from output.log"""
    try:
        with open(output_log_path, 'r') as f:
            content = f.read()
            
        # For specific workloads: parse "Average Time: X.XX" format
        if workload in ['bc-urand', 'bc-web', 'bfs-urand', 'bfs-web', 'cc-urand', 'cc-web', 'pr-urand', 'pr-web']:
            match = re.search(r'Average Time:\s*(\d+\.?\d*)', content)
            if match:
                return float(match.group(1))
        
        # Default case: Find "execution time X.XX (s)" format
        match = re.search(r'execution time (\d+\.?\d*)\s*\(s\)', content)
        if match:
            return float(match.group(1))
            
    except FileNotFoundError:
        print(f"Warning: File not found {output_log_path}")
    except Exception as e:
        print(f"Error parsing execution time {output_log_path}: {e}")
    return None

def extract_throughput(output_log_path, workload):
    """Extract throughput from output.log based on workload type"""
    try:
        with open(output_log_path, 'r') as f:
            content = f.read()
            
        # For bc, bfs, cc, pr, tpch: throughput = 1/execution_time
        if workload in ['bc-urand', 'bc-web', 'bfs-urand', 'bfs-web', 'cc-urand', 'cc-web', 'pr-urand', 'pr-web'] or workload.startswith('tpch'):
            execution_time = extract_execution_time(output_log_path, workload)
            if execution_time and execution_time > 0:
                return round(1.0 / execution_time * 10000, 2)
            return None
        
        # For workloads ending with -2c, -3c, -4c: throughput = 1/execution_time
        elif workload.endswith('-2c') or workload.endswith('-3c') or workload.endswith('-4c'):
            execution_time = extract_execution_time(output_log_path, workload)
            if execution_time and execution_time > 0:
                return round(1.0 / execution_time * 10000, 2)
            return None
        
        # For faster workloads: parse "Finished benchmark: X.XX ops/second/thread"
        elif workload.startswith('faster'):
            match = re.search(r'Finished benchmark:\s*(\d+\.?\d*)\s*ops/second/thread', content)
            if match:
                return float(match.group(1))
            return None
         
        # For NPB workloads: parse "Mop/s total = X.XX"
        elif workload.startswith('NPB'):
            match = re.search(r'Mop/s total\s*=\s*(\d+\.?\d*)', content)
            if match:
                return float(match.group(1))
            return None
        
        # Default case: throughput = 1/execution_time
        else:
            execution_time = extract_execution_time(output_log_path, workload)
            if execution_time and execution_time > 0:
                return round(1.0 / execution_time * 10000, 2)
            return None
            
    except FileNotFoundError:
        print(f"Warning: File not found {output_log_path}")
    except Exception as e:
        print(f"Error parsing throughput {output_log_path}: {e}")
    return None

def extract_rss_difference(rss_log_path):
    """Extract RSS difference from rss.log (last RSS - first RSS)"""
    try:
        with open(rss_log_path, 'r') as f:
            lines = f.readlines()
            
        # Extract all RSS values
        rss_values = []
        for line in lines:
            # Find "Total RSS: X.XXX GB" format
            match = re.search(r'Total RSS:\s*(\d+\.?\d*)\s*GB', line)
            if match:
                rss_values.append(float(match.group(1)))
        
        if len(rss_values) >= 2:
            return round(rss_values[-1] - rss_values[0], 1)
        else:
            print(f"Warning: Not enough data points in RSS log {rss_log_path}")
    except FileNotFoundError:
        print(f"Warning: File not found {rss_log_path}")
    except Exception as e:
        print(f"Error parsing RSS {rss_log_path}: {e}")
    return None

def parse_vmstat_file(vmstat_path):
    """Parse vmstat file, return dictionary of key metrics"""
    vmstat_data = {}
    try:
        with open(vmstat_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0]
                        try:
                            value = int(parts[1])
                            vmstat_data[key] = value
                        except ValueError:
                            continue
    except FileNotFoundError:
        print(f"Warning: File not found {vmstat_path}")
    except Exception as e:
        print(f"Error parsing vmstat file {vmstat_path}: {e}")
    return vmstat_data

def extract_vmstat_differences(before_vmstat_path, after_vmstat_path):
    """Calculate differences in vmstat metrics"""
    before_data = parse_vmstat_file(before_vmstat_path)
    after_data = parse_vmstat_file(after_vmstat_path)
    
    if not before_data or not after_data:
        return None
    
    # Metrics to extract
    metrics = [
        'pgpromote_success',
        'numa_pte_updates', 
        'numa_huge_pte_updates',
        'numa_hint_faults',
        'pgmigrate_success',
        'pgmigrate_fail',
        'numa_pages_migrated',
        'thp_migration_success',
        'thp_migration_success_2',
        'thp_migration_success_3',
        'thp_migration_success_4',
        'thp_migration_success_5',
        'thp_migration_success_6',
        'thp_migration_success_7',
        'thp_migration_success_8',
        'thp_migration_success_9',
        'thp_fault_alloc',
        'thp_fault_alloc_2',
        'thp_fault_alloc_3',
        'thp_fault_alloc_4',
        'thp_fault_alloc_5',
        'thp_fault_alloc_6',
        'thp_fault_alloc_7',
        'thp_fault_alloc_8',
        'thp_fault_alloc_9',
        "thp_migration_split",
        "thp_migration_split_2",
        "thp_migration_split_3",
        "thp_migration_split_4",
        "thp_migration_split_5",
        "thp_migration_split_6",
        "thp_migration_split_7",
        "thp_migration_split_8",
        "thp_migration_split_9",
        "thp_migration_fail",
        "thp_migration_fail_2",
        "thp_migration_fail_3",
        "thp_migration_fail_4",
        "thp_migration_fail_5",
        "thp_migration_fail_6",
        "thp_migration_fail_7",
        "thp_migration_fail_8",
        "thp_migration_fail_9",
        'numa_local',
        'numa_other',
        'pgsteal_kswapd',
        'pgsteal_direct',
        'pgsteal_khugepaged',
        'pgdemote_kswapd',
        'pgdemote_direct',
        'pgdemote_khugepaged'
    ]
    
    differences = {}
    for metric in metrics:
        if metric in before_data and metric in after_data:
            differences[metric] = after_data[metric] - before_data[metric]
        else:
            differences[metric] = None
    
    return differences

def extract_ldram_size(mem_dir_path):
    """Extract LDRAM size from directory name (e.g., '80G' -> 80)"""
    try:
        # Get the directory name (e.g., '80G')
        dir_name = os.path.basename(mem_dir_path)
        # Extract the number before 'G'
        match = re.search(r'(\d+)G', dir_name)
        if match:
            return int(match.group(1))
    except Exception as e:
        print(f"Error extracting LDRAM size from {mem_dir_path}: {e}")
    return None

def get_config_from_env():
    """Get configuration from environment variables"""
    # Get benchmarks from environment variable
    benchmarks_env = os.getenv('DATA_ANAL_BENCHMARKS')
    if not benchmarks_env:
        print("Error: DATA_ANAL_BENCHMARKS environment variable is not set or empty")
        return None, None, None, None
    
    # Get tiering versions from environment variable
    tiering_env = os.getenv('DATA_ANAL_TIERING_VERS')
    if not tiering_env:
        print("Error: DATA_ANAL_TIERING_VERS environment variable is not set or empty")
        return None, None, None, None
    
    # Get memory policies from environment variable
    mem_policies_env = os.getenv('DATA_ANAL_MEM_POLICYS')
    if not mem_policies_env:
        print("Error: DATA_ANAL_MEM_POLICYS environment variable is not set or empty")
        return None, None, None, None
    
    # Get LDRAM sizes from environment variable
    ldram_sizes_env = os.getenv('DATA_ANAL_LDRAM_SIZES')
    if not ldram_sizes_env:
        print("Error: DATA_ANAL_LDRAM_SIZES environment variable is not set or empty")
        return None, None, None, None
    
    workloads = benchmarks_env.split()
    tiering_versions = tiering_env.split()
    mem_policies = mem_policies_env.split()
    ldram_sizes = ldram_sizes_env.split()
    
    print(f"Configuration from environment:")
    print(f"  Benchmarks: {workloads}")
    print(f"  Tiering versions: {tiering_versions}")
    print(f"  Memory policies: {mem_policies}")
    print(f"  LDRAM sizes: {ldram_sizes}")
    
    return workloads, tiering_versions, mem_policies, ldram_sizes

def parse_single_run(timestamp_dir_path, workload):
    """
    Parse data from a single run (timestamp directory)

    Args:
        timestamp_dir_path: Path to timestamp directory
        workload: Workload name for parsing

    Returns:
        Dictionary with parsed metrics or None if parsing fails
    """
    # File paths
    output_log_path = os.path.join(timestamp_dir_path, "output.log")
    rss_log_path = os.path.join(timestamp_dir_path, "rss.log")
    before_vmstat_path = os.path.join(timestamp_dir_path, "before_vmstat.log")
    after_vmstat_path = os.path.join(timestamp_dir_path, "after_vmstat.log")

    # Check if essential files exist
    if not os.path.exists(output_log_path):
        return None

    # Extract data
    execution_time = extract_execution_time(output_log_path, workload)
    throughput = extract_throughput(output_log_path, workload)
    rss = extract_rss_difference(rss_log_path)
    vmstat_diffs = extract_vmstat_differences(before_vmstat_path, after_vmstat_path)

    # Build metrics dictionary
    metrics = {
        'execution_time': execution_time,
        'throughput': throughput,
        'rss': rss
    }

    # Add vmstat data
    if vmstat_diffs:
        metrics.update(vmstat_diffs)

    return metrics


def find_result_directories(results_base_path):
    """
    Find all result directories and parse multiple runs per case
    Returns aggregated data with averages and std deviations
    """
    config_result = get_config_from_env()
    if config_result[0] is None:
        print("Error: Failed to get configuration from environment variables")
        return []

    workloads, tiering_versions, mem_policies, ldram_sizes = config_result

    result_dirs = []

    for workload in workloads:
        workload_path = os.path.join(results_base_path, workload)
        if not os.path.exists(workload_path):
            print(f"Warning: Workload directory not found {workload_path}")
            continue

        for tiering in tiering_versions:
            tiering_path = os.path.join(workload_path, tiering)
            if not os.path.exists(tiering_path):
                print(f"Warning: Tiering directory not found {tiering_path}")
                continue

            # Find memory policy directories
            for mem_policy in mem_policies:
                mem_policy_dirs = glob.glob(os.path.join(tiering_path, mem_policy))
                for mem_policy_dir in mem_policy_dirs:
                    # Use LDRAM sizes from environment variable
                    for ldram_size in ldram_sizes:
                        case_dir = os.path.join(mem_policy_dir, f"{ldram_size}")
                        if not os.path.exists(case_dir):
                            print(f"Warning: LDRAM directory not found {case_dir}")
                            continue

                        # Find all timestamp subdirectories for this case
                        timestamp_dirs = timestamp_utils.get_all_timestamp_dirs(case_dir)

                        if not timestamp_dirs:
                            print(f"Warning: No timestamp directories found in {case_dir}")
                            continue

                        # Parse all runs for this case
                        all_runs_data = []
                        for timestamp_dir in timestamp_dirs:
                            run_data = parse_single_run(timestamp_dir, workload)
                            if run_data:
                                all_runs_data.append(run_data)

                        if not all_runs_data:
                            print(f"Warning: No valid run data found in {case_dir}")
                            continue

                        # Aggregate the data (calculate averages and std)
                        aggregated_data = {
                            'workload': workload,
                            'tiering': tiering,
                            'mem_policy': mem_policy,
                            'ldram_size': ldram_size,
                            'num_runs': len(all_runs_data)
                        }

                        # Calculate statistics for each metric
                        metrics_to_aggregate = [
                            'execution_time', 'throughput', 'rss',
                            'pgpromote_success', 'numa_pte_updates', 'numa_huge_pte_updates',
                            'numa_hint_faults', 'pgmigrate_success', 'pgmigrate_fail', 'numa_pages_migrated',
                            'thp_migration_success', 'thp_migration_success_2', 'thp_migration_success_3',
                            'thp_migration_success_4', 'thp_migration_success_5', 'thp_migration_success_6',
                            'thp_migration_success_7', 'thp_migration_success_8', 'thp_migration_success_9',
                            'thp_fault_alloc', 'thp_fault_alloc_2', 'thp_fault_alloc_3', 'thp_fault_alloc_4',
                            'thp_fault_alloc_5', 'thp_fault_alloc_6', 'thp_fault_alloc_7', 'thp_fault_alloc_8',
                            'thp_fault_alloc_9', 'thp_migration_split', 'thp_migration_split_2',
                            'thp_migration_split_3', 'thp_migration_split_4', 'thp_migration_split_5',
                            'thp_migration_split_6', 'thp_migration_split_7', 'thp_migration_split_8',
                            'thp_migration_split_9', 'thp_migration_fail', 'thp_migration_fail_2',
                            'thp_migration_fail_3', 'thp_migration_fail_4', 'thp_migration_fail_5',
                            'thp_migration_fail_6', 'thp_migration_fail_7', 'thp_migration_fail_8',
                            'thp_migration_fail_9', 'numa_local', 'numa_other',
                            'pgsteal_kswapd', 'pgsteal_direct', 'pgsteal_khugepaged',
                            'pgdemote_kswapd', 'pgdemote_direct', 'pgdemote_khugepaged'
                        ]

                        for metric in metrics_to_aggregate:
                            values = [run.get(metric) for run in all_runs_data if run.get(metric) is not None]
                            if values:
                                aggregated_data[metric] = np.mean(values)
                                aggregated_data[f'{metric}_std'] = np.std(values) if len(values) > 1 else 0
                            else:
                                aggregated_data[metric] = None
                                aggregated_data[f'{metric}_std'] = None

                        result_dirs.append(aggregated_data)

    return result_dirs

def main():
    """Main function"""
    results_base_path = "../results"

    # Find all result directories and get aggregated data
    result_dirs = find_result_directories(results_base_path)

    if not result_dirs:
        print("Error: No result directories found")
        return

    print(f"\nTotal cases processed: {len(result_dirs)}")

    # CSV data is already prepared by find_result_directories (with averages and std)
    csv_data = result_dirs
    
    # Write CSV file
    if csv_data:
        csv_filename = os.getenv('CSV_FILE')

        if csv_filename and not os.path.dirname(csv_filename):
            csv_filename = f"perf_results/{csv_filename}"

        os.makedirs("perf_results", exist_ok=True)

        # Define fieldnames with num_runs, averages, and std columns
        fieldnames = [
            'workload', 'tiering', 'mem_policy', 'ldram_size', 'num_runs',
            'execution_time', 'execution_time_std', 'throughput', 'throughput_std', 'rss', 'rss_std',
            'pgpromote_success', 'pgpromote_success_std',
            'numa_pte_updates', 'numa_pte_updates_std', 'numa_huge_pte_updates', 'numa_huge_pte_updates_std',
            'numa_hint_faults', 'numa_hint_faults_std', 'pgmigrate_success', 'pgmigrate_success_std',
            'pgmigrate_fail', 'pgmigrate_fail_std', 'numa_pages_migrated', 'numa_pages_migrated_std',
            'thp_migration_success', 'thp_migration_success_std',
            'thp_migration_success_2', 'thp_migration_success_2_std',
            'thp_migration_success_3', 'thp_migration_success_3_std',
            'thp_migration_success_4', 'thp_migration_success_4_std',
            'thp_migration_success_5', 'thp_migration_success_5_std',
            'thp_migration_success_6', 'thp_migration_success_6_std',
            'thp_migration_success_7', 'thp_migration_success_7_std',
            'thp_migration_success_8', 'thp_migration_success_8_std',
            'thp_migration_success_9', 'thp_migration_success_9_std',
            'thp_fault_alloc', 'thp_fault_alloc_std',
            'thp_fault_alloc_2', 'thp_fault_alloc_2_std',
            'thp_fault_alloc_3', 'thp_fault_alloc_3_std',
            'thp_fault_alloc_4', 'thp_fault_alloc_4_std',
            'thp_fault_alloc_5', 'thp_fault_alloc_5_std',
            'thp_fault_alloc_6', 'thp_fault_alloc_6_std',
            'thp_fault_alloc_7', 'thp_fault_alloc_7_std',
            'thp_fault_alloc_8', 'thp_fault_alloc_8_std',
            'thp_fault_alloc_9', 'thp_fault_alloc_9_std',
            'thp_migration_split', 'thp_migration_split_std',
            'thp_migration_split_2', 'thp_migration_split_2_std',
            'thp_migration_split_3', 'thp_migration_split_3_std',
            'thp_migration_split_4', 'thp_migration_split_4_std',
            'thp_migration_split_5', 'thp_migration_split_5_std',
            'thp_migration_split_6', 'thp_migration_split_6_std',
            'thp_migration_split_7', 'thp_migration_split_7_std',
            'thp_migration_split_8', 'thp_migration_split_8_std',
            'thp_migration_split_9', 'thp_migration_split_9_std',
            'thp_migration_fail', 'thp_migration_fail_std',
            'thp_migration_fail_2', 'thp_migration_fail_2_std',
            'thp_migration_fail_3', 'thp_migration_fail_3_std',
            'thp_migration_fail_4', 'thp_migration_fail_4_std',
            'thp_migration_fail_5', 'thp_migration_fail_5_std',
            'thp_migration_fail_6', 'thp_migration_fail_6_std',
            'thp_migration_fail_7', 'thp_migration_fail_7_std',
            'thp_migration_fail_8', 'thp_migration_fail_8_std',
            'thp_migration_fail_9', 'thp_migration_fail_9_std',
            'numa_local', 'numa_local_std', 'numa_other', 'numa_other_std',
            'pgsteal_kswapd', 'pgsteal_kswapd_std', 'pgsteal_direct', 'pgsteal_direct_std',
            'pgsteal_khugepaged', 'pgsteal_khugepaged_std',
            'pgdemote_kswapd', 'pgdemote_kswapd_std', 'pgdemote_direct', 'pgdemote_direct_std',
            'pgdemote_khugepaged', 'pgdemote_khugepaged_std'
        ]

        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)

        print(f"Successfully generated CSV file: {csv_filename}")
        print(f"Total processed results: {len(csv_data)}")
    else:
        print("Error: No data successfully parsed")

if __name__ == "__main__":
    main() 