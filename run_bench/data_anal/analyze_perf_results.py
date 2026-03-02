#!/usr/bin/env python3
"""
Script to parse perf_results.csv and display results using pandas
"""

import pandas as pd
import os
import sys
from datetime import datetime

def get_config_from_env():
    """Get configuration from environment variables"""
    # Get memory policies from environment variable
    mem_policies_env = os.getenv('DATA_ANAL_MEM_POLICYS')
    if not mem_policies_env:
        print("Warning: DATA_ANAL_MEM_POLICYS environment variable is not set, will use data from CSV")
        return None, None
    
    # Get tiering versions from environment variable
    tiering_env = os.getenv('DATA_ANAL_NET_CONFIGS')
    if not tiering_env:
        print("Warning: DATA_ANAL_NET_CONFIGS environment variable is not set, will use data from CSV")
        return None, None
    
    mem_policies = mem_policies_env.split()
    NET_CONFIGsions = tiering_env.split()
    
    print(f"Configuration from environment:")
    print(f"  Memory policies: {mem_policies}")
    print(f"  Tiering versions: {NET_CONFIGsions}")
    
    return mem_policies, NET_CONFIGsions

def load_perf_results(csv_file="perf_results.csv"):
    """Load perf results from CSV file"""
    try:
        # If csv_file is just a filename, look for it in perf_results directory
        if not os.path.dirname(csv_file):
            csv_file = f"perf_results/{csv_file}"
        
        if not os.path.exists(csv_file):
            print(f"Error: File {csv_file} not found")
            return None
        
        df = pd.read_csv(csv_file)
        print(f"Successfully loaded {csv_file}")
        print(f"Data shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

def capture_output(func, *args, **kwargs):
    """Capture function output and return as string"""
    import io
    import sys
    
    # Redirect stdout to capture output
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    try:
        func(*args, **kwargs)
        output = new_stdout.getvalue()
    finally:
        sys.stdout = old_stdout
    
    return output

def display_basic_info(df):
    """Display basic information about the dataset"""
    print("\n" + "="*60)
    print("BASIC DATASET INFORMATION")
    print("="*60)
    
    print(f"Dataset shape: {df.shape}")
    print(f"Number of rows: {len(df)}")
    print(f"Number of columns: {len(df.columns)}")
    
    print("\nColumn names:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i:2d}. {col}")
    
    print(f"\nData types:")
    print(df.dtypes)
    
    print(f"\nMissing values:")
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(missing[missing > 0])
    else:
        print("No missing values found")

def display_summary_statistics(df):
    """Display summary statistics for numerical columns"""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    
    # Get numerical columns
    numerical_cols = df.select_dtypes(include=['number']).columns
    if len(numerical_cols) > 0:
        print("Numerical columns summary:")
        print(df[numerical_cols].describe())
    else:
        print("No numerical columns found")
    
    # Get categorical columns
    categorical_cols = df.select_dtypes(include=['object']).columns
    if len(categorical_cols) > 0:
        print(f"\nCategorical columns ({len(categorical_cols)}):")
        for col in categorical_cols:
            print(f"\n{col}:")
            print(f"  Unique values: {df[col].nunique()}")
            print(f"  Most common values:")
            value_counts = df[col].value_counts().head(5)
            for value, count in value_counts.items():
                print(f"    {value}: {count}")

def display_workload_analysis(df):
    """Display analysis grouped by workload"""
    if 'workload' not in df.columns:
        print("No 'workload' column found for workload analysis")
        return
    
    print("\n" + "="*60)
    print("WORKLOAD ANALYSIS")
    print("="*60)
    
    # Workload distribution
    print("Workload distribution:")
    workload_counts = df['workload'].value_counts()
    print(workload_counts)
    
    # Summary by workload
    if 'execution_time' in df.columns:
        print(f"\nExecution time by workload:")
        workload_time = df.groupby('workload')['execution_time'].agg(['count', 'mean', 'std', 'min', 'max'])
        print(workload_time.round(2))
    
    if 'throughput' in df.columns:
        print(f"\nThroughput by workload:")
        workload_throughput = df.groupby('workload')['throughput'].agg(['count', 'mean', 'std', 'min', 'max'])
        print(workload_throughput.round(4))
    
    if 'rss' in df.columns:
        print(f"\nRSS by workload:")
        workload_rss = df.groupby('workload')['rss'].agg(['count', 'mean', 'std', 'min', 'max'])
        print(workload_rss.round(2))

def display_cross_analysis(df):
    """Display cross-analysis between workload and tiering for different memory policies"""
    if 'workload' not in df.columns or 'tiering' not in df.columns or 'mem_policy' not in df.columns:
        print("Missing 'workload', 'tiering', or 'mem_policy' columns for cross analysis")
        return
    
    print("\n" + "="*60)
    print("CROSS ANALYSIS: WORKLOAD vs TIERING")
    print("="*60)
    
    # Get memory policies from environment or data
    config_mem_policies, config_NET_CONFIGsions = get_config_from_env()
    if config_mem_policies is not None:
        mem_policies = config_mem_policies
        print(f"Using memory policies from environment: {mem_policies}")
    else:
        mem_policies = df['mem_policy'].unique()
        print(f"Using memory policies from data: {mem_policies}")
    
    # Set pandas options to show all columns without truncation
    with pd.option_context('display.max_columns', None, 'display.width', None):
        for mem_policy in mem_policies:
            print(f"\n" + "="*80)
            print(f"CROSS ANALYSIS: WORKLOAD vs TIERING when mem_policy is {mem_policy}")
            print("="*80)
            
            # Filter data for current memory policy
            df_policy = df[df['mem_policy'] == mem_policy]
            
            if 'execution_time' in df.columns:
                print(f"Execution time (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_time = df_policy.pivot_table(values='execution_time', index='workload', columns='tiering', aggfunc='mean')
                print(cross_time.round(2))
            
            if 'throughput' in df.columns:
                print(f"\nThroughput (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_throughput = df_policy.pivot_table(values='throughput', index='workload', columns='tiering', aggfunc='mean')
                print(cross_throughput.round(4))
                
                # Calculate performance improvement percentages
                print(f"\nThroughput Performance Improvement (%) when mem_policy is {mem_policy}:")
                print("THP improvement on AutoNUMA | THP improvement on nobalance")
                print("-" * 80)
                
                if ('autonuma_tiering' in cross_throughput.columns and 'autonuma_tiering_thp' in cross_throughput.columns and 
                    'nobalance' in cross_throughput.columns and 'nobalance_thp' in cross_throughput.columns):
                    
                    improvement_autonuma = ((cross_throughput['autonuma_tiering_thp'] - cross_throughput['autonuma_tiering']) / cross_throughput['autonuma_tiering'] * 100).round(2)
                    improvement_nobalance = ((cross_throughput['nobalance_thp'] - cross_throughput['nobalance']) / cross_throughput['nobalance'] * 100).round(2)
                    
                    for workload in cross_throughput.index:
                        autonuma_improvement = improvement_autonuma.get(workload, 0)
                        nobalance_improvement = improvement_nobalance.get(workload, 0)
                        print(f"{workload:<20} {autonuma_improvement:>8.2f}% {nobalance_improvement:>8.2f}%")
            
            if 'numa_pages_migrated' in df.columns:
                print(f"\nNUMA pages migrated (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_migrated = df_policy.pivot_table(values='numa_pages_migrated', index='workload', columns='tiering', aggfunc='mean')
                print(cross_migrated)
            
            if 'numa_hint_faults' in df.columns:
                print(f"\nNUMA hint faults (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_faults = df_policy.pivot_table(values='numa_hint_faults', index='workload', columns='tiering', aggfunc='mean')
                print(cross_faults)
            
            if 'thp_migration_success' in df.columns:
                print(f"\nTHP migration success (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_thp_migration = df_policy.pivot_table(values='thp_migration_success', index='workload', columns='tiering', aggfunc='mean')
                print(cross_thp_migration)
            
            if 'pgmigrate_success' in df.columns:
                print(f"\nPage migration success (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_pgmigrate = df_policy.pivot_table(values='pgmigrate_success', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgmigrate)
            
            if 'pgmigrate_fail' in df.columns:
                print(f"\nPage migration fail (mean) by workload and tiering when mem_policy is {mem_policy}:")
                cross_pgmigrate_fail = df_policy.pivot_table(values='pgmigrate_fail', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgmigrate_fail)
            
            # Page steal analysis
            if 'pgsteal_kswapd' in df.columns and 'pgsteal_direct' in df.columns:
                print(f"\nPage steal analysis (mean) by workload and tiering when mem_policy is {mem_policy}:")
                print("pgsteal_kswapd:")
                cross_pgsteal_kswapd = df_policy.pivot_table(values='pgsteal_kswapd', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgsteal_kswapd)
                
                print("\npgsteal_direct:")
                cross_pgsteal_direct = df_policy.pivot_table(values='pgsteal_direct', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgsteal_direct)
                
                # Calculate total page steals
                print("\nTotal page steals (pgsteal_kswapd + pgsteal_direct):")
                df_total_steal = df_policy.copy()
                df_total_steal['total_pgsteal'] = df_total_steal['pgsteal_kswapd'] + df_total_steal['pgsteal_direct']
                cross_total_steal = df_total_steal.pivot_table(values='total_pgsteal', index='workload', columns='tiering', aggfunc='mean')
                print(cross_total_steal)
            
            # Page demote analysis
            if 'pgdemote_kswapd' in df.columns and 'pgdemote_direct' in df.columns:
                print(f"\nPage demote analysis (mean) by workload and tiering when mem_policy is {mem_policy}:")
                print("pgdemote_kswapd:")
                cross_pgdemote_kswapd = df_policy.pivot_table(values='pgdemote_kswapd', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgdemote_kswapd)
                
                print("\npgdemote_direct:")
                cross_pgdemote_direct = df_policy.pivot_table(values='pgdemote_direct', index='workload', columns='tiering', aggfunc='mean')
                print(cross_pgdemote_direct)
                
                # Calculate total page demotes
                print("\nTotal page demotes (pgdemote_kswapd + pgdemote_direct):")
                df_total_demote = df_policy.copy()
                df_total_demote['total_pgdemote'] = df_total_demote['pgdemote_kswapd'] + df_total_demote['pgdemote_direct']
                cross_total_demote = df_total_demote.pivot_table(values='total_pgdemote', index='workload', columns='tiering', aggfunc='mean')
                print(cross_total_demote)
            
            if 'numa_local' in df.columns and 'numa_other' in df.columns:
                print(f"\nNUMA local:other ratio (mean) by workload and tiering when mem_policy is {mem_policy}:")
                # Calculate the ratio for each row
                df_ratio = df_policy.copy()
                df_ratio['numa_local_other_ratio'] = df_ratio['numa_local'] / df_ratio['numa_other']
                cross_ratio = df_ratio.pivot_table(values='numa_local_other_ratio', index='workload', columns='tiering', aggfunc='mean')
                print(cross_ratio.round(2))
            
            # Add new section for throughput performance improvement analysis
            if 'throughput' in df.columns:
                print(f"\n" + "="*80)
                print(f"THROUGHPUT PERFORMANCE IMPROVEMENT vs nobalance when mem_policy is {mem_policy}")
                print("="*80)
                
                if 'nobalance' in cross_throughput.columns:
                    nobalance_baseline = cross_throughput['nobalance']
                    
                    # Calculate improvement for each tiering strategy
                    improvements = {}
                    for tiering in cross_throughput.columns:
                        if tiering != 'nobalance':
                            improvements[tiering] = ((cross_throughput[tiering] - nobalance_baseline) / nobalance_baseline * 100).round(2)
                    
                    # Print header with proper spacing
                    header = f"{'Workload':<25}"
                    for tiering in improvements.keys():
                        header += f"{tiering:>25}"
                    print(header)
                    print("-" * 250)
                    
                    # Print improvement percentages for each workload
                    for workload in cross_throughput.index:
                        row = f"{workload:<25}"
                        for tiering in improvements.keys():
                            improvement = improvements[tiering].get(workload, 0)
                            row += f"{improvement:>25.2f}%"
                        print(row)
                    
                    # Print average improvement across all workloads
                    print("-" * 250)
                    avg_row = f"{'AVERAGE':<25}"
                    for tiering in improvements.keys():
                        avg_improvement = improvements[tiering].mean()
                        avg_row += f"{avg_improvement:>25.2f}%"
                    print(avg_row)

def display_cross_analysis_mem_policy_tiering(df):
    """Display cross-analysis between workload and mem_policy+tiering combination"""
    if 'workload' not in df.columns or 'tiering' not in df.columns or 'mem_policy' not in df.columns:
        print("Missing 'workload', 'tiering', or 'mem_policy' columns for cross analysis")
        return
    
    print("\n" + "="*60)
    print("CROSS ANALYSIS: WORKLOAD vs MEM_POLICY+TIERING")
    print("="*60)
    
    # Create mem_policy+tiering combination column
    df_combined = df.copy()
    df_combined['mem_policy_tiering'] = df_combined['tiering'] + '+' + df_combined['mem_policy']
    
    # Set pandas options to show all columns without truncation
    with pd.option_context('display.max_columns', None, 'display.width', None):
        if 'execution_time' in df.columns:
            print("Execution time (mean) by workload and mem_policy+tiering:")
            cross_time = df_combined.pivot_table(values='execution_time', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_time.round(2))
        
        if 'throughput' in df.columns:
            print(f"\nThroughput (mean) by workload and mem_policy+tiering:")
            cross_throughput = df_combined.pivot_table(values='throughput', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_throughput.round(4))
            
            # Calculate performance improvement percentages
            print(f"\nThroughput Performance Improvement (%) vs nobalance baseline:")
            print("-" * 80)
            
            # Find nobalance baseline columns
            nobalance_columns = [col for col in cross_throughput.columns if 'nobalance' in col]
            
            if nobalance_columns:
                # Use the first nobalance column as baseline
                baseline_col = nobalance_columns[0]
                print(f"Baseline: {baseline_col}")
                print("-" * 80)
                
                # Calculate improvement for each combination
                improvements = {}
                for col in cross_throughput.columns:
                    if col != baseline_col:
                        improvements[col] = ((cross_throughput[col] - cross_throughput[baseline_col]) / cross_throughput[baseline_col] * 100).round(2)
                
                # Print header with proper spacing
                header = f"{'Workload':<25}"
                for col in improvements.keys():
                    header += f"{col:>25}"
                print(header)
                print("-" * 250)
                
                # Print improvement percentages for each workload
                for workload in cross_throughput.index:
                    row = f"{workload:<25}"
                    for col in improvements.keys():
                        improvement = improvements[col].get(workload, 0)
                        row += f"{improvement:>25.2f}%"
                    print(row)
                
                # Print average improvement across all workloads
                print("-" * 250)
                avg_row = f"{'AVERAGE':<25}"
                for col in improvements.keys():
                    avg_improvement = improvements[col].mean()
                    avg_row += f"{avg_improvement:>25.2f}%"
                print(avg_row)
        
        if 'numa_pages_migrated' in df.columns:
            print(f"\nNUMA pages migrated (mean) by workload and mem_policy+tiering:")
            cross_migrated = df_combined.pivot_table(values='numa_pages_migrated', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_migrated)
        
        if 'numa_hint_faults' in df.columns:
            print(f"\nNUMA hint faults (mean) by workload and mem_policy+tiering:")
            cross_faults = df_combined.pivot_table(values='numa_hint_faults', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_faults)
        
        if 'thp_migration_success' in df.columns:
            print(f"\nTHP migration success (mean) by workload and mem_policy+tiering:")
            cross_thp_migration = df_combined.pivot_table(values='thp_migration_success', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_thp_migration)
        
        if 'pgmigrate_success' in df.columns:
            print(f"\nPage migration success (mean) by workload and mem_policy+tiering:")
            cross_pgmigrate = df_combined.pivot_table(values='pgmigrate_success', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgmigrate)
        
        if 'pgmigrate_fail' in df.columns:
            print(f"\nPage migration fail (mean) by workload and mem_policy+tiering:")
            cross_pgmigrate_fail = df_combined.pivot_table(values='pgmigrate_fail', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgmigrate_fail)
        
        # Page steal analysis
        if 'pgsteal_kswapd' in df.columns and 'pgsteal_direct' in df.columns:
            print(f"\nPage steal analysis (mean) by workload and mem_policy+tiering:")
            print("pgsteal_kswapd:")
            cross_pgsteal_kswapd = df_combined.pivot_table(values='pgsteal_kswapd', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgsteal_kswapd)
            
            print("\npgsteal_direct:")
            cross_pgsteal_direct = df_combined.pivot_table(values='pgsteal_direct', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgsteal_direct)
            
            # Calculate total page steals
            print("\nTotal page steals (pgsteal_kswapd + pgsteal_direct):")
            df_total_steal = df_combined.copy()
            df_total_steal['total_pgsteal'] = df_total_steal['pgsteal_kswapd'] + df_total_steal['pgsteal_direct']
            cross_total_steal = df_total_steal.pivot_table(values='total_pgsteal', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_total_steal)
        
        # Page demote analysis
        if 'pgdemote_kswapd' in df.columns and 'pgdemote_direct' in df.columns:
            print(f"\nPage demote analysis (mean) by workload and mem_policy+tiering:")
            print("pgdemote_kswapd:")
            cross_pgdemote_kswapd = df_combined.pivot_table(values='pgdemote_kswapd', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgdemote_kswapd)
            
            print("\npgdemote_direct:")
            cross_pgdemote_direct = df_combined.pivot_table(values='pgdemote_direct', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_pgdemote_direct)
            
            # Calculate total page demotes
            print("\nTotal page demotes (pgdemote_kswapd + pgdemote_direct):")
            df_total_demote = df_combined.copy()
            df_total_demote['total_pgdemote'] = df_total_demote['pgdemote_kswapd'] + df_total_demote['pgdemote_direct']
            cross_total_demote = df_total_demote.pivot_table(values='total_pgdemote', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_total_demote)
        
        if 'numa_local' in df.columns and 'numa_other' in df.columns:
            print(f"\nNUMA local:other ratio (mean) by workload and mem_policy+tiering:")
            # Calculate the ratio for each row
            df_ratio = df_combined.copy()
            df_ratio['numa_local_other_ratio'] = df_ratio['numa_local'] / df_ratio['numa_other']
            cross_ratio = df_ratio.pivot_table(values='numa_local_other_ratio', index='workload', columns='mem_policy_tiering', aggfunc='mean')
            print(cross_ratio.round(2))
        
def display_all_data(df):
    """Display all data from the dataset"""
    print("\n" + "="*60)
    print(f"ALL DATA ({len(df)} rows)")
    print("="*60)
    
    # Set pandas to display all rows and columns without truncation
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', None):
        print(df.to_string(index=False))

def save_analysis_to_file(df, csv_file, output_file=None):
    """Save complete analysis to a text file"""
    if output_file is None:
        # Generate output filename based on input CSV file
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"perf_results/{base_name}_analysis_{timestamp}.txt"
        
        # Create perf_results directory if it doesn't exist
        os.makedirs("perf_results", exist_ok=True)
    
    print(f"\nSaving analysis to: {output_file}")
    
    # Capture all analysis output
    analysis_output = []
    
    # Header
    analysis_output.append("="*80)
    analysis_output.append("PERFORMANCE RESULTS ANALYSIS")
    analysis_output.append("="*80)
    analysis_output.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    analysis_output.append(f"Source File: {csv_file}")
    analysis_output.append(f"Dataset Shape: {df.shape}")
    analysis_output.append("")
    
    # Capture each analysis section
    analysis_output.append(capture_output(display_basic_info, df))
    analysis_output.append(capture_output(display_summary_statistics, df))
    analysis_output.append(capture_output(display_workload_analysis, df))
    analysis_output.append(capture_output(display_cross_analysis, df))
    analysis_output.append(capture_output(display_cross_analysis_mem_policy_tiering, df))
    analysis_output.append(capture_output(display_all_data, df))
    
    # Footer
    analysis_output.append("="*80)
    analysis_output.append("ANALYSIS COMPLETED")
    analysis_output.append("="*80)
    
    # Write to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(analysis_output))
        print(f"Analysis successfully saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error saving analysis to file: {e}")
        return None

def main():
    """Main function"""
    # Set pandas display options to avoid scientific notation and format numbers properly
    pd.set_option('display.float_format', '{:.2f}'.format)
    # Set pandas to show all columns without truncation
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    
    # Load configuration from environment
    print("Loading configuration from environment variables...")
    config_mem_policies, config_NET_CONFIGsions = get_config_from_env()
    
    # Check command line arguments for CSV file
    csv_file = "perf_results.csv"
    output_file = None
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print(f"Loading performance results from: {csv_file}")
    
    # Load data
    df = load_perf_results(csv_file)
    if df is None:
        return
    
    # Display various analyses (console output)
    display_basic_info(df)
    display_summary_statistics(df)
    display_workload_analysis(df)
    display_cross_analysis(df)
    display_cross_analysis_mem_policy_tiering(df)
    display_all_data(df)
    
    # Save analysis to file
    saved_file = save_analysis_to_file(df, csv_file, output_file)
    
    print("\n" + "="*60)
    print("ANALYSIS COMPLETED")
    print("="*60)
    if saved_file:
        print(f"Results saved to: {saved_file}")

if __name__ == "__main__":
    main() 