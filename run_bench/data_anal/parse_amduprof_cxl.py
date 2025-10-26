#!/usr/bin/env python3
"""
解析AMDuProf CXL日志并生成内存流量趋势图
为每个工作负载在特定内存策略下绘制CXL读写带宽趋势
每个图表包含两个子图：CXL Read Memory BW 和 CXL Write Memory BW
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
    """解析单个AMDuProf CXL日志文件，提取时间序列数据"""
    data = []
    
    try:
        with open(amduprof_file_path, 'r') as f:
            lines = f.readlines()
        
        # 查找数据开始的位置
        data_start_idx = None
        header_found = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 查找表头行
            if "Total CXL Memory BW (GB/s),Total CXL Read Memory BW (GB/s),Total CXL Write Memory BW (GB/s)" in line:
                header_found = True
                data_start_idx = i + 1
                break
        
        if not header_found or data_start_idx is None:
            print(f"Warning: 未找到CXL内存带宽数据表头: {amduprof_file_path}")
            return []
        
        # 解析数据行
        time_seconds = 0
        for i in range(data_start_idx, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            
            # 跳过非数据行（如包含字母的行）
            if re.search(r'[a-zA-Z]', line):
                continue
            
            # 解析CSV格式的数据: total_bw,read_bw,write_bw,
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
                    
                    time_seconds += 1  # 假设每秒一个数据点
                except ValueError:
                    continue
        
        print(f"解析到 {len(data)} 个CXL数据点: {amduprof_file_path}")
        return data
        
    except FileNotFoundError:
        print(f"Warning: 文件未找到: {amduprof_file_path}")
    except Exception as e:
        print(f"Error parsing AMDuProf file {amduprof_file_path}: {e}")
    
    return []

def get_config_from_env():
    """从环境变量获取配置"""
    # 获取工作负载
    benchmarks_env = os.getenv('DATA_ANAL_BENCHMARKS')
    if not benchmarks_env:
        print("Warning: DATA_ANAL_BENCHMARKS environment variable is not set")
        return None, None, None, None
    
    # 获取分层版本
    tiering_env = os.getenv('DATA_ANAL_TIERING_VERS')
    if not tiering_env:
        print("Warning: DATA_ANAL_TIERING_VERS environment variable is not set")
        return None, None, None, None
    
    # 获取内存策略
    mem_policies_env = os.getenv('DATA_ANAL_MEM_POLICYS')
    if not mem_policies_env:
        print("Warning: DATA_ANAL_MEM_POLICYS environment variable is not set")
        return None, None, None, None
    
    # 获取LDRAM大小
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
    """查找所有包含AMDuProf CXL数据的结果目录（使用最新的timestamp运行）"""
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

                        # Get latest timestamp directory for this case
                        latest_timestamp_dir = timestamp_utils.get_latest_timestamp_dir(case_dir)

                        if latest_timestamp_dir is None:
                            # No timestamp subdirectories found, skip
                            continue

                        amduprof_log = os.path.join(latest_timestamp_dir, "amduprof_cxl.log")

                        # 检查是否存在AMDuProf CXL数据
                        if os.path.exists(amduprof_log):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'amduprof_log': amduprof_log
                            })

    return result_dirs

def plot_cxl_memory_trends(workload, mem_policy, tiering_data):
    """
    为特定工作负载和内存策略绘制CXL内存流量趋势图
    tiering_data: {tiering_version: cxl_data}
    """
    fig, axes = plt.subplots(3, 1, figsize=(16, 16))
    fig.suptitle(f'CXL Memory Traffic Trends: {workload} with {mem_policy}', fontsize=22, fontweight='bold')
    
    # 颜色和线型设置
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    line_styles = ['-', '--', '-.', ':']
    
    # 子图1: CXL Read Memory BW (GB/s)
    ax1 = axes[0]
    ax1.set_title('CXL Read Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax1.set_xlabel('Time (seconds)', fontsize=16)
    ax1.set_ylabel('Read BW (GB/s)', fontsize=16)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='both', which='major', labelsize=14)
    
    # 子图2: CXL Write Memory BW (GB/s)
    ax2 = axes[1]
    ax2.set_title('CXL Write Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax2.set_xlabel('Time (seconds)', fontsize=16)
    ax2.set_ylabel('Write BW (GB/s)', fontsize=16)
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='both', which='major', labelsize=14)
    
    # 子图3: CXL Total Memory BW (GB/s)
    ax3 = axes[2]
    ax3.set_title('CXL Total Memory BW (GB/s)', fontsize=18, fontweight='bold')
    ax3.set_xlabel('Time (seconds)', fontsize=16)
    ax3.set_ylabel('Total BW (GB/s)', fontsize=16)
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='both', which='major', labelsize=14)
    
    # 为每个tiering版本绘制数据
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
            
            # 绘制CXL Read BW
            ax1.plot(times, read_bws, color=color, linestyle=line_style,
                    marker='o', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
            
            # 绘制CXL Write BW  
            ax2.plot(times, write_bws, color=color, linestyle=line_style,
                    marker='s', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
            
            # 绘制CXL Total BW
            ax3.plot(times, total_bws, color=color, linestyle=line_style,
                    marker='^', markersize=3, label=tiering_version, linewidth=2, alpha=0.8)
    
    # 设置图例
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=14)
    ax2.legend(loc='upper right', framealpha=0.9, fontsize=14)
    ax3.legend(loc='upper right', framealpha=0.9, fontsize=14)
    
    # 自动调整y轴范围
    for ax in axes:
        ax.relim()
        ax.autoscale_view()
        # 确保y轴从0开始
        ylim = ax.get_ylim()
        ax.set_ylim(0, ylim[1])
    
    plt.tight_layout()
    
    # 保存图片
    output_dir = "cxl_plots"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{workload}_{mem_policy}_cxl_memory_trends.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filepath}")
    
    # 关闭图表释放内存
    plt.close(fig)

def print_cxl_statistics(workload, mem_policy, tiering_data):
    """打印CXL内存流量统计信息"""
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
    """主函数"""
    # 设置matplotlib字体和大小
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
    
    print("正在查找AMDuProf CXL结果目录...")
    result_dirs = find_amduprof_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: 未找到AMDuProf CXL结果目录")
        return
    
    print(f"找到 {len(result_dirs)} 个AMDuProf CXL结果目录")
    
    # 按工作负载和内存策略分组数据
    grouped_data = {}
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        tiering = result_dir['tiering']
        amduprof_log = result_dir['amduprof_log']
        
        print(f"正在处理: {workload} - {tiering} - {mem_policy}")
        
        # 解析AMDuProf CXL数据
        cxl_data = parse_amduprof_cxl_file(amduprof_log)
        
        # 按工作负载和内存策略分组
        key = (workload, mem_policy)
        if key not in grouped_data:
            grouped_data[key] = {}
        
        grouped_data[key][tiering] = cxl_data
    
    # 为每个工作负载和内存策略组合生成图表
    for (workload, mem_policy), tiering_data in grouped_data.items():
        print(f"正在生成图表: {workload} with {mem_policy}")
        plot_cxl_memory_trends(workload, mem_policy, tiering_data)
        print_cxl_statistics(workload, mem_policy, tiering_data)
    
    print("\n所有CXL内存流量趋势图表已生成完成!")

if __name__ == "__main__":
    main()
