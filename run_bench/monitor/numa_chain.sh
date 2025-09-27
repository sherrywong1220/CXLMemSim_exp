#!/bin/bash

# NUMA Chain Tracker - 原生 eBPF 版本
# 使用便捷脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否以root身份运行
check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "此程序需要root权限运行"
        echo "请使用: sudo $0 $*"
        exit 1
    fi
}

# 检查依赖
check_dependencies() {
    print_info "检查系统依赖..."
    
    local missing_deps=()
    
    # 检查编译工具
    command -v clang >/dev/null 2>&1 || missing_deps+=("clang")
    command -v bpftool >/dev/null 2>&1 || missing_deps+=("bpftool")
    command -v make >/dev/null 2>&1 || missing_deps+=("make")
    
    # 检查库
    pkg-config --exists libbpf 2>/dev/null || missing_deps+=("libbpf-dev")
    
    # 检查内核支持
    [[ -f /sys/kernel/btf/vmlinux ]] || missing_deps+=("kernel-btf-support")
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        print_error "缺少以下依赖:"
        printf '%s\n' "${missing_deps[@]}"
        print_info "运行以下命令安装依赖:"
        echo "sudo make install-deps"
        return 1
    fi
    
    print_success "所有依赖已满足"
    return 0
}

# 编译程序
build() {
    print_info "编译 NUMA Chain Tracker..."
    
    if ! make clean; then
        print_error "清理失败"
        return 1
    fi
    
    if ! make all; then
        print_error "编译失败"
        return 1
    fi
    
    print_success "编译完成"
    return 0
}

# 运行程序
run() {
    local background=false
    local pid_filter=""
    local verbose=false
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -b|--background)
                background=true
                shift
                ;;
            -p|--pid)
                pid_filter="$2"
                shift 2
                ;;
            -v|--verbose)
                verbose=true
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_usage
                return 1
                ;;
        esac
    done
    
    # 检查程序是否存在
    if [[ ! -f numa_chain ]]; then
        print_warning "程序未编译，正在编译..."
        if ! build; then
            return 1
        fi
    fi
    
    # 设置环境
    print_info "设置运行环境..."
    make setup >/dev/null 2>&1
    
    # 构建运行命令
    local cmd="./numa_chain"
    
    if [[ -n "$pid_filter" ]]; then
        cmd="$cmd --pid $pid_filter"
    fi
    
    if [[ "$verbose" == true ]]; then
        cmd="$cmd --verbose"
    fi
    
    # 运行程序
    if [[ "$background" == true ]]; then
        print_info "后台运行 NUMA Chain Tracker..."
        $cmd > numa_chain_output.log 2>&1 &
        local pid=$!
        echo $pid > numa_chain.pid
        print_success "已启动 (PID: $pid)"
        print_info "输出日志: numa_chain_output.log"
        print_info "停止命令: $0 stop"
    else
        print_info "前台运行 NUMA Chain Tracker (按 Ctrl+C 停止)..."
        exec $cmd
    fi
}

# 停止后台程序
stop() {
    if [[ -f numa_chain.pid ]]; then
        local pid=$(cat numa_chain.pid)
        if kill -0 "$pid" 2>/dev/null; then
            print_info "停止程序 (PID: $pid)..."
            kill -TERM "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                print_warning "正常停止失败，强制终止..."
                kill -KILL "$pid"
            fi
            print_success "程序已停止"
        else
            print_warning "程序未运行"
        fi
        rm -f numa_chain.pid
    else
        print_warning "未找到PID文件，尝试按进程名停止..."
        pkill -f numa_chain
    fi
}

# 查看状态
status() {
    if [[ -f numa_chain.pid ]]; then
        local pid=$(cat numa_chain.pid)
        if kill -0 "$pid" 2>/dev/null; then
            print_success "程序正在运行 (PID: $pid)"
            # 显示最近的输出
            if [[ -f numa_chain_output.log ]]; then
                print_info "最近输出:"
                tail -10 numa_chain_output.log
            fi
        else
            print_warning "PID文件存在但程序未运行"
            rm -f numa_chain.pid
        fi
    else
        print_info "程序未运行"
    fi
}

# 查看输出日志
logs() {
    if [[ -f numa_chain_output.log ]]; then
        if [[ "$1" == "-f" ]]; then
            print_info "实时跟踪日志 (按 Ctrl+C 退出)..."
            tail -f numa_chain_output.log
        else
            print_info "显示日志内容:"
            cat numa_chain_output.log
        fi
    else
        print_warning "未找到日志文件"
    fi
}

# 系统信息检查
system_info() {
    print_info "系统信息检查:"
    echo
    echo "内核版本: $(uname -r)"
    echo "架构: $(uname -m)"
    echo
    
    print_info "eBPF 支持检查:"
    [[ -d /sys/kernel/debug/tracing ]] && echo "✓ debugfs 已挂载" || echo "✗ debugfs 未挂载"
    [[ -f /sys/kernel/btf/vmlinux ]] && echo "✓ BTF 支持" || echo "✗ BTF 不支持"
    [[ -f /proc/sys/kernel/bpf_stats_enabled ]] && echo "✓ BPF 统计支持" || echo "✗ BPF 统计不支持"
    echo
    
    print_info "目标函数可用性:"
    make check-functions 2>/dev/null
    echo
    
    print_info "编译依赖:"
    check_dependencies >/dev/null 2>&1 && echo "✓ 所有依赖满足" || echo "✗ 缺少依赖"
}

# 使用说明
show_usage() {
    cat << EOF
NUMA Chain Tracker - 原生 eBPF 版本

用法: $0 <command> [options]

命令:
  build               编译程序
  run [options]       运行程序
  stop                停止后台程序
  status              查看运行状态
  logs [-f]           查看日志 (-f 实时跟踪)
  system-info         显示系统信息
  install-deps        安装系统依赖
  help                显示此帮助

运行选项:
  -b, --background    后台运行
  -p, --pid PID       按进程ID过滤
  -v, --verbose       详细输出

示例:
  $0 build                    # 编译程序
  $0 run                      # 前台运行
  $0 run -b                   # 后台运行
  $0 run -p 1234              # 只跟踪PID 1234
  $0 run -b -v                # 后台运行并启用详细输出
  $0 stop                     # 停止后台程序
  $0 logs -f                  # 实时查看日志

首次使用:
  $0 install-deps             # 安装依赖
  $0 system-info              # 检查系统
  $0 build                    # 编译
  $0 run                      # 运行

注意: 此程序需要root权限运行
EOF
}

# 主函数
main() {
    case "${1:-}" in
        build)
            build
            ;;
        run)
            check_root
            shift
            run "$@"
            ;;
        stop)
            check_root
            stop
            ;;
        status)
            status
            ;;
        logs)
            shift
            logs "$@"
            ;;
        system-info)
            system_info
            ;;
        install-deps)
            print_info "安装系统依赖..."
            make install-deps
            ;;
        help|--help|-h)
            show_usage
            ;;
        "")
            print_error "请指定命令"
            echo
            show_usage
            exit 1
            ;;
        *)
            print_error "未知命令: $1"
            echo
            show_usage
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"