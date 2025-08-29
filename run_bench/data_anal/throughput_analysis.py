#!/usr/bin/env python3
import pandas as pd
import numpy as np

# 读取CSV文件
data = pd.read_csv('11_vs_12.csv', sep=r'\s+')

# 提取第一组数据（前5列）
workloads = data.iloc[:, 0]  # workload列
autonuma_tiering = data.iloc[:, 1]  # autonuma_tiering列
autonuma_tiering_thp = data.iloc[:, 2]  # autonuma_tiering_thp列
nobalance = data.iloc[:, 3]  # nobalance列
nobalance_thp = data.iloc[:, 4]  # nobalance_thp列

# 提取第二组数据（后5列）
autonuma_tiering_1_2 = data.iloc[:, 6]  # autonuma_tiering_1_2列
autonuma_tiering_thp_1_2 = data.iloc[:, 7]  # autonuma_tiering_thp_1_2列
nobalance_1_2 = data.iloc[:, 8]  # nobalance_1_2列
nobalance_thp_1_2 = data.iloc[:, 9]  # nobalance_thp_1_2列

# 计算性能改进百分比
def calculate_improvement(baseline, comparison):
    """计算相对于基准的改进百分比"""
    if baseline == 0:
        return 0.0
    return ((comparison - baseline) / baseline) * 100

# 计算各配置相对于autonuma_tiering的改进
results = []
for i in range(len(workloads)):
    workload = workloads.iloc[i]
    baseline = autonuma_tiering.iloc[i]
    
    # 计算所有配置相对于autonuma_tiering的改进
    thp_improvement = calculate_improvement(baseline, autonuma_tiering_thp.iloc[i])
    nobalance_improvement = calculate_improvement(baseline, nobalance.iloc[i])
    nobalance_thp_improvement = calculate_improvement(baseline, nobalance_thp.iloc[i])
    autonuma_tiering_1_2_improvement = calculate_improvement(baseline, autonuma_tiering_1_2.iloc[i])
    autonuma_tiering_thp_1_2_improvement = calculate_improvement(baseline, autonuma_tiering_thp_1_2.iloc[i])
    nobalance_1_2_improvement = calculate_improvement(baseline, nobalance_1_2.iloc[i])
    nobalance_thp_1_2_improvement = calculate_improvement(baseline, nobalance_thp_1_2.iloc[i])
    
    results.append({
        'workload': workload,
        'thp': thp_improvement,
        'nobalance': nobalance_improvement,
        'nobalance_thp': nobalance_thp_improvement,
        'autonuma_tiering_1_2': autonuma_tiering_1_2_improvement,
        'autonuma_tiering_thp_1_2': autonuma_tiering_thp_1_2_improvement,
        'nobalance_1_2': nobalance_1_2_improvement,
        'nobalance_thp_1_2': nobalance_thp_1_2_improvement
    })

# 准备输出内容
output_lines = []
output_lines.append("Throughput Performance Improvement (%) - All columns vs autonuma_tiering:")
output_lines.append("=" * 120)
output_lines.append(f"{'Workload':<20} {'THP':>8} {'NoBal':>8} {'NoBal_THP':>8} {'Auto_1_2':>8} {'Auto_THP_1_2':>8} {'NoBal_1_2':>8} {'NoBal_THP_1_2':>8}")
output_lines.append("-" * 120)

for result in results:
    line = (f"{result['workload']:<20} "
            f"{result['thp']:>8.2f}% "
            f"{result['nobalance']:>8.2f}% "
            f"{result['nobalance_thp']:>8.2f}% "
            f"{result['autonuma_tiering_1_2']:>8.2f}% "
            f"{result['autonuma_tiering_thp_1_2']:>8.2f}% "
            f"{result['nobalance_1_2']:>8.2f}% "
            f"{result['nobalance_thp_1_2']:>8.2f}%")
    output_lines.append(line)

output_lines.append("")
output_lines.append("=" * 120)
output_lines.append("Legend:")
output_lines.append("THP: autonuma_tiering_thp")
output_lines.append("NoBal: nobalance") 
output_lines.append("NoBal_THP: nobalance_thp")
output_lines.append("Auto_1_2: autonuma_tiering_1_2")
output_lines.append("Auto_THP_1_2: autonuma_tiering_thp_1_2")
output_lines.append("NoBal_1_2: nobalance_1_2")
output_lines.append("NoBal_THP_1_2: nobalance_thp_1_2")

# 保存到文件
with open('11_vs_12.txt', 'w') as f:
    for line in output_lines:
        f.write(line + '\n')

# 同时打印到控制台
for line in output_lines:
    print(line)

print(f"\n结果已保存到 11_vs_12.txt") 

