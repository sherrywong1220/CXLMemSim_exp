#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Usage: $0 <PID> [time_seconds,optional]"
    echo "If no time specified, will monitor until process ends"
    exit 1
fi

PID=$1
TIME=$2

echo "AMD IBS-based Hot Pages Analysis..."
echo "Target PID: $PID"

# Check if process exists
if ! kill -0 "$PID" 2>/dev/null; then
    echo "Error: Process $PID does not exist"
    exit 1
fi

# Use IBS Op event for data access sampling
echo "Collecting IBS Op data..."

if [ -n "$TIME" ]; then
    # Fixed time monitoring
    echo "Monitoring time: ${TIME} seconds"
    if sudo perf record -e ibs_op// -a --data --phys-data \
        -o "ibs_hotpages_${PID}.data" \
        sleep "$TIME" 2>/dev/null; then
        SUCCESS=1
    else
        SUCCESS=0
    fi
else
    # Monitor until process ends
    echo "Monitoring until process $PID ends..."
    sudo perf record -e ibs_op// -a --data --phys-data \
        -o "ibs_hotpages_${PID}.data" &
    
    PERF_PID=$!
    
    # Wait for target process to end
    while kill -0 "$PID" 2>/dev/null; do
        sleep 1
    done
    
    echo "Process $PID ended, stopping monitoring..."
    kill $PERF_PID 2>/dev/null
    wait $PERF_PID 2>/dev/null
    SUCCESS=1
fi

if [ $SUCCESS -eq 1 ]; then
    
    echo "IBS data collection completed, starting analysis..."
    
    # Python analysis script
    python3 << PYTHON_EOF
import subprocess
import re
from collections import defaultdict
import sys

def analyze_ibs_hot_pages():
    try:
        pid = "$PID"
        
        # Get IBS data for target PID
        result = subprocess.run([
            'sudo', 'perf', 'script', '-i', f'ibs_hotpages_{pid}.data'
        ], capture_output=True, text=True)
        
        page_hits = defaultdict(int)
        va_to_pa = {}
        instruction_addrs = defaultdict(int)
        
        target_pid_samples = 0
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            if not line or pid not in line:
                continue
                
            target_pid_samples += 1
            
            # Parse IBS output: "comm pid [cpu] timestamp: period event: addr function"
            parts = line.split()
            if len(parts) >= 6:
                # Find address (usually after colon)
                for i, part in enumerate(parts):
                    if ':' in part and i < len(parts) - 1:
                        addr_part = parts[i + 1]
                        if re.match(r'^[0-9a-fA-F]+$', addr_part):
                            addr = int(addr_part, 16)
                            
                            # 4KB page alignment
                            page = addr & ~0xFFF
                            page_hits[page] += 1
                            
                            # Record instruction address (for hot code analysis)
                            instruction_addrs[addr] += 1
                            break
        
        if not page_hits:
            print(f"❌ No IBS data found for PID {pid}")
            return
            
        # Sort and output hot pages
        sorted_pages = sorted(page_hits.items(), key=lambda x: x[1], reverse=True)
        
        print(f"🔥 IBS Hot 4KB Pages Analysis (PID {pid}):")
        print("Virtual Address\t\tHits\t\tTHP Offset\tPercentage")
        print("-" * 70)
        
        total_hits = sum(page_hits.values())
        
        for i, (vpage, hits) in enumerate(sorted_pages[:25]):
            # Calculate offset within THP
            thp_base = vpage & ~0x1FFFFF  # 2MB alignment
            offset_in_thp = (vpage - thp_base) // 4096
            percentage = (hits / total_hits) * 100
            
            print(f"0x{vpage:x}\t{hits}\t\t{offset_in_thp}/512\t{percentage:.1f}%")
        
        print(f"\n📊 Statistics:")
        print(f"- Total IBS Samples: {target_pid_samples:,}")
        print(f"- Unique Pages: {len(page_hits):,}")
        print(f"- Total Accesses: {total_hits:,}")
        print(f"- Average Accesses per Page: {total_hits / len(page_hits):.1f}")
        
        # Analyze hot instructions
        sorted_instructions = sorted(instruction_addrs.items(), key=lambda x: x[1], reverse=True)
        print(f"\n🎯 Hot Instruction Addresses (Top 10):")
        for addr, count in sorted_instructions[:10]:
            print(f"0x{addr:x}: {count:,} hits")
        
        # Generate THP page access frequency histogram
        print(f"\n" + "="*80)
        print(f"📊 THP Page Access Frequency Histogram (PID {pid})")
        print(f"="*80)
        
        # Count page access distribution within each THP
        thp_page_counts = defaultdict(int)
        for vpage, hits in page_hits.items():
            thp_base = vpage & ~0x1FFFFF  # 2MB alignment
            offset_in_thp = (vpage - thp_base) // 4096
            thp_page_counts[offset_in_thp] += hits
        
        # Sort by offset
        sorted_thp_pages = sorted(thp_page_counts.items())
        
        # Calculate histogram statistics
        max_hits = max(thp_page_counts.values()) if thp_page_counts else 0
        total_thp_hits = sum(thp_page_counts.values())
        
        print(f"THP Offset\tAccess Count\tPercentage\tHistogram")
        print(f"-" * 60)
        
        for offset, hits in sorted_thp_pages:
            percentage = (hits / total_thp_hits) * 100
            # Create simple ASCII histogram (max 50 characters)
            bar_length = int((hits / max_hits) * 50) if max_hits > 0 else 0
            bar = "█" * bar_length
            print(f"{offset:3d}/512\t{hits:8d}\t{percentage:5.1f}%\t{bar}")
        
        # Generate base page access histogram
        print(f"\n" + "="*80)
        print(f"📊 Base Page Access Histogram (PID {pid})")
        print(f"="*80)
        
        # Group statistics by access count
        access_ranges = [
            (1, 10, "1-10"),
            (11, 50, "11-50"),
            (51, 100, "51-100"),
            (101, 500, "101-500"),
            (501, 1000, "501-1K"),
            (1001, 5000, "1K-5K"),
            (5001, 10000, "5K-10K"),
            (10001, 50000, "10K-50K"),
            (50001, float('inf'), "50K+")
        ]
        
        range_counts = defaultdict(int)
        for vpage, hits in page_hits.items():
            for min_val, max_val, label in access_ranges:
                if min_val <= hits <= max_val:
                    range_counts[label] += 1
                    break
        
        print(f"Access Range\tPage Count\tPercentage\tHistogram")
        print(f"-" * 60)
        
        total_pages = len(page_hits)
        max_pages = max(range_counts.values()) if range_counts else 0
        
        for min_val, max_val, label in access_ranges:
            count = range_counts[label]
            if count > 0:
                percentage = (count / total_pages) * 100
                bar_length = int((count / max_pages) * 50) if max_pages > 0 else 0
                bar = "█" * bar_length
                print(f"{label:12s}\t{count:8d}\t{percentage:5.1f}%\t{bar}")
        
        # Output THP usage efficiency analysis
        print(f"\n" + "="*80)
        print(f"🎯 THP Usage Efficiency Analysis (PID {pid})")
        print(f"="*80)
        
        used_offsets = len(thp_page_counts)
        total_offsets = 512
        efficiency = (used_offsets / total_offsets) * 100
        
        print(f"📈 THP Usage Statistics:")
        print(f"- Used Offsets: {used_offsets}/512 ({efficiency:.1f}%)")
        print(f"- Unused Offsets: {total_offsets - used_offsets}/512 ({100-efficiency:.1f}%)")
        
        if thp_page_counts:
            min_offset = min(thp_page_counts.keys())
            max_offset = max(thp_page_counts.keys())
            print(f"- Usage Range: {min_offset}-{max_offset}/512")
            print(f"- Usage Span: {max_offset - min_offset + 1} pages")
        
        # Automatic analysis and conclusion output
        print(f"\n" + "="*80)
        print(f"🎯 Automatic Analysis Conclusion (PID {pid})")
        print(f"="*80)
        
        # Analyze THP usage efficiency
        print(f"📊 THP Usage Efficiency Analysis:")
        print(f"• Usage Rate: {efficiency:.1f}% ({used_offsets}/512 offset positions used)")
        if thp_page_counts:
            print(f"• Usage Range: {min_offset}-{max_offset}/512 (span {max_offset - min_offset + 1} pages)")
        print(f"• Efficiency Assessment: {'Relatively concentrated usage' if efficiency < 50 else 'Relatively scattered usage'}, {100-efficiency:.1f}% of THP space remains unused")
        
        # Analyze THP usage patterns
        print(f"\n🎯 THP Usage Pattern Analysis:")
        if thp_page_counts:
            # Calculate hot region concentration
            sorted_thp_pages = sorted(thp_page_counts.items(), key=lambda x: x[1], reverse=True)
            total_thp_hits = sum(thp_page_counts.values())
            
            # Find top 20% offset positions by access count
            top_20_percent = max(1, len(sorted_thp_pages) // 5)
            top_offsets = [offset for offset, hits in sorted_thp_pages[:top_20_percent]]
            
            if top_offsets:
                min_hot_offset = min(top_offsets)
                max_hot_offset = max(top_offsets)
                hot_region_start = (min_hot_offset / 512) * 100
                hot_region_end = (max_hot_offset / 512) * 100
                
                print(f"• Hot Region: {hot_region_start:.0f}%-{hot_region_end:.0f}% (offset {min_hot_offset}-{max_hot_offset}/512)")
                
                # Calculate hot region access percentage
                hot_region_hits = sum(thp_page_counts[offset] for offset in top_offsets)
                hot_region_percent = (hot_region_hits / total_thp_hits) * 100
                print(f"• Hot Region Access: {hot_region_percent:.1f}% ({hot_region_hits:,} accesses)")
                
                # Analyze hot distribution characteristics
                if max_hot_offset - min_hot_offset < 50:
                    distribution = "Highly Concentrated"
                elif max_hot_offset - min_hot_offset < 100:
                    distribution = "Relatively Concentrated"
                elif max_hot_offset - min_hot_offset < 200:
                    distribution = "Moderately Scattered"
                else:
                    distribution = "Relatively Scattered"
                
                print(f"• Hot Distribution: {distribution} (span {max_hot_offset - min_hot_offset + 1} pages)")
                
                # Analyze THP usage efficiency
                if hot_region_percent > 70:
                    efficiency_desc = "Very High Efficiency"
                elif hot_region_percent > 50:
                    efficiency_desc = "High Efficiency"
                elif hot_region_percent > 30:
                    efficiency_desc = "Medium Efficiency"
                else:
                    efficiency_desc = "Low Efficiency"
                
                print(f"• THP Efficiency: {efficiency_desc} (hot region accounts for {hot_region_percent:.1f}% of accesses)")
            else:
                print(f"• Hot Region: No significant hotspots")
        else:
            print(f"• Hot Region: No data")
        
        # Analyze Base Page access patterns
        print(f"\n📈 Base Page Access Pattern Analysis:")
        low_access = range_counts.get("1-10", 0)
        medium_access = range_counts.get("11-50", 0) + range_counts.get("51-100", 0) + range_counts.get("101-500", 0)
        high_access = range_counts.get("501-1K", 0) + range_counts.get("1K-5K", 0) + range_counts.get("5K-10K", 0)
        very_high_access = range_counts.get("10K-50K", 0) + range_counts.get("50K+", 0)
        
        low_percent = (low_access / total_pages) * 100
        medium_percent = (medium_access / total_pages) * 100
        high_percent = (high_access / total_pages) * 100
        very_high_percent = (very_high_access / total_pages) * 100
        
        print(f"• Low Access Pages: {low_percent:.1f}% ({low_access} pages, 1-10 accesses)")
        print(f"• Medium Access Pages: {medium_percent:.1f}% ({medium_access} pages, 11-500 accesses)")
        print(f"• High Access Pages: {high_percent:.1f}% ({high_access} pages, 501-10K accesses)")
        print(f"• Very High Access Pages: {very_high_percent:.1f}% ({very_high_access} pages, 10K+ accesses)")
        
        # Analyze access concentration
        print(f"\n🔥 Access Concentration Analysis:")
        if very_high_percent > 5:
            concentration = "Very High"
        elif high_percent > 20:
            concentration = "High"
        elif medium_percent > 40:
            concentration = "Medium"
        else:
            concentration = "Low"
        
        print(f"• Access Concentration: {concentration}")
        print(f"• Hot Page Characteristics: {'Few pages heavily accessed' if very_high_percent > 2 else 'Relatively uniform access distribution'}")
        
        # Performance optimization recommendations
        print(f"\n💡 Performance Optimization Recommendations:")
        if efficiency < 30:
            print(f"• Low THP usage rate ({efficiency:.1f}%), consider optimizing memory allocation strategy")
        elif efficiency > 80:
            print(f"• High THP usage rate ({efficiency:.1f}%), current memory usage efficiency is good")
        else:
            print(f"• Medium THP usage rate ({efficiency:.1f}%), there is room for further optimization")
        
        if very_high_percent > 5:
            print(f"• Very high access pages exist ({very_high_percent:.1f}%), consider data locality optimization")
        elif low_percent > 60:
            print(f"• Many low access pages ({low_percent:.1f}%), consider memory compression or paging strategies")
        
        # Algorithm characteristics analysis
        print(f"\n🧮 Algorithm Characteristics Analysis:")
        if concentration in ["Very High", "High"]:
            print(f"• Matches graph algorithm characteristics: few key data structures are frequently accessed")
            print(f"• Recommendation: optimize cache-friendliness of hot data structures")
        else:
            print(f"• Relatively uniform access pattern: may be suitable for parallel processing")
            print(f"• Recommendation: consider data sharding and load balancing")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

analyze_ibs_hot_pages()
PYTHON_EOF

    echo -e "\nData file saved as: ibs_hotpages_${PID}.data"
    echo "You can view raw data using:"
    echo "  sudo perf script -i ibs_hotpages_${PID}.data | grep ${PID}"
    
else
    echo "IBS data collection failed"
fi