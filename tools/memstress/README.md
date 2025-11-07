# memstress - Userspace Memory Antagonist

memstress is a userspace tool designed to create controlled memory interconnect contention for NUMA performance testing. It pins memory buffers to specific NUMA nodes and runs antagonist threads that continuously perform sequential non-temporal read/write operations.

## Features

- **NUMA Node Pinning**: Allocates buffer on specified NUMA node using `numa_alloc_onnode()`
- **Memory Locking**: Uses `mbind()` with `MPOL_BIND` and `mlock()` to prevent page migration
- **CPU Core Binding**: Binds antagonist threads to designated cores (default: 48-63)
- **Non-temporal Access**: Uses SSE instructions to bypass cache and maximize memory bandwidth
- **Configurable Contention**: Supports 0×, 1×, 2×, 3×, 4× contention levels (0, 4, 8, 12, 16 threads)
- **Bandwidth Monitoring**: Reports bandwidth statistics every 10 seconds

## Build

```bash
make
```

Requires:
- `libnuma-dev` package
- SSE4.1 support (CPU from ~2008 or later)

## Usage

### Command-line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-n <node>` | Target NUMA node for buffer allocation | 1 |
| `-b <MB>` | Buffer size in MB | 1024 |
| `-t <threads>` | Number of antagonist threads (0, 4, 8, 12, 16) | 0 |
| `-c <core>` | Starting CPU core for thread binding | 48 |
| `-h` | Show help message | - |

### Running the Tool


**1× Contention (4 threads):**
```bash
./memstress -n 1 -b 1024 -t 4 -c 48
```
or
```bash
make run-1x
```

**2× Contention (8 threads):**
```bash
make run-2x
```

**3× Contention (12 threads):**
```bash
make run-3x
```

**4× Contention (16 threads):**
```bash
make run-4x
```

### Stopping the Tool

Press `Ctrl+C` to gracefully stop all threads and exit.

### Monitoring

Bandwidth statistics are printed to stdout every 10 seconds:
```
Bandwidth = 45000 MB/s, Total = 450 GB
```

## How It Works

1. **Buffer Allocation**: Allocates memory on specified NUMA node using `numa_alloc_onnode()`
2. **Memory Pinning**:
   - Uses `mbind()` with `MPOL_BIND` and `MPOL_MF_STRICT` to bind pages to NUMA node
   - Uses `mlock()` to lock pages in physical memory
   - This prevents NUMA balancing from migrating pages
3. **Thread Creation**: Creates N POSIX threads, each bound to consecutive CPU cores starting from `-c`
4. **Memory Access Pattern**: Each thread performs sequential 1:1 read/write operations:
   - Non-temporal read (64B) using `movntdqa` (SSE4.1)
   - Non-temporal write (64B) using `movntdq` (SSE2)
   - Bypasses CPU cache to maximize memory interconnect traffic
5. **Steady-State Contention**: Threads run continuously until Ctrl+C, creating sustained memory bandwidth pressure

## Example Workflow

```bash
# Build the tool
make

# Run with 8 antagonist threads (2× contention)
./memstress -n 1 -b 1024 -t 8 -c 48 &

# Run your benchmark in another terminal
./your_benchmark

# Stop memstress when done
killall memstress
# or press Ctrl+C in the memstress terminal

# Clean build artifacts
make clean
```

## Notes

- **Privileges**: May require increased `ulimit -l` (locked memory limit) or `CAP_IPC_LOCK` capability to lock large buffers
  - Check current limit: `ulimit -l`
  - Increase limit: `ulimit -l unlimited` (in current shell)
  - Or run with: `sudo setcap cap_ipc_lock=+ep ./memstress`
- **CPU Cores**: Designed for systems with cores 48-63 available; adjust `-c` if needed
- **NUMA Nodes**: Use `numactl --hardware` to see available NUMA nodes
- **Page Migration**: The combination of `mbind()` + `mlock()` ensures pages stay on target NUMA node
- **Cache Bypass**: Non-temporal instructions bypass cache hierarchy to maximize memory bus utilization

## Troubleshooting

**Error: "Failed to mlock buffer"**
- Increase locked memory limit: `ulimit -l unlimited`
- Or grant capability: `sudo setcap cap_ipc_lock=+ep ./memstress`
- The tool will continue with just `mbind()`, which should still prevent migration

**Error: "NUMA is not available"**
- Install libnuma: `sudo apt-get install libnuma-dev`
- Check NUMA support: `numactl --hardware`

**Error: "Invalid NUMA node"**
- Check available nodes: `numactl --hardware`
- Use a valid node number with `-n`

**Low bandwidth or CPU binding fails**
- Verify CPU cores exist: `lscpu`
- Check thread affinity: `ps -eLo pid,tid,psr,comm | grep memstress`
