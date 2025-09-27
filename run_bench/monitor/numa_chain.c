#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <string.h>
#include <errno.h>
#include <time.h>
#include <getopt.h>
#include <sys/resource.h>
#include <bpf/libbpf.h>
#include <bpf/bpf.h>
#include "numa_chain.h"
#include "numa_chain.skel.h"

static volatile bool exiting = false;

// 信号处理
static void sig_handler(int sig)
{
    exiting = true;
}

// 全局统计变量（用于聚合显示）
static struct numa_chain_stats global_stats = {};
static struct {
    unsigned long long huge_pmd_calls[256];
    unsigned long long numa_page_calls[256];
    unsigned long long migration_calls[256];
    int huge_pmd_hist_size;
    int numa_page_hist_size;
    int migration_hist_size;
} histograms = {};

// 事件处理回调
static int handle_event(void *ctx, void *data, size_t data_sz)
{
    const struct numa_event *e = data;
    
    // 可选：打印详细事件（调试用）
    if (getenv("NUMA_CHAIN_VERBOSE")) {
        printf("[%llu] %s[%d:%d] type=%d page=0x%llx addr=0x%llx ret=%d\n",
               e->ts, e->comm, e->pid, e->tid, e->event_type, 
               e->page_addr, e->address, e->ret_val);
    }
    
    return 0;
}

// 打印histogram
static void print_histogram(const char *title, unsigned long long *hist, int size)
{
    printf("\n%s:\n", title);
    
    if (size == 0) {
        printf("  No data\n");
        return;
    }
    
    // 找到最大值用于缩放
    unsigned long long max_val = 0;
    for (int i = 0; i < size; i++) {
        if (hist[i] > max_val) {
            max_val = hist[i];
        }
    }
    
    if (max_val == 0) {
        printf("  No data\n");
        return;
    }
    
    // 打印histogram
    for (int i = 0; i < size; i++) {
        if (hist[i] > 0) {
            int bar_len = (hist[i] * 50) / max_val;
            printf("  [%2d, %2d) %8llu |", 1 << i, 1 << (i + 1), hist[i]);
            for (int j = 0; j < bar_len; j++) {
                printf("*");
            }
            printf("\n");
        }
    }
}

// 更新histogram
static void update_histogram(unsigned long long *hist, int *hist_size, unsigned long long value)
{
    if (value == 0) return;
    
    // 找到合适的bucket (2的幂次)
    int bucket = 0;
    unsigned long long temp = value;
    while (temp > 1) {
        temp >>= 1;
        bucket++;
    }
    
    if (bucket >= 256) bucket = 255;
    
    hist[bucket]++;
    if (bucket >= *hist_size) {
        *hist_size = bucket + 1;
    }
}

// 读取并显示统计信息
static void print_stats(struct numa_chain_bpf *skel)
{
    __u32 key = 0;
    struct numa_chain_stats stats = {};
    
    // 读取全局统计
    if (bpf_map_lookup_elem(bpf_map__fd(skel->maps.stats_map), &key, &stats) == 0) {
        global_stats = stats;
    }
    
    printf("\n======== NUMA THP CHAIN DISTRIBUTION ANALYSIS ========\n");
    
    // 基础统计
    printf("\n=== TOTAL CALL STATISTICS ===\n");
    printf("do_huge_pmd_numa_page:\n");
    printf("  Total calls: %llu\n", global_stats.total_huge_pmd);
    printf("  Handled directly: %llu\n", global_stats.huge_pmd_handled);
    printf("  Fallback to do_numa_page: %llu\n", global_stats.huge_pmd_fallback);
    if (global_stats.total_huge_pmd > 0) {
        printf("  Fallback rate: %.1f%%\n", 
               (global_stats.huge_pmd_fallback * 100.0) / global_stats.total_huge_pmd);
    }
    
    printf("\ndo_numa_page:\n");
    printf("  Total calls: %llu\n", global_stats.total_numa_page);
    
    printf("\nmigrate_misplaced_folio:\n");
    printf("  Total calls: %llu\n", global_stats.total_migration);
    printf("  Successful calls: %llu\n", global_stats.total_migration_success);
    if (global_stats.total_migration > 0) {
        printf("  Success rate: %.1f%%\n", 
               (global_stats.total_migration_success * 100.0) / global_stats.total_migration);
    }
    
    // 读取页面计数并构建histogram
    __u64 page_addr;
    struct page_call_count count;
    int fd = bpf_map__fd(skel->maps.page_counts);
    int unique_pages = 0, unique_huge_pmd = 0, unique_numa_page = 0, unique_migration = 0;
    
    memset(&histograms, 0, sizeof(histograms));
    
    page_addr = 0;
    while (bpf_map_get_next_key(fd, &page_addr, &page_addr) == 0) {
        if (bpf_map_lookup_elem(fd, &page_addr, &count) == 0) {
            unique_pages++;
            
            if (count.huge_pmd_count > 0) {
                unique_huge_pmd++;
                update_histogram(histograms.huge_pmd_calls, 
                               &histograms.huge_pmd_hist_size, count.huge_pmd_count);
            }
            
            if (count.numa_page_count > 0) {
                unique_numa_page++;
                update_histogram(histograms.numa_page_calls, 
                               &histograms.numa_page_hist_size, count.numa_page_count);
            }
            
            if (count.migration_count > 0) {
                unique_migration++;
                update_histogram(histograms.migration_calls, 
                               &histograms.migration_hist_size, count.migration_count);
            }
        }
    }
    
    // 更新统计
    printf("\nUnique pages statistics:\n");
    printf("  Pages in huge_pmd stage: %d\n", unique_huge_pmd);
    printf("  Pages in numa_page stage: %d\n", unique_numa_page);
    printf("  Pages in migration stage: %d\n", unique_migration);
    
    if (unique_huge_pmd > 0) {
        printf("  Avg huge_pmd calls per page: %.1f\n", 
               (global_stats.total_huge_pmd * 1.0) / unique_huge_pmd);
    }
    if (unique_numa_page > 0) {
        printf("  Avg numa_page calls per page: %.1f\n", 
               (global_stats.total_numa_page * 1.0) / unique_numa_page);
    }
    if (unique_migration > 0) {
        printf("  Avg migration calls per page: %.1f\n", 
               (global_stats.total_migration * 1.0) / unique_migration);
    }
    
    // 打印histograms
    printf("\n=== CALL DISTRIBUTION HISTOGRAMS ===\n");
    print_histogram("do_huge_pmd_numa_page calls per page", 
                   histograms.huge_pmd_calls, histograms.huge_pmd_hist_size);
    print_histogram("do_numa_page calls per page", 
                   histograms.numa_page_calls, histograms.numa_page_hist_size);
    print_histogram("migrate_misplaced_folio calls per page", 
                   histograms.migration_calls, histograms.migration_hist_size);
    
    // 链式分析
    printf("\n=== KEY INSIGHTS ===\n");
    
    if (global_stats.total_migration > 0 && global_stats.total_numa_page > 0) {
        double numa_migration_ratio = (global_stats.total_numa_page * 1.0) / global_stats.total_migration;
        printf("numa_page:migration ratio = %.1f:1\n", numa_migration_ratio);
    }
    
    if (global_stats.total_huge_pmd > 0 && global_stats.total_numa_page > 0) {
        double huge_numa_ratio = (global_stats.total_huge_pmd * 1.0) / global_stats.total_numa_page;
        printf("huge_pmd:numa_page ratio = %.1f:1\n", huge_numa_ratio);
    }
    
    if (unique_migration > 0 && unique_huge_pmd > 0) {
        double completion_rate = (unique_migration * 100.0) / unique_huge_pmd;
        printf("Chain completion estimate: %.1f%% (migration pages / huge_pmd pages)\n", completion_rate);
    }
    
    // 重试模式检测
    if (unique_migration > 0) {
        double avg_migration_retries = (global_stats.total_migration * 1.0) / unique_migration;
        if (avg_migration_retries > 3) {
            printf("✓ High migration retry pattern detected (avg %.1f retries per page)\n", avg_migration_retries);
        }
    }
    
    if (unique_numa_page > 0) {
        double avg_numa_retries = (global_stats.total_numa_page * 1.0) / unique_numa_page;
        if (avg_numa_retries > 2) {
            printf("✓ High numa_page retry pattern detected (avg %.1f retries per page)\n", avg_numa_retries);
        }
    }
    
    printf("=====================================================\n");
}

// 周期性统计报告
static void periodic_report(struct numa_chain_bpf *skel)
{
    static time_t last_report = 0;
    time_t now = time(NULL);
    
    if (now - last_report >= 20) {  // 每20秒报告一次
        __u32 key = 0;
        struct numa_chain_stats stats = {};
        
        if (bpf_map_lookup_elem(bpf_map__fd(skel->maps.stats_map), &key, &stats) == 0) {
            struct tm *tm = localtime(&now);
            printf("[%02d:%02d:%02d] Calls: huge_pmd=%llu (fallback=%llu), numa_page=%llu, migration=%llu (success=%llu)\n",
                   tm->tm_hour, tm->tm_min, tm->tm_sec,
                   stats.total_huge_pmd, stats.huge_pmd_fallback, stats.total_numa_page, 
                   stats.total_migration, stats.total_migration_success);
        }
        
        last_report = now;
    }
}

// 使用说明
static void usage(const char *prog)
{
    printf("Usage: %s [OPTIONS]\n", prog);
    printf("Options:\n");
    printf("  -p, --pid PID        Filter by process ID (can be used multiple times)\n");
    printf("  -v, --verbose        Enable verbose event logging\n");
    printf("  -h, --help           Show this help\n");
    printf("\nEnvironment variables:\n");
    printf("  NUMA_CHAIN_VERBOSE   Enable verbose event logging\n");
}

int main(int argc, char **argv)
{
    struct numa_chain_bpf *skel;
    struct ring_buffer *rb = NULL;
    int err;
    int pid_filter_fd;
    
    static struct option long_options[] = {
        {"pid", required_argument, 0, 'p'},
        {"verbose", no_argument, 0, 'v'},
        {"help", no_argument, 0, 'h'},
        {0, 0, 0, 0}
    };
    
    // 命令行参数解析
    int opt, option_index = 0;
    while ((opt = getopt_long(argc, argv, "p:vh", long_options, &option_index)) != -1) {
        switch (opt) {
            case 'p': {
                // 稍后处理PID过滤
                break;
            }
            case 'v':
                setenv("NUMA_CHAIN_VERBOSE", "1", 1);
                break;
            case 'h':
                usage(argv[0]);
                return 0;
            default:
                usage(argv[0]);
                return 1;
        }
    }
    
    // 设置信号处理
    signal(SIGINT, sig_handler);
    signal(SIGTERM, sig_handler);
    
    // 提升内存限制
    struct rlimit rlim_new = {
        .rlim_cur = RLIM_INFINITY,
        .rlim_max = RLIM_INFINITY,
    };
    if (setrlimit(RLIMIT_MEMLOCK, &rlim_new)) {
        fprintf(stderr, "Failed to increase RLIMIT_MEMLOCK limit!\n");
        return 1;
    }
    
    // 打开并加载BPF程序
    skel = numa_chain_bpf__open();
    if (!skel) {
        fprintf(stderr, "Failed to open and parse BPF skeleton\n");
        return 1;
    }
    
    // 加载并验证BPF程序
    err = numa_chain_bpf__load(skel);
    if (err) {
        fprintf(stderr, "Failed to load and verify BPF skeleton: %d\n", err);
        goto cleanup;
    }
    
    // 附加BPF程序
    err = numa_chain_bpf__attach(skel);
    if (err) {
        fprintf(stderr, "Failed to attach BPF skeleton: %d\n", err);
        goto cleanup;
    }
    
    // 初始化统计map
    __u32 key = 0;
    struct numa_chain_stats init_stats = {};
    bpf_map_update_elem(bpf_map__fd(skel->maps.stats_map), &key, &init_stats, BPF_ANY);
    
    // 设置PID过滤（如果指定了）
    pid_filter_fd = bpf_map__fd(skel->maps.pid_filter);
    optind = 1;  // 重置getopt
    while ((opt = getopt_long(argc, argv, "p:vh", long_options, &option_index)) != -1) {
        if (opt == 'p') {
            __u32 pid = atoi(optarg);
            __u8 value = 1;
            bpf_map_update_elem(pid_filter_fd, &pid, &value, BPF_ANY);
            printf("Added PID filter: %u\n", pid);
        }
    }
    
    // 设置ringbuf
    rb = ring_buffer__new(bpf_map__fd(skel->maps.rb), handle_event, NULL, NULL);
    if (!rb) {
        err = -1;
        fprintf(stderr, "Failed to create ring buffer\n");
        goto cleanup;
    }
    
    printf("NUMA THP Chain Tracker (native eBPF)\n");
    printf("Functions: huge_pmd | numa_page | migration\n");
    printf("Press Ctrl+C for distribution analysis.\n\n");
    
    // 主循环
    while (!exiting) {
        err = ring_buffer__poll(rb, 100 /* timeout, ms */);
        if (err == -EINTR) {
            err = 0;
            break;
        }
        if (err < 0) {
            printf("Error polling ring buffer: %d\n", err);
            break;
        }
        
        // 周期性报告
        periodic_report(skel);
    }
    
    // 最终统计
    print_stats(skel);

cleanup:
    ring_buffer__free(rb);
    numa_chain_bpf__destroy(skel);
    return err < 0 ? -err : 0;
}
