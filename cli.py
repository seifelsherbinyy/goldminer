#!/usr/bin/env python3
"""
GoldMiner CLI - Command-line interface for ETL pipeline operations.
"""
import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.config import ConfigManager
from goldminer.etl import ETLPipeline, DatabaseManager, XLSXExporter
from goldminer.analysis import DataAnalyzer, MonteCarloForecaster
import json


def run_pipeline(args):
    """Run the ETL pipeline."""
    config = ConfigManager(args.config) if args.config else ConfigManager()
    pipeline = ETLPipeline(config)
    
    print(f"Running ETL pipeline on: {args.source}")
    
    df = pipeline.run_pipeline(
        source_path=args.source,
        table_name=args.table,
        is_directory=args.directory,
        skip_duplicates=not args.keep_duplicates,
        skip_outliers=args.remove_outliers,
        detect_anomalies=args.detect_anomalies
    )
    
    print(f"\n✓ Pipeline completed successfully!")
    print(f"✓ Processed {len(df)} rows with {len(df.columns)} columns")
    print(f"✓ Data saved to table: {args.table}")
    
    if args.detect_anomalies and 'anomalies' in df.columns:
        anomaly_count = len([v for v in df['anomalies'] if v is not None])
        print(f"✓ Anomaly detection: {anomaly_count} anomalies detected")
    
    if args.analyze:
        analyze_data(args, df, config)


def analyze_data(args, df=None, config=None):
    """Run data analysis."""
    if config is None:
        config = ConfigManager(args.config) if args.config else ConfigManager()
    
    if df is None:
        # Load from database
        from goldminer.etl import DatabaseManager
        db_path = config.get('database.path')
        db = DatabaseManager(db_path, config)
        df = db.load_dataframe(args.table)
        print(f"Loaded {len(df)} rows from table: {args.table}")
    
    analyzer = DataAnalyzer(config)
    
    print("\n" + "=" * 70)
    print("Data Analysis Report")
    print("=" * 70)
    
    # Generate summary
    summary = analyzer.generate_summary_metrics(df)
    print(f"\nOverview:")
    print(f"  Total Rows: {summary['overview']['total_rows']}")
    print(f"  Total Columns: {summary['overview']['total_columns']}")
    print(f"  Memory Usage: {summary['overview']['memory_usage_mb']:.2f} MB")
    
    # Show numeric columns stats
    if summary['numeric_columns']:
        print(f"\nNumeric Columns: {len(summary['numeric_columns'])}")
        for col, stats in summary['numeric_columns'].items():
            print(f"  {col}:")
            print(f"    Mean: {stats['mean']:.2f}, Median: {stats['50%']:.2f}")
            print(f"    Range: [{stats['min']:.2f}, {stats['max']:.2f}]")
    
    # Detect anomalies
    anomalies = analyzer.detect_anomalies(df, method='iqr')
    if anomalies:
        print(f"\nAnomalies Detected:")
        for col, anomaly_df in anomalies.items():
            print(f"  {col}: {len(anomaly_df)} anomalies found")
    else:
        print("\n✓ No anomalies detected")
    
    # Identify outliers
    outliers = analyzer.identify_outliers(df)
    if outliers:
        print(f"\nOutliers Identified:")
        for col, info in outliers.items():
            print(f"  {col}: {info['count']} outliers ({info['percentage']:.2f}%)")
    
    if args.output:
        # Save full report to JSON
        report = analyzer.generate_full_report(df)
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n✓ Full report saved to: {args.output}")


def run_forecast(args):
    """Run Monte Carlo forecasts from the unified ledger."""
    import pandas as pd

    config = ConfigManager(args.config) if args.config else ConfigManager()
    db_path = config.get('database.path')

    db = DatabaseManager(db_path, config)
    df = db.load_dataframe(args.table)

    if 'amount' not in df.columns:
        raise ValueError("Forecasting requires an 'amount' column in the ledger")

    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    df = df.dropna(subset=['amount'])

    forecaster = MonteCarloForecaster(config)
    result = forecaster.run_forecast(
        df,
        horizon_months=args.horizon,
        risk_level=args.risk,
        simulations=args.simulations,
        initial_balance=args.initial_balance,
    )

    summary_table = result.percentiles.copy()
    summary_table['table_name'] = args.table
    summary_table['run_label'] = f"{args.risk}-{args.horizon}m"
    db.save_dataframe(summary_table, args.persist_table)

    print("\nForecast complete")
    print(f"  Risk profile: {result.assumptions['risk_level']}")
    print(f"  Horizon: {result.assumptions['horizon_months']} months")
    print(f"  Simulations: {result.assumptions['simulations']}")
    print(f"  Suggested monthly savings: ${result.savings_summary['monthly_savings_capacity']}")

    if args.output:
        exporter = XLSXExporter()
        saved_path = exporter.export_forecast_results(result, args.output)
        print(f"  Excel forecast saved to: {saved_path}")


def list_tables(args):
    """List all database tables."""
    config = ConfigManager(args.config) if args.config else ConfigManager()

    db_path = config.get('database.path')
    db = DatabaseManager(db_path, config)
    tables = db.list_tables()
    
    print(f"Database: {db_path}")
    print(f"\nTables ({len(tables)}):")
    for table in tables:
        info = db.get_table_info(table)
        print(f"  • {table}: {info['row_count']} rows, {len(info['columns'])} columns")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='GoldMiner - ETL Pipeline and Data Analysis Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run pipeline on a CSV file
  python cli.py run data/raw/file.csv

  # Run pipeline on a directory
  python cli.py run data/raw/ --directory

  # Run pipeline and analyze
  python cli.py run data/raw/ --directory --analyze

  # Analyze existing data
  python cli.py analyze --table unified_data

  # List database tables
  python cli.py list

  # Save analysis report to JSON
  python cli.py analyze --table unified_data --output report.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run pipeline command
    run_parser = subparsers.add_parser('run', help='Run ETL pipeline')
    run_parser.add_argument('source', help='Path to data source (file or directory)')
    run_parser.add_argument('--directory', action='store_true', 
                           help='Treat source as directory')
    run_parser.add_argument('--table', default='unified_data',
                           help='Database table name (default: unified_data)')
    run_parser.add_argument('--keep-duplicates', action='store_true',
                           help='Keep duplicate rows')
    run_parser.add_argument('--remove-outliers', action='store_true',
                           help='Remove outliers from data')
    run_parser.add_argument('--analyze', action='store_true',
                           help='Run analysis after pipeline')
    run_parser.add_argument('--detect-anomalies', action='store_true',
                           help='Detect anomalies in transactions')
    run_parser.add_argument('--config', help='Path to config file')
    run_parser.add_argument('--output', help='Save analysis report to JSON file')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze existing data')
    analyze_parser.add_argument('--table', default='unified_data',
                               help='Database table to analyze')
    analyze_parser.add_argument('--output', help='Save report to JSON file')
    analyze_parser.add_argument('--config', help='Path to config file')

    # Forecast command
    forecast_parser = subparsers.add_parser('forecast', help='Run Monte Carlo forecast')
    forecast_parser.add_argument('--table', default='unified_data',
                                 help='Database table to forecast from')
    forecast_parser.add_argument('--horizon', type=int, help='Horizon in months (overrides config)')
    forecast_parser.add_argument('--simulations', type=int, help='Number of Monte Carlo simulations')
    forecast_parser.add_argument('--risk', default='balanced', help='Risk level (conservative|balanced|aggressive)')
    forecast_parser.add_argument('--initial-balance', type=float, default=0.0,
                                 help='Starting balance before simulations')
    forecast_parser.add_argument('--persist-table', default='forecast_results',
                                 help='Table name to persist percentile cones')
    forecast_parser.add_argument('--output', help='Path to Excel workbook with forecasts')
    forecast_parser.add_argument('--config', help='Path to config file')

    # List tables command
    list_parser = subparsers.add_parser('list', help='List database tables')
    list_parser.add_argument('--config', help='Path to config file')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        run_pipeline(args)
    elif args.command == 'analyze':
        analyze_data(args)
    elif args.command == 'forecast':
        run_forecast(args)
    elif args.command == 'list':
        list_tables(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
