#!/usr/bin/env python3
"""
解析numa_page.log文件并生成表格
展示不同TIERING版本下的do_numa_page和do_huge_pmd_numa_page的count和latency
每个表格代表一个工作负载在特定内存策略下的统计数据
"""

import os
import re
import glob
import pandas as pd
from pathlib import Path

def parse_numa_page_log(numa_page_log_path):
    """解析numa_page.log文件，提取最终统计数据"""
    data = {}
    
    try:
        with open(numa_page_log_path, 'r') as f:
            content = f.read()
        
        # 提取Final Statistics部分
        final_stats_match = re.search(r'=== Final Statistics ===(.*?)(?=\n\n|\ndo_numa_page latency|$)', content, re.DOTALL)
        if final_stats_match:
            final_stats = final_stats_match.group(1)
            
            # 提取do_numa_page统计
            numa_page_calls_match = re.search(r'do_numa_page:\s*(\d+)', final_stats)
            numa_page_latency_match = re.search(r'do_numa_page average latency:\s*(\d+)\s*microseconds', final_stats)
            
            # 提取do_huge_pmd_numa_page统计
            huge_pmd_calls_match = re.search(r'do_huge_pmd_numa_page:\s*(\d+)', final_stats)
            huge_pmd_latency_match = re.search(r'do_huge_pmd_numa_page average latency:\s*(\d+)\s*microseconds', final_stats)
            
            if numa_page_calls_match:
                data['do_numa_page_calls'] = int(numa_page_calls_match.group(1))
            
            if numa_page_latency_match:
                data['do_numa_page_latency_us'] = int(numa_page_latency_match.group(1))
            
            if huge_pmd_calls_match:
                data['do_huge_pmd_numa_page_calls'] = int(huge_pmd_calls_match.group(1))
            
            if huge_pmd_latency_match:
                data['do_huge_pmd_numa_page_latency_us'] = int(huge_pmd_latency_match.group(1))
        
        return data
    
    except FileNotFoundError:
        print(f"Warning: numa_page.log file not found: {numa_page_log_path}")
        return None
    except Exception as e:
        print(f"Error parsing numa_page.log {numa_page_log_path}: {e}")
        return None

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

def find_numa_page_result_directories(results_base_path):
    """查找所有包含numa_page.log数据的结果目录"""
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
                        numa_page_log = os.path.join(mem_dir, "numa_page.log")
                        
                        # 检查是否存在numa_page.log文件
                        if os.path.exists(numa_page_log):
                            result_dirs.append({
                                'workload': workload,
                                'tiering': tiering,
                                'mem_policy': mem_policy,
                                'ldram_size': ldram_size,
                                'numa_page_log': numa_page_log
                            })
    
    return result_dirs

def create_numa_page_tables(grouped_data):
    """为每个工作负载和内存策略组合创建表格"""
    
    output_dir = "numa_page_tables"
    os.makedirs(output_dir, exist_ok=True)
    
    for (workload, mem_policy), tiering_data in grouped_data.items():
        print(f"正在生成表格: {workload} with {mem_policy}")
        
        # 准备表格数据
        table_data = []
        
        for tiering_version, numa_data in tiering_data.items():
            if numa_data:  # 确保数据存在
                row = {
                    'Tiering_Version': tiering_version,
                    'do_numa_page_calls': numa_data.get('do_numa_page_calls', 0),
                    'do_numa_page_latency_us': numa_data.get('do_numa_page_latency_us', 0),
                    'do_huge_pmd_numa_page_calls': numa_data.get('do_huge_pmd_numa_page_calls', 0),
                    'do_huge_pmd_numa_page_latency_us': numa_data.get('do_huge_pmd_numa_page_latency_us', 0)
                }
                table_data.append(row)
        
        if table_data:
            # 创建DataFrame
            df = pd.DataFrame(table_data)
            
            # 重新排序列以便更好的显示
            column_order = [
                'Tiering_Version',
                'do_numa_page_calls',
                'do_numa_page_latency_us',
                'do_huge_pmd_numa_page_calls',
                'do_huge_pmd_numa_page_latency_us'
            ]
            df = df[column_order]
            
            # 设置更友好的列名
            df.columns = [
                'Tiering Version',
                'do_numa_page Calls',
                'do_numa_page Latency (μs)',
                'do_huge_pmd_numa_page Calls',
                'do_huge_pmd_numa_page Latency (μs)'
            ]
            
            # 按tiering版本排序
            df = df.sort_values('Tiering Version')
            
            # 显示表格
            print(f"\n{'='*80}")
            print(f"NUMA Page Statistics: {workload} with {mem_policy}")
            print(f"{'='*80}")
            print(df.to_string(index=False))
            
            # 保存到CSV文件
            csv_filename = f"{workload}_{mem_policy}_numa_page_stats.csv"
            csv_filepath = os.path.join(output_dir, csv_filename)
            df.to_csv(csv_filepath, index=False)
            print(f"Table saved to: {csv_filepath}")
            
            # 保存到HTML文件（格式化更好）
            html_filename = f"{workload}_{mem_policy}_numa_page_stats.html"
            html_filepath = os.path.join(output_dir, html_filename)
            
            # 创建HTML表格
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NUMA Page Statistics: {workload} with {mem_policy}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; text-align: center; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: right; }}
        th {{ background-color: #f2f2f2; font-weight: bold; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .tiering-col {{ text-align: left; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>NUMA Page Statistics: {workload} with {mem_policy}</h1>
    {df.to_html(index=False, table_id='numa_stats', classes=['table'], escape=False)}
    <script>
        // 让第一列左对齐
        document.querySelectorAll('#numa_stats td:first-child').forEach(function(cell) {{
            cell.className = 'tiering-col';
        }});
    </script>
</body>
</html>
"""
            
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"HTML table saved to: {html_filepath}")
            
            # 计算一些统计信息
            print(f"\nStatistics Summary for {workload} with {mem_policy}:")
            print(f"  Total tiering versions analyzed: {len(df)}")
            
            if len(df) > 0:
                print(f"  do_numa_page calls range: {df['do_numa_page Calls'].min():,} - {df['do_numa_page Calls'].max():,}")
                print(f"  do_numa_page latency range: {df['do_numa_page Latency (μs)'].min()} - {df['do_numa_page Latency (μs)'].max()} μs")
                print(f"  do_huge_pmd_numa_page calls range: {df['do_huge_pmd_numa_page Calls'].min():,} - {df['do_huge_pmd_numa_page Calls'].max():,}")
                print(f"  do_huge_pmd_numa_page latency range: {df['do_huge_pmd_numa_page Latency (μs)'].min()} - {df['do_huge_pmd_numa_page Latency (μs)'].max()} μs")
                
                # 计算huge page vs regular page的比例
                total_numa_calls = df['do_numa_page Calls'].sum()
                total_huge_calls = df['do_huge_pmd_numa_page Calls'].sum()
                if total_numa_calls + total_huge_calls > 0:
                    huge_ratio = total_huge_calls / (total_numa_calls + total_huge_calls) * 100
                    print(f"  Huge page ratio: {huge_ratio:.1f}% (huge pages / total pages)")

def main():
    """主函数"""
    results_base_path = "../results"
    
    print("正在查找numa_page.log结果目录...")
    result_dirs = find_numa_page_result_directories(results_base_path)
    
    if not result_dirs:
        print("Error: 未找到numa_page.log结果目录")
        return
    
    print(f"找到 {len(result_dirs)} 个numa_page.log结果目录")
    
    # 按工作负载和内存策略分组数据
    grouped_data = {}
    
    for result_dir in result_dirs:
        workload = result_dir['workload']
        mem_policy = result_dir['mem_policy']
        tiering = result_dir['tiering']
        numa_page_log = result_dir['numa_page_log']
        
        print(f"正在处理: {workload} - {tiering} - {mem_policy}")
        
        # 解析numa_page.log数据
        numa_data = parse_numa_page_log(numa_page_log)
        
        # 按工作负载和内存策略分组
        key = (workload, mem_policy)
        if key not in grouped_data:
            grouped_data[key] = {}
        
        grouped_data[key][tiering] = numa_data
    
    # 为每个工作负载和内存策略组合生成表格
    create_numa_page_tables(grouped_data)
    
    print("\n所有NUMA Page统计表格已生成完成!")
    print("表格文件保存在 numa_page_tables/ 目录中")

if __name__ == "__main__":
    main()

