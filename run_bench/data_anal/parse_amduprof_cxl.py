#!/usr/bin/env python3
"""
Parse AMDuProf CXL logs and generate memory traffic trend plots
"""

import os
import re
import glob
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path
import timestamp_utils

def parse_amduprof_cxl_file(amduprof_file_path):
    """Parse a single AMDuProf CXL log file and extract time series data"""
    data = []
    
    try:
        with open(amduprof_file_path, 'r') as f:
            lines = f.readlines()
        
        data_start_idx = None
        header_found = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if "Total CXL Memory BW (GB/s),Total CXL Read Memory BW (GB/s),Total CXL Write Memory BW (GB/s)" in line:
                header_found = True
                data_start_idx = i + 1
                break
        
        if not header_found or data_start_idx is None:
            print(f"Warning: CXL memory bandwidth data header not found: {amduprof_file_path}")
            return []
        
        time_seconds = 0
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            
            if re.search(r'[a-zA-Z]', line):
                continue
            
            parts = line.rstrip(',').split(',')
            if len(parts) >= 3:
                try:
                    total_bw = float(parts[0])
                    read_bw = float(parts[1])  
                    write_bw = float(parts[2])
                    
                    data.append({
                        'time_seconds': time_seconds,
                        'total_cxl_bw': total_bw,
                        'cxl_read_bw': read_bw,
                        'cxl_write_bw': write_bw
                    })
                    
                    time_seconds += 1  # Assume one data point per second
                except ValueError:
                    continue
        
        print(f"Parsed {len(data)} CXL data points: {amduprof_file_path}")
        return data
        
    except FileNotFoundError:
        print(f"Warning: File not found: {amduprof_file_path}")
    except Exception as e:
        print(f"Error parsing AMDuProf file {amduprof_file_path}: {e}")
    
    return []

def get_config_from_env():
    """Get configuration from environment variables"""
    benchmarks_env = os.getenv('DATA_ANAL_BENCHMARKS')
    if not benchmarks_env:
        print("Warning: DATA_ANAL_BENCHMARKS environment variable is not set")
        return None, None, None, None
    
    tiering_env = os.getenv('DATA_ANAL_TIERING_VERS')
    if not tiering_env:
        print("Warning: DATA_ANAL_TIERING_VERS environment variable is not set")
        return None, None, None, None
    
    mem_policies_env = os.getenv('DATA_ANAL_MEM_POLICYS')
    if not mem_policies_env:
        print("Warning: DATA_ANAL_MEM_POLICYS environment variable is not set")
        return None, None, None, None
    
    ldram_sizes_env = os.getenv('DATA_ANAL_LDRAM_SIZES')
    if not ldram_sizes_env:
        print("Warning: DATA_ANAL_LDRAM_SIZES environment variable is not set")
        return None, None, None, None
    
    workloads = benchmarks_env.split()
    tiering_versions = tiering_env.split()
    mem_policies = mem_policies_env.split()
    ldram_sizes = ldram_sizes_env.split()
    
    return workloads, tiering_versions, mem_policies, ldram_sizes

def find_amduprof_result_directories(results_base_path):
    """Find all result directories containing AMDuProf CXL data (using the latest timestamp run)"""
    config_result = get_config_from_env()
    if config_result[0] is None:
        print("Error: Failed to get configuration from environment variables")
        return []

    workloads, tiering_versions, mem_policies, ldram_sizes = config_result

    result_dirs = []

    for workload in workloads:
        workload_path = os.path.join(results_base_path, workload)
        if not os.path.exists(workload_path):
            continue

        for tiering in tiering_versions:
            tiering_path = os.path.join(workload_path, tiering)
            if not os.path.exists(tiering_path):
                continue

            for mem_policy in mem_policies:
                mem_policy_dirs = glob.glob(os.path.join(tiering_path, mem_policy))
                for mem_policy_dir in mem_policy_dirs:
                    for ldram_size in ldram_sizes:
                        case_dir = os.path.join(mem_policy_dir, ldram_size)
                        if not os.path.exists(case_dir):
                            continue

                        latest_timestamp_dir = timestamp_utils.get_latest_timestamp_dir(case_dir)

                        if latest_timestamp_dir is None:
                            continue

                        amduprof_log = os.path.join(latest_timestamp_dir, "amduprof_cxl.log")

                        if os.path.exists(amduprof_log):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'amduprof_log': amduprof_log
                            })

    return result_dirs

def plot_cxl_memory_trends(workload, mem_policy, ldram_size, tiering_data):
    """
    Plot CXL memory traffic trends for a specific workload and memory policy
    tiering_data: {tiering_version: cxl_data}
    """
    fig, axes = plt.subplots(3, 1, figsize=(16, 16))
    fig.suptitle(f'CXL Memory Traffic Trends: {workload} with {mem_policy}', fontsize=22, fontweight='bold')
    
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    line_styles = ['-', '--', '-.', ':']
    
    ax1 = axes[0]
    ax1.set_title('CXL Read Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax1.set_xlabel('Time (seconds)', fontsize=16)
    ax1.set_ylabel('Read BW (GB/s)', fontsize=16)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=14)
    
    ax2 = axes[1]
    ax2.set_title('CXL Write Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=16)
    ax2.set_ylabel('Write BW (GB/s)', fontsize=16)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=14)
    
    ax3 = axes[2]
    ax3.set_title('CXL Total Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=16)
    ax3.set_ylabel('Total BW (GB/s)', fontsize=16)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=14)
    
    color_idx = 0
    for tiering_version, cxl_data in tiering_data.items():
        color = colors[color_idx % len(colors)]
        line_style = line_styles[color_idx % len(line_styles)]
        color_idx += 1
        
        if cxl_data:
            times = [entry['time_seconds'] for entry in cxl_data]
            read_bws = [entry['cxl_read_bw'] for entry in cxl_data]
            write_bws = [entry['cxl_write_bw'] for entry in cxl_data]
            total_bws = [entry['total_cxl_bw'] for entry in cxl_data]
            
            ax1.plot(times, read_bws, color=color, linestyle=line_style,
                    marker='o', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
            
            ax2.plot(times, write_bws, color=color, linestyle=line_style,
                    marker='s', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
            
            ax3.plot(times, total_bws, color=color, linestyle=line_style,
                    marker='^', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
    
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=14)
    ax2.legend(loc='upper right', framealpha=0.9, fontsize=14)
    ax3.legend(loc='upper right', framealpha=0.9, fontsize=14)
    
    for ax in axes:
        ax.relim()
        ax.autoscale_view()
        # Ensure y-axis starts from 0
        ylim = ax.get_ylim()
        ax.set_ylim(0, ylim[1])
    
    plt.tight_layout()
    
    output_dir = "cxl_plots"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{workload}_{mem_policy}_{ldram_size}_cxl_memory_trends.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filepath}")
    
    plt.close(fig)

def print_cxl_statistics(workload, mem_policy, tiering_data):
    """Print CXL memory traffic statistics"""
    print(f"\n{'='*80}")
    print(f"CXL MEMORY TRAFFIC STATISTICS: {workload} with {mem_policy}")
    print(f"{'='*80}")
    
    for tiering_version, cxl_data in tiering_data.items():
        if cxl_data:
            read_bws = [entry['cxl_read_bw'] for entry in cxl_data]
            write_bws = [entry['cxl_write_bw'] for entry in cxl_data]
            total_bws = [entry['total_cxl_bw'] for entry in cxl_data]
            
            print(f"\n{tiering_version}:")
            print(f"  Duration: {len(cxl_data)} seconds")
            print(f"  Average Read BW: {np.mean(read_bws):.2f} GB/s")
            print(f"  Average Write BW: {np.mean(write_bws):.2f} GB/s")
            print(f"  Average Total BW: {np.mean(total_bws):.2f} GB/s")
            print(f"  Peak Read BW: {np.max(read_bws):.2f} GB/s")
            print(f"  Peak Write BW: {np.max(write_bws):.2f} GB/s")
            print(f"  Peak Total BW: {np.max(total_bws):.2f} GB/s")
            print(f"  Total Data Read: {np.sum(read_bws):.2f} GB")
            print(f"  Total Data Written: {np.sum(write_bws):.2f} GB")

def main():
    """Main function"""
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 16
    plt.rcParams['axes.titlesize'] = 18
    plt.rcParams['axes.labelsize'] = 16
    plt.rcParams['xtick.labelsize'] = 14
    plt.rcParams['ytick.labelsize'] = 14
    plt.rcParams['legend.fontsize'] = 14
    plt.rcParams['figure.titlesize'] = 20
    
    results_base_path = "../results"
    
    print("Searching for AMDuProf CXL result directories...")
    result_dirs = find_amduprof_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: No AMDuProf CXL result directories found")
        return
    
    print(f"Found {len(result_dirs)} AMDuProf CXL result directories")
    
    grouped_data = {}
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        tiering = result_dir['tiering']
        ldram_size = result_dir['ldram_size']
        amduprof_log = result_dir['amduprof_log']
        
        print(f"Processing: {workload} - {tiering} - {mem_policy} - {ldram_size}")
        
        cxl_data = parse_amduprof_cxl_file(amduprof_log)
        
        key = (workload, mem_policy, ldram_size)
        if key not in grouped_data:
            grouped_data[key] = {}
        
        grouped_data[key][tiering] = cxl_data
    
    for (workload, mem_policy, ldram_size), tiering_data in grouped_data.items():
        print(f"Generating plot: {workload} with {mem_policy} ({ldram_size})")
        plot_cxl_memory_trends(workload, mem_policy, ldram_size, tiering_data)
        print_cxl_statistics(workload, mem_policy, tiering_data)
    
    print("\nAll CXL memory traffic trend plots have been generated!")

if __name__ == "__main__":
    main()
