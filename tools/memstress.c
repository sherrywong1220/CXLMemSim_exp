#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include <sched.h>
#include <errno.h>
#include <signal.h>
#include <sys/mman.h>
#include <numa.h>
#include <numaif.h>

typedef struct {
    int *cpu_list;          // 绑定的CPU列表
    int cpu_count;          // CPU数量
    int numa_node;          // NUMA节点
    size_t buffer_size_mb;  // 缓冲区大小(MB)
    double target_bw_mbps;  // 目标带宽(MB/s)
    int warmup_time;        // 预热时间(秒)
} config_t;

static volatile int stop_flag = 0;
static void *memory_buffer = NULL;
static size_t buffer_size = 0;

void print_usage(const char *prog_name) {
    printf("使用方法: %s [选项]\n", prog_name);
    printf("选项:\n");
    printf("  -c <cpu_list>     绑定的CPU列表 (例如: 0,1,2 或 0-3)\n");
    printf("  -n <numa_node>    绑定的NUMA节点 (0, 1, 2, ...)\n");
    printf("  -s <size_mb>      缓冲区大小 (MB)\n");
    printf("  -b <bandwidth>    目标内存带宽 (MB/s)\n");
    printf("  -w <warmup>       预热时间 (秒) [默认: 5]\n");
    printf("  -h                显示帮助信息\n");
    printf("\n");
    printf("注意: 程序将持续运行直到手动停止 (Ctrl+C)\n");
    printf("\n");
    printf("示例:\n");
    printf("  %s -c 0,1 -n 0 -s 1024 -b 500\n", prog_name);
    printf("  在CPU 0,1上运行，使用NUMA节点0的1GB内存，目标带宽500MB/s\n");
}

int parse_cpu_list(const char *cpu_str, int **cpu_list, int *cpu_count) {
    int max_cpus = 256;
    *cpu_list = malloc(max_cpus * sizeof(int));
    *cpu_count = 0;
    
    char *str = strdup(cpu_str);
    char *token = strtok(str, ",");
    
    while (token != NULL && *cpu_count < max_cpus) {
        char *dash = strchr(token, '-');
        if (dash) {
            // 处理范围格式 (例如: 0-3)
            *dash = '\0';
            int start = atoi(token);
            int end = atoi(dash + 1);
            for (int i = start; i <= end && *cpu_count < max_cpus; i++) {
                (*cpu_list)[(*cpu_count)++] = i;
            }
        } else {
            // 处理单个CPU
            (*cpu_list)[(*cpu_count)++] = atoi(token);
        }
        token = strtok(NULL, ",");
    }
    
    free(str);
    return *cpu_count > 0 ? 0 : -1;
}

int bind_to_cpus(const int *cpu_list, int cpu_count) {
    cpu_set_t cpu_set;
    CPU_ZERO(&cpu_set);
    
    for (int i = 0; i < cpu_count; i++) {
        CPU_SET(cpu_list[i], &cpu_set);
    }
    
    if (sched_setaffinity(0, sizeof(cpu_set), &cpu_set) != 0) {
        perror("绑定CPU失败");
        return -1;
    }
    
    printf("成功绑定到CPU: ");
    for (int i = 0; i < cpu_count; i++) {
        printf("%d%s", cpu_list[i], (i == cpu_count - 1) ? "\n" : ",");
    }
    
    return 0;
}

int allocate_numa_memory(int numa_node, size_t size) {
    if (numa_available() == -1) {
        fprintf(stderr, "NUMA不可用\n");
        return -1;
    }
    
    if (numa_node >= numa_max_node() + 1) {
        fprintf(stderr, "无效的NUMA节点: %d (最大: %d)\n", numa_node, numa_max_node());
        return -1;
    }
    
    // 使用numa_alloc_onnode直接在指定节点分配内存
    // 这类似于内核的GFP_THISNODE标志，强制在指定节点分配
    memory_buffer = numa_alloc_onnode(size, numa_node);
    if (!memory_buffer) {
        fprintf(stderr, "在NUMA节点 %d 上分配内存失败\n", numa_node);
        return -1;
    }
    
    // 使用mlock锁定内存页面，防止被swap出去或迁移
    if (mlock(memory_buffer, size) != 0) {
        fprintf(stderr, "警告: 无法锁定内存页面: %s\n", strerror(errno));
        fprintf(stderr, "      内存可能会被系统迁移或swap，建议使用sudo运行\n");
        // 不返回错误，继续执行
    } else {
        printf("成功锁定内存页面，防止迁移和swap\n");
    }
    
    // 设置NUMA内存策略为MPOL_BIND，进一步防止页面迁移
    struct bitmask *nodemask = numa_allocate_nodemask();
    numa_bitmask_setbit(nodemask, numa_node);
    
    // 对已分配的内存区域设置严格的NUMA策略，防止numa_balancing迁移
    // 使用MPOL_MF_STRICT确保严格绑定，MPOL_MF_MOVE允许必要时移动页面到目标节点
    if (mbind(memory_buffer, size, MPOL_BIND, nodemask->maskp, 
              nodemask->size + 1, MPOL_MF_STRICT | MPOL_MF_MOVE) != 0) {
        fprintf(stderr, "警告: 设置内存绑定策略失败: %s\n", strerror(errno));
        fprintf(stderr, "      内存可能不会严格绑定到节点 %d\n", numa_node);
    } else {
        printf("成功设置严格的NUMA绑定策略\n");
    }
    
    // 额外设置：优化这块内存的行为，防止不必要的迁移
    // 禁用大页面以获得更稳定的页面管理
    if (madvise(memory_buffer, size, MADV_NOHUGEPAGE) == 0) {
        printf("禁用大页面，使用常规页面以提高稳定性\n");
    }
    
    // 设置内存访问模式为随机，告知内核不要进行预取优化
    if (madvise(memory_buffer, size, MADV_RANDOM) == 0) {
        printf("设置随机访问模式，优化内存访问行为\n");
    }
    
    // 使用MADV_DONTFORK防止fork时的copy-on-write
    if (madvise(memory_buffer, size, MADV_DONTFORK) == 0) {
        printf("设置DONTFORK，防止进程fork时的页面复制\n");
    }
    
    numa_free_nodemask(nodemask);
    
    // 触摸所有页面以确保物理内存分配和页表建立
    printf("正在预分配所有页面...\n");
    volatile char *ptr = (volatile char *)memory_buffer;
    for (size_t i = 0; i < size; i += 4096) { // 按页面大小访问
        ptr[i] = 0;
    }
    // 确保最后一个字节也被访问
    if (size > 0) {
        ptr[size - 1] = 0;
    }
    
    // 验证内存是否真的分配在指定节点上
    int actual_node = -1;
    if (get_mempolicy(&actual_node, NULL, 0, memory_buffer, MPOL_F_NODE | MPOL_F_ADDR) == 0) {
        if (actual_node == numa_node) {
            printf("验证成功: 内存确实分配在NUMA节点 %d 上\n", actual_node);
        } else {
            fprintf(stderr, "警告: 内存实际分配在节点 %d，而非指定的节点 %d\n", 
                    actual_node, numa_node);
        }
    }
    
    printf("成功在NUMA节点 %d 上分配并锁定 %zu MB 内存\n", numa_node, size / (1024 * 1024));
    buffer_size = size;
    
    return 0;
}

// 设置进程级别的优化，不影响全局设置
void optimize_process_for_numa() {
    // 设置进程调度策略为SCHED_FIFO以获得更稳定的行为（需要权限）
    struct sched_param param;
    param.sched_priority = 1;
    if (sched_setscheduler(0, SCHED_FIFO, &param) == 0) {
        printf("设置实时调度策略成功，提高进程稳定性\n");
    } else if (errno == EPERM) {
        // 不输出任何建议，只是静默处理
    }
}


void signal_handler(int sig) {
    (void)sig; // 避免未使用参数警告
    stop_flag = 1;
}

void cleanup() {
    if (memory_buffer && buffer_size > 0) {
        // 解锁内存页面
        if (munlock(memory_buffer, buffer_size) != 0) {
            fprintf(stderr, "警告: 解锁内存页面失败: %s\n", strerror(errno));
        }
        
        // 使用numa_free释放通过numa_alloc_onnode分配的内存
        numa_free(memory_buffer, buffer_size);
        memory_buffer = NULL;
        buffer_size = 0;
        
        printf("已释放并解锁内存\n");
    }
}

// 生成随机访问模式
void generate_random_access_pattern(size_t *indices, size_t count) {
    // 初始化顺序索引
    for (size_t i = 0; i < count; i++) {
        indices[i] = i;
    }
    
    // Fisher-Yates洗牌算法
    for (size_t i = count - 1; i > 0; i--) {
        size_t j = rand() % (i + 1);
        size_t temp = indices[i];
        indices[i] = indices[j];
        indices[j] = temp;
    }
}

// 计算需要的延迟来达到目标带宽
long calculate_delay_ns(double target_bw_mbps, size_t access_size) {
    // 计算每次访问应该花费的时间（纳秒）
    double bytes_per_second = target_bw_mbps * 1024 * 1024;
    double seconds_per_access = (double)access_size / bytes_per_second;
    return (long)(seconds_per_access * 1000000000.0); // 转换为纳秒
}

// 平滑启动带宽控制
double get_current_bandwidth_limit(double target_bw, int warmup_time, time_t start_time) {
    time_t current_time = time(NULL);
    int elapsed = current_time - start_time;
    
    if (elapsed >= warmup_time) {
        return target_bw; // 预热完成，使用目标带宽
    }
    
    // 线性增长到目标带宽
    double progress = (double)elapsed / warmup_time;
    return target_bw * progress;
}

void memory_stress_loop(const config_t *config) {
    const size_t cache_line_size = 64; // 典型的缓存行大小
    const size_t access_count = buffer_size / cache_line_size;
    
    // 生成随机访问模式
    size_t *access_indices = malloc(access_count * sizeof(size_t));
    if (!access_indices) {
        fprintf(stderr, "分配访问索引数组失败\n");
        return;
    }
    
    volatile char *buffer = (volatile char *)memory_buffer;
    time_t start_time = time(NULL);
    time_t last_report = start_time;
    
    size_t total_accesses = 0;
    size_t bytes_accessed = 0;
    
    printf("开始内存压力测试...\n");
    printf("缓冲区大小: %zu MB, 访问点数: %zu\n", 
           buffer_size / (1024 * 1024), access_count);
    
    while (!stop_flag) {
        // 重新生成随机访问模式
        generate_random_access_pattern(access_indices, access_count);
        
        // 每次生成新的访问模式时更新带宽限制
        time_t current_time = time(NULL);
        double current_bw_limit = get_current_bandwidth_limit(
            config->target_bw_mbps, config->warmup_time, start_time);
        
        long delay_ns = calculate_delay_ns(current_bw_limit, cache_line_size);
        
        struct timespec access_start, access_end, delay_time;
        
        // 批量处理：每批处理一定数量的访问，然后统一控制延迟
        // 根据目标带宽动态调整批量大小：高带宽使用更大批次
        size_t batch_size = (size_t)(current_bw_limit / 10.0); // 带宽(MB/s) / 10
        if (batch_size < 100) batch_size = 100;      // 最小100次
        if (batch_size > 100000) batch_size = 100000;  // 最大100000次
        clock_gettime(CLOCK_MONOTONIC, &access_start);
        
        for (size_t i = 0; i < access_count && !stop_flag; i++) {
            // 随机访问内存
            size_t index = access_indices[i] * cache_line_size;
            if (index < buffer_size) {
                volatile char dummy = buffer[index];
                buffer[index] = dummy + 1; // 写操作确保内存访问
            }
            
            total_accesses++;
            bytes_accessed += cache_line_size;
            
            // 每批处理完后控制延迟
            if ((i + 1) % batch_size == 0 || i == access_count - 1) {
                clock_gettime(CLOCK_MONOTONIC, &access_end);
                
                // 计算这批访问花费的时间
                long elapsed_ns = (access_end.tv_sec - access_start.tv_sec) * 1000000000L +
                                 (access_end.tv_nsec - access_start.tv_nsec);
                
                // 计算这批访问应该花费的时间
                size_t accesses_in_batch = (i + 1) % batch_size;
                if (accesses_in_batch == 0) accesses_in_batch = batch_size;
                long expected_ns = delay_ns * accesses_in_batch;
                
                // 如果需要延迟来控制带宽
                if (expected_ns > elapsed_ns) {
                    long sleep_ns = expected_ns - elapsed_ns;
                    // 只有当延迟超过1毫秒时才sleep，避免过度频繁的系统调用
                    if (sleep_ns > 1000000) { // 1毫秒 = 1,000,000纳秒
                        delay_time.tv_sec = 0;
                        delay_time.tv_nsec = sleep_ns;
                        nanosleep(&delay_time, NULL);
                    }
                }
                
                // 为下一批重新计时
                clock_gettime(CLOCK_MONOTONIC, &access_start);
            }
        }
        
        // 每秒报告一次状态
        current_time = time(NULL);
        if (current_time - last_report >= 1) {
            double elapsed_seconds = current_time - start_time;
            double actual_bw = (bytes_accessed / (1024.0 * 1024.0)) / elapsed_seconds;
            double report_bw_limit = get_current_bandwidth_limit(
                config->target_bw_mbps, config->warmup_time, start_time);
            
            printf("运行时间: %.0fs, 目标带宽: %.1f MB/s, 实际带宽: %.1f MB/s, "
                   "总访问次数: %zu\n",
                   elapsed_seconds, report_bw_limit, actual_bw, total_accesses);
            
            last_report = current_time;
        }
        
        // 程序将持续运行直到收到停止信号
    }
    
    free(access_indices);
    
    time_t end_time = time(NULL);
    double total_time = end_time - start_time;
    double avg_bandwidth = (bytes_accessed / (1024.0 * 1024.0)) / total_time;
    
    printf("\n测试完成!\n");
    printf("总运行时间: %.1f 秒\n", total_time);
    printf("总访问次数: %zu\n", total_accesses);
    printf("总访问字节数: %zu MB\n", bytes_accessed / (1024 * 1024));
    printf("平均带宽: %.2f MB/s\n", avg_bandwidth);
}

int main(int argc, char *argv[]) {
    config_t config = {0};
    config.warmup_time = 5; // 默认5秒预热
    
    int opt;
    while ((opt = getopt(argc, argv, "c:n:s:b:w:h")) != -1) {
        switch (opt) {
            case 'c':
                if (parse_cpu_list(optarg, &config.cpu_list, &config.cpu_count) != 0) {
                    fprintf(stderr, "无效的CPU列表: %s\n", optarg);
                    return 1;
                }
                break;
            case 'n':
                config.numa_node = atoi(optarg);
                break;
            case 's':
                config.buffer_size_mb = atoi(optarg);
                break;
            case 'b':
                config.target_bw_mbps = atof(optarg);
                break;
            case 'w':
                config.warmup_time = atoi(optarg);
                break;
            case 'h':
                print_usage(argv[0]);
                return 0;
            default:
                print_usage(argv[0]);
                return 1;
        }
    }
    
    // 检查必需参数
    if (!config.cpu_list || config.buffer_size_mb == 0 || config.target_bw_mbps == 0) {
        fprintf(stderr, "错误: 必须指定 -c (CPU列表), -s (缓冲区大小), -b (目标带宽)\n");
        print_usage(argv[0]);
        return 1;
    }
    
    printf("memstress 配置:\n");
    printf("  绑定CPU: ");
    for (int i = 0; i < config.cpu_count; i++) {
        printf("%d%s", config.cpu_list[i], (i == config.cpu_count - 1) ? "\n" : ",");
    }
    printf("  NUMA节点: %d\n", config.numa_node);
    printf("  缓冲区大小: %zu MB\n", config.buffer_size_mb);
    printf("  目标带宽: %.1f MB/s\n", config.target_bw_mbps);
    printf("  运行模式: 持续运行 (Ctrl+C停止)\n");
    printf("  预热时间: %d 秒\n", config.warmup_time);
    
    // 优化进程设置以提高稳定性
    optimize_process_for_numa();
    
    // 设置信号处理
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    atexit(cleanup);
    
    // 绑定CPU
    if (bind_to_cpus(config.cpu_list, config.cpu_count) != 0) {
        return 1;
    }
    
    // 分配NUMA内存
    size_t buffer_bytes = config.buffer_size_mb * 1024 * 1024;
    if (allocate_numa_memory(config.numa_node, buffer_bytes) != 0) {
        return 1;
    }
    
    // 初始化随机数生成器
    srand(time(NULL));
    
    // 开始内存压力测试
    memory_stress_loop(&config);
    
    free(config.cpu_list);
    return 0;
}
