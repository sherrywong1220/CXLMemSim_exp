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

// Event data structure
struct numa_event {
    __u64 ts;                   // timestamp
    __u32 pid;                  // process ID
    __u32 tid;                  // thread ID
    __u32 event_type;           // event type
    __u64 page_addr;            // page address
    __u64 vmf_addr;             // vm_fault address
    __u64 folio_addr;           // folio address
    __u64 address;              // virtual address
    __u32 ret_val;              // return value
    char comm[16];              // process name
};

// Statistics data structure (renamed to avoid kernel conflicts)
struct numa_chain_stats {
    __u64 total_huge_pmd;       // total huge_pmd call count
    __u64 huge_pmd_handled;     // directly handled count
    __u64 huge_pmd_fallback;    // fallback to numa_page count
    __u64 total_numa_page;      // total numa_page call count
    __u64 total_migration;      // total migration call count
    __u64 total_migration_success; // successful migration count
};

// Page call count structure
struct page_call_count {
    __u64 huge_pmd_count;
    __u64 numa_page_count;
    __u64 migration_count;
};

#define MAX_ENTRIES 65536

#endif /* __NUMA_CHAIN_H__ */
