#!/usr/bin/env python3
"""
Parse PCM memory traffic data and generate time series charts
Parse pcm_memory.csv files to plot DRAM and PMM traffic trends for each workload under specific memory policies
Each chart represents the performance of a workload under a specific memory policy
Each subplot represents a metric: DRAM Read (MB/s), DRAM Write (MB/s), PMM_Read (MB/s), PMM_Write (MB/s)
Different legends represent different TIERING versions
"""

import os
import re
import glob
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

def parse_pcm_memory_csv(csv_file_path):
    """Parse PCM memory CSV file and extract time series data"""
    data = []
    
    try:
        with open(csv_file_path, 'r') as f:
            lines = f.readlines()
            
        if len(lines) < 3:
            print(f"Warning: CSV file has insufficient lines: {csv_file_path}")
            return data
            
        # Skip first two lines (header information)
        header_line = lines[1].strip()
        headers = [h.strip() for h in header_line.split(',')]
        
        # Find required column indices - use SKT0 data
        date_idx = None
        time_idx = None
        skt0_mem_read_idx = None
        skt0_mem_write_idx = None
        skt0_pmm_read_idx = None
        skt0_pmm_write_idx = None
        
        for i, header in enumerate(headers):
            if header == 'Date':
                date_idx = i
            elif header == 'Time':
                time_idx = i
            elif header == 'Mem Read (MB/s)' and skt0_mem_read_idx is None:  # First one is SKT0
                skt0_mem_read_idx = i
            elif header == 'Mem Write (MB/s)' and skt0_mem_write_idx is None:  # First one is SKT0
                skt0_mem_write_idx = i
            elif header == 'PMM_Read (MB/s)' and skt0_pmm_read_idx is None:  # First one is SKT0
                skt0_pmm_read_idx = i
            elif header == 'PMM_Write (MB/s)' and skt0_pmm_write_idx is None:  # First one is SKT0
                skt0_pmm_write_idx = i
        
        if None in [date_idx, time_idx, skt0_mem_read_idx, skt0_mem_write_idx, 
                   skt0_pmm_read_idx, skt0_pmm_write_idx]:
            print(f"Warning: Cannot find required columns in file: {csv_file_path}")
            print(f"Found column indices: Date={date_idx}, Time={time_idx}, SKT0_MemRead={skt0_mem_read_idx}, "
                  f"SKT0_MemWrite={skt0_mem_write_idx}, SKT0_PMMRead={skt0_pmm_read_idx}, SKT0_PMMWrite={skt0_pmm_write_idx}")
            return data
        
        # Parse data rows (starting from line 3)
        for line_idx, line in enumerate(lines[2:], start=3):
            line = line.strip()
            if not line:
                continue
                
            parts = [p.strip() for p in line.split(',')]
            if len(parts) <= max(date_idx, time_idx, skt0_mem_read_idx, 
                               skt0_mem_write_idx, skt0_pmm_read_idx, skt0_pmm_write_idx):
                continue
                
            try:
                # Parse timestamp
                date_str = parts[date_idx]
                time_str = parts[time_idx]
                
                # Parse datetime format "2025-09-27" "19:13:34.284"
                datetime_str = f"{date_str} {time_str}"
                timestamp = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S.%f")
                
                # Parse metric values - use SKT0 data
                mem_read = float(parts[skt0_mem_read_idx]) if parts[skt0_mem_read_idx] else 0.0
                mem_write = float(parts[skt0_mem_write_idx]) if parts[skt0_mem_write_idx] else 0.0
                pmm_read = float(parts[skt0_pmm_read_idx]) if parts[skt0_pmm_read_idx] else 0.0
                pmm_write = float(parts[skt0_pmm_write_idx]) if parts[skt0_pmm_write_idx] else 0.0
                
                data.append({
                    'timestamp': timestamp,
                    'time_seconds': 0,  # Calculate later
                    'mem_read_mb_s': mem_read,
                    'mem_write_mb_s': mem_write,
                    'pmm_read_mb_s': pmm_read,
                    'pmm_write_mb_s': pmm_write
                })
                
            except (ValueError, IndexError) as e:
                print(f"Warning: Error parsing line {line_idx}: {e}")
                continue
        
        # Calculate relative time (in seconds)
        if data:
            start_time = data[0]['timestamp']
            for entry in data:
                entry['time_seconds'] = (entry['timestamp'] - start_time).total_seconds()
        
    except Exception as e:
        print(f"Error parsing PCM memory CSV file {csv_file_path}: {e}")
    
    return data

def get_config_from_env():
    """Get configuration from environment variables"""
    # Get workloads
    benchmarks_env = os.getenv('DATA_ANAL_BENCHMARKS')
    if not benchmarks_env:
        print("Warning: DATA_ANAL_BENCHMARKS environment variable is not set")
        return None, None, None, None
    
    # Get tiering versions
    tiering_env = os.getenv('DATA_ANAL_TIERING_VERS')
    if not tiering_env:
        print("Warning: DATA_ANAL_TIERING_VERS environment variable is not set")
        return None, None, None, None
    
    # Get memory policies
    mem_policies_env = os.getenv('DATA_ANAL_MEM_POLICYS')
    if not mem_policies_env:
        print("Warning: DATA_ANAL_MEM_POLICYS environment variable is not set")
        return None, None, None, None
    
    # Get LDRAM sizes
    ldram_sizes_env = os.getenv('DATA_ANAL_LDRAM_SIZES')
    if not ldram_sizes_env:
        print("Warning: DATA_ANAL_LDRAM_SIZES environment variable is not set")
        return None, None, None, None
    
    workloads = benchmarks_env.split()
    tiering_versions = tiering_env.split()
    mem_policies = mem_policies_env.split()
    ldram_sizes = ldram_sizes_env.split()
    
    return workloads, tiering_versions, mem_policies, ldram_sizes

def find_pcm_result_directories(results_base_path):
    """Find all result directories containing PCM memory data"""
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
                        mem_dir = os.path.join(mem_policy_dir, f"{ldram_size}")
                        pcm_csv = os.path.join(mem_dir, "pcm_memory.csv")
                        
                        # Check if PCM data exists
                        if os.path.exists(pcm_csv):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'pcm_csv': pcm_csv
                            })
    
    return result_dirs

def plot_memory_traffic_trends(workload, mem_policy, tiering_data):
    """
    Plot memory traffic trends for specific workload and memory policy
    tiering_data: {tiering_version: pcm_data}
    """
    fig, axes = plt.subplots(4, 1, figsize=(14, 16))
    fig.suptitle(f'DRAM & PMM Traffic Trends: {workload} with {mem_policy}', fontsize=16, fontweight='bold')
    
    # Color and line style settings
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    line_styles = ['-', '--', '-.', ':']
    
    # Subplot 1: DRAM Read (MB/s)
    ax1 = axes[0]
    ax1.set_title('DRAM Read (MB/s)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('DRAM Read Rate (MB/s)')
    ax1.grid(True, alpha=0.3)
    
    # Subplot 2: DRAM Write (MB/s)  
    ax2 = axes[1]
    ax2.set_title('DRAM Write (MB/s)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('DRAM Write Rate (MB/s)')
    ax2.grid(True, alpha=0.3)
    
    # Subplot 3: PMM Read (MB/s)
    ax3 = axes[2]
    ax3.set_title('PMM Read (MB/s)', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('PMM Read Rate (MB/s)')
    ax3.grid(True, alpha=0.3)
    
    # Subplot 4: PMM Write (MB/s)
    ax4 = axes[3]
    ax4.set_title('PMM Write (MB/s)', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Time (seconds)')
    ax4.set_ylabel('PMM Write Rate (MB/s)')
    ax4.grid(True, alpha=0.3)
    
    # Plot data for each tiering version
    color_idx = 0
    for tiering_version, pcm_data in tiering_data.items():
        color = colors[color_idx % len(colors)]
        line_style = line_styles[color_idx % len(line_styles)]
        color_idx += 1
        
        if not pcm_data:
            continue
            
        # Extract time and metrics
        times = [entry['time_seconds'] for entry in pcm_data]
        mem_reads = [entry['mem_read_mb_s'] for entry in pcm_data]
        mem_writes = [entry['mem_write_mb_s'] for entry in pcm_data]
        pmm_reads = [entry['pmm_read_mb_s'] for entry in pcm_data]
        pmm_writes = [entry['pmm_write_mb_s'] for entry in pcm_data]
        
        # Plot DRAM Read
        ax1.plot(times, mem_reads, color=color, linestyle=line_style, 
                marker='o', markersize=3, label=tiering_version, linewidth=2)
        
        # Plot DRAM Write
        ax2.plot(times, mem_writes, color=color, linestyle=line_style,
                marker='s', markersize=3, label=tiering_version, linewidth=2)
        
        # Plot PMM Read
        ax3.plot(times, pmm_reads, color=color, linestyle=line_style,
                marker='^', markersize=3, label=tiering_version, linewidth=2)
        
        # Plot PMM Write
        ax4.plot(times, pmm_writes, color=color, linestyle=line_style,
                marker='d', markersize=3, label=tiering_version, linewidth=2)
    
    # Set legends
    ax1.legend(loc='upper right', framealpha=0.9)
    ax2.legend(loc='upper right', framealpha=0.9)  
    ax3.legend(loc='upper right', framealpha=0.9)
    ax4.legend(loc='upper right', framealpha=0.9)
    
    # Auto-adjust y-axis range
    for ax in axes:
        ax.relim()
        ax.autoscale_view()
        # Set y-axis to start from 0
        ylim = ax.get_ylim()
        ax.set_ylim(0, ylim[1])
    
    plt.tight_layout()
    
    # Save plot
    output_dir = "memory_traffic_plots"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{workload}_{mem_policy}_memory_traffic_trends.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filepath}")
    
    # Close figure to free memory
    plt.close(fig)

def main():
    """Main function"""
    # Set matplotlib font settings
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    results_base_path = "../results"
    
    print("Searching for PCM memory traffic result directories...")
    result_dirs = find_pcm_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: No PCM memory traffic result directories found")
        return
    
    print(f"Found {len(result_dirs)} PCM memory traffic result directories")
    print()
    
    # Group data by workload and memory policy first to plan processing
    grouped_dirs = {}
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        key = (workload, mem_policy)
        if key not in grouped_dirs:
            grouped_dirs[key] = []
        grouped_dirs[key].append(result_dir)
    
    total_charts = len(grouped_dirs)
    chart_count = 0
    
    # Process and generate chart for each workload and memory policy combination
    for (workload, mem_policy), result_dir_list in grouped_dirs.items():
        chart_count += 1
        print(f"[{chart_count}/{total_charts}] Processing {workload} with {mem_policy}...")
        
        # Parse data for all tiering versions of this workload+policy combination
        tiering_data = {}
        for result_dir in result_dir_list:
            tiering = result_dir['tiering']
            pcm_csv = result_dir['pcm_csv']
            
            print(f"    → Parsing {tiering} data...")
            pcm_data = parse_pcm_memory_csv(pcm_csv)
            
            if not pcm_data:
                print(f"    ⚠ Warning: Unable to parse PCM data: {pcm_csv}")
                continue
            
            tiering_data[tiering] = pcm_data
            print(f"    ✓ Parsed {len(pcm_data)} data points for {tiering}")
        
        # Generate chart immediately after parsing this workload
        if tiering_data:
            print(f"    → Generating chart for {workload} with {mem_policy}...")
            plot_memory_traffic_trends(workload, mem_policy, tiering_data)
            print(f"    ✓ Chart saved for {workload} with {mem_policy}")
        else:
            print(f"    ⚠ No valid data found for {workload} with {mem_policy}")
        
        print()
    
    print("All memory traffic trend charts have been generated!")

if __name__ == "__main__":
    main()
