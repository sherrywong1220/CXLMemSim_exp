# NUMA Chain Tracker Makefile
# Builds native eBPF C program for NUMA THP chain tracking

OUTPUT := numa_chain
CLANG ?= clang
LLC ?= llc
ARCH ?= $(shell uname -m | sed 's/x86_64/x86/' | sed 's/aarch64/arm64/')

# BPF相关路径
LIBBPF_DIR ?= /usr/include
BPF_CFLAGS := -I$(LIBBPF_DIR) -I/usr/include/$(shell uname -m)-linux-gnu

# 目标文件
BPFOBJ := $(OUTPUT).bpf.o
SKELETON := $(OUTPUT).skel.h
USEROBJ := $(OUTPUT)

# 默认目标
.PHONY: all clean vmlinux install

all: $(USEROBJ)

# 检查依赖
check-deps:
	@echo "检查依赖..."
	@which $(CLANG) > /dev/null || (echo "错误: 需要安装 clang"; exit 1)
	@which bpftool > /dev/null || (echo "错误: 需要安装 bpftool"; exit 1)
	@pkg-config --exists libbpf || (echo "错误: 需要安装 libbpf-dev"; exit 1)
	@test -f /sys/kernel/btf/vmlinux || (echo "错误: 需要内核BTF支持"; exit 1)
	@echo "依赖检查完成 ✓"

# 生成vmlinux.h（如果不存在）
vmlinux.h:
	@echo "生成 vmlinux.h..."
	bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h

# 生成vmlinux.h的目标
vmlinux: vmlinux.h

# 编译BPF字节码
$(BPFOBJ): $(OUTPUT).bpf.c numa_chain.h vmlinux.h check-deps
	@echo "编译 BPF 程序..."
	$(CLANG) -g -O2 -target bpf -D__TARGET_ARCH_$(ARCH) \
		$(BPF_CFLAGS) \
		-c $(OUTPUT).bpf.c -o $@

# 生成skeleton
$(SKELETON): $(BPFOBJ)
	@echo "生成 BPF skeleton..."
	bpftool gen skeleton $< > $@

# 编译用户空间程序
$(USEROBJ): $(OUTPUT).c $(SKELETON) numa_chain.h
	@echo "编译用户空间程序..."
	$(CC) -g -Wall -O2 \
		$(BPF_CFLAGS) \
		-o $@ $(OUTPUT).c \
		-lbpf -lelf -lz

# 安装系统依赖
install-deps:
	@echo "安装系统依赖..."
	sudo apt update
	sudo apt install -y \
		clang llvm \
		libbpf-dev \
		linux-tools-common linux-tools-generic \
		pkg-config \
		build-essential

# 检查内核支持
check-kernel:
	@echo "检查内核 eBPF 支持..."
	@echo "内核版本: $$(uname -r)"
	@test -d /sys/kernel/debug/tracing || (echo "错误: 需要挂载 debugfs"; exit 1)
	@test -f /proc/sys/kernel/bpf_stats_enabled || (echo "警告: BPF统计未启用")
	@test -f /sys/kernel/btf/vmlinux || (echo "错误: 需要内核BTF支持 (CONFIG_DEBUG_INFO_BTF=y)"; exit 1)
	@echo "内核支持检查完成 ✓"

# 设置权限和环境
setup: check-kernel
	@echo "设置运行环境..."
	# 启用BPF统计
	-sudo sysctl kernel.bpf_stats_enabled=1
	# 确保debugfs已挂载
	@mountpoint -q /sys/kernel/debug || sudo mount -t debugfs none /sys/kernel/debug
	@echo "环境设置完成 ✓"

# 运行程序
run: $(USEROBJ) setup
	@echo "运行 NUMA Chain Tracker..."
	sudo ./$(USEROBJ)

# 后台运行并输出到文件
run-background: $(USEROBJ) setup
	@echo "后台运行 NUMA Chain Tracker..."
	sudo ./$(USEROBJ) > numa_chain_output.log 2>&1 &
	@echo "已启动，输出保存到 numa_chain_output.log"
	@echo "使用 'sudo pkill numa_chain' 停止"

# 显示内核函数是否可用
check-functions:
	@echo "检查目标内核函数..."
	@echo -n "do_huge_pmd_numa_page: "
	@grep -q "do_huge_pmd_numa_page" /proc/kallsyms && echo "✓ 可用" || echo "✗ 不可用"
	@echo -n "do_numa_page: "
	@grep -q "do_numa_page" /proc/kallsyms && echo "✓ 可用" || echo "✗ 不可用"
	@echo -n "migrate_misplaced_folio: "
	@grep -q "migrate_misplaced_folio" /proc/kallsyms && echo "✓ 可用" || echo "✗ 不可用"

# 测试编译（不运行）
test-build: $(USEROBJ)
	@echo "编译测试完成 ✓"
	@ls -la $(USEROBJ) $(BPFOBJ)

# 清理
clean:
	@echo "清理编译文件..."
	rm -f $(BPFOBJ) $(SKELETON) $(USEROBJ)
	rm -f numa_chain_output.log

# 深度清理（包括vmlinux.h）
distclean: clean
	rm -f vmlinux.h

# 调试信息
debug: $(BPFOBJ)
	@echo "=== BPF 程序信息 ==="
	@echo "BPF对象: $(BPFOBJ)"
	@file $(BPFOBJ)
	@echo
	@echo "=== BPF 程序sections ==="
	@readelf -S $(BPFOBJ) 2>/dev/null | grep -E "(fentry|fexit|kprobe)" || echo "未找到BPF程序section"
	@echo
	@echo "=== BTF 信息 ==="
	@bpftool btf dump file $(BPFOBJ) 2>/dev/null | head -20 || echo "未找到BTF信息"

# 帮助信息
help:
	@echo "NUMA Chain Tracker - 可用的make目标："
	@echo ""
	@echo "构建目标："
	@echo "  all           - 编译所有组件（默认）"
	@echo "  vmlinux       - 生成vmlinux.h头文件"
	@echo "  test-build    - 测试编译但不运行"
	@echo ""
	@echo "环境设置："
	@echo "  install-deps  - 安装系统依赖包"
	@echo "  check-deps    - 检查编译依赖"
	@echo "  check-kernel  - 检查内核eBPF支持"
	@echo "  check-functions - 检查目标内核函数可用性"
	@echo "  setup         - 设置运行环境"
	@echo ""
	@echo "运行目标："
	@echo "  run           - 前台运行程序"
	@echo "  run-background - 后台运行程序"
	@echo ""
	@echo "调试目标："
	@echo "  debug         - 显示BPF程序调试信息"
	@echo ""
	@echo "清理目标："
	@echo "  clean         - 清理编译文件"
	@echo "  distclean     - 深度清理（包括vmlinux.h）"
	@echo ""
	@echo "使用示例："
	@echo "  make install-deps  # 首次安装依赖"
	@echo "  make              # 编译"
	@echo "  make run          # 运行"
