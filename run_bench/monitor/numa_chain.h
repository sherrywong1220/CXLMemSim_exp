#ifndef __NUMA_CHAIN_H__
#define __NUMA_CHAIN_H__

// 事件类型
enum event_type {
    EVENT_HUGE_PMD_ENTRY = 1,
    EVENT_HUGE_PMD_EXIT,
    EVENT_NUMA_PAGE_ENTRY,
    EVENT_NUMA_PAGE_EXIT,
    EVENT_MIGRATION_ENTRY,
    EVENT_MIGRATION_EXIT,
};

// 事件数据结构
struct numa_event {
    __u64 ts;                   // 时间戳
    __u32 pid;                  // 进程ID
    __u32 tid;                  // 线程ID
    __u32 event_type;           // 事件类型
    __u64 page_addr;            // 页面地址
    __u64 vmf_addr;             // vm_fault 地址
    __u64 folio_addr;           // folio 地址
    __u64 address;              // 虚拟地址
    __u32 ret_val;              // 返回值
    char comm[16];              // 进程名
};

// 统计数据结构 (重命名避免与内核冲突)
struct numa_chain_stats {
    __u64 total_huge_pmd;       // 总的 huge_pmd 调用次数
    __u64 huge_pmd_handled;     // 直接处理的次数
    __u64 huge_pmd_fallback;    // 回退到 numa_page 的次数
    __u64 total_numa_page;      // 总的 numa_page 调用次数
    __u64 total_migration;      // 总的迁移调用次数
    __u64 total_migration_success; // 成功的迁移次数
};

// 页面调用计数结构
struct page_call_count {
    __u64 huge_pmd_count;
    __u64 numa_page_count;
    __u64 migration_count;
};

#define MAX_ENTRIES 65536

#endif /* __NUMA_CHAIN_H__ */
