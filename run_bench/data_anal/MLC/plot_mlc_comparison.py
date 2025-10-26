#!/usr/bin/env python3
"""
Script to plot MLC (Memory Latency Checker) results comparison
Compare AMD CXL vs Intel RDRAM bandwidth-latency characteristics
"""

import matplotlib.pyplot as plt
import numpy as np
import re

def parse_mlc_file(file_path):
    """Parse MLC output file and extract bandwidth and latency data"""
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
                        lat = float(parts[1])  # Latency (ns)
                        bw = float(parts[2])   # Bandwidth (MB/sec)
                        latency.append(lat)
                        bandwidth.append(bw)
                    except ValueError:
                        continue
    
    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
        return [], []
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return [], []
    
    return bandwidth, latency

def plot_mlc_comparison():
    """Plot bandwidth vs latency comparison"""
    # Parse data files
    amd_bandwidth, amd_latency = parse_mlc_file("AMD_CXL_RdOnly_new")
    intel_bandwidth, intel_latency = parse_mlc_file("Intel_LSOCKET_RDRAM_RdOnly")
    intel_rsocket_bandwidth, intel_rsocket_latency = parse_mlc_file("Intel_RSOCKET_DRAM_RdOnly")
    
    if not amd_bandwidth or not intel_bandwidth:
        print("Error: Could not load data from files")
        return
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    
    # Plot AMD CXL data
    plt.plot(amd_bandwidth, amd_latency, 'ro-', linewidth=2, markersize=6, 
             label='AMD CXL', alpha=0.8)
    
    # Plot Intel RDRAM data
    plt.plot(intel_bandwidth, intel_latency, 'bs-', linewidth=2, markersize=6, 
             label='Intel RDRAM (Local Socket)', alpha=0.8)
    
    # Plot Intel Remote Socket DRAM data
    plt.plot(intel_rsocket_bandwidth, intel_rsocket_latency, 'g^-', linewidth=2, markersize=6, 
             label='Intel RDRAM (Remote Socket)', alpha=0.8)
    
    # Customize the plot
    plt.xlabel('Bandwidth (MB/sec)', fontsize=14)
    plt.ylabel('Latency (ns)', fontsize=14)
    plt.title('Memory Latency vs Bandwidth Comparison\nAMD CXL vs Intel RDRAM (Local & Remote Socket)', fontsize=16)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Set axis limits for better visualization
    all_bandwidths = amd_bandwidth + intel_bandwidth
    all_latencies = amd_latency + intel_latency
    if intel_rsocket_bandwidth and intel_rsocket_latency:
        all_bandwidths += intel_rsocket_bandwidth
        all_latencies += intel_rsocket_latency
    
    plt.xlim(0, max(all_bandwidths) * 1.1)
    plt.ylim(0, max(all_latencies) * 1.1)
    
    # Add annotations for key points
    if amd_bandwidth and amd_latency:
        max_bw_idx = amd_bandwidth.index(max(amd_bandwidth))
        plt.annotate(f'AMD Peak: {max(amd_bandwidth):.1f} MB/s\n{amd_latency[max_bw_idx]:.1f} ns',
                    xy=(max(amd_bandwidth), amd_latency[max_bw_idx]),
                    xytext=(max(amd_bandwidth)*0.7, amd_latency[max_bw_idx]*1.3),
                    arrowprops=dict(arrowstyle='->', color='red', alpha=0.7),
                    fontsize=10, ha='center')
    
    if intel_bandwidth and intel_latency:
        max_bw_idx = intel_bandwidth.index(max(intel_bandwidth))
        plt.annotate(f'Intel Local Peak: {max(intel_bandwidth):.1f} MB/s\n{intel_latency[max_bw_idx]:.1f} ns',
                    xy=(max(intel_bandwidth), intel_latency[max_bw_idx]),
                    xytext=(max(intel_bandwidth)*0.7, intel_latency[max_bw_idx]*0.7),
                    arrowprops=dict(arrowstyle='->', color='blue', alpha=0.7),
                    fontsize=10, ha='center')
    
    if intel_rsocket_bandwidth and intel_rsocket_latency:
        max_bw_idx = intel_rsocket_bandwidth.index(max(intel_rsocket_bandwidth))
        plt.annotate(f'Intel Remote Peak: {max(intel_rsocket_bandwidth):.1f} MB/s\n{intel_rsocket_latency[max_bw_idx]:.1f} ns',
                    xy=(max(intel_rsocket_bandwidth), intel_rsocket_latency[max_bw_idx]),
                    xytext=(max(intel_rsocket_bandwidth)*0.8, intel_rsocket_latency[max_bw_idx]*1.2),
                    arrowprops=dict(arrowstyle='->', color='green', alpha=0.7),
                    fontsize=10, ha='center')
    
    # Tight layout and save
    plt.tight_layout()
    
    # Save the plot
    output_file = "mlc_bandwidth_latency_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_file}")
    
    # Show the plot
    plt.show()
    
    # Print summary statistics
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    if amd_bandwidth and amd_latency:
        print(f"AMD CXL:")
        print(f"  Peak Bandwidth: {max(amd_bandwidth):.1f} MB/sec")
        print(f"  Min Latency: {min(amd_latency):.1f} ns")
        print(f"  Max Latency: {max(amd_latency):.1f} ns")
        print(f"  Latency at Peak BW: {amd_latency[amd_bandwidth.index(max(amd_bandwidth))]:.1f} ns")
    
    if intel_bandwidth and intel_latency:
        print(f"\nIntel RDRAM (Local Socket):")
        print(f"  Peak Bandwidth: {max(intel_bandwidth):.1f} MB/sec")
        print(f"  Min Latency: {min(intel_latency):.1f} ns")
        print(f"  Max Latency: {max(intel_latency):.1f} ns")
        print(f"  Latency at Peak BW: {intel_latency[intel_bandwidth.index(max(intel_bandwidth))]:.1f} ns")
    
    if intel_rsocket_bandwidth and intel_rsocket_latency:
        print(f"\nIntel RDRAM (Remote Socket):")
        print(f"  Peak Bandwidth: {max(intel_rsocket_bandwidth):.1f} MB/sec")
        print(f"  Min Latency: {min(intel_rsocket_latency):.1f} ns")
        print(f"  Max Latency: {max(intel_rsocket_latency):.1f} ns")
        print(f"  Latency at Peak BW: {intel_rsocket_latency[intel_rsocket_bandwidth.index(max(intel_rsocket_bandwidth))]:.1f} ns")
    
    # Performance comparison
    if amd_bandwidth and intel_bandwidth and amd_latency and intel_latency:
        bw_ratio = max(intel_bandwidth) / max(amd_bandwidth)
        lat_ratio = min(amd_latency) / min(intel_latency)
        print(f"\nPerformance Comparison:")
        print(f"  Intel RDRAM bandwidth is {bw_ratio:.2f}x higher than AMD CXL")
        print(f"  AMD CXL latency is {lat_ratio:.2f}x higher than Intel RDRAM")

if __name__ == "__main__":
    # Create perf_results directory if it doesn't exist
    import os
    os.makedirs("perf_results", exist_ok=True)
    
    plot_mlc_comparison()
