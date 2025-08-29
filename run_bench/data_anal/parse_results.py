#!/usr/bin/env python3
"""
Script to parse result data and generate CSV file
Parse execution time, RSS and vmstat data for workloads under different tiering versions
"""

import os
import re
import csv
import glob
from pathlib import Path

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

def find_result_directories(results_base_path):
    """Find all result directories based on environment configuration"""
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
                        mem_dir = os.path.join(mem_policy_dir, f"{ldram_size}")
                        if os.path.exists(mem_dir):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'path': mem_dir
                            })
                        else:
                            print(f"Warning: LDRAM directory not found {mem_dir}")
    
    return result_dirs

def main():
    """Main function"""
    results_base_path = "../results"
    
    # Find all result directories
    result_dirs = find_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: No result directories found")
        return
    
    # Prepare CSV data
    csv_data = []
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        tiering = result_dir['tiering']
        mem_policy = result_dir['mem_policy']
        ldram_size = result_dir['ldram_size']
        base_path = result_dir['path']
        
        print(f"Processing: {workload} - {tiering} - {mem_policy} - {ldram_size}")
        
        # File paths
        output_log_path = os.path.join(base_path, "output.log")
        rss_log_path = os.path.join(base_path, "rss.log")
        before_vmstat_path = os.path.join(base_path, "before_vmstat.log")
        after_vmstat_path = os.path.join(base_path, "after_vmstat.log")
        
        # Extract data
        execution_time = extract_execution_time(output_log_path, workload)
        throughput = extract_throughput(output_log_path, workload)
        rss = extract_rss_difference(rss_log_path)
        vmstat_diffs = extract_vmstat_differences(before_vmstat_path, after_vmstat_path)
        
        # Build row data
        row = {
            'workload': workload,
            'tiering': tiering,
            'mem_policy': mem_policy,
            'ldram_size': ldram_size,
            'execution_time': execution_time,
            'throughput': throughput,
            'rss': rss
        }
        
        # Add vmstat data
        if vmstat_diffs:
            for metric, value in vmstat_diffs.items():
                row[metric] = value
        else:
            # If vmstat data is not available, fill with 0 for all metrics
            metrics = [
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
            for metric in metrics:
                row[metric] = 0
        
        csv_data.append(row)
    
    # Write CSV file
    if csv_data:
        csv_filename = os.getenv('CSV_FILE')
        fieldnames = [
            'workload', 'tiering', 'mem_policy', 'ldram_size', 'execution_time', 'throughput', 'rss',
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