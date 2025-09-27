# memstress - 内存带宽压力测试工具

memstress 是一个用于生成可控内存带宽竞争的工具，特别设计用于 NUMA 环境下的内存性能测试。

## 功能特性

- **CPU绑定**: 可以绑定到指定的CPU核心或核心范围
- **NUMA内存绑定**: 强制内存分配到指定的NUMA节点
- **随机内存访问**: 使用随机访问模式避免缓存预取优化
- **带宽控制**: 精确控制内存访问带宽
- **平滑启动**: 渐进式增加带宽，避免突发峰值
- **实时监控**: 显示实际带宽使用情况

## 编译依赖

### Ubuntu/Debian
```bash
sudo apt-get install gcc libnuma-dev
```

### RHEL/CentOS/Fedora
```bash
sudo yum install gcc numactl-devel
# 或者 (新版本)
sudo dnf install gcc numactl-devel
```

## 编译

```bash
cd tools/
make check-deps  # 检查依赖
make             # 编译
```

## 使用方法

### 基本语法
```bash
./memstress -c <CPU列表> -n <NUMA节点> -s <缓冲区大小MB> -b <目标带宽MB/s> [选项]
```

**注意：程序将持续运行直到手动停止 (Ctrl+C)**

### 参数说明

| 参数 | 描述 | 示例 |
|------|------|------|
| `-c` | 绑定的CPU列表 | `0,1,2` 或 `0-3` |
| `-n` | NUMA节点编号 | `0`, `1`, `2` |
| `-s` | 缓冲区大小(MB) | `1024` |
| `-b` | 目标带宽(MB/s) | `500` |
| `-w` | 预热时间(秒) | `5` (默认) |
| `-h` | 显示帮助 | |

### 使用示例

#### 1. 基本使用
在CPU 0,1上运行，使用NUMA节点0的1GB内存，目标带宽500MB/s：
```bash
./memstress -c 0,1 -n 0 -s 1024 -b 500
```

#### 2. 使用CPU范围
绑定到CPU 0-7，使用NUMA节点1：
```bash
./memstress -c 0-7 -n 1 -s 2048 -b 1000 -d 120
```

#### 3. 低带宽长时间测试
模拟低强度但持续的内存压力：
```bash
./memstress -c 4,5 -n 0 -s 512 -b 100 -d 300 -w 10
```

#### 4. 高强度测试
高带宽压力测试：
```bash
./memstress -c 0-3 -n 1 -s 4096 -b 2000 -d 60
```

## 工作原理

### 1. CPU和内存绑定
- 使用 `sched_setaffinity()` 将进程绑定到指定CPU
- 使用 `set_mempolicy()` 强制内存分配到指定NUMA节点

### 2. 随机访问模式
- 将内存缓冲区分割为缓存行大小的块(64字节)
- 使用Fisher-Yates洗牌算法生成随机访问序列
- 定期重新生成访问模式避免规律性

### 3. 带宽控制
- 计算每次内存访问应消耗的时间
- 测量实际访问时间，动态调整延迟
- 使用 `nanosleep()` 进行精确的微秒级延迟

### 4. 平滑启动
- 在预热期间线性增加目标带宽
- 避免突然的带宽峰值对系统造成冲击

## 监控输出

程序运行时会实时显示：
- 当前运行时间
- 目标带宽 vs 实际带宽
- 累计内存访问次数

示例输出：
```
运行时间: 10s, 目标带宽: 500.0 MB/s, 实际带宽: 498.2 MB/s, 总访问次数: 81920000
```

## 注意事项

1. **权限要求**: 绑定CPU和设置NUMA策略可能需要特殊权限
2. **系统影响**: 高带宽测试会显著影响系统性能
3. **NUMA拓扑**: 确保指定的NUMA节点存在
4. **内存大小**: 确保系统有足够的可用内存

## 故障排除

### 编译错误
- 确保安装了 `libnuma-dev` 或 `numactl-devel`
- 检查gcc版本是否支持C99标准

### 运行时错误
- **CPU绑定失败**: 检查CPU编号是否有效
- **内存分配失败**: 检查可用内存和NUMA节点
- **权限错误**: 尝试使用sudo运行

### 检查NUMA拓扑
```bash
numactl --hardware
lscpu
```

## 性能调优建议

1. **禁用CPU频率缩放**: 
   ```bash
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

2. **禁用NUMA平衡**:
   ```bash
   echo 0 | sudo tee /proc/sys/kernel/numa_balancing
   ```

3. **设置进程优先级**:
   ```bash
   nice -n -20 ./memstress [参数]
   ```

## 许可证

本工具遵循项目的整体许可证。
