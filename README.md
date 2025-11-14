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

### Run Example Script

```bash
python example_usage.py
```

This will:
1. Create sample data files (CSV and Excel)
2. Run the complete ETL pipeline
3. Store data in SQLite database
4. Perform comprehensive analysis
5. Display results and metrics

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
│   │   └── analyzer.py    # Data analysis
│   └── utils/             # Utilities
│       └── logger.py      # Logging configuration
├── tests/                 # Test suite
│   └── unit/             # Unit tests
├── data/                  # Data directories
│   ├── raw/              # Raw data files
│   └── processed/        # Processed data and database
├── logs/                  # Log files
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

## Use Cases

- **Financial Data Processing**: Consolidate transactions from multiple sources
- **Data Quality Monitoring**: Detect anomalies and outliers in datasets
- **ETL Automation**: Build automated data pipelines for regular processing
- **Data Integration**: Combine and normalize data from various formats
- **Analysis & Reporting**: Generate insights and trends from processed data

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
