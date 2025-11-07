/*
 * memstress.c - Userspace Memory Antagonist
 *
 * Creates controlled memory interconnect contention by running antagonist
 * threads that perform sequential non-temporal read/write operations.
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <errno.h>
#include <signal.h>
#include <sys/mman.h>
#include <numa.h>
#include <numaif.h>
#include <stdint.h>
#include <time.h>
#include <stdatomic.h>

#define CACHELINE_SIZE 64

static int target_node = 1;
static size_t buffer_mb = 1024;
static int num_threads = 0;
static int cpu_start = 48;
static int read_ops = 1;   /* Number of read operations in pattern */
static int write_ops = 1;  /* Number of write operations in pattern */

static void *buffer_base = NULL;
static size_t buffer_size = 0;
static pthread_t *worker_threads = NULL;
static pthread_t stats_thread;
static atomic_ullong total_bytes = 0;
static volatile int stop_threads = 0;

static inline void nt_write_64B(void *dst, const void *src)
{
	__asm__ __volatile__(
		"movdqa   (%1), %%xmm0\n\t"
		"movdqa 16(%1), %%xmm1\n\t"
		"movdqa 32(%1), %%xmm2\n\t"
		"movdqa 48(%1), %%xmm3\n\t"
		"movntdq %%xmm0,   (%0)\n\t"
		"movntdq %%xmm1, 16(%0)\n\t"
		"movntdq %%xmm2, 32(%0)\n\t"
		"movntdq %%xmm3, 48(%0)\n\t"
		"sfence\n\t"
		:
		: "r" (dst), "r" (src)
		: "memory", "xmm0", "xmm1", "xmm2", "xmm3"
	);
}

static inline void nt_read_64B(const void *src, void *tmp)
{
	__asm__ __volatile__(
		"movntdqa   (%1), %%xmm0\n\t"
		"movntdqa 16(%1), %%xmm1\n\t"
		"movntdqa 32(%1), %%xmm2\n\t"
		"movntdqa 48(%1), %%xmm3\n\t"
		"movdqa %%xmm0,   (%0)\n\t"
		"movdqa %%xmm1, 16(%0)\n\t"
		"movdqa %%xmm2, 32(%0)\n\t"
		"movdqa %%xmm3, 48(%0)\n\t"
		:
		: "r" (tmp), "r" (src)
		: "memory", "xmm0", "xmm1", "xmm2", "xmm3"
	);
}

typedef struct {
	int thread_id;
	int cpu_id;
} thread_args_t;

static void *worker_thread_fn(void *arg)
{
	thread_args_t *args = (thread_args_t *)arg;
	int thread_id = args->thread_id;
	int cpu_id = args->cpu_id;
	char tmp_buf[64] __attribute__((aligned(64)));
	unsigned long long bytes_processed = 0;
	size_t offset;
	cpu_set_t cpuset;
	int pattern_total = read_ops + write_ops;
	int pattern_idx = 0;

	CPU_ZERO(&cpuset);
	CPU_SET(cpu_id, &cpuset);
	if (pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset) != 0) {
		fprintf(stderr, "Thread %d: Failed to set CPU affinity to CPU %d\n",
			thread_id, cpu_id);
		return NULL;
	}

	printf("Thread %d: Started on CPU %d with %d:%d read:write pattern\n",
	       thread_id, cpu_id, read_ops, write_ops);

	while (!stop_threads) {
		/* Sequential access pattern */
		for (offset = 0; offset < buffer_size; offset += CACHELINE_SIZE) {
			void *addr = buffer_base + offset;

			/* Simple fixed pattern: read_ops reads, then write_ops writes
			 * e.g., 1:10 means 1 read, 10 writes, 1 read, 10 writes, ... */
			if (pattern_idx < read_ops) {
				/* Perform read */
				nt_read_64B(addr, tmp_buf);
				bytes_processed += 64;
			} else {
				/* Perform write */
				nt_write_64B(addr, tmp_buf);
				bytes_processed += 64;
			}

			pattern_idx = (pattern_idx + 1) % pattern_total;
		}

		atomic_fetch_add(&total_bytes, bytes_processed);
		bytes_processed = 0;
	}

	printf("Thread %d: Stopped\n", thread_id);
	free(args);
	return NULL;
}

static void *stats_thread_fn(void *arg)
{
	unsigned long long last_bytes = 0;
	unsigned long long curr_bytes;
	unsigned long long delta_bytes;
	unsigned long long bandwidth_mbps;
	struct timespec sleep_time = {10, 0}; /* 10 seconds */

	(void)arg;

	while (!stop_threads) {
		nanosleep(&sleep_time, NULL);

		curr_bytes = atomic_load(&total_bytes);
		delta_bytes = curr_bytes - last_bytes;
		bandwidth_mbps = delta_bytes / (10 * 1024 * 1024); /* MB/s */

		printf("Bandwidth = %llu MB/s, Total = %llu GB\n",
		       bandwidth_mbps, curr_bytes / (1024ULL * 1024 * 1024));

		last_bytes = curr_bytes;
	}

	return NULL;
}

static int allocate_buffer(void)
{
	unsigned long nodemask;
	int ret;

	buffer_size = (size_t)buffer_mb * 1024 * 1024;

	printf("Allocating %zu MB buffer on NUMA node %d\n", buffer_mb, target_node);

	if (numa_available() < 0) {
		fprintf(stderr, "NUMA is not available\n");
		return -1;
	}

	if (target_node < 0 || target_node >= numa_max_node() + 1) {
		fprintf(stderr, "Invalid NUMA node %d (max: %d)\n",
			target_node, numa_max_node());
		return -1;
	}

	buffer_base = numa_alloc_onnode(buffer_size, target_node);
	if (!buffer_base) {
		fprintf(stderr, "Failed to allocate buffer on NUMA node %d: %s\n",
			target_node, strerror(errno));
		return -1;
	}

	memset(buffer_base, 0xAB, buffer_size);

	nodemask = 1UL << target_node;
	ret = mbind(buffer_base, buffer_size, MPOL_BIND, &nodemask,
		    sizeof(nodemask) * 8, MPOL_MF_STRICT | MPOL_MF_MOVE);
	if (ret < 0) {
		fprintf(stderr, "Failed to mbind buffer: %s\n", strerror(errno));
		numa_free(buffer_base, buffer_size);
		return -1;
	}

	ret = mlock(buffer_base, buffer_size);
	if (ret < 0) {
		fprintf(stderr, "Warning: Failed to mlock buffer: %s\n", strerror(errno));
		fprintf(stderr, "You may need to increase ulimit or run with CAP_IPC_LOCK\n");
		/* Continue anyway - mbind should be sufficient */
	}

	printf("Buffer allocated and pinned at %p\n", buffer_base);
	return 0;
}

static void free_buffer(void)
{
	if (buffer_base) {
		munlock(buffer_base, buffer_size);
		numa_free(buffer_base, buffer_size);
		buffer_base = NULL;
	}
}

static void signal_handler(int signum)
{
	(void)signum;
	printf("\nReceived signal, stopping threads...\n");
	stop_threads = 1;
}

static void print_usage(const char *prog)
{
	printf("Usage: %s [options]\n", prog);
	printf("Options:\n");
	printf("  -n <node>     Target NUMA node (default: 1)\n");
	printf("  -b <MB>       Buffer size in MB (default: 1024)\n");
	printf("  -t <threads>  Number of threads (0, 4, 8, 12, 16) (default: 0)\n");
	printf("  -c <core>     Starting CPU core (default: 48)\n");
	printf("  -r <R:W>      Read:Write ratio (default: 1:1)\n");
	printf("                Format: <reads>:<writes> e.g., 1:10, 2:10, 5:10\n");
	printf("  -h            Show this help\n");
	printf("\nExamples:\n");
	printf("  %s -n 1 -b 1024 -t 8 -c 48 -r 1:1    # 1 read, 1 write (alternating)\n", prog);
	printf("  %s -n 1 -b 1024 -t 8 -c 48 -r 1:10   # 1 read, 10 writes, repeat\n", prog);
	printf("  %s -n 1 -b 1024 -t 8 -c 48 -r 2:10   # 2 reads, 10 writes, repeat\n", prog);
	printf("  %s -n 1 -b 1024 -t 8 -c 48 -r 5:10   # 5 reads, 10 writes, repeat\n", prog);
	printf("  %s -n 1 -b 1024 -t 8 -c 48 -r 10:1   # 10 reads, 1 write, repeat\n", prog);
}

int main(int argc, char *argv[])
{
	int opt;
	int i;
	int ret;

	while ((opt = getopt(argc, argv, "n:b:t:c:r:h")) != -1) {
		switch (opt) {
		case 'n':
			target_node = atoi(optarg);
			break;
		case 'b':
			buffer_mb = atoi(optarg);
			break;
		case 't':
			num_threads = atoi(optarg);
			break;
		case 'c':
			cpu_start = atoi(optarg);
			break;
		case 'r':
			/* Parse ratio in format R:W (e.g., 1:10, 2:10, 5:10) */
			if (sscanf(optarg, "%d:%d", &read_ops, &write_ops) != 2) {
				fprintf(stderr, "Invalid ratio format. Use R:W (e.g., 1:10)\n");
				return 1;
			}
			break;
		case 'h':
			print_usage(argv[0]);
			return 0;
		default:
			print_usage(argv[0]);
			return 1;
		}
	}

	printf("memstress: Userspace Memory Antagonist\n");
	printf("Parameters: target_node=%d, buffer_mb=%zu, num_threads=%d, cpu_start=%d, ratio=%d:%d\n",
	       target_node, buffer_mb, num_threads, cpu_start, read_ops, write_ops);

	if (buffer_mb == 0) {
		fprintf(stderr, "Invalid buffer size\n");
		return 1;
	}

	if (num_threads < 0 || num_threads > 64) {
		fprintf(stderr, "Invalid number of threads\n");
		return 1;
	}

	if (read_ops < 0 || write_ops < 0 || (read_ops == 0 && write_ops == 0)) {
		fprintf(stderr, "Invalid read:write ratio (both must be >= 0, at least one > 0)\n");
		return 1;
	}

	signal(SIGINT, signal_handler);
	signal(SIGTERM, signal_handler);

	ret = allocate_buffer();
	if (ret < 0)
		return 1;

	if (num_threads == 0) {
		printf("No antagonist threads requested (0× contention)\n");
		printf("Press Ctrl+C to exit...\n");
		while (!stop_threads)
			sleep(1);
		free_buffer();
		return 0;
	}

	worker_threads = malloc(num_threads * sizeof(pthread_t));
	if (!worker_threads) {
		fprintf(stderr, "Failed to allocate thread array\n");
		free_buffer();
		return 1;
	}

	for (i = 0; i < num_threads; i++) {
		thread_args_t *args = malloc(sizeof(thread_args_t));
		if (!args) {
			fprintf(stderr, "Failed to allocate thread args\n");
			stop_threads = 1;
			goto cleanup;
		}

		args->thread_id = i;
		args->cpu_id = cpu_start + i;

		ret = pthread_create(&worker_threads[i], NULL, worker_thread_fn, args);
		if (ret != 0) {
			fprintf(stderr, "Failed to create thread %d: %s\n",
				i, strerror(ret));
			free(args);
			stop_threads = 1;
			goto cleanup;
		}
	}

	ret = pthread_create(&stats_thread, NULL, stats_thread_fn, NULL);
	if (ret != 0) {
		fprintf(stderr, "Warning: Failed to create stats thread: %s\n",
			strerror(ret));
	}

	printf("%d antagonist threads started\n", num_threads);
	printf("Press Ctrl+C to stop...\n");

	while (!stop_threads)
		sleep(1);

cleanup:
	for (i = 0; i < num_threads; i++) {
		pthread_join(worker_threads[i], NULL);
	}

	pthread_cancel(stats_thread);
	pthread_join(stats_thread, NULL);

	free(worker_threads);
	free_buffer();

	printf("memstress: Exiting\n");
	return 0;
}
