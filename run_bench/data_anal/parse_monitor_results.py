#!/usr/bin/env python3
"""
解析监控结果并生成时间序列图表
解析vmstat数据（每5秒）和TLB数据，为每个工作负载在特定内存策略下绘制趋势图
每个图表代表一个工作负载在特定内存策略下的表现
每个子图代表一个指标，使用不同的图例表示不同的TIERING版本
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
import timestamp_utils

def parse_vmstat_file(vmstat_file_path):
    """解析单个vmstat文件，提取时间戳和numa指标"""
    data = {}
    try:
        # 从文件名提取时间戳
        filename = os.path.basename(vmstat_file_path)
        # 文件名格式: 2025.09.09-09.14.12.txt
        time_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})\.txt', filename)
        if time_match:
            year, month, day, hour, minute, second = map(int, time_match.groups())
            timestamp = datetime(year, month, day, hour, minute, second)
            data['timestamp'] = timestamp
        else:
            print(f"Warning: 无法从文件名解析时间戳: {filename}")
            return None
        
        # 解析文件内容
        with open(vmstat_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        metric_name = parts[0]
                        try:
                            metric_value = int(parts[1])
                            
                            # 提取我们关心的指标
                            if metric_name in ['numa_hint_faults', 'numa_pages_migrated']:
                                data[metric_name] = metric_value
                        except ValueError:
                            continue
        
        return data
    except Exception as e:
        print(f"Error parsing vmstat file {vmstat_file_path}: {e}")
        return None

def parse_vmstat_directory(vmstat_dir_path):
    """解析vmstat目录中的所有文件，返回时间序列数据"""
    vmstat_files = glob.glob(os.path.join(vmstat_dir_path, "*.txt"))
    vmstat_files.sort()  # 按文件名排序确保时间顺序
    
    time_series_data = []
    
    for vmstat_file in vmstat_files:
        data = parse_vmstat_file(vmstat_file)
        if data:
            time_series_data.append(data)
    
    # 按时间戳排序
    time_series_data.sort(key=lambda x: x['timestamp'])
    
    return time_series_data

def parse_tlb_log(tlb_log_path):
    """解析TLB日志文件，提取时间序列数据"""
    tlb_data = []
    
    try:
        with open(tlb_log_path, 'r') as f:
            current_time = None
            current_data = {}
            
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析时间和计数
                # 格式: "     5.004219492          1,253,796      bp_l1_tlb_miss_l2_tlb_miss.all"
                match = re.match(r'\s*(\d+\.\d+)\s+([0-9,]+)\s+(\S+)', line)
                if match:
                    time_seconds = float(match.group(1))
                    count_str = match.group(2).replace(',', '')
                    event_name = match.group(3)
                    
                    try:
                        count = int(count_str)
                    except ValueError:
                        continue
                    
                    # 如果时间变了，保存之前的数据
                    if current_time is not None and time_seconds != current_time:
                        if current_data:
                            tlb_data.append({
                                'time_seconds': current_time,
                                **current_data
                            })
                        current_data = {}
                    
                    current_time = time_seconds
                    
                    # 提取关键的TLB miss事件
                    if ('tlb_miss' in event_name or 'tlb_hit' in event_name or 
                        event_name in ['bp_l1_tlb_miss_l2_tlb_miss.all', 'bp_l1_tlb_miss_l2_tlb_hit',
                                      'ls_l1_d_tlb_miss.all_l2_miss', 'ls_l1_d_tlb_miss.all']):
                        current_data[event_name] = count
            
            # 保存最后一个数据点
            if current_time is not None and current_data:
                tlb_data.append({
                    'time_seconds': current_time,
                    **current_data
                })
    
    except FileNotFoundError:
        print(f"Warning: TLB log file not found: {tlb_log_path}")
    except Exception as e:
        print(f"Error parsing TLB log {tlb_log_path}: {e}")
    
    return tlb_data

def get_config_from_env():
    """从环境变量获取配置"""
    # 获取工作负载
    benchmarks_env = os.getenv('DATA_ANAL_BENCHMARKS')
    if not benchmarks_env:
        print("Warning: DATA_ANAL_BENCHMARKS environment variable is not set")
        return None, None, None, None
    
    # 获取分层版本
    tiering_env = os.getenv('DATA_ANAL_NET_CONFIGS')
    if not tiering_env:
        print("Warning: DATA_ANAL_NET_CONFIGS environment variable is not set")
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
    NET_CONFIGsions = tiering_env.split()
    mem_policies = mem_policies_env.split()
    ldram_sizes = ldram_sizes_env.split()
    
    return workloads, NET_CONFIGsions, mem_policies, ldram_sizes

def find_monitor_result_directories(results_base_path):
    """查找所有包含监控数据的结果目录（使用最新的timestamp运行）"""
    config_result = get_config_from_env()
    if config_result[0] is None:
        print("Error: Failed to get configuration from environment variables")
        return []

    workloads, NET_CONFIGsions, mem_policies, ldram_sizes = config_result

    result_dirs = []

    for workload in workloads:
        workload_path = os.path.join(results_base_path, workload)
        if not os.path.exists(workload_path):
            continue

        for tiering in NET_CONFIGsions:
            tiering_path = os.path.join(workload_path, tiering)
            if not os.path.exists(tiering_path):
                continue

            for mem_policy in mem_policies:
                mem_policy_dirs = glob.glob(os.path.join(tiering_path, mem_policy))
                for mem_policy_dir in mem_policy_dirs:
                    for ldram_size in ldram_sizes:
                        case_dir = os.path.join(mem_policy_dir, f"{ldram_size}")
                        if not os.path.exists(case_dir):
                            continue

                        # Get latest timestamp directory for this case
                        latest_timestamp_dir = timestamp_utils.get_latest_timestamp_dir(case_dir)

                        if latest_timestamp_dir is None:
                            # No timestamp subdirectories found, skip
                            continue

                        vmstat_dir = os.path.join(latest_timestamp_dir, "vmstat")
                        tlb_log = os.path.join(latest_timestamp_dir, "perf_tlb.log")

                        # 检查是否存在监控数据
                        if os.path.exists(vmstat_dir) and os.path.exists(tlb_log):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'vmstat_dir': vmstat_dir,
                                'tlb_log': tlb_log
                            })

    return result_dirs

def calculate_rate_metrics(time_series_data):
    """计算速率指标（每秒的变化量）"""
    if len(time_series_data) < 2:
        return time_series_data
    
    rate_data = []
    prev_data = time_series_data[0]
    
    for i in range(1, len(time_series_data)):
        curr_data = time_series_data[i]
        time_diff = (curr_data['timestamp'] - prev_data['timestamp']).total_seconds()
        
        if time_diff > 0:
            rate_entry = {
                'timestamp': curr_data['timestamp'],
                'time_seconds': i * 5  # 假设每5秒一个数据点
            }
            
            for metric in ['numa_hint_faults', 'numa_pages_migrated']:
                if metric in curr_data and metric in prev_data:
                    rate = (curr_data[metric] - prev_data[metric]) / time_diff
                    rate_entry[f'{metric}_rate'] = max(0, rate)  # 确保速率非负
            
            rate_data.append(rate_entry)
        
        prev_data = curr_data
    
    return rate_data

def plot_monitoring_trends(workload, mem_policy, tiering_data):
    """
    为特定工作负载和内存策略绘制监控趋势图
    tiering_data: {NET_CONFIGsion: {'vmstat': vmstat_data, 'tlb': tlb_data}}
    """
    fig, axes = plt.subplots(5, 1, figsize=(14, 20))
    fig.suptitle(f'Monitoring Trends: {workload} with {mem_policy}', fontsize=16, fontweight='bold')
    
    # 颜色和线型设置
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    line_styles = ['-', '--', '-.', ':']
    
    # 子图1: NUMA Hint Faults Rate (per second)
    ax1 = axes[0]
    ax1.set_title('NUMA Hint Faults Rate (per second)', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Time (seconds)')
    ax1.set_ylabel('Hint Faults/sec')
    ax1.grid(True, alpha=0.3)
    
    # 子图2: NUMA Pages Migrated Rate (per second)  
    ax2 = axes[1]
    ax2.set_title('NUMA Pages Migrated Rate (per second)', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Pages Migrated/sec')
    ax2.grid(True, alpha=0.3)
    
    # 子图3: Data TLB Misses (Memory Access)
    ax3 = axes[2]
    ax3.set_title('Data TLB Misses - ls_l1_d_tlb_miss.all + ls_l1_d_tlb_miss.all_l2_miss', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Time (seconds)')
    ax3.set_ylabel('Data TLB Misses')
    ax3.grid(True, alpha=0.3)
    
    # 子图4: All TLB Misses
    ax4 = axes[3]
    ax4.set_title('All TLB Misses - bp_l1_tlb_miss_l2_tlb_miss.all + bp_l1_tlb_miss_l2_tlb_hit + ls_l1_d_tlb_miss.all + ls_l1_d_tlb_miss.all_l2_miss', fontsize=10, fontweight='bold')
    ax4.set_xlabel('Time (seconds)')
    ax4.set_ylabel('Total TLB Misses')
    ax4.grid(True, alpha=0.3)
    
    # 子图5: NUMA Pages Migrated Cumulative
    ax5 = axes[4]
    ax5.set_title('NUMA Pages Migrated Cumulative', fontsize=12, fontweight='bold')
    ax5.set_xlabel('Time (seconds)')
    ax5.set_ylabel('Cumulative Pages Migrated')
    ax5.grid(True, alpha=0.3)
    
    # 为每个tiering版本绘制数据
    color_idx = 0
    for NET_CONFIGsion, data in tiering_data.items():
        color = colors[color_idx % len(colors)]
        line_style = line_styles[color_idx % len(line_styles)]
        color_idx += 1
        
        # 处理vmstat数据
        vmstat_data = data.get('vmstat', [])
        if vmstat_data:
            # 计算速率指标
            rate_data = calculate_rate_metrics(vmstat_data)
            
            if rate_data:
                times = [entry['time_seconds'] for entry in rate_data]
                
                # 绘制NUMA hint faults rate
                if any('numa_hint_faults_rate' in entry for entry in rate_data):
                    hint_faults_rates = [entry.get('numa_hint_faults_rate', 0) for entry in rate_data]
                    ax1.plot(times, hint_faults_rates, color=color, linestyle=line_style, 
                            marker='o', markersize=4, label=NET_CONFIGsion, linewidth=2)
                
                # 绘制NUMA pages migrated rate
                if any('numa_pages_migrated_rate' in entry for entry in rate_data):
                    migrated_rates = [entry.get('numa_pages_migrated_rate', 0) for entry in rate_data]
                    ax2.plot(times, migrated_rates, color=color, linestyle=line_style,
                            marker='s', markersize=4, label=NET_CONFIGsion, linewidth=2)
                
                # 绘制NUMA pages migrated 累加值
                if vmstat_data and any('numa_pages_migrated' in entry for entry in vmstat_data):
                    # 计算相对时间（以秒为单位）
                    start_time = vmstat_data[0]['timestamp']
                    cumulative_times = [(entry['timestamp'] - start_time).total_seconds() for entry in vmstat_data]
                    
                    # 获取初始值并计算增量
                    initial_migrated = vmstat_data[0].get('numa_pages_migrated', 0)
                    cumulative_migrated = [entry.get('numa_pages_migrated', 0) - initial_migrated for entry in vmstat_data]
                    
                    ax5.plot(cumulative_times, cumulative_migrated, color=color, linestyle=line_style,
                            marker='o', markersize=4, label=NET_CONFIGsion, linewidth=2)
        
        # 处理TLB数据
        tlb_data = data.get('tlb', [])
        if tlb_data:
            times = [entry['time_seconds'] for entry in tlb_data]
            
            # 汇总数据TLB miss事件（内存访问相关）
            data_tlb_misses = []
            # 汇总所有TLB miss事件
            total_tlb_misses = []
            
            for entry in tlb_data:
                # 计算数据TLB miss - 使用 ls_l1_d_tlb_miss.all + ls_l1_d_tlb_miss.all_l2_miss
                data_miss = 0
                for key, value in entry.items():
                    if key in ['ls_l1_d_tlb_miss.all', 'ls_l1_d_tlb_miss.all_l2_miss']:
                        data_miss += value
                data_tlb_misses.append(data_miss)
                
                # 计算总TLB miss
                total_miss = 0
                for key, value in entry.items():
                    if 'tlb_miss' in key and key != 'time_seconds':
                        total_miss += value
                total_tlb_misses.append(total_miss)
            
            # 绘制数据TLB miss (子图3)
            if data_tlb_misses:
                ax3.plot(times, data_tlb_misses, color=color, linestyle=line_style,
                        marker='s', markersize=4, label=NET_CONFIGsion, linewidth=2)
            
            # 绘制总TLB miss (子图4)
            if total_tlb_misses:
                ax4.plot(times, total_tlb_misses, color=color, linestyle=line_style,
                        marker='^', markersize=4, label=NET_CONFIGsion, linewidth=2)
    
    # 设置图例
    ax1.legend(loc='upper right', framealpha=0.9)
    ax2.legend(loc='upper right', framealpha=0.9)  
    ax3.legend(loc='upper right', framealpha=0.9)
    ax4.legend(loc='upper right', framealpha=0.9)
    ax5.legend(loc='upper right', framealpha=0.9)
    
    # 自动调整y轴范围
    for ax in axes:
        ax.relim()
        ax.autoscale_view()
    
    plt.tight_layout()
    
    # 保存图片
    output_dir = "monitoring_plots"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{workload}_{mem_policy}_monitoring_trends.png"
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved plot: {filepath}")
    
    # 关闭图表释放内存
    plt.close(fig)

def main():
    """主函数"""
    # 设置matplotlib中文字体
    plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
    plt.rcParams['axes.unicode_minus'] = False
    
    results_base_path = "../results"
    
    print("正在查找监控结果目录...")
    result_dirs = find_monitor_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: 未找到监控结果目录")
        return
    
    print(f"找到 {len(result_dirs)} 个监控结果目录")
    
    # 按工作负载和内存策略分组数据
    grouped_data = {}
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        tiering = result_dir['tiering']
        vmstat_dir = result_dir['vmstat_dir']
        tlb_log = result_dir['tlb_log']
        
        print(f"正在处理: {workload} - {tiering} - {mem_policy}")
        
        # 解析vmstat数据
        vmstat_data = parse_vmstat_directory(vmstat_dir)
        
        # 解析TLB数据
        tlb_data = parse_tlb_log(tlb_log)
        
        # 按工作负载和内存策略分组
        key = (workload, mem_policy)
        if key not in grouped_data:
            grouped_data[key] = {}
        
        grouped_data[key][tiering] = {
            'vmstat': vmstat_data,
            'tlb': tlb_data
        }
    
    # 为每个工作负载和内存策略组合生成图表
    for (workload, mem_policy), tiering_data in grouped_data.items():
        print(f"正在生成图表: {workload} with {mem_policy}")
        plot_monitoring_trends(workload, mem_policy, tiering_data)
    
    print("所有监控趋势图表已生成完成!")

if __name__ == "__main__":
    main()
