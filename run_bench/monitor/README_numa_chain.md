# NUMA Chain Tracker - 原生 eBPF 版本

这是原始 `numa_chain.bt` bpftrace 脚本的原生 eBPF C 语言重写版本，具有更好的性能和更丰富的功能。

## 功能特性

- 🚀 **高性能**: 使用原生 eBPF C 和 fentry/fexit，比 bpftrace 更高效
- 📊 **详细统计**: 跟踪 NUMA THP 调用链的完整统计信息
- 🔍 **实时监控**: 支持实时事件流和周期性统计报告
- 🎯 **精确过滤**: 支持按进程ID过滤
- 📈 **Histogram分析**: 提供详细的调用分布直方图
- 🔧 **易于使用**: 提供便捷的脚本工具

## 跟踪的内核函数

1. **do_huge_pmd_numa_page** - THP NUMA 页面处理入口
2. **do_numa_page** - NUMA 页面处理
3. **migrate_misplaced_folio** - 错位页面迁移

## 文件结构

```
numa_chain/
├── numa_chain.h         # 头文件和数据结构定义
├── numa_chain.bpf.c     # eBPF 内核程序
├── numa_chain.c         # 用户空间控制程序
├── numa_chain.sh        # 便捷使用脚本
├── Makefile            # 编译配置
└── README_numa_chain.md # 本文档
```

## 快速开始

### 1. 安装依赖

```bash
# 使用脚本安装
sudo ./numa_chain.sh install-deps

# 或手动安装
sudo apt update
sudo apt install -y clang llvm libbpf-dev linux-tools-common linux-tools-generic pkg-config build-essential
```

### 2. 检查系统支持

```bash
./numa_chain.sh system-info
```

### 3. 编译程序

```bash
./numa_chain.sh build
```

### 4. 运行监控

```bash
# 前台运行（推荐用于测试）
sudo ./numa_chain.sh run

# 后台运行
sudo ./numa_chain.sh run --background

# 只监控特定进程
sudo ./numa_chain.sh run --pid 1234

# 启用详细输出
sudo ./numa_chain.sh run --verbose
```

## 使用方法

### 基本命令

```bash
# 编译
./numa_chain.sh build

# 运行监控
sudo ./numa_chain.sh run

# 后台运行
sudo ./numa_chain.sh run -b

# 查看状态
./numa_chain.sh status

# 停止后台程序
sudo ./numa_chain.sh stop

# 查看日志
./numa_chain.sh logs

# 实时跟踪日志
./numa_chain.sh logs -f
```

### 高级用法

```bash
# 按进程过滤
sudo ./numa_chain.sh run --pid 1234

# 多个进程过滤（需要直接使用可执行文件）
sudo ./numa_chain --pid 1234 --pid 5678

# 详细输出（显示每个事件）
sudo ./numa_chain.sh run --verbose

# 仅编译测试
make test-build

# 检查目标函数可用性
make check-functions

# 显示BPF程序调试信息
make debug
```

## 输出说明

### 实时输出
程序运行时每20秒输出一次统计摘要：
```
[14:30:15] Calls: huge_pmd=1234 (fallback=987), numa_page=2341, migration=456 (success=398)
```

### 最终分析报告
程序结束时（Ctrl+C）显示完整的分析报告，包括：

1. **总计统计** - 各函数的总调用次数
2. **页面统计** - 唯一页面数量和平均调用次数
3. **调用分布直方图** - 每个页面的调用次数分布
4. **关键洞察** - 调用比例、完成率、重试模式等

### 示例输出
```
======== NUMA THP CHAIN DISTRIBUTION ANALYSIS ========

=== TOTAL CALL STATISTICS ===
do_huge_pmd_numa_page:
  Total calls: 1234
  Handled directly: 247
  Fallback to do_numa_page: 987
  Fallback rate: 80.0%

do_numa_page:
  Total calls: 2341
  Unique pages: 856
  Avg calls per page: 2.7

migrate_misplaced_folio:
  Total calls: 456
  Successful calls: 398
  Success rate: 87.3%

=== CALL DISTRIBUTION HISTOGRAMS ===
(显示各函数每页调用次数的分布图)

=== KEY INSIGHTS ===
numa_page:migration ratio = 5.1:1
Chain completion estimate: 12.3%
✓ High numa_page retry pattern detected (avg 2.7 retries per page)
```

## 与 bpftrace 版本的对比

| 特性 | bpftrace 版本 | 原生 eBPF 版本 |
|------|---------------|----------------|
| 性能 | 较低 | 高 |
| 内存使用 | 较高 | 低 |
| 启动时间 | 慢 | 快 |
| 实时事件流 | 有限 | 完整支持 |
| 过滤功能 | 基础 | 高级（多PID等） |
| 错误处理 | 基础 | 完善 |
| 扩展性 | 有限 | 高 |

## 故障排除

### 常见问题

1. **编译失败**
   ```bash
   # 检查依赖
   ./numa_chain.sh system-info
   # 重新安装依赖
   sudo ./numa_chain.sh install-deps
   ```

2. **权限错误**
   ```bash
   # 确保以root身份运行
   sudo ./numa_chain.sh run
   ```

3. **内核函数不可用**
   ```bash
   # 检查函数可用性
   make check-functions
   # 如果函数不可用，可能需要更新内核或使用kprobe版本
   ```

4. **BTF支持问题**
   ```bash
   # 检查BTF支持
   ls -la /sys/kernel/btf/vmlinux
   # 如果不存在，需要启用CONFIG_DEBUG_INFO_BTF内核选项
   ```

### 调试选项

```bash
# 显示详细编译信息
make V=1

# 显示BPF程序信息
make debug

# 启用详细运行日志
sudo ./numa_chain.sh run --verbose
```

## 性能考虑

- 使用 fentry/fexit 比 kprobe/kretprobe 性能更好
- ringbuf 比 perf_event 更高效
- CO-RE 支持减少了内核版本兼容性问题
- 原子操作确保多核系统的数据一致性

## 系统要求

- Linux 内核 >= 5.8 (支持 fentry/fexit)
- BTF 支持 (CONFIG_DEBUG_INFO_BTF=y)
- libbpf >= 0.6
- clang >= 10.0

## 许可证

GPL v2

## 贡献

欢迎提交问题报告和功能请求！
