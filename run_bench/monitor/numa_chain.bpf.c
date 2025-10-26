#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>
#include "numa_chain.h"

char LICENSE[] SEC("license") = "GPL";

// Event ring buffer
struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} rb SEC(".maps");

// Global statistics counters
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, 1);
    __type(key, __u32);
    __type(value, struct numa_chain_stats);
} stats_map SEC(".maps");

// Page call count table
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_ENTRIES);
    __type(key, __u64);  // Page address
    __type(value, struct page_call_count);
} page_counts SEC(".maps");

// Process ID filter (optional)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);
    __type(value, __u8);
} pid_filter SEC(".maps");

// Tracking state (for matching entry and exit)
struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u64);  // tid
    __type(value, __u64); // timestamp
} tracking_state SEC(".maps");

// Helper function: get statistics data
static struct numa_chain_stats* get_stats(void)
{
    __u32 key = 0;
    return bpf_map_lookup_elem(&stats_map, &key);
}

// Helper function: update page count
static void update_page_count(__u64 page_addr, int type)
{
    struct page_call_count *count, init_count = {};
    
    count = bpf_map_lookup_elem(&page_counts, &page_addr);
    if (!count) {
        count = &init_count;
    }
    
    switch (type) {
        case EVENT_HUGE_PMD_ENTRY:
            count->huge_pmd_count++;
            break;
        case EVENT_NUMA_PAGE_ENTRY:
            count->numa_page_count++;
            break;
        case EVENT_MIGRATION_ENTRY:
            count->migration_count++;
            break;
    }
    
    bpf_map_update_elem(&page_counts, &page_addr, count, BPF_ANY);
}

// Helper function: send event
static void send_event(__u32 event_type, __u64 page_addr, __u64 vmf_addr, 
                       __u64 folio_addr, __u64 address, __u32 ret_val)
{
    struct numa_event *e;
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;
    
    // Optional PID filtering
    if (bpf_map_lookup_elem(&pid_filter, &pid)) {
        // Skip if PID is in filter table
        return;
    }
    
    e = bpf_ringbuf_reserve(&rb, sizeof(*e), 0);
    if (!e) {
        return;
    }
    
    e->ts = bpf_ktime_get_ns();
    e->pid = pid;
    e->tid = (__u32)pid_tgid;
    e->event_type = event_type;
    e->page_addr = page_addr;
    e->vmf_addr = vmf_addr;
    e->folio_addr = folio_addr;
    e->address = address;
    e->ret_val = ret_val;
    bpf_get_current_comm(&e->comm, sizeof(e->comm));
    
    bpf_ringbuf_submit(e, 0);
}

// fentry: do_huge_pmd_numa_page
SEC("fentry/do_huge_pmd_numa_page")
int BPF_PROG(on_huge_pmd_numa_entry, struct vm_fault *vmf)
{
    struct numa_chain_stats *stats;
    __u64 page_addr = 0;
    __u64 address = 0;
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;
    
    if (vmf) {
        // Use CO-RE safe reading
        bpf_core_read(&address, sizeof(address), &vmf->address);
        bpf_core_read(&page_addr, sizeof(page_addr), &vmf->page);
    }
    
    // Update statistics - only count total calls at entry
    stats = get_stats();
    if (stats) {
        __sync_fetch_and_add(&stats->total_huge_pmd, 1);
    }
    
    // 更新页面计数 - 使用虚拟地址+PID作为标识符
    __u64 page_id = 0;
    if (page_addr) {
        page_id = page_addr;
    } else if (address) {
        // 使用虚拟地址+PID的组合作为唯一标识符
        page_id = address ^ ((__u64)pid << 32);
    }
    
    if (page_id) {
        update_page_count(page_id, EVENT_HUGE_PMD_ENTRY);
    }
    
    // Record timestamp for matching
    __u64 ts = bpf_ktime_get_ns();
    __u64 tid = (__u32)pid_tgid;
    bpf_map_update_elem(&tracking_state, &tid, &ts, BPF_ANY);
    
    // Send event
    send_event(EVENT_HUGE_PMD_ENTRY, page_addr, (__u64)vmf, 0, address, 0);
    
    return 0;
}

// fexit: do_huge_pmd_numa_page
SEC("fexit/do_huge_pmd_numa_page")
int BPF_PROG(on_huge_pmd_numa_exit, struct vm_fault *vmf, int ret)
{
    struct numa_chain_stats *stats;
    __u64 page_addr = 0;
    __u64 address = 0;
    
    if (vmf) {
        bpf_core_read(&address, sizeof(address), &vmf->address);
        bpf_core_read(&page_addr, sizeof(page_addr), &vmf->page);
    }
    
    // Update statistics
    stats = get_stats();
    if (stats) {
        // VM_FAULT_FALLBACK = 0x800
        if (ret & 0x800) {
            __sync_fetch_and_add(&stats->huge_pmd_fallback, 1);
        } else {
            __sync_fetch_and_add(&stats->huge_pmd_handled, 1);
        }
    }
    
    // Send event
    send_event(EVENT_HUGE_PMD_EXIT, page_addr, (__u64)vmf, 0, address, ret);
    
    return 0;
}

// fentry: do_numa_page
SEC("fentry/do_numa_page")
int BPF_PROG(on_numa_page_entry, struct vm_fault *vmf)
{
    struct numa_chain_stats *stats;
    __u64 page_addr = 0;
    __u64 address = 0;
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    __u32 pid = pid_tgid >> 32;
    
    if (vmf) {
        bpf_core_read(&address, sizeof(address), &vmf->address);
        bpf_core_read(&page_addr, sizeof(page_addr), &vmf->page);
    }
    
    // Update statistics
    stats = get_stats();
    if (stats) {
        __sync_fetch_and_add(&stats->total_numa_page, 1);
    }
    
    // Update page count - use virtual address + PID as identifier
    __u64 page_id = 0;
    if (page_addr) {
        page_id = page_addr;
    } else if (address) {
        // Use combination of virtual address + PID as unique identifier
        page_id = address ^ ((__u64)pid << 32);
    }
    
    if (page_id) {
        update_page_count(page_id, EVENT_NUMA_PAGE_ENTRY);
    }
    
    // Send event
    send_event(EVENT_NUMA_PAGE_ENTRY, page_addr, (__u64)vmf, 0, address, 0);
    
    return 0;
}

// fexit: do_numa_page
SEC("fexit/do_numa_page")
int BPF_PROG(on_numa_page_exit, struct vm_fault *vmf, int ret)
{
    __u64 page_addr = 0;
    __u64 address = 0;
    
    if (vmf) {
        bpf_core_read(&address, sizeof(address), &vmf->address);
        bpf_core_read(&page_addr, sizeof(page_addr), &vmf->page);
    }
    
    // Send event
    send_event(EVENT_NUMA_PAGE_EXIT, page_addr, (__u64)vmf, 0, address, ret);
    
    return 0;
}

// fentry: migrate_misplaced_folio
SEC("fentry/migrate_misplaced_folio")
int BPF_PROG(on_migration_entry, struct folio *folio, struct vm_area_struct *vma, int node)
{
    struct numa_chain_stats *stats;
    __u64 folio_addr = (__u64)folio;
    
    // Update statistics
    stats = get_stats();
    if (stats) {
        __sync_fetch_and_add(&stats->total_migration, 1);
    }
    
    // Update page count (use folio address as identifier)
    if (folio_addr) {
        update_page_count(folio_addr, EVENT_MIGRATION_ENTRY);
    }
    
    // Send event
    send_event(EVENT_MIGRATION_ENTRY, 0, 0, folio_addr, 0, node);
    
    return 0;
}

// fexit: migrate_misplaced_folio
SEC("fexit/migrate_misplaced_folio")
int BPF_PROG(on_migration_exit, struct folio *folio, struct vm_area_struct *vma, int node, int ret)
{
    struct numa_chain_stats *stats;
    __u64 folio_addr = (__u64)folio;
    
    // Update statistics
    if (ret == 0) {
        stats = get_stats();
        if (stats) {
            __sync_fetch_and_add(&stats->total_migration_success, 1);
        }
    }
    
    // Send event
    send_event(EVENT_MIGRATION_EXIT, 0, 0, folio_addr, 0, ret);
    
    return 0;
}
