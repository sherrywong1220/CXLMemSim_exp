#!/bin/bash

# Linux Kernel Configuration Check Script
# This script checks if the kernel is compiled with NUMA balancing and THP support

echo "========================================="
echo "Linux Kernel Configuration Check"
echo "========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    local status=$1
    local message=$2
    if [ "$status" == "OK" ]; then
        echo -e "${GREEN}[OK]${NC} $message"
    elif [ "$status" == "WARNING" ]; then
        echo -e "${YELLOW}[WARNING]${NC} $message"
    else
        echo -e "${RED}[FAIL]${NC} $message"
    fi
}

# Check kernel config file locations
CONFIG_FILES=(
    "/proc/config.gz"
    "/boot/config-$(uname -r)"
    "/usr/src/linux/.config"
    "/lib/modules/$(uname -r)/build/.config"
)

echo "1. Looking for kernel configuration..."
CONFIG_FILE=""
for config in "${CONFIG_FILES[@]}"; do
    if [ -f "$config" ]; then
        CONFIG_FILE="$config"
        echo "   Found config: $config"
        break
    fi
done

if [ -z "$CONFIG_FILE" ]; then
    print_status "FAIL" "Kernel configuration file not found"
    echo "   Searched locations:"
    for config in "${CONFIG_FILES[@]}"; do
        echo "   - $config"
    done
    echo ""
    echo "   To make kernel config available:"
    echo "   - Install kernel headers: sudo apt install linux-headers-\$(uname -r)"
    echo "   - Or enable CONFIG_IKCONFIG_PROC and recompile kernel"
    exit 1
fi

echo ""

# Function to read config
read_config() {
    local option=$1
    if [[ "$CONFIG_FILE" == *.gz ]]; then
        zcat "$CONFIG_FILE" | grep "^$option"
    else
        grep "^$option" "$CONFIG_FILE"
    fi
}

# Check NUMA support
echo "2. Checking NUMA configuration..."
numa_config=$(read_config "CONFIG_NUMA=")
if [ -n "$numa_config" ]; then
    if echo "$numa_config" | grep -q "=y"; then
        print_status "OK" "NUMA support is enabled in kernel"
    else
        print_status "FAIL" "NUMA support is disabled in kernel"
    fi
else
    print_status "FAIL" "NUMA support not found in kernel config"
fi

# Check NUMA balancing
numa_balancing_config=$(read_config "CONFIG_NUMA_BALANCING=")
if [ -n "$numa_balancing_config" ]; then
    if echo "$numa_balancing_config" | grep -q "=y"; then
        print_status "OK" "NUMA balancing is enabled in kernel"
    else
        print_status "FAIL" "NUMA balancing is disabled in kernel"
    fi
else
    print_status "FAIL" "NUMA balancing not found in kernel config"
fi

echo ""

# Check THP support
echo "3. Checking THP (Transparent Huge Pages) configuration..."
thp_config=$(read_config "CONFIG_TRANSPARENT_HUGEPAGE=")
if [ -n "$thp_config" ]; then
    if echo "$thp_config" | grep -q "=y"; then
        print_status "OK" "Transparent Huge Pages support is enabled in kernel"
    else
        print_status "FAIL" "Transparent Huge Pages support is disabled in kernel"
    fi
else
    print_status "FAIL" "Transparent Huge Pages support not found in kernel config"
fi

# Check THP always option
thp_always_config=$(read_config "CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS=")
thp_madvise_config=$(read_config "CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=")
if [ -n "$thp_always_config" ] && echo "$thp_always_config" | grep -q "=y"; then
    print_status "OK" "THP always mode is available"
elif [ -n "$thp_madvise_config" ] && echo "$thp_madvise_config" | grep -q "=y"; then
    print_status "OK" "THP madvise mode is available"
else
    print_status "WARNING" "THP mode configuration not clear"
fi

echo ""

# Check huge page support
echo "4. Checking huge page configuration..."
hugepage_config=$(read_config "CONFIG_HUGETLBFS=")
if [ -n "$hugepage_config" ]; then
    if echo "$hugepage_config" | grep -q "=y"; then
        print_status "OK" "Huge page filesystem support is enabled"
    else
        print_status "WARNING" "Huge page filesystem support is disabled"
    fi
else
    print_status "WARNING" "Huge page filesystem support not found in config"
fi

hugepage_pool_config=$(read_config "CONFIG_HUGETLB_PAGE=")
if [ -n "$hugepage_pool_config" ]; then
    if echo "$hugepage_pool_config" | grep -q "=y"; then
        print_status "OK" "Huge page pool support is enabled"
    else
        print_status "WARNING" "Huge page pool support is disabled"
    fi
fi

echo ""

# Check memory management features
echo "5. Checking memory management features..."

# Check memory compaction
compaction_config=$(read_config "CONFIG_COMPACTION=")
if [ -n "$compaction_config" ] && echo "$compaction_config" | grep -q "=y"; then
    print_status "OK" "Memory compaction is enabled"
else
    print_status "WARNING" "Memory compaction is not enabled"
fi

# Check memory migration
migration_config=$(read_config "CONFIG_MIGRATION=")
if [ -n "$migration_config" ] && echo "$migration_config" | grep -q "=y"; then
    print_status "OK" "Page migration is enabled"
else
    print_status "WARNING" "Page migration is not enabled"
fi

# Check NUMA balancing default
numa_balancing_default=$(read_config "CONFIG_NUMA_BALANCING_DEFAULT_ENABLED=")
if [ -n "$numa_balancing_default" ] && echo "$numa_balancing_default" | grep -q "=y"; then
    print_status "OK" "NUMA balancing is enabled by default"
else
    print_status "WARNING" "NUMA balancing is not enabled by default"
fi

echo ""

# Check kernel information
echo "6. Kernel information..."
kernel_version=$(uname -r)
echo "   Kernel version: $kernel_version"
kernel_arch=$(uname -m)
echo "   Kernel architecture: $kernel_arch"

# Check for mTHP support (Linux 6.7+)
kernel_major=$(echo "$kernel_version" | cut -d. -f1)
kernel_minor=$(echo "$kernel_version" | cut -d. -f2)

if [ "$kernel_major" -gt 6 ] || ([ "$kernel_major" -eq 6 ] && [ "$kernel_minor" -ge 7 ]); then
    print_status "OK" "Kernel version supports mTHP (multi-size THP)"
elif [ "$kernel_major" -gt 5 ] || ([ "$kernel_major" -eq 5 ] && [ "$kernel_minor" -ge 4 ]); then
    print_status "OK" "Kernel version supports modern NUMA balancing"
    print_status "WARNING" "mTHP requires Linux 6.7+"
else
    print_status "WARNING" "Kernel version may have limited memory management features"
fi

echo ""
echo "========================================="
echo "Configuration Check Summary"
echo "========================================="

# Count critical features
numa_ok=false
thp_ok=false

if [ -n "$(read_config "CONFIG_NUMA=" | grep "=y")" ] && [ -n "$(read_config "CONFIG_NUMA_BALANCING=" | grep "=y")" ]; then
    numa_ok=true
fi

if [ -n "$(read_config "CONFIG_TRANSPARENT_HUGEPAGE=" | grep "=y")" ]; then
    thp_ok=true
fi

if $numa_ok && $thp_ok; then
    print_status "OK" "Kernel is properly configured for memory tiering experiments"
elif $numa_ok || $thp_ok; then
    print_status "WARNING" "Kernel has partial support for memory tiering"
    [ ! $numa_ok ] && echo "   - NUMA balancing support is missing or disabled"
    [ ! $thp_ok ] && echo "   - THP support is missing or disabled"
else
    print_status "FAIL" "Kernel lacks essential memory tiering features"
    echo "   - NUMA balancing support is missing or disabled"
    echo "   - THP support is missing or disabled"
fi

echo ""
