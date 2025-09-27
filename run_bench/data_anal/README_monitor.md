# 监控结果解析工具

这个工具用于解析和可视化内存分层系统的监控数据，包括NUMA和TLB性能指标。

## 功能特性

- 解析vmstat目录中的时间序列数据（每5秒采样）
- 解析TLB性能计数器数据
- 生成包含多个指标的时间趋势图
- 支持多个分层版本的对比分析

## 数据源

### vmstat数据
- 位置: `results/{workload}/{tiering}/{mem_policy}/{ldram_size}/vmstat/`
- 格式: `YYYY.MM.DD-HH.MM.SS.txt`
- 指标: `numa_hint_faults`, `numa_pages_migrated`

### TLB数据  
- 位置: `results/{workload}/{tiering}/{mem_policy}/{ldram_size}/perf_tlb.log`
- 格式: perf stat输出格式
- 指标: 各种TLB miss事件

## 输出图表

每个图表代表一个工作负载在特定内存策略下的表现，包含3个子图：

1. **NUMA Hint Faults Rate (per second)**: NUMA提示错误的发生频率
2. **NUMA Pages Migrated Rate (per second)**: NUMA页面迁移的频率  
3. **TLB Misses**: TLB缺失次数

每个子图使用不同的图例表示不同的分层版本（TIERING_VERs）。

## 使用方法

### 1. 设置环境变量

```bash
export DATA_ANAL_BENCHMARKS="NPB-MG.D bc-urand"
export DATA_ANAL_TIERING_VERS="autonuma_tiering autonuma_tiering_thp nobalance nobalance_thp"
export DATA_ANAL_MEM_POLICYS="cpu0.weightedinterleave0_2"
export DATA_ANAL_LDRAM_SIZES="cxl_232G_mo"
```

### 2. 运行分析

```bash
# 使用脚本运行
./run_monitor_analysis.sh

# 或直接运行Python脚本
python3 parse_monitor_results.py
```

### 3. 查看结果

生成的图表保存在 `monitoring_plots/` 目录中，文件命名格式：
```
{workload}_{mem_policy}_monitoring_trends.png
```

## 环境变量说明

- `DATA_ANAL_BENCHMARKS`: 要分析的工作负载列表（空格分隔）
- `DATA_ANAL_TIERING_VERS`: 要对比的分层版本列表（空格分隔）
- `DATA_ANAL_MEM_POLICYS`: 内存策略列表（空格分隔）
- `DATA_ANAL_LDRAM_SIZES`: LDRAM大小配置列表（空格分隔）

## 依赖

```bash
pip3 install matplotlib pandas numpy
```

## 注意事项

1. 确保结果目录结构正确：`results/{workload}/{tiering}/{mem_policy}/{ldram_size}/`
2. vmstat目录和perf_tlb.log文件必须存在
3. 时间序列数据按时间戳自动排序
4. 速率指标通过相邻数据点差值计算
5. 图表会自动调整Y轴范围以适应数据

## 示例输出

- NPB-MG.D工作负载在cpu0.weightedinterleave0_2策略下的监控趋势图
- 对比不同分层版本（autonuma_tiering, autonuma_tiering_thp等）的性能表现
- 时间序列显示系统行为的动态变化
