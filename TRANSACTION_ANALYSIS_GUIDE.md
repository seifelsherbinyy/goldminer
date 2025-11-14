# Transaction Analysis Module - Comprehensive Guide

## Overview

The Transaction Analysis Module is a powerful, scalable analytical workflow designed to analyze transaction datasets with hourly, daily, and monthly information. It provides clear insights into patterns, anomalies, and performance indicators while maintaining clean, well-commented code optimized for both beginners and advanced users.

## Features

### Core Capabilities

1. **Time-Based Aggregations**
   - Hourly transaction summaries
   - Daily transaction summaries
   - Monthly transaction summaries
   - Multiple aggregation methods (sum, mean, count, min, max)

2. **Anomaly Detection**
   - Detect unusual spikes in transaction values
   - Identify unexpected drops in activity
   - Two methods: Z-score and IQR (Interquartile Range)
   - Configurable thresholds

3. **Trend Analysis**
   - Moving averages (7-day, 14-day, 30-day, custom)
   - Percentage change tracking
   - Growth rate calculation
   - Trend direction indicators

4. **Performance Metrics**
   - Comprehensive statistical indicators
   - Top-performing periods identification
   - Quartile analysis
   - Coefficient of variation
   - Date range analysis

5. **Error Handling**
   - Missing data handling
   - Invalid date format detection
   - Empty dataset validation
   - Column existence verification
   - Graceful degradation

6. **Visualization Support**
   - Pre-formatted data for charts and graphs
   - Time series data export
   - Hourly distribution data
   - Monthly trend data
   - JSON export for dashboard integration

## Installation & Setup

### Prerequisites

```bash
# Required dependencies (already in requirements.txt)
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
```

### Import

```python
from goldminer.analysis import TransactionAnalyzer
from goldminer.config import ConfigManager
```

## Quick Start

### Basic Usage

```python
import pandas as pd
from goldminer.analysis import TransactionAnalyzer

# Initialize analyzer
analyzer = TransactionAnalyzer()

# Load your transaction data
df = pd.read_csv('transactions.csv')
# Ensure you have columns: 'timestamp' (datetime) and 'amount' (numeric)

# Generate hourly summary
hourly_summary = analyzer.summarize_by_hour(
    df, 
    value_column='amount',
    date_column='timestamp'
)

# Generate daily summary with trends
daily_summary = analyzer.summarize_by_day(df, 'amount', 'timestamp')
daily_with_trends = analyzer.calculate_moving_averages(
    daily_summary, 
    'amount_sum',
    windows=[7, 14, 30]
)

# Detect anomalies
anomalies = analyzer.detect_spikes_and_drops(
    daily_summary, 
    'amount_sum',
    method='iqr'
)

print(f"Spikes detected: {anomalies['spike_count']}")
print(f"Drops detected: {anomalies['drop_count']}")
```

### Comprehensive Analysis

```python
# Generate full analysis report
report = analyzer.generate_comprehensive_report(
    df,
    value_column='amount',
    date_column='timestamp'
)

# Access different sections
print(report['overview'])  # Overall metrics
print(report['hourly_analysis'])  # Hourly patterns
print(report['daily_analysis'])  # Daily trends and anomalies
print(report['monthly_analysis'])  # Monthly summaries

# Save to JSON
import json
with open('analysis_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)
```

## API Reference

### TransactionAnalyzer Class

#### `__init__(config=None)`

Initialize the analyzer with optional configuration.

**Parameters:**
- `config` (ConfigManager, optional): Configuration manager instance

**Example:**
```python
from goldminer.config import ConfigManager

config = ConfigManager('config.yaml')
analyzer = TransactionAnalyzer(config)
```

#### `validate_dataframe(df, date_column=None)`

Validate and prepare DataFrame for analysis.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `date_column` (str, optional): Date column name (auto-detected if None)

**Returns:**
- Tuple of (validated DataFrame, date column name)

**Raises:**
- `ValueError`: If DataFrame is empty or no valid date column found

**Example:**
```python
validated_df, date_col = analyzer.validate_dataframe(df, 'timestamp')
```

#### `summarize_by_hour(df, value_column, date_column=None, aggregation='sum')`

Summarize transactions by hour of day (0-23).

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column
- `aggregation` (str): Aggregation method ('sum', 'mean', 'count', 'min', 'max')

**Returns:**
- DataFrame with hourly summaries (24 rows, one per hour)

**Example:**
```python
hourly = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='sum')
peak_hour = hourly.loc[hourly['amount_sum'].idxmax(), 'hour']
print(f"Peak hour: {peak_hour}")
```

#### `summarize_by_day(df, value_column, date_column=None, aggregation='sum')`

Summarize transactions by day.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column
- `aggregation` (str): Aggregation method

**Returns:**
- DataFrame with daily summaries including day of week

**Example:**
```python
daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
# Access columns: 'date', 'amount_sum', 'transaction_count', 'day_of_week'
```

#### `summarize_by_month(df, value_column, date_column=None, aggregation='sum')`

Summarize transactions by month.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column
- `aggregation` (str): Aggregation method

**Returns:**
- DataFrame with monthly summaries

**Example:**
```python
monthly = analyzer.summarize_by_month(df, 'amount', 'timestamp')
# Access columns: 'year_month', 'amount_sum', 'transaction_count', 'month_name'
```

#### `detect_spikes_and_drops(df, value_column, threshold=None, method='zscore')`

Detect unusual spikes or drops in values.

**Parameters:**
- `df` (pd.DataFrame): Aggregated DataFrame (e.g., daily summary)
- `value_column` (str): Column to analyze
- `threshold` (float, optional): Detection threshold (uses defaults if None)
- `method` (str): Detection method ('zscore' or 'iqr')

**Returns:**
- Dictionary containing spike and drop information

**Example:**
```python
daily_summary = analyzer.summarize_by_day(df, 'amount', 'timestamp')
anomalies = analyzer.detect_spikes_and_drops(daily_summary, 'amount_sum', method='iqr')

for spike in anomalies['spikes']:
    print(f"Spike on {spike['date']}: ${spike['value']:,.2f}")
```

#### `calculate_moving_averages(df, value_column, windows=None)`

Calculate moving averages for different window sizes.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame (sorted by time)
- `value_column` (str): Column containing values
- `windows` (list, optional): Window sizes (default: [7, 14, 30])

**Returns:**
- DataFrame with moving averages added

**Example:**
```python
daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
with_trends = analyzer.calculate_moving_averages(daily, 'amount_sum', windows=[7, 14, 30])
# New columns: 'amount_sum_ma7', 'amount_sum_ma14', 'amount_sum_ma30', 'amount_sum_pct_change'
```

#### `identify_top_periods(df, value_column, top_n=10, period_type='all')`

Identify top-performing periods.

**Parameters:**
- `df` (pd.DataFrame): Aggregated DataFrame
- `value_column` (str): Column containing values
- `top_n` (int): Number of top periods to return
- `period_type` (str): 'all', 'positive', or 'negative'

**Returns:**
- Dictionary with top and bottom performers

**Example:**
```python
daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
top_periods = analyzer.identify_top_periods(daily, 'amount_sum', top_n=10)

for period in top_periods['top_performers']:
    print(f"{period['date']}: ${period['value']:,.2f}")
```

#### `calculate_performance_indicators(df, value_column, date_column=None)`

Calculate comprehensive performance indicators.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column

**Returns:**
- Dictionary with performance metrics

**Example:**
```python
indicators = analyzer.calculate_performance_indicators(df, 'amount', 'timestamp')
print(f"Total transactions: {indicators['total_transactions']}")
print(f"Average value: ${indicators['average_value']:.2f}")
print(f"Growth rate: {indicators['growth_rate']:.2f}%")
```

#### `generate_comprehensive_report(df, value_column, date_column=None)`

Generate a complete analysis report.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column

**Returns:**
- Dictionary containing full analysis report

**Report Sections:**
- `overview`: Overall metrics and statistics
- `hourly_analysis`: Hourly patterns and peak times
- `daily_analysis`: Daily summaries, trends, and anomalies
- `monthly_analysis`: Monthly summaries and patterns

**Example:**
```python
report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')

# Save to JSON
import json
with open('report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)
```

#### `generate_visualization_data(df, value_column, date_column=None)`

Generate data formatted for visualization.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame
- `value_column` (str): Column containing transaction values
- `date_column` (str, optional): Date/timestamp column

**Returns:**
- Dictionary with visualization-ready data

**Example:**
```python
viz_data = analyzer.generate_visualization_data(df, 'amount', 'timestamp')

# Use for charts
dates = viz_data['time_series']['dates']
values = viz_data['time_series']['values']
ma7 = viz_data['time_series']['moving_average_7']
```

## Configuration

### YAML Configuration

Add to your `config.yaml`:

```yaml
analysis:
  anomaly_detection:
    zscore_threshold: 3.0    # Z-score threshold for anomalies
    iqr_multiplier: 1.5      # IQR multiplier for anomalies
  trend_window: 7            # Default window for trends
```

### Programmatic Configuration

```python
from goldminer.config import ConfigManager

config = ConfigManager()
config.set('analysis.anomaly_detection.zscore_threshold', 2.5)
config.set('analysis.trend_window', 14)

analyzer = TransactionAnalyzer(config)
```

## Use Cases & Examples

### Financial Transaction Monitoring

```python
# Load transaction data
df = pd.read_csv('financial_transactions.csv')

# Analyze daily patterns
daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
anomalies = analyzer.detect_spikes_and_drops(daily, 'amount_sum', method='iqr')

# Alert on anomalies
if anomalies['spike_count'] > 0:
    print("⚠️ Unusual activity detected!")
    for spike in anomalies['spikes']:
        print(f"  Spike on {spike['date']}: ${spike['value']:,.2f}")
```

### E-commerce Sales Analysis

```python
# Identify peak shopping hours
hourly = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='sum')
peak_hour = hourly.loc[hourly['amount_sum'].idxmax(), 'hour']
print(f"Peak shopping hour: {peak_hour}:00")

# Find best-performing months
monthly = analyzer.summarize_by_month(df, 'amount', 'timestamp')
top_months = analyzer.identify_top_periods(monthly, 'amount_sum', top_n=3)
```

### Business Performance Tracking

```python
# Calculate KPIs
indicators = analyzer.calculate_performance_indicators(df, 'amount', 'timestamp')

print(f"Total Revenue: ${indicators['total_value']:,.2f}")
print(f"Growth Rate: {indicators['growth_rate']:.2f}%")
print(f"Avg Transaction: ${indicators['average_value']:.2f}")
```

### Automated Reporting

```python
# Generate and email daily report
report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')

with open('daily_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)

# Send report via email (pseudo-code)
# send_email(to='team@company.com', attachment='daily_report.json')
```

## Integration with GoldMiner ETL

```python
from goldminer.config import ConfigManager
from goldminer.etl import ETLPipeline
from goldminer.analysis import TransactionAnalyzer

# Run ETL pipeline
config = ConfigManager()
pipeline = ETLPipeline(config)
df = pipeline.run_pipeline('data/transactions.csv', table_name='transactions')

# Analyze processed data
analyzer = TransactionAnalyzer(config)
report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')

# Save results
import json
with open('analysis_report.json', 'w') as f:
    json.dump(report, f, indent=2, default=str)
```

## Error Handling Best Practices

```python
import pandas as pd
from goldminer.analysis import TransactionAnalyzer

analyzer = TransactionAnalyzer()

try:
    # Validate data first
    df, date_col = analyzer.validate_dataframe(df, 'timestamp')
    
    # Check for required columns
    if 'amount' not in df.columns:
        raise ValueError("Missing 'amount' column")
    
    # Perform analysis
    report = analyzer.generate_comprehensive_report(df, 'amount', date_col)
    
except ValueError as e:
    print(f"Data validation error: {e}")
except Exception as e:
    print(f"Analysis error: {e}")
```

## Performance Optimization Tips

1. **For Large Datasets**
   ```python
   # Process in chunks
   chunk_size = 100000
   for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
       daily = analyzer.summarize_by_day(chunk, 'amount', 'timestamp')
       # Process each chunk
   ```

2. **Pre-filter Data**
   ```python
   # Filter to relevant date range first
   df_filtered = df[df['timestamp'] >= '2024-01-01']
   report = analyzer.generate_comprehensive_report(df_filtered, 'amount', 'timestamp')
   ```

3. **Use Appropriate Aggregations**
   ```python
   # For large hourly data, aggregate to daily first
   daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
   # Then analyze daily data
   anomalies = analyzer.detect_spikes_and_drops(daily, 'amount_sum')
   ```

## Extensions & Customization

### Custom Aggregation Functions

```python
# Extend the analyzer for custom metrics
class CustomTransactionAnalyzer(TransactionAnalyzer):
    def calculate_custom_metric(self, df, value_column):
        # Your custom logic here
        return df[value_column].custom_calculation()
```

### Adding New Visualization Formats

```python
# Add custom visualization data format
viz_data = analyzer.generate_visualization_data(df, 'amount', 'timestamp')

# Convert to your preferred format (e.g., Plotly, Matplotlib)
import plotly.graph_objects as go

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=viz_data['time_series']['dates'],
    y=viz_data['time_series']['values'],
    mode='lines',
    name='Transaction Value'
))
fig.show()
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover -s tests/unit -p "test_*.py" -v

# Run only transaction analyzer tests
python -m unittest tests.unit.test_transaction_analyzer -v
```

## Demo Script

Run the comprehensive demo:

```bash
python transaction_analysis_demo.py
```

This will:
1. Generate sample transaction data (90 days)
2. Perform hourly, daily, and monthly analysis
3. Detect anomalies and spikes
4. Calculate trends and moving averages
5. Identify top-performing periods
6. Generate comprehensive reports
7. Create visualization data
8. Demonstrate error handling

## Troubleshooting

### Common Issues

**Issue: "Date column not found"**
```python
# Solution: Explicitly specify the date column
df, date_col = analyzer.validate_dataframe(df, date_column='transaction_date')
```

**Issue: "All dates are invalid"**
```python
# Solution: Convert string dates to datetime first
df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M:%S')
```

**Issue: "No anomalies detected despite visible spikes"**
```python
# Solution: Adjust threshold or use different method
anomalies = analyzer.detect_spikes_and_drops(
    daily_summary, 
    'amount_sum',
    threshold=2.0,  # Lower threshold
    method='iqr'    # Try IQR instead of zscore
)
```

## Best Practices

1. **Always validate data first**
   ```python
   df, date_col = analyzer.validate_dataframe(df)
   ```

2. **Handle missing values before analysis**
   ```python
   df = df.dropna(subset=['amount', 'timestamp'])
   ```

3. **Use appropriate time granularity**
   - Use hourly for intraday patterns
   - Use daily for weekly/monthly trends
   - Use monthly for long-term trends

4. **Choose the right anomaly detection method**
   - Z-score: When data is normally distributed
   - IQR: More robust to outliers and non-normal distributions

5. **Save reports for audit trail**
   ```python
   report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')
   filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
   with open(filename, 'w') as f:
       json.dump(report, f, indent=2, default=str)
   ```

## Support & Contributing

For issues, feature requests, or contributions, please refer to the main GoldMiner repository documentation.

## License

This module is part of the GoldMiner project and is available under the MIT License.
