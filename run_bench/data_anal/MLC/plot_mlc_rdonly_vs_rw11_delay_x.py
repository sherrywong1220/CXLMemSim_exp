#!/usr/bin/env python3
"""
Script to plot MLC (Memory Latency Checker) results comparison
Compare ReadOnly vs Read-Write 1:1 ratio for different memory nodes
Five subfigures: AMD_LDRAM, Intel_LDRAM, Intel_RDRAM, Intel_RSOCKET_DRAM, AMD_CXL
X-axis: Latency, Y-axis: Bandwidth
"""

import matplotlib.pyplot as plt
import numpy as np
import re

def parse_mlc_file(file_path):
    """Parse MLC output file and extract inject delay, bandwidth and latency data"""
    inject_delay = []
    bandwidth = []
    latency = []
    
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        # Find the data section (after the header)
        data_started = False
        for line in lines:
            line = line.strip()
            
            # Skip until we find the header line
            if line.startswith("=========================="):
                data_started = True
                continue
            
            if data_started and line:
                # Parse data lines like: " 00000	410.36	  37621.8"
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        delay = float(parts[0])  # Inject Delay
                        lat = float(parts[1])    # Latency (ns)
                        bw = float(parts[2])     # Bandwidth (MB/sec)
                        inject_delay.append(delay)
                        latency.append(lat)
                        bandwidth.append(bw)
                    except ValueError:
                        continue
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return [], [], []
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], [], []
    
    return inject_delay, bandwidth, latency

def plot_mlc_rdonly_vs_rw11():
    """Plot ReadOnly vs RW11 comparison for all memory nodes"""
    
    # Memory nodes configuration
    nodes = [
        {'name': 'Intel LSOCKET LDRAM', 'rdonly_file': 'Intel_LSOCKET_LDRAM_RdOnly', 'rw11_file': 'Intel_LSOCKET_LDRAM_RW11'},
        {'name': 'Intel LSOCKET RDRAM', 'rdonly_file': 'Intel_LSOCKET_RDRAM_RdOnly', 'rw11_file': 'Intel_LSOCKET_RDRAM_RW11'},
        {'name': 'Intel RSOCKET DRAM', 'rdonly_file': 'Intel_RSOCKET_DRAM_RdOnly', 'rw11_file': 'Intel_RSOCKET_DRAM_RW11'},
        {'name': 'AMD LDRAM', 'rdonly_file': 'AMD_LDRAM_RdOnly', 'rw11_file': 'AMD_LDRAM_RW11'},
        {'name': 'AMD CXL', 'rdonly_file': 'AMD_CXL_RdOnly_new', 'rw11_file': 'AMD_CXL_RW11_new'}
    ]
    
    # Create figure with 5 subfigures (2x3 layout, with last subplot empty)
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Memory Bandwidth vs Inject Delay: ReadOnly vs Read-Write 1:1 Comparison', fontsize=20, fontweight='bold')
    
    # Flatten axes for easier indexing
    axes_flat = axes.flatten()
    
    # Colors and styles
    rdonly_color = 'blue'
    rw11_color = 'red'
    
    for i, node in enumerate(nodes):
        ax = axes_flat[i]
        
        # Parse data files
        rdonly_delay, rdonly_bw, rdonly_lat = parse_mlc_file(node['rdonly_file'])
        rw11_delay, rw11_bw, rw11_lat = parse_mlc_file(node['rw11_file'])
        
        # Plot ReadOnly data (X=inject_delay, Y=bandwidth)
        if rdonly_delay and rdonly_bw:
            ax.plot(rdonly_delay, rdonly_bw, 'o-', color=rdonly_color, linewidth=2, 
                   markersize=4, label='ReadOnly', alpha=0.8)
        
        # Plot RW11 data (X=inject_delay, Y=bandwidth)
        if rw11_delay and rw11_bw:
            ax.plot(rw11_delay, rw11_bw, 's-', color=rw11_color, linewidth=2, 
                   markersize=4, label='Read-Write 1:1', alpha=0.8)
        
        # Customize subplot
        ax.set_title(node['name'], fontsize=16, fontweight='bold')
        ax.set_xlabel('Inject Delay', fontsize=14)
        ax.set_ylabel('Bandwidth (MB/sec)', fontsize=14)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=12)
        ax.tick_params(axis='both', which='major', labelsize=12)
        
        # Set axis limits
        all_bw = rdonly_bw + rw11_bw
        all_delay = rdonly_delay + rw11_delay
        if all_bw and all_delay:
            ax.set_xlim(0, max(all_delay) * 1.1)
            ax.set_ylim(0, max(all_bw) * 1.1)
    
    # Hide the last subplot (index 5)
    axes_flat[5].set_visible(False)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_file = "mlc_rdonly_vs_rw11_comparison_delay_x.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    # Show the plot
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS: ReadOnly vs Read-Write 1:1")
    print("="*80)
    
    for node in nodes:
        print(f"\n{node['name']}:")
        
        # Parse data
        rdonly_delay, rdonly_bw, rdonly_lat = parse_mlc_file(node['rdonly_file'])
        rw11_delay, rw11_bw, rw11_lat = parse_mlc_file(node['rw11_file'])
        
        if rdonly_bw and rdonly_lat:
            print(f"  ReadOnly - Peak BW: {max(rdonly_bw):.1f} MB/s, Min Latency: {min(rdonly_lat):.1f} ns")
        
        if rw11_bw and rw11_lat:
            print(f"  RW 1:1   - Peak BW: {max(rw11_bw):.1f} MB/s, Min Latency: {min(rw11_lat):.1f} ns")
        
        # Performance comparison
        if rdonly_bw and rw11_bw and rdonly_lat and rw11_lat:
            bw_ratio = max(rdonly_bw) / max(rw11_bw) if max(rw11_bw) > 0 else 0
            lat_ratio = min(rw11_lat) / min(rdonly_lat) if min(rdonly_lat) > 0 else 0
            print(f"  ReadOnly BW is {bw_ratio:.2f}x higher than RW 1:1")
            print(f"  RW 1:1 latency is {lat_ratio:.2f}x higher than ReadOnly")

if __name__ == "__main__":
    # Create perf_results directory if it doesn't exist
    import os
    os.makedirs("perf_results", exist_ok=True)
    
    plot_mlc_rdonly_vs_rw11()

