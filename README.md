# GoldMiner

A robust Python ETL (Extract, Transform, Load) pipeline for data processing and analysis. GoldMiner ingests raw CSV and Excel data sources, infers schemas, normalizes fields, standardizes dates, cleans duplicates, and unifies data into a SQLite database. It includes modular ETL stages, config-driven pipelines, comprehensive logging, tests, and a lightweight analysis module providing summary metrics, trend views, and anomaly detection.

## Features

### ETL Pipeline
- **Data Ingestion**: Read CSV and Excel files from single files or entire directories
- **Schema Inference**: Automatically detect data types and infer optimal schemas
- **Data Normalization**: 
  - Normalize column names (lowercase, underscores)
  - Strip whitespace from text fields
  - Standardize date formats
  - Clean numeric values (remove currency symbols, commas)
- **Data Cleaning**:
  - Remove duplicate records
  - Handle missing values (drop, fill, forward/backward fill)
  - Detect and remove outliers (IQR and Z-score methods)
  - Clean text columns
- **Database Storage**: Store unified data in SQLite database with full CRUD operations

### Analysis Module
- **Summary Metrics**: Generate comprehensive statistics for numeric, categorical, and date columns
- **Anomaly Detection**: Identify anomalies using Z-score or IQR methods
- **Trend Analysis**: Calculate moving averages and trend directions
- **Correlation Analysis**: Generate correlation matrices for numeric data
- **Outlier Identification**: Detect and report outliers with detailed statistics
- **Full Reports**: Generate comprehensive analysis reports in one call

### Transaction Analysis Module (NEW)
- **Time-Based Aggregations**: Hourly, daily, and monthly transaction summaries
- **Spike & Drop Detection**: Identify unusual patterns in transaction data
- **Moving Averages**: Calculate trends with customizable windows (7-day, 14-day, 30-day)
- **Performance Indicators**: Comprehensive KPIs including growth rates and quartiles
- **Top Period Identification**: Find best and worst performing time periods
- **Visualization Support**: Pre-formatted data for charts and dashboards
- **Error Handling**: Robust validation for missing data and invalid formats
- **JSON Export**: Generate reports suitable for automated systems

### Configuration & Logging
- **Config-Driven**: YAML-based configuration for easy customization
- **Comprehensive Logging**: Structured logging to console and file
- **Modular Design**: Independent, reusable components

## Installation

```bash
# Clone the repository
git clone https://github.com/seifelsherbinyy/goldminer.git
cd goldminer

# Install dependencies
pip install -r requirements.txt

# Verify installation and pipeline readiness
python verify_setup.py
```

The verification script will check:
- All required dependencies are installed
- Directory structure is correct
- Configuration is valid
- All modules can be imported
- Basic pipeline functionality works
- All unit tests pass

## Quick Start

### Using the CLI

```bash
# Run pipeline on a directory
python cli.py run data/raw/ --directory --analyze

# Analyze existing data
python cli.py analyze --table unified_data

# List database tables
python cli.py list

# Save analysis report to JSON
python cli.py analyze --table unified_data --output report.json
```

### Basic Usage

```python
from goldminer.config import ConfigManager
from goldminer.etl import ETLPipeline
from goldminer.analysis import DataAnalyzer

# Initialize configuration
config = ConfigManager()

# Run ETL pipeline on a directory
pipeline = ETLPipeline(config)
df = pipeline.run_pipeline(
    source_path='data/raw',
    table_name='unified_data',
    is_directory=True,
    skip_duplicates=True
)

# Analyze the data
analyzer = DataAnalyzer(config)
report = analyzer.generate_full_report(df)
print(report)
```

### Transaction Analysis Example

```python
from goldminer.analysis import TransactionAnalyzer

# Initialize transaction analyzer
analyzer = TransactionAnalyzer(config)

# Analyze transaction data with hourly, daily, and monthly insights
report = analyzer.generate_comprehensive_report(
    df,
    value_column='amount',
    date_column='timestamp'
)

# Access specific analysis sections
print(report['hourly_analysis'])  # Peak hours and patterns
print(report['daily_analysis'])   # Daily trends and anomalies
print(report['monthly_analysis']) # Monthly performance

# Detect spikes and drops
daily_summary = analyzer.summarize_by_day(df, 'amount', 'timestamp')
anomalies = analyzer.detect_spikes_and_drops(daily_summary, 'amount_sum')
print(f"Spikes: {anomalies['spike_count']}, Drops: {anomalies['drop_count']}")
```

### Run Example Scripts

```bash
# General ETL and analysis example
python example_usage.py

# Transaction analysis demo with comprehensive examples
python transaction_analysis_demo.py
```

**example_usage.py** will:
1. Create sample data files (CSV and Excel)
2. Run the complete ETL pipeline
3. Store data in SQLite database
4. Perform comprehensive analysis
5. Display results and metrics

**transaction_analysis_demo.py** will:
1. Generate 90 days of realistic transaction data
2. Perform hourly, daily, and monthly analysis
3. Detect anomalies and identify spikes/drops
4. Calculate moving averages and trends
5. Identify top-performing periods
6. Generate JSON reports for automation
7. Create visualization-ready data
8. Demonstrate error handling capabilities

## Project Structure

```
goldminer/
├── goldminer/              # Main package
│   ├── config/            # Configuration management
│   │   └── config_manager.py
│   ├── etl/               # ETL modules
│   │   ├── ingest.py      # Data ingestion
│   │   ├── schema.py      # Schema inference
│   │   ├── normalize.py   # Data normalization
│   │   ├── clean.py       # Data cleaning
│   │   ├── database.py    # Database operations
│   │   └── pipeline.py    # Pipeline orchestrator
│   ├── analysis/          # Analysis module
│   │   ├── analyzer.py    # General data analysis
│   │   └── transaction_analyzer.py  # Transaction time-series analysis
│   └── utils/             # Utilities
│       └── logger.py      # Logging configuration
├── tests/                 # Test suite
│   └── unit/             # Unit tests (52 tests)
├── data/                  # Data directories
│   ├── raw/              # Raw data files
│   └── processed/        # Processed data and database
├── logs/                  # Log files
├── transaction_analysis_demo.py  # Transaction analysis demo
├── TRANSACTION_ANALYSIS_GUIDE.md # Comprehensive guide
├── config.yaml           # Configuration file
├── requirements.txt      # Dependencies
└── example_usage.py      # Example script
```

## Configuration

The `config.yaml` file allows you to customize:

- **Database settings**: Path and table names
- **Data sources**: Input and output directories
- **ETL options**: Date formats, normalization rules, duplicate handling
- **Analysis settings**: Anomaly detection thresholds, trend windows
- **Logging**: Log levels, formats, and file locations

Example configuration:

```yaml
database:
  path: data/processed/goldminer.db
  table_name: unified_data

etl:
  date_formats:
    - "%Y-%m-%d"
    - "%m/%d/%Y"
    - "%d-%m-%Y"
  normalization:
    strip_whitespace: true
    lowercase_columns: true

analysis:
  anomaly_detection:
    zscore_threshold: 3.0
    iqr_multiplier: 1.5
  trend_window: 7
```

## API Reference

### ETL Pipeline

#### DataIngestion
```python
from goldminer.etl import DataIngestion

ingest = DataIngestion(config)
df = ingest.read_csv('file.csv')
df = ingest.read_excel('file.xlsx')
dfs = ingest.ingest_directory('data/raw')
```

#### SchemaInference
```python
from goldminer.etl import SchemaInference

schema_inf = SchemaInference(config)
schema = schema_inf.infer_schema(df)
suggestions = schema_inf.suggest_data_types(df)
```

#### DataNormalizer
```python
from goldminer.etl import DataNormalizer

normalizer = DataNormalizer(config)
df = normalizer.normalize_dataframe(df)
df = normalizer.standardize_dates(df)
```

#### DataCleaner
```python
from goldminer.etl import DataCleaner

cleaner = DataCleaner(config)
df = cleaner.remove_duplicates(df)
df = cleaner.handle_missing_values(df, strategy='drop')
df = cleaner.remove_outliers(df, columns=['amount'])
```

#### DatabaseManager
```python
from goldminer.etl import DatabaseManager

with DatabaseManager('database.db') as db:
    db.save_dataframe(df, 'table_name')
    df = db.load_dataframe('table_name')
    tables = db.list_tables()
```

### Analysis

#### DataAnalyzer
```python
from goldminer.analysis import DataAnalyzer

analyzer = DataAnalyzer(config)
summary = analyzer.generate_summary_metrics(df)
anomalies = analyzer.detect_anomalies(df, method='iqr')
trends = analyzer.calculate_trends(df, 'amount')
report = analyzer.generate_full_report(df)
```

#### TransactionAnalyzer
```python
from goldminer.analysis import TransactionAnalyzer

analyzer = TransactionAnalyzer(config)

# Time-based aggregations
hourly = analyzer.summarize_by_hour(df, 'amount', 'timestamp')
daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
monthly = analyzer.summarize_by_month(df, 'amount', 'timestamp')

# Anomaly detection
anomalies = analyzer.detect_spikes_and_drops(daily, 'amount_sum', method='iqr')

# Trend analysis
trends = analyzer.calculate_moving_averages(daily, 'amount_sum', windows=[7, 14, 30])

# Performance indicators
indicators = analyzer.calculate_performance_indicators(df, 'amount', 'timestamp')

# Top periods
top_periods = analyzer.identify_top_periods(daily, 'amount_sum', top_n=10)

# Comprehensive report
report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')

# Visualization data
viz_data = analyzer.generate_visualization_data(df, 'amount', 'timestamp')
```

For detailed documentation on TransactionAnalyzer, see [TRANSACTION_ANALYSIS_GUIDE.md](TRANSACTION_ANALYSIS_GUIDE.md).

## Testing

Run the unit tests:

```bash
python -m unittest discover -s tests/unit -p "test_*.py" -v
```

All tests should pass, covering:
- Configuration management
- Data ingestion (CSV and Excel)
- Schema inference
- Data normalization
- Data cleaning
- Database operations
- Data analysis
- Transaction analysis (time-series)

## Use Cases

- **Financial Data Processing**: Consolidate transactions from multiple sources
- **Transaction Monitoring**: Analyze hourly, daily, and monthly transaction patterns
- **Anomaly Detection**: Identify unusual spikes and drops in business metrics
- **Data Quality Monitoring**: Detect anomalies and outliers in datasets
- **ETL Automation**: Build automated data pipelines for regular processing
- **Data Integration**: Combine and normalize data from various formats
- **Analysis & Reporting**: Generate insights and trends from processed data
- **Performance Tracking**: Monitor KPIs and identify top-performing periods

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy >= 1.24.0
- openpyxl >= 3.1.0
- pyyaml >= 6.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Author

Seif Elsherbiny
# Test change
