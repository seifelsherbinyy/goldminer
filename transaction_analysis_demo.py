"""
Transaction Analysis Demo Script

This script demonstrates the comprehensive transaction analysis capabilities
of the GoldMiner TransactionAnalyzer module. It generates sample transaction data
and performs various analyses including hourly, daily, and monthly summaries,
anomaly detection, trend analysis, and more.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from goldminer.analysis import TransactionAnalyzer
from goldminer.config import ConfigManager


def generate_sample_transaction_data(num_days=90, transactions_per_hour=5):
    """
    Generate realistic sample transaction data.
    
    Args:
        num_days: Number of days to generate data for
        transactions_per_hour: Average number of transactions per hour
        
    Returns:
        DataFrame with transaction data
    """
    print(f"Generating {num_days} days of sample transaction data...")
    
    dates = []
    amounts = []
    transaction_ids = []
    categories = ['online', 'in-store', 'mobile', 'phone']
    transaction_categories = []
    
    base_date = datetime.now() - timedelta(days=num_days)
    transaction_id = 1000
    
    for day in range(num_days):
        for hour in range(24):
            # Vary the number of transactions based on hour and day
            if hour < 6 or hour > 22:  # Late night/early morning - fewer transactions
                num_transactions = max(1, transactions_per_hour // 2)
            elif 9 <= hour <= 20:  # Business hours - more transactions
                num_transactions = transactions_per_hour + np.random.randint(-2, 5)
            else:
                num_transactions = transactions_per_hour
            
            # Weekend adjustment (days 5 and 6 are weekends)
            if day % 7 in [5, 6]:
                num_transactions = int(num_transactions * 1.3)  # More weekend activity
            
            for _ in range(num_transactions):
                # Create timestamp with random minutes/seconds
                timestamp = base_date + timedelta(
                    days=day,
                    hours=hour,
                    minutes=np.random.randint(0, 60),
                    seconds=np.random.randint(0, 60)
                )
                
                # Generate transaction amount with patterns
                base_amount = 50
                if hour >= 9 and hour <= 17:  # Business hours - higher values
                    base_amount = 100
                if day % 7 in [5, 6]:  # Weekends - higher average
                    base_amount *= 1.2
                
                # Add randomness and occasional large transactions
                if np.random.random() > 0.95:  # 5% chance of large transaction
                    amount = base_amount * np.random.uniform(5, 20)
                else:
                    amount = base_amount * np.random.uniform(0.3, 2.0)
                
                dates.append(timestamp)
                amounts.append(round(amount, 2))
                transaction_ids.append(f"TXN-{transaction_id}")
                transaction_categories.append(np.random.choice(categories))
                transaction_id += 1
    
    # Add some anomalies
    # Add spike
    spike_idx = len(dates) // 2
    dates.append(base_date + timedelta(days=num_days//2, hours=14))
    amounts.append(10000.0)  # Large spike
    transaction_ids.append(f"TXN-{transaction_id}")
    transaction_categories.append('online')
    
    # Add drop
    drop_idx = len(dates) // 4
    dates.append(base_date + timedelta(days=num_days//4, hours=10))
    amounts.append(1.0)  # Unusually low
    transaction_ids.append(f"TXN-{transaction_id + 1}")
    transaction_categories.append('in-store')
    
    df = pd.DataFrame({
        'transaction_id': transaction_ids,
        'timestamp': dates,
        'amount': amounts,
        'category': transaction_categories
    })
    
    # Sort by timestamp
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"Generated {len(df)} transactions from {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Total transaction value: ${df['amount'].sum():,.2f}")
    print(f"Average transaction value: ${df['amount'].mean():.2f}")
    print()
    
    return df


def analyze_transactions(df):
    """
    Perform comprehensive transaction analysis.
    
    Args:
        df: Transaction DataFrame
    """
    print("=" * 80)
    print("COMPREHENSIVE TRANSACTION ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize analyzer
    analyzer = TransactionAnalyzer()
    
    # 1. HOURLY ANALYSIS
    print("-" * 80)
    print("1. HOURLY ANALYSIS")
    print("-" * 80)
    
    hourly_sum = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='sum')
    hourly_mean = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='mean')
    
    print("\nTop 5 Hours by Total Transaction Value:")
    top_hours = hourly_sum.nlargest(5, 'amount_sum')
    for _, row in top_hours.iterrows():
        print(f"  Hour {int(row['hour']):02d}:00 - ${row['amount_sum']:,.2f} "
              f"({int(row['transaction_count'])} transactions)")
    
    print("\nHours with Lowest Activity:")
    low_hours = hourly_sum.nsmallest(5, 'amount_sum')
    for _, row in low_hours.iterrows():
        print(f"  Hour {int(row['hour']):02d}:00 - ${row['amount_sum']:,.2f} "
              f"({int(row['transaction_count'])} transactions)")
    print()
    
    # 2. DAILY ANALYSIS
    print("-" * 80)
    print("2. DAILY ANALYSIS")
    print("-" * 80)
    
    daily_summary = analyzer.summarize_by_day(df, 'amount', 'timestamp')
    daily_with_trends = analyzer.calculate_moving_averages(
        daily_summary, 
        'amount_sum', 
        windows=[7, 14, 30]
    )
    
    print(f"\nTotal Days Analyzed: {len(daily_summary)}")
    print(f"Average Daily Transaction Value: ${daily_summary['amount_sum'].mean():,.2f}")
    print(f"Highest Daily Value: ${daily_summary['amount_sum'].max():,.2f}")
    print(f"Lowest Daily Value: ${daily_summary['amount_sum'].min():,.2f}")
    
    # Detect spikes and drops in daily data
    anomalies = analyzer.detect_spikes_and_drops(daily_summary, 'amount_sum', method='iqr')
    print(f"\nAnomaly Detection (IQR Method):")
    print(f"  Spikes detected: {anomalies['spike_count']}")
    print(f"  Drops detected: {anomalies['drop_count']}")
    
    if anomalies['spikes']:
        print("\n  Top Spikes:")
        for spike in anomalies['spikes'][:3]:
            print(f"    {spike.get('date', 'N/A')} - ${spike['value']:,.2f}")
    
    # Top performing days
    top_days = analyzer.identify_top_periods(daily_summary, 'amount_sum', top_n=5)
    print("\n  Top 5 Performing Days:")
    for day in top_days['top_performers']:
        print(f"    {day.get('date', 'N/A')} ({day.get('day_of_week', 'N/A')}) - "
              f"${day['value']:,.2f}")
    print()
    
    # 3. MONTHLY ANALYSIS
    print("-" * 80)
    print("3. MONTHLY ANALYSIS")
    print("-" * 80)
    
    monthly_summary = analyzer.summarize_by_month(df, 'amount', 'timestamp')
    monthly_with_trends = analyzer.calculate_moving_averages(
        monthly_summary,
        'amount_sum',
        windows=[3]
    )
    
    print(f"\nTotal Months Analyzed: {len(monthly_summary)}")
    print("\nMonthly Performance:")
    for _, row in monthly_summary.iterrows():
        print(f"  {row['month_name']} {int(row['year'])}: ${row['amount_sum']:,.2f} "
              f"({int(row['transaction_count'])} transactions)")
    
    if len(monthly_summary) > 1:
        monthly_anomalies = analyzer.detect_spikes_and_drops(
            monthly_summary, 
            'amount_sum',
            method='zscore'
        )
        if monthly_anomalies['spikes']:
            print("\n  Exceptional Months (Spikes):")
            for spike in monthly_anomalies['spikes']:
                print(f"    {spike.get('year_month', 'N/A')} - ${spike['value']:,.2f}")
    print()
    
    # 4. PERFORMANCE INDICATORS
    print("-" * 80)
    print("4. COMPREHENSIVE PERFORMANCE INDICATORS")
    print("-" * 80)
    
    indicators = analyzer.calculate_performance_indicators(df, 'amount', 'timestamp')
    
    print(f"\nOverall Metrics:")
    print(f"  Total Transactions: {indicators['total_transactions']:,}")
    print(f"  Total Value: ${indicators['total_value']:,.2f}")
    print(f"  Average Transaction: ${indicators['average_value']:.2f}")
    print(f"  Median Transaction: ${indicators['median_value']:.2f}")
    print(f"  Std Deviation: ${indicators['std_deviation']:.2f}")
    print(f"  Min Transaction: ${indicators['min_value']:.2f}")
    print(f"  Max Transaction: ${indicators['max_value']:,.2f}")
    
    print(f"\nDate Range:")
    print(f"  Start: {indicators['date_range']['start']}")
    print(f"  End: {indicators['date_range']['end']}")
    print(f"  Total Days: {indicators['date_range']['days']}")
    
    print(f"\nQuartiles:")
    print(f"  Q1 (25th percentile): ${indicators['quartiles']['q1']:.2f}")
    print(f"  Q2 (50th percentile): ${indicators['quartiles']['q2']:.2f}")
    print(f"  Q3 (75th percentile): ${indicators['quartiles']['q3']:.2f}")
    
    if indicators.get('growth_rate') is not None:
        print(f"\nGrowth Rate: {indicators['growth_rate']:.2f}%")
    print()
    
    # 5. GENERATE COMPREHENSIVE REPORT
    print("-" * 80)
    print("5. GENERATING COMPREHENSIVE JSON REPORT")
    print("-" * 80)
    
    full_report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')
    
    # Save report to JSON file
    report_filename = '/tmp/transaction_analysis_report.json'
    with open(report_filename, 'w') as f:
        json.dump(full_report, f, indent=2, default=str)
    
    print(f"\nFull analysis report saved to: {report_filename}")
    print(f"Report sections: {', '.join(full_report.keys())}")
    print()
    
    # 6. VISUALIZATION DATA
    print("-" * 80)
    print("6. GENERATING VISUALIZATION DATA")
    print("-" * 80)
    
    viz_data = analyzer.generate_visualization_data(df, 'amount', 'timestamp')
    
    viz_filename = '/tmp/transaction_visualization_data.json'
    with open(viz_filename, 'w') as f:
        json.dump(viz_data, f, indent=2, default=str)
    
    print(f"\nVisualization data saved to: {viz_filename}")
    print(f"Available visualizations:")
    print(f"  - Time Series: {len(viz_data['time_series']['dates'])} data points")
    print(f"  - Hourly Distribution: {len(viz_data['hourly_distribution']['hours'])} hours")
    print(f"  - Monthly Trends: {len(viz_data['monthly_trends']['months'])} months")
    print()
    
    return full_report, viz_data


def demonstrate_error_handling():
    """Demonstrate error handling capabilities."""
    print("=" * 80)
    print("ERROR HANDLING DEMONSTRATION")
    print("=" * 80)
    print()
    
    analyzer = TransactionAnalyzer()
    
    # Test 1: Empty DataFrame
    print("Test 1: Empty DataFrame")
    try:
        empty_df = pd.DataFrame()
        analyzer.validate_dataframe(empty_df)
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly handled: {e}")
    print()
    
    # Test 2: Missing date column
    print("Test 2: Missing Date Column")
    try:
        df_no_date = pd.DataFrame({'amount': [100, 200, 300]})
        analyzer.validate_dataframe(df_no_date, 'nonexistent_column')
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly handled: {e}")
    print()
    
    # Test 3: Invalid column in analysis
    print("Test 3: Invalid Column in Analysis")
    try:
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'amount': [100] * 10
        })
        analyzer.summarize_by_hour(df, 'invalid_column', 'timestamp')
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly handled: {e}")
    print()
    
    # Test 4: Invalid aggregation method
    print("Test 4: Invalid Aggregation Method")
    try:
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'amount': [100] * 10
        })
        analyzer.summarize_by_day(df, 'amount', 'timestamp', aggregation='invalid')
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly handled: {e}")
    print()


def main():
    """Main execution function."""
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  GOLDMINER TRANSACTION ANALYSIS MODULE - COMPREHENSIVE DEMO".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")
    
    # Generate sample data
    df = generate_sample_transaction_data(num_days=90, transactions_per_hour=5)
    
    # Perform comprehensive analysis
    full_report, viz_data = analyze_transactions(df)
    
    # Demonstrate error handling
    demonstrate_error_handling()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print("The TransactionAnalyzer module provides:")
    print("  ✓ Hourly transaction analysis and aggregation")
    print("  ✓ Daily transaction analysis with trends")
    print("  ✓ Monthly transaction analysis and patterns")
    print("  ✓ Anomaly detection (spikes and drops)")
    print("  ✓ Moving averages (7-day, 14-day, 30-day)")
    print("  ✓ Performance indicators and metrics")
    print("  ✓ Top-performing period identification")
    print("  ✓ Comprehensive error handling")
    print("  ✓ JSON export for reports and visualizations")
    print()
    print("Integration:")
    print("  • Can be used standalone or integrated with GoldMiner ETL pipeline")
    print("  • Supports both API and programmatic usage")
    print("  • Compatible with pandas DataFrames from any source")
    print("  • Configurable via YAML configuration files")
    print()
    print("Next Steps:")
    print("  1. Review generated reports in /tmp/transaction_analysis_report.json")
    print("  2. Use visualization data for creating charts/dashboards")
    print("  3. Integrate with existing ETL workflows")
    print("  4. Customize analysis parameters via config.yaml")
    print("  5. Extend with additional custom analytics as needed")
    print()
    print("*" * 80)
    print("Demo completed successfully!")
    print("*" * 80)
    print()


if __name__ == "__main__":
    main()
