# Performance Results Analysis Script

This script analyzes performance results from CSV files using pandas and displays comprehensive statistics and insights. The analysis results are both displayed in the console and saved to a text file.

## Files

- `analyze_perf_results.py`: Main Python analysis script
- `run_perf_analysis.sh`: Shell script to run the analysis
- `README_perf_analysis.md`: This documentation file

## Features

The analysis script provides the following insights:

### 1. Basic Dataset Information
- Dataset shape and dimensions
- Column names and data types
- Missing value analysis

### 2. Summary Statistics
- Statistical summary for numerical columns (mean, std, min, max, etc.)
- Categorical column analysis (unique values, frequency counts)

### 3. Workload Analysis
- Workload distribution
- Execution time statistics by workload
- RSS difference statistics by workload

### 4. Tiering Version Analysis
- Tiering version distribution
- Execution time statistics by tiering version
- RSS difference statistics by tiering version

### 5. Cross Analysis
- Execution time comparison across workloads and tiering versions
- RSS difference comparison across workloads and tiering versions

### 6. All Data Display
- Shows all rows of the dataset for complete inspection

### 7. File Output
- Saves complete analysis to a timestamped text file
- Includes all console output plus additional metadata

## Requirements

- Python 3
- pandas library

Install pandas if not already installed:
```bash
pip3 install pandas
```

## Usage

### Method 1: Using shell script (Recommended)
```bash
cd run_bench/data_anal
bash run_perf_analysis.sh
```

### Method 2: Direct Python script execution
```bash
cd run_bench/data_anal

# Analyze default file (perf_results.csv) with auto-generated output file
python3 analyze_perf_results.py

# Analyze specific CSV file with auto-generated output file
python3 analyze_perf_results.py your_results.csv

# Analyze specific CSV file with custom output file name
python3 analyze_perf_results.py your_results.csv my_analysis.txt
```

### Method 3: Using shell script with custom files
```bash
cd run_bench/data_anal

# Analyze specific CSV file with auto-generated output
./run_perf_analysis.sh your_results.csv

# Analyze specific CSV file with custom output file
./run_perf_analysis.sh your_results.csv my_analysis.txt
```

## Output Files

The script generates a text file with the complete analysis. The filename format is:
- Auto-generated: `{csv_filename}_analysis_{timestamp}.txt`
- Custom: `{your_filename}.txt`

Example auto-generated filename: `perf_results_analysis_20241201_143022.txt`

## Expected CSV Format

The script expects a CSV file with columns similar to:
- workload: Workload name
- tiering: Memory tiering version
- mem_policy: Memory policy configuration
- execution_time: Execution time (seconds)
- rss: RSS difference (GB)
- Various vmstat metrics (pgpromote_success, numa_pte_updates, etc.)

## Output Example

### Console Output
```
Loading performance results from: perf_results.csv
Successfully loaded perf_results.csv
Data shape: (120, 15)
Columns: ['workload', 'tiering', 'mem_policy', 'execution_time', 'rss', ...]

Saving analysis to: perf_results_analysis_20241201_143022.txt
Analysis successfully saved to: perf_results_analysis_20241201_143022.txt

============================================================
ANALYSIS COMPLETED
============================================================
Results saved to: perf_results_analysis_20241201_143022.txt
```

### Text File Content
```
================================================================================
PERFORMANCE RESULTS ANALYSIS
================================================================================
Analysis Date: 2024-12-01 14:30:22
Source File: perf_results.csv
Dataset Shape: (120, 15)

============================================================
BASIC DATASET INFORMATION
============================================================
Dataset shape: (120, 15)
Number of rows: 120
Number of columns: 15

Column names:
   1. workload
   2. tiering
   3. mem_policy
   4. execution_time
   5. rss
   ...

============================================================
SUMMARY STATISTICS
============================================================
Numerical columns summary:
       execution_time  rss  pgpromote_success  ...
count          120.0           120.0             120.0
mean           156.23           20.1           12345.6
std             45.67            5.2            2345.7
min             89.12           12.3            9876.5
25%            123.45           16.8           11234.5
50%            145.67           19.5           12345.6
75%            178.90           23.2           13456.7
max            234.56           28.9           14876.8

============================================================
WORKLOAD ANALYSIS
============================================================
Workload distribution:
bc-urand    30
bc-web      30
bfs-urand   30
bfs-web     30

Execution time by workload:
           count    mean     std     min     max
workload                                        
bc-urand      30  145.23   12.34  123.45  167.89
bc-web        30  167.89   15.67  145.67  189.12
...

============================================================
CROSS ANALYSIS: WORKLOAD vs TIERING
============================================================
Execution time (mean) by workload and tiering:
tiering              nobalance  nobalance_thp  autonuma_tiering  autonuma_tiering_thp
workload                                                                              
bc-urand                 145.23          134.56            156.78                167.89
bc-web                   167.89          145.67            178.90                189.12
...

============================================================
ALL DATA (120 rows)
============================================================
workload   tiering              mem_policy  execution_time  rss  ...
bc-urand   nobalance            cpu0.weightedinterleave0_2  145.23          20.1  ...
bc-urand   nobalance_thp        cpu0.weightedinterleave0_2  134.56          18.9  ...
bc-urand   autonuma_tiering     cpu0.weightedinterleave0_2  156.78          21.3  ...
bc-urand   autonuma_tiering_thp cpu0.weightedinterleave0_2  167.89          22.7  ...
bc-web     nobalance            cpu0.weightedinterleave0_2  167.89          19.8  ...
bc-web     nobalance_thp        cpu0.weightedinterleave0_2  145.67          17.2  ...
bc-web     autonuma_tiering     cpu0.weightedinterleave0_2  178.90          23.1  ...
bc-web     autonuma_tiering_thp cpu0.weightedinterleave0_2  189.12          24.5  ...
bfs-urand  nobalance            cpu0.weightedinterleave0_2  123.45          15.6  ...
bfs-urand  nobalance_thp        cpu0.weightedinterleave0_2  112.34          14.2  ...
bfs-urand  autonuma_tiering     cpu0.weightedinterleave0_2  134.56          16.8  ...
bfs-urand  autonuma_tiering_thp cpu0.weightedinterleave0_2  145.67          18.1  ...
bfs-web    nobalance            cpu0.weightedinterleave0_2  145.67          18.9  ...
bfs-web    nobalance_thp        cpu0.weightedinterleave0_2  134.56          17.3  ...
bfs-web    autonuma_tiering     cpu0.weightedinterleave0_2  156.78          20.2  ...
bfs-web    autonuma_tiering_thp cpu0.weightedinterleave0_2  167.89          21.7  ...
...

================================================================================
ANALYSIS COMPLETED
================================================================================
```

## Notes

- The script automatically handles missing columns and provides appropriate warnings
- All numerical results are rounded to 2 decimal places for readability
- The analysis is comprehensive and covers multiple dimensions of the data
- The script can analyze any CSV file with similar structure
- Analysis results are both displayed in console and saved to a text file
- Text file includes timestamp and source file information for traceability 