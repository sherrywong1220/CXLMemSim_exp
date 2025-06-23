#!/bin/bash

# Simple RSS monitoring script
# Usage: ./rss.sh [log_directory] [interval_seconds]

LOG_DIR=${1:-"/tmp/rss_logs"}
INTERVAL=${2:-5}  # Default 5 second interval

# Create log directory if it doesn't exist
mkdir -p ${LOG_DIR}

# Function to get current timestamp
get_timestamp() {
    date '+%Y-%m-%d %H:%M:%S.%3N'
}

# Main monitoring loop
echo "Starting RSS monitoring at $(get_timestamp)" > ${LOG_DIR}/rss.log
echo "Log directory: ${LOG_DIR}" >> ${LOG_DIR}/rss.log
echo "Interval: ${INTERVAL} seconds" >> ${LOG_DIR}/rss.log
echo "" >> ${LOG_DIR}/rss.log

while true; do
    timestamp=$(get_timestamp)
    
    # Get total system RSS in KB and convert to GB
    total_rss_kb=$(ps -eo rss | awk 'NR>1 {sum+=$1} END {print sum}')
    total_rss_gb=$(echo "scale=3; ${total_rss_kb} / 1024 / 1024" | bc)
    
    # Log timestamp and total RSS in GB
    echo "${timestamp} - Total RSS: ${total_rss_gb} GB" >> ${LOG_DIR}/rss.log
    
    sleep ${INTERVAL}
done
