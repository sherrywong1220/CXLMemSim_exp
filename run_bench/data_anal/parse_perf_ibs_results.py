#!/usr/bin/env python3
"""
解析perf_ibs_op.log文件并生成表格
展示不同TIERING版本下的IBS hot pages分析结果
每个表格代表一个工作负载在特定内存策略下的统计数据
"""

import os
import re
import glob
import pandas as pd
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
import timestamp_utils

def parse_perf_ibs_log(perf_ibs_log_path, workload_pid_path):
    """解析perf_ibs_op.log文件，提取IBS统计数据"""
    data = {}
    
    try:
        # 首先读取workload.pid文件获取目标PID
        target_pid = None
        if os.path.exists(workload_pid_path):
            with open(workload_pid_path, 'r') as f:
                target_pid = f.read().strip()
        
        if not target_pid:
            print(f"Warning: workload.pid file not found: {workload_pid_path}")
            return None
            
        # 检查perf_ibs_op.log文件是否存在
        if not os.path.exists(perf_ibs_log_path):
            print(f"Warning: perf_ibs_op.log file not found: {perf_ibs_log_path}")
            return None
        
        # 使用perf script解析perf数据
        import subprocess
        try:
            result = subprocess.run([
                'sudo', 'perf', 'script', '-i', perf_ibs_log_path
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"Error running perf script: {result.stderr}")
                return None
                
            perf_output = result.stdout
        except subprocess.TimeoutExpired:
            print(f"Timeout running perf script for {perf_ibs_log_path}")
            return None
        except Exception as e:
            print(f"Error running perf script: {e}")
            return None
        
        # 解析IBS数据
        page_hits = defaultdict(int)
        instruction_addrs = defaultdict(int)
        target_pid_samples = 0
        
        for line in perf_output.split('\n'):
            line = line.strip()
            if not line or target_pid not in line:
                continue
                
            target_pid_samples += 1
            
            # Parse IBS output: "comm pid [cpu] timestamp: period event: addr function"
            parts = line.split()
            if len(parts) >= 6:
                # Find address (usually after colon)
                for i, part in enumerate(parts):
                    if ':' in part and i < len(parts) - 1:
                        addr_part = parts[i + 1]
                        if re.match(r'^[0-9a-fA-F]+$', addr_part):
                            addr = int(addr_part, 16)
                            
                            # 4KB page alignment
                            page = addr & ~0xFFF
                            page_hits[page] += 1
                            
                            # Record instruction address (for hot code analysis)
                            instruction_addrs[addr] += 1
                            break
        
        if not page_hits:
            print(f"Warning: No IBS data found for PID {target_pid} in {perf_ibs_log_path}")
            return None
        
        # 计算统计信息
        total_hits = sum(page_hits.values())
        unique_pages = len(page_hits)
        avg_accesses_per_page = total_hits / unique_pages if unique_pages > 0 else 0
        
        # 计算THP使用效率
        thp_page_counts = defaultdict(int)
        for vpage, hits in page_hits.items():
            thp_base = vpage & ~0x1FFFFF  # 2MB alignment
            offset_in_thp = (vpage - thp_base) // 4096
            thp_page_counts[offset_in_thp] += hits
        
        used_offsets = len(thp_page_counts)
        total_offsets = 512
        thp_efficiency = (used_offsets / total_offsets) * 100 if total_offsets > 0 else 0
        
        # 计算访问模式统计
        access_ranges = [
            (1, 10, "1-10"),
            (11, 50, "11-50"),
            (51, 100, "51-100"),
            (101, 500, "101-500"),
            (501, 1000, "501-1K"),
            (1001, 5000, "1K-5K"),
            (5001, 10000, "5K-10K"),
            (10001, 50000, "10K-50K"),
            (50001, float('inf'), "50K+")
        ]
        
        range_counts = defaultdict(int)
        for vpage, hits in page_hits.items():
            for min_val, max_val, label in access_ranges:
                if min_val <= hits <= max_val:
                    range_counts[label] += 1
                    break
        
        # 计算热点区域分析
        sorted_pages = sorted(page_hits.items(), key=lambda x: x[1], reverse=True)
        top_20_percent = max(1, len(sorted_pages) // 5)
        top_pages = sorted_pages[:top_20_percent]
        
        hot_region_hits = sum(hits for _, hits in top_pages)
        hot_region_percent = (hot_region_hits / total_hits) * 100 if total_hits > 0 else 0
        
        # 存储解析的数据
        data = {
            'target_pid': target_pid,
            'total_samples': target_pid_samples,
            'unique_pages': unique_pages,
            'total_hits': total_hits,
            'avg_accesses_per_page': avg_accesses_per_page,
            'thp_efficiency': thp_efficiency,
            'used_thp_offsets': used_offsets,
            'total_thp_offsets': total_offsets,
            'hot_region_percent': hot_region_percent,
            'low_access_pages': range_counts.get("1-10", 0),
            'medium_access_pages': (range_counts.get("11-50", 0) + 
                                  range_counts.get("51-100", 0) + 
                                  range_counts.get("101-500", 0)),
            'high_access_pages': (range_counts.get("501-1K", 0) + 
                                range_counts.get("1K-5K", 0) + 
                                range_counts.get("5K-10K", 0)),
            'very_high_access_pages': (range_counts.get("10K-50K", 0) + 
                                     range_counts.get("50K+", 0)),
            # 添加用于生成直方图的原始数据
            'page_hits': dict(page_hits),
            'thp_page_counts': dict(thp_page_counts),
            'range_counts': dict(range_counts)
        }
        
        return data
    
    except Exception as e:
        print(f"Error parsing perf_ibs_op.log {perf_ibs_log_path}: {e}")
        return None

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

def find_perf_ibs_result_directories(results_base_path):
    """查找所有包含perf_ibs_op.log数据的结果目录（使用最新的timestamp运行）"""
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

                        perf_ibs_log = os.path.join(latest_timestamp_dir, "perf_ibs_op.log")
                        workload_pid = os.path.join(latest_timestamp_dir, "workload.pid")

                        # 检查是否存在perf_ibs_op.log和workload.pid文件
                        if os.path.exists(perf_ibs_log) and os.path.exists(workload_pid):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'perf_ibs_log': perf_ibs_log,
                                'workload_pid': workload_pid
                            })
    
    return result_dirs

def generate_access_distribution_histograms(grouped_data):
    """生成base page和huge page访问分布直方图"""
    
    output_dir = "perf_ibs_tables"
    plots_dir = os.path.join(output_dir, "histograms")
    os.makedirs(plots_dir, exist_ok=True)
    
    # 设置matplotlib中文字体
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    for (workload, mem_policy), tiering_data in grouped_data.items():
        print(f"正在生成直方图: {workload} with {mem_policy}")
        
        # 为每个tiering版本生成单独的直方图
        for NET_CONFIGsion, ibs_data in tiering_data.items():
            if not ibs_data or 'page_hits' not in ibs_data:
                continue
                
            page_hits = ibs_data['page_hits']
            thp_page_counts = ibs_data['thp_page_counts']
            
            if not page_hits:
                continue
            
            # 创建图形
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
            fig.suptitle(f'IBS Access Distribution: {workload} - {mem_policy} - {NET_CONFIGsion}', 
                        fontsize=16, fontweight='bold')
            
            # 1. Base Page Access Count Histogram
            access_counts = list(page_hits.values())
            ax1.hist(access_counts, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.set_xlabel('Access Count per Page')
            ax1.set_ylabel('Number of Pages')
            ax1.set_title('Base Page Access Count Distribution')
            ax1.set_yscale('log')
            ax1.grid(True, alpha=0.3)
            
            # 添加统计信息
            ax1.text(0.7, 0.8, f'Total Pages: {len(access_counts):,}\n'
                               f'Max Access: {max(access_counts):,}\n'
                               f'Avg Access: {np.mean(access_counts):.1f}', 
                    transform=ax1.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            # 2. THP Offset Access Distribution
            if thp_page_counts:
                offsets = sorted(thp_page_counts.keys())
                counts = [thp_page_counts[offset] for offset in offsets]
                
                ax2.bar(offsets, counts, alpha=0.8, color='coral', edgecolor='black', width=1.0)
                ax2.set_xlabel('THP Offset (4KB pages)')
                ax2.set_ylabel('Access Count')
                ax2.set_title('THP Offset Access Distribution')
                ax2.grid(True, alpha=0.3)
                
                # 添加统计信息
                used_offsets = len(thp_page_counts)
                total_offsets = 512
                efficiency = (used_offsets / total_offsets) * 100
                ax2.text(0.7, 0.8, f'Used Offsets: {used_offsets}/512\n'
                                   f'Efficiency: {efficiency:.1f}%\n'
                                   f'Max Count: {max(counts):,}', 
                        transform=ax2.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            # 3. Access Range Distribution (Bar Chart)
            range_labels = ['1-10', '11-50', '51-100', '101-500', '501-1K', '1K-5K', '5K-10K', '10K-50K', '50K+']
            range_counts = ibs_data.get('range_counts', {})
            range_values = [range_counts.get(label, 0) for label in range_labels]
            
            bars = ax3.bar(range_labels, range_values, alpha=0.7, color='lightgreen', edgecolor='black')
            ax3.set_xlabel('Access Count Range')
            ax3.set_ylabel('Number of Pages')
            ax3.set_title('Base Page Access Range Distribution')
            ax3.tick_params(axis='x', rotation=45)
            ax3.grid(True, alpha=0.3)
            
            # 添加数值标签
            for bar, value in zip(bars, range_values):
                if value > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(range_values)*0.01,
                            f'{value:,}', ha='center', va='bottom', fontsize=8)
            
            # 4. Cumulative Access Distribution
            sorted_access_counts = sorted(access_counts, reverse=True)
            cumulative_pages = np.arange(1, len(sorted_access_counts) + 1)
            cumulative_access = np.cumsum(sorted_access_counts)
            total_access = cumulative_access[-1]
            cumulative_percent = (cumulative_access / total_access) * 100
            
            ax4.plot(cumulative_pages, cumulative_percent, linewidth=2, color='purple')
            ax4.set_xlabel('Number of Pages (sorted by access count)')
            ax4.set_ylabel('Cumulative Access Percentage (%)')
            ax4.set_title('Base Page Cumulative Access Distribution (Pareto-like)')
            ax4.grid(True, alpha=0.3)
            
            # 添加80-20规则线
            ax4.axhline(y=80, color='red', linestyle='--', alpha=0.7, label='80% line')
            ax4.axvline(x=len(sorted_access_counts)*0.2, color='red', linestyle='--', alpha=0.7, label='20% line')
            ax4.legend()
            
            # 添加统计信息
            top_20_percent = int(len(sorted_access_counts) * 0.2)
            top_20_access = cumulative_access[top_20_percent-1] if top_20_percent > 0 else 0
            top_20_percent_access = (top_20_access / total_access) * 100
            ax4.text(0.6, 0.2, f'Top 20% pages: {top_20_percent_access:.1f}% of access\n'
                               f'Pareto ratio: {top_20_percent_access/20:.2f}', 
                    transform=ax4.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图片
            plot_filename = f"{workload}_{mem_policy}_{NET_CONFIGsion}_access_distribution.png"
            plot_filepath = os.path.join(plots_dir, plot_filename)
            plt.savefig(plot_filepath, dpi=300, bbox_inches='tight')
            print(f"Histogram saved to: {plot_filepath}")
            
            plt.close()
        
        # 生成对比直方图（所有tiering版本在同一图中）
        if len(tiering_data) > 1:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
            fig.suptitle(f'IBS Access Distribution Comparison: {workload} - {mem_policy}', 
                        fontsize=16, fontweight='bold')
            
            # THP Efficiency Comparison
            NET_CONFIGsions = []
            thp_efficiencies = []
            colors = plt.cm.Set3(np.linspace(0, 1, len(tiering_data)))
            
            for i, (NET_CONFIGsion, ibs_data) in enumerate(tiering_data.items()):
                if ibs_data and 'thp_efficiency' in ibs_data:
                    NET_CONFIGsions.append(NET_CONFIGsion)
                    thp_efficiencies.append(ibs_data['thp_efficiency'])
            
            if NET_CONFIGsions:
                bars = ax1.bar(NET_CONFIGsions, thp_efficiencies, color=colors, alpha=0.7, edgecolor='black')
                ax1.set_xlabel('Tiering Version')
                ax1.set_ylabel('THP Efficiency (%)')
                ax1.set_title('THP Efficiency Comparison')
                ax1.tick_params(axis='x', rotation=45)
                ax1.grid(True, alpha=0.3)
                
                # 添加数值标签
                for bar, value in zip(bars, thp_efficiencies):
                    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(thp_efficiencies)*0.01,
                            f'{value:.1f}%', ha='center', va='bottom', fontsize=10)
            
            # Hot Region Percentage Comparison
            hot_region_percents = []
            for NET_CONFIGsion, ibs_data in tiering_data.items():
                if ibs_data and 'hot_region_percent' in ibs_data:
                    hot_region_percents.append(ibs_data['hot_region_percent'])
                else:
                    hot_region_percents.append(0)
            
            if NET_CONFIGsions:
                bars = ax2.bar(NET_CONFIGsions, hot_region_percents, color=colors, alpha=0.7, edgecolor='black')
                ax2.set_xlabel('Tiering Version')
                ax2.set_ylabel('Hot Region Percentage (%)')
                ax2.set_title('Hot Region Percentage Comparison')
                ax2.tick_params(axis='x', rotation=45)
                ax2.grid(True, alpha=0.3)
                
                # 添加数值标签
                for bar, value in zip(bars, hot_region_percents):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(hot_region_percents)*0.01,
                            f'{value:.1f}%', ha='center', va='bottom', fontsize=10)
            
            plt.tight_layout()
            
            # 保存对比图
            comparison_filename = f"{workload}_{mem_policy}_comparison.png"
            comparison_filepath = os.path.join(plots_dir, comparison_filename)
            plt.savefig(comparison_filepath, dpi=300, bbox_inches='tight')
            print(f"Comparison chart saved to: {comparison_filepath}")
            
            plt.close()

def create_perf_ibs_tables(grouped_data):
    """为每个工作负载和内存策略组合创建表格"""
    
    output_dir = "perf_ibs_tables"
    os.makedirs(output_dir, exist_ok=True)
    
    for (workload, mem_policy), tiering_data in grouped_data.items():
        print(f"正在生成表格: {workload} with {mem_policy}")
        
        # 为每个tiering版本生成单独的CSV文件
        for NET_CONFIGsion, ibs_data in tiering_data.items():
            if not ibs_data:  # 跳过空数据
                continue
                
            # 准备单行数据
            row = {
                'NET_CONFIGsion': NET_CONFIGsion,
                'Target_PID': ibs_data.get('target_pid', 'N/A'),
                'Total_Samples': ibs_data.get('total_samples', 0),
                'Unique_Pages': ibs_data.get('unique_pages', 0),
                'Total_Hits': ibs_data.get('total_hits', 0),
                'Avg_Accesses_Per_Page': round(ibs_data.get('avg_accesses_per_page', 0), 2),
                'THP_Efficiency_Percent': round(ibs_data.get('thp_efficiency', 0), 2),
                'Used_THP_Offsets': ibs_data.get('used_thp_offsets', 0),
                'Hot_Region_Percent': round(ibs_data.get('hot_region_percent', 0), 2),
                'Low_Access_Pages': ibs_data.get('low_access_pages', 0),
                'Medium_Access_Pages': ibs_data.get('medium_access_pages', 0),
                'High_Access_Pages': ibs_data.get('high_access_pages', 0),
                'Very_High_Access_Pages': ibs_data.get('very_high_access_pages', 0)
            }
            
            # 创建DataFrame
            df = pd.DataFrame([row])
            
            # 重新排序列以便更好的显示
            column_order = [
                'NET_CONFIGsion',
                'Target_PID',
                'Total_Samples',
                'Unique_Pages',
                'Total_Hits',
                'Avg_Accesses_Per_Page',
                'THP_Efficiency_Percent',
                'Used_THP_Offsets',
                'Hot_Region_Percent',
                'Low_Access_Pages',
                'Medium_Access_Pages',
                'High_Access_Pages',
                'Very_High_Access_Pages'
            ]
            df = df[column_order]
            
            # 设置更友好的列名
            df.columns = [
                'Tiering Version',
                'Target PID',
                'Total Samples',
                'Unique Pages',
                'Total Hits',
                'Avg Accesses/Page',
                'THP Efficiency (%)',
                'Used THP Offsets',
                'Hot Region (%)',
                'Low Access Pages',
                'Medium Access Pages',
                'High Access Pages',
                'Very High Access Pages'
            ]
            
            # 显示表格
            print(f"\n{'='*120}")
            print(f"Perf IBS Statistics: {workload} with {mem_policy} - {NET_CONFIGsion}")
            print(f"{'='*120}")
            print(df.to_string(index=False))
            
            # 保存到CSV文件
            csv_filename = f"{workload}_{mem_policy}_{NET_CONFIGsion}_perf_ibs_stats.csv"
            csv_filepath = os.path.join(output_dir, csv_filename)
            df.to_csv(csv_filepath, index=False)
            print(f"Table saved to: {csv_filepath}")
            
            # 计算一些统计信息
            print(f"\nStatistics Summary for {workload} with {mem_policy} - {NET_CONFIGsion}:")
            print(f"  Total samples: {df['Total Samples'].iloc[0]:,}")
            print(f"  Unique pages: {df['Unique Pages'].iloc[0]:,}")
            print(f"  THP efficiency: {df['THP Efficiency (%)'].iloc[0]:.1f}%")
            print(f"  Hot region: {df['Hot Region (%)'].iloc[0]:.1f}%")

import subprocess
import re
from collections import defaultdict
import sys

def analyze_ibs_hot_pages(perf_ibs_log, workload_pid, workload, mem_policy, NET_CONFIGsion, output_dir="perf_ibs_tables"):
    pid = workload_pid
    try:
        # Get IBS data for target PID
        result = subprocess.run([
            'sudo', 'perf', 'script', '-i', perf_ibs_log
        ], capture_output=True, text=True)
        
        page_hits = defaultdict(int)
        va_to_pa = {}
        instruction_addrs = defaultdict(int)
        
        target_pid_samples = 0
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or pid not in line:
                continue
                
            target_pid_samples += 1
            
            # Parse IBS output: "comm pid [cpu] timestamp: period event: addr function"
            parts = line.split()
            if len(parts) >= 6:
                # Find address (usually after colon)
                for i, part in enumerate(parts):
                    if ':' in part and i < len(parts) - 1:
                        addr_part = parts[i + 1]
                        if re.match(r'^[0-9a-fA-F]+$', addr_part):
                            addr = int(addr_part, 16)
                            
                            # 4KB page alignment
                            page = addr & ~0xFFF
                            page_hits[page] += 1
                            
                            # Record instruction address (for hot code analysis)
                            instruction_addrs[addr] += 1
                            break
        
        if not page_hits:
            print(f"❌ No IBS data found for PID {pid}")
            return
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成输出文件名
        analysis_filename = f"{workload}_{mem_policy}_{NET_CONFIGsion}_ibs_hot_pages_analysis.txt"
        analysis_filepath = os.path.join(output_dir, analysis_filename)
        
        # 打开文件进行写入
        with open(analysis_filepath, 'w', encoding='utf-8') as f:
            # Sort and output hot pages
            sorted_pages = sorted(page_hits.items(), key=lambda x: x[1], reverse=True)
            
            f.write(f"🔥 IBS Hot 4KB Pages Analysis (PID {pid}):\n")
            f.write("Virtual Address\t\tHits\t\tTHP Offset\tPercentage\n")
            f.write("-" * 70 + "\n")
            
            total_hits = sum(page_hits.values())
            
            for i, (vpage, hits) in enumerate(sorted_pages[:25]):
                # Calculate offset within THP
                thp_base = vpage & ~0x1FFFFF  # 2MB alignment
                offset_in_thp = (vpage - thp_base) // 4096
                percentage = (hits / total_hits) * 100
                
                f.write(f"0x{vpage:x}\t{hits}\t\t{offset_in_thp}/512\t{percentage:.1f}%\n")
            
            f.write(f"\n📊 Statistics:\n")
            f.write(f"- Total IBS Samples: {target_pid_samples:,}\n")
            f.write(f"- Unique Pages: {len(page_hits):,}\n")
            f.write(f"- Total Accesses: {total_hits:,}\n")
            f.write(f"- Average Accesses per Page: {total_hits / len(page_hits):.1f}\n")
            
            # Analyze hot instructions
            sorted_instructions = sorted(instruction_addrs.items(), key=lambda x: x[1], reverse=True)
            f.write(f"\n🎯 Hot Instruction Addresses (Top 10):\n")
            for addr, count in sorted_instructions[:10]:
                f.write(f"0x{addr:x}: {count:,} hits\n")
            
            # Generate THP page access frequency histogram
            f.write(f"\n" + "="*80 + "\n")
            f.write(f"📊 THP Page Access Frequency Histogram (PID {pid})\n")
            f.write(f"="*80 + "\n")
            
            # Count page access distribution within each THP
            thp_page_counts = defaultdict(int)
            for vpage, hits in page_hits.items():
                thp_base = vpage & ~0x1FFFFF  # 2MB alignment
                offset_in_thp = (vpage - thp_base) // 4096
                thp_page_counts[offset_in_thp] += hits
            
            # Sort by offset
            sorted_thp_pages = sorted(thp_page_counts.items())
            
            # Calculate histogram statistics
            max_hits = max(thp_page_counts.values()) if thp_page_counts else 0
            total_thp_hits = sum(thp_page_counts.values())
            
            f.write(f"THP Offset\tAccess Count\tPercentage\tHistogram\n")
            f.write(f"-" * 60 + "\n")
            
            for offset, hits in sorted_thp_pages:
                percentage = (hits / total_thp_hits) * 100
                # Create simple ASCII histogram (max 50 characters)
                bar_length = int((hits / max_hits) * 50) if max_hits > 0 else 0
                bar = "█" * bar_length
                f.write(f"{offset:3d}/512\t{hits:8d}\t{percentage:5.1f}%\t{bar}\n")
            
            # Generate base page access histogram
            f.write(f"\n" + "="*80 + "\n")
            f.write(f"📊 Base Page Access Histogram (PID {pid})\n")
            f.write(f"="*80 + "\n")
            
            # Group statistics by access count
            access_ranges = [
                (1, 10, "1-10"),
                (11, 50, "11-50"),
                (51, 100, "51-100"),
                (101, 500, "101-500"),
                (501, 1000, "501-1K"),
                (1001, 5000, "1K-5K"),
                (5001, 10000, "5K-10K"),
                (10001, 50000, "10K-50K"),
                (50001, float('inf'), "50K+")
            ]
            
            range_counts = defaultdict(int)
            for vpage, hits in page_hits.items():
                for min_val, max_val, label in access_ranges:
                    if min_val <= hits <= max_val:
                        range_counts[label] += 1
                        break
            
            f.write(f"Access Range\tPage Count\tPercentage\tHistogram\n")
            f.write(f"-" * 60 + "\n")
            
            total_pages = len(page_hits)
            max_pages = max(range_counts.values()) if range_counts else 0
            
            for min_val, max_val, label in access_ranges:
                count = range_counts[label]
                if count > 0:
                    percentage = (count / total_pages) * 100
                    bar_length = int((count / max_pages) * 50) if max_pages > 0 else 0
                    bar = "█" * bar_length
                    f.write(f"{label:12s}\t{count:8d}\t{percentage:5.1f}%\t{bar}\n")
            
            # Output THP usage efficiency analysis
            f.write(f"\n" + "="*80 + "\n")
            f.write(f"🎯 THP Usage Efficiency Analysis (PID {pid})\n")
            f.write(f"="*80 + "\n")
            
            used_offsets = len(thp_page_counts)
            total_offsets = 512
            efficiency = (used_offsets / total_offsets) * 100
            
            f.write(f"📈 THP Usage Statistics:\n")
            f.write(f"- Used Offsets: {used_offsets}/512 ({efficiency:.1f}%)\n")
            f.write(f"- Unused Offsets: {total_offsets - used_offsets}/512 ({100-efficiency:.1f}%)\n")
            
            if thp_page_counts:
                min_offset = min(thp_page_counts.keys())
                max_offset = max(thp_page_counts.keys())
                f.write(f"- Usage Range: {min_offset}-{max_offset}/512\n")
                f.write(f"- Usage Span: {max_offset - min_offset + 1} pages\n")
            
            # Automatic analysis and conclusion output
            f.write(f"\n" + "="*80 + "\n")
            f.write(f"🎯 Automatic Analysis Conclusion (PID {pid})\n")
            f.write(f"="*80 + "\n")
            
            # Analyze THP usage efficiency
            f.write(f"📊 THP Usage Efficiency Analysis:\n")
            f.write(f"• Usage Rate: {efficiency:.1f}% ({used_offsets}/512 offset positions used)\n")
            if thp_page_counts:
                f.write(f"• Usage Range: {min_offset}-{max_offset}/512 (span {max_offset - min_offset + 1} pages)\n")
            f.write(f"• Efficiency Assessment: {'Relatively concentrated usage' if efficiency < 50 else 'Relatively scattered usage'}, {100-efficiency:.1f}% of THP space remains unused\n")
            
            # Analyze THP usage patterns
            f.write(f"\n🎯 THP Usage Pattern Analysis:\n")
            if thp_page_counts:
                # Calculate hot region concentration
                sorted_thp_pages = sorted(thp_page_counts.items(), key=lambda x: x[1], reverse=True)
                total_thp_hits = sum(thp_page_counts.values())
                
                # Find top 20% offset positions by access count
                top_20_percent = max(1, len(sorted_thp_pages) // 5)
                top_offsets = [offset for offset, hits in sorted_thp_pages[:top_20_percent]]
                
                if top_offsets:
                    min_hot_offset = min(top_offsets)
                    max_hot_offset = max(top_offsets)
                    hot_region_start = (min_hot_offset / 512) * 100
                    hot_region_end = (max_hot_offset / 512) * 100
                    
                    f.write(f"• Hot Region: {hot_region_start:.0f}%-{hot_region_end:.0f}% (offset {min_hot_offset}-{max_hot_offset}/512)\n")
                    
                    # Calculate hot region access percentage
                    hot_region_hits = sum(thp_page_counts[offset] for offset in top_offsets)
                    hot_region_percent = (hot_region_hits / total_thp_hits) * 100
                    f.write(f"• Hot Region Access: {hot_region_percent:.1f}% ({hot_region_hits:,} accesses)\n")
                    
                    # Analyze hot distribution characteristics
                    if max_hot_offset - min_hot_offset < 50:
                        distribution = "Highly Concentrated"
                    elif max_hot_offset - min_hot_offset < 100:
                        distribution = "Relatively Concentrated"
                    elif max_hot_offset - min_hot_offset < 200:
                        distribution = "Moderately Scattered"
                    else:
                        distribution = "Relatively Scattered"
                    
                    f.write(f"• Hot Distribution: {distribution} (span {max_hot_offset - min_hot_offset + 1} pages)\n")
                    
                    # Analyze THP usage efficiency
                    if hot_region_percent > 70:
                        efficiency_desc = "Very High Efficiency"
                    elif hot_region_percent > 50:
                        efficiency_desc = "High Efficiency"
                    elif hot_region_percent > 30:
                        efficiency_desc = "Medium Efficiency"
                    else:
                        efficiency_desc = "Low Efficiency"
                    
                    f.write(f"• THP Efficiency: {efficiency_desc} (hot region accounts for {hot_region_percent:.1f}% of accesses)\n")
                else:
                    f.write(f"• Hot Region: No significant hotspots\n")
            else:
                f.write(f"• Hot Region: No data\n")
            
            # Analyze Base Page access patterns
            f.write(f"\n📈 Base Page Access Pattern Analysis:\n")
            low_access = range_counts.get("1-10", 0)
            medium_access = range_counts.get("11-50", 0) + range_counts.get("51-100", 0) + range_counts.get("101-500", 0)
            high_access = range_counts.get("501-1K", 0) + range_counts.get("1K-5K", 0) + range_counts.get("5K-10K", 0)
            very_high_access = range_counts.get("10K-50K", 0) + range_counts.get("50K+", 0)
            
            low_percent = (low_access / total_pages) * 100
            medium_percent = (medium_access / total_pages) * 100
            high_percent = (high_access / total_pages) * 100
            very_high_percent = (very_high_access / total_pages) * 100
            
            f.write(f"• Low Access Pages: {low_percent:.1f}% ({low_access} pages, 1-10 accesses)\n")
            f.write(f"• Medium Access Pages: {medium_percent:.1f}% ({medium_access} pages, 11-500 accesses)\n")
            f.write(f"• High Access Pages: {high_percent:.1f}% ({high_access} pages, 501-10K accesses)\n")
            f.write(f"• Very High Access Pages: {very_high_percent:.1f}% ({very_high_access} pages, 10K+ accesses)\n")
            
            # Analyze access concentration
            f.write(f"\n🔥 Access Concentration Analysis:\n")
            if very_high_percent > 5:
                concentration = "Very High"
            elif high_percent > 20:
                concentration = "High"
            elif medium_percent > 40:
                concentration = "Medium"
            else:
                concentration = "Low"
            
            f.write(f"• Access Concentration: {concentration}\n")
            f.write(f"• Hot Page Characteristics: {'Few pages heavily accessed' if very_high_percent > 2 else 'Relatively uniform access distribution'}\n")
            
            # Performance optimization recommendations
            f.write(f"\n💡 Performance Optimization Recommendations:\n")
            if efficiency < 30:
                f.write(f"• Low THP usage rate ({efficiency:.1f}%), consider optimizing memory allocation strategy\n")
            elif efficiency > 80:
                f.write(f"• High THP usage rate ({efficiency:.1f}%), current memory usage efficiency is good\n")
            else:
                f.write(f"• Medium THP usage rate ({efficiency:.1f}%), there is room for further optimization\n")
            
            if very_high_percent > 5:
                f.write(f"• Very high access pages exist ({very_high_percent:.1f}%), consider data locality optimization\n")
            elif low_percent > 60:
                f.write(f"• Many low access pages ({low_percent:.1f}%), consider memory compression or paging strategies\n")
            
            # Algorithm characteristics analysis
            f.write(f"\n🧮 Algorithm Characteristics Analysis:\n")
            if concentration in ["Very High", "High"]:
                f.write(f"• Matches graph algorithm characteristics: few key data structures are frequently accessed\n")
                f.write(f"• Recommendation: optimize cache-friendliness of hot data structures\n")
            else:
                f.write(f"• Relatively uniform access pattern: may be suitable for parallel processing\n")
                f.write(f"• Recommendation: consider data sharding and load balancing\n")
        
        print(f"✅ IBS hot pages analysis saved to: {analysis_filepath}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def main():
    """主函数"""
    results_base_path = "../results"
    
    print("正在查找perf_ibs_op.log结果目录...")
    result_dirs = find_perf_ibs_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: 未找到perf_ibs_op.log结果目录")
        return
    
    print(f"找到 {len(result_dirs)} 个perf_ibs_op.log结果目录")
    
    # 按工作负载和内存策略分组数据
    grouped_data = {}
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        tiering = result_dir['tiering']
        perf_ibs_log = result_dir['perf_ibs_log']
        workload_pid = result_dir['workload_pid']
        
        print(f"正在处理: {workload} - {tiering} - {mem_policy}")
        
        # 解析perf_ibs_op.log数据
        ibs_data = parse_perf_ibs_log(perf_ibs_log, workload_pid)
        
        # 生成详细的IBS hot pages分析报告
        if ibs_data and 'target_pid' in ibs_data:
            print(f"正在生成详细分析报告: {workload} - {tiering} - {mem_policy}")
            analyze_ibs_hot_pages(perf_ibs_log, ibs_data['target_pid'], workload, mem_policy, tiering)
        
        # 按工作负载和内存策略分组
        key = (workload, mem_policy)
        if key not in grouped_data:
            grouped_data[key] = {}
        
        grouped_data[key][tiering] = ibs_data
    
    # 为每个工作负载和内存策略组合生成表格
    create_perf_ibs_tables(grouped_data)
    
    # 生成访问分布直方图
    print("\n正在生成访问分布直方图...")
    generate_access_distribution_histograms(grouped_data)
    
    print("\n所有Perf IBS统计表格和直方图已生成完成!")
    print("CSV表格文件保存在 perf_ibs_tables/ 目录中")
    print("直方图文件保存在 perf_ibs_tables/histograms/ 目录中")

if __name__ == "__main__":
    main()
