#!/bin/bash
# memstress 测试示例脚本

set -e

echo "=== memstress 工具测试示例 ==="
echo

# 检查工具是否存在
if [ ! -f "./memstress" ]; then
    echo "错误: memstress 工具不存在，请先运行 make 编译"
    exit 1
fi

echo "1. 基本功能测试 (低强度) - 10秒"
echo "   命令: ./memstress -c 0,1 -n 0 -s 64 -b 30 -w 2"
echo "   说明: 使用CPU 0,1，NUMA节点0，64MB内存，30MB/s带宽"
echo
timeout 10s ./memstress -c 0,1 -n 0 -s 64 -b 30 -w 2 || true
echo

echo "2. 中等强度测试 - 15秒"
echo "   命令: ./memstress -c 0-3 -n 0 -s 256 -b 200 -w 3"
echo "   说明: 使用CPU 0-3，NUMA节点0，256MB内存，200MB/s带宽"
echo
timeout 15s ./memstress -c 0-3 -n 0 -s 256 -b 200 -w 3 || true
echo

echo "3. 跨NUMA节点测试 - 8秒"
echo "   命令: ./memstress -c 64,65 -n 1 -s 128 -b 100 -w 2"
echo "   说明: 使用NUMA节点1的CPU，在NUMA节点1分配内存"
echo
timeout 8s ./memstress -c 64,65 -n 1 -s 128 -b 100 -w 2 || true
echo

echo "=== 测试完成 ==="
echo
echo "使用提示:"
echo "- 程序现在会持续运行直到手动停止 (Ctrl+C)"
echo "- 使用 numactl --hardware 查看系统NUMA拓扑"
echo "- 使用 htop 或 top 监控CPU使用情况"
echo "- 调整参数 -s (内存大小) 和 -b (带宽) 来适应不同测试需求"
echo "- 在生产环境中运行时请谨慎，高带宽会影响系统性能"
