#!/usr/bin/env python3
"""
Example script demonstrating GoldMiner ETL pipeline usage.
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.config import ConfigManager
from goldminer.etl import ETLPipeline
from goldminer.analysis import DataAnalyzer


def create_sample_data():
    """Create sample CSV and Excel files for demonstration."""
    import random
    from datetime import datetime, timedelta
    
    # Ensure data directory exists
    os.makedirs('data/raw', exist_ok=True)
    
    # Generate sample financial data
    dates = [datetime.now() - timedelta(days=x) for x in range(100)]
    
    data = {
        'Date': [d.strftime('%Y-%m-%d') for d in dates],
        'Transaction ID': [f'TXN{i:05d}' for i in range(100)],
        'Amount': [round(random.uniform(10, 1000), 2) for _ in range(100)],
        'Category': [random.choice(['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping']) 
                    for _ in range(100)],
        'Description': [f'Transaction {i}' for i in range(100)],
        'Status': [random.choice(['Completed', 'Pending', 'Failed']) for _ in range(100)]
    }
    
    df = pd.DataFrame(data)
    
    # Save as CSV
    csv_path = 'data/raw/sample_data.csv'
    df.to_csv(csv_path, index=False)
    print(f"Created sample CSV: {csv_path}")
    
    # Save as Excel
    excel_path = 'data/raw/sample_data.xlsx'
    df.to_excel(excel_path, index=False)
    print(f"Created sample Excel: {excel_path}")
    
    # Create a second file with some duplicates
    df2 = df.copy()
    df2['Amount'] = [round(random.uniform(50, 2000), 2) for _ in range(100)]
    df2.to_csv('data/raw/additional_data.csv', index=False)
    print(f"Created additional CSV: data/raw/additional_data.csv")
    
    return csv_path


def main():
    """Main execution function."""
    print("=" * 70)
    print("GoldMiner ETL Pipeline - Example Usage")
    print("=" * 70)
    
    # Step 1: Create sample data
    print("\n[1] Creating sample data...")
    sample_file = create_sample_data()
    
    # Step 2: Initialize configuration
    print("\n[2] Loading configuration...")
    config = ConfigManager()
    print(f"Database path: {config.get('database.path')}")
    
    # Step 3: Initialize ETL pipeline
    print("\n[3] Initializing ETL pipeline...")
    pipeline = ETLPipeline(config)
    
    # Step 4: Run pipeline on directory (process all files)
    print("\n[4] Running ETL pipeline on data directory...")
    processed_df = pipeline.run_pipeline(
        source_path='data/raw',
        table_name='unified_data',
        is_directory=True,
        skip_duplicates=True,
        skip_outliers=False
    )
    
    print(f"\nProcessed DataFrame shape: {processed_df.shape}")
    print(f"Columns: {list(processed_df.columns)}")
    
    # Step 5: Get pipeline status
    print("\n[5] Getting pipeline status...")
    status = pipeline.get_pipeline_status()
    print(f"Database: {status['database_path']}")
    for table in status['tables']:
        print(f"  Table '{table['name']}': {table['row_count']} rows")
    
    # Step 6: Initialize analyzer
    print("\n[6] Running data analysis...")
    analyzer = DataAnalyzer(config)
    
    # Generate summary metrics
    print("\n[6.1] Generating summary metrics...")
    summary = analyzer.generate_summary_metrics(processed_df)
    print(f"  Total rows: {summary['overview']['total_rows']}")
    print(f"  Total columns: {summary['overview']['total_columns']}")
    print(f"  Memory usage: {summary['overview']['memory_usage_mb']:.2f} MB")
    
    # Detect anomalies
    print("\n[6.2] Detecting anomalies...")
    anomalies = analyzer.detect_anomalies(processed_df, method='iqr')
    if anomalies:
        for col, anomaly_df in anomalies.items():
            print(f"  Found {len(anomaly_df)} anomalies in '{col}'")
    else:
        print("  No anomalies detected")
    
    # Identify outliers
    print("\n[6.3] Identifying outliers...")
    outliers = analyzer.identify_outliers(processed_df)
    for col, info in outliers.items():
        print(f"  {col}: {info['count']} outliers ({info['percentage']:.2f}%)")
    
    # Generate full report
    print("\n[6.4] Generating comprehensive report...")
    report = analyzer.generate_full_report(processed_df)
    print("  Report sections:")
    for section in report.keys():
        print(f"    - {section}")
    
    # Step 7: Display sample of processed data
    print("\n[7] Sample of processed data:")
    print(processed_df.head(5).to_string())
    
    print("\n" + "=" * 70)
    print("ETL Pipeline Example Completed Successfully!")
    print("=" * 70)
    print(f"\nDatabase location: {config.get('database.path')}")
    print(f"Log file: {config.get('logging.file')}")


if __name__ == '__main__':
    main()
