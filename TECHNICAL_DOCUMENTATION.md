# Transaction Analysis Module - Technical Documentation

## Module Overview

The Transaction Analysis Module (`transaction_analyzer.py`) is a comprehensive Python-based solution for analyzing time-series transaction data. It provides scalable, modular analytical workflows capable of handling large volumes of entries while providing clear insights into patterns, anomalies, and performance indicators.

## Architecture

### Class: TransactionAnalyzer

**Purpose**: Provides comprehensive transaction analysis capabilities for time-series data.

**Key Features**:
- Time-based aggregations (hourly, daily, monthly)
- Anomaly detection (spikes and drops)
- Trend analysis with moving averages
- Performance indicator calculation
- Top-performing period identification
- Visualization data generation

### Design Principles

1. **Modularity**: Each method is independent and can be used separately
2. **Scalability**: Efficient pandas operations for large datasets
3. **Error Handling**: Comprehensive validation and graceful degradation
4. **Configurability**: Supports both config-driven and programmatic usage
5. **Integration**: Works seamlessly with GoldMiner ETL pipeline

## How Each Part Works

### 1. DataFrame Validation (`validate_dataframe`)

**Purpose**: Validates input data and ensures date column is properly formatted.

**Process**:
1. Checks if DataFrame is empty
2. Auto-detects date column if not specified
3. Converts date column to datetime type
4. Removes rows with invalid dates
5. Returns validated DataFrame and date column name

**Error Handling**:
- Raises `ValueError` for empty DataFrames
- Raises `ValueError` if no valid date column found
- Logs warnings for removed rows

### 2. Time-Based Aggregations

#### Hourly Summary (`summarize_by_hour`)

**Purpose**: Aggregate transactions by hour of day (0-23).

**Process**:
1. Validates DataFrame
2. Extracts hour from timestamp
3. Groups by hour and applies aggregation
4. Creates result with all 24 hours (fills missing hours with 0)
5. Adds transaction count

**Use Cases**:
- Identify peak business hours
- Optimize staffing schedules
- Detect hourly patterns

#### Daily Summary (`summarize_by_day`)

**Purpose**: Aggregate transactions by calendar day.

**Process**:
1. Validates DataFrame
2. Extracts date (without time)
3. Groups by date and applies aggregation
4. Adds day of week for pattern analysis
5. Sorts by date

**Use Cases**:
- Track daily performance
- Identify weekly patterns
- Detect weekend vs weekday differences

#### Monthly Summary (`summarize_by_month`)

**Purpose**: Aggregate transactions by month.

**Process**:
1. Validates DataFrame
2. Extracts year and month
3. Groups by year-month and applies aggregation
4. Adds month name and additional metrics
5. Sorts chronologically

**Use Cases**:
- Long-term trend analysis
- Seasonal pattern detection
- Year-over-year comparisons

### 3. Anomaly Detection (`detect_spikes_and_drops`)

**Purpose**: Identify unusual spikes or drops in transaction values.

**Methods Available**:

#### Z-Score Method
- Calculates standard deviations from mean
- Identifies values beyond threshold (default: 3.0)
- Best for normally distributed data

#### IQR (Interquartile Range) Method
- Uses quartiles to define normal range
- More robust to outliers
- Better for skewed distributions

**Process**:
1. Calculates threshold based on method
2. Identifies anomalies (spikes and drops)
3. Returns detailed information about each anomaly
4. Includes context (date, value, etc.)

**Use Cases**:
- Fraud detection
- System failure detection
- Unusual activity monitoring

### 4. Moving Averages (`calculate_moving_averages`)

**Purpose**: Calculate trends using moving averages.

**Process**:
1. Calculates rolling averages for specified windows
2. Computes percentage change
3. Preserves original data
4. Handles edge cases (insufficient data)

**Default Windows**: 7-day, 14-day, 30-day

**Use Cases**:
- Trend identification
- Smoothing noisy data
- Forecasting preparation

### 5. Performance Indicators (`calculate_performance_indicators`)

**Purpose**: Calculate comprehensive statistical metrics.

**Metrics Included**:
- Total transactions and value
- Average and median
- Standard deviation and coefficient of variation
- Min, max, and range
- Quartiles (Q1, Q2, Q3)
- Date range
- Growth rate (first to last value)

**Use Cases**:
- Executive dashboards
- KPI tracking
- Performance comparison

### 6. Top Period Identification (`identify_top_periods`)

**Purpose**: Find best and worst performing periods.

**Process**:
1. Sorts data by value
2. Extracts top N periods
3. Optionally includes bottom performers
4. Returns detailed information for each period

**Use Cases**:
- Best practice identification
- Problem period analysis
- Benchmarking

### 7. Comprehensive Report (`generate_comprehensive_report`)

**Purpose**: Generate complete analysis in one call.

**Sections**:
- Overview: Overall metrics and statistics
- Hourly Analysis: Peak hours and patterns
- Daily Analysis: Daily trends, anomalies, and top days
- Monthly Analysis: Monthly summaries and patterns

**Process**:
1. Calculates performance indicators
2. Performs hourly analysis
3. Performs daily analysis with trends and anomalies
4. Performs monthly analysis with trends
5. Compiles everything into structured report

**Error Handling**:
- Each section has try-except blocks
- Failures in one section don't affect others
- Errors logged with details

### 8. Visualization Data (`generate_visualization_data`)

**Purpose**: Generate data formatted for charts and graphs.

**Output Format**:
```json
{
  "time_series": {
    "dates": [...],
    "values": [...],
    "moving_average_7": [...]
  },
  "hourly_distribution": {
    "hours": [0-23],
    "values": [...]
  },
  "monthly_trends": {
    "months": [...],
    "values": [...],
    "transaction_counts": [...]
  }
}
```

**Use Cases**:
- Dashboard integration
- Report visualization
- Interactive charts

## Integration into Larger Systems

### Automated Workflow Integration

```python
# Example: Daily automated analysis
from goldminer.analysis import TransactionAnalyzer
from goldminer.etl import ETLPipeline
import schedule
import time

def daily_analysis():
    # Load yesterday's transactions
    pipeline = ETLPipeline(config)
    df = pipeline.run_pipeline('transactions.csv')
    
    # Analyze
    analyzer = TransactionAnalyzer(config)
    report = analyzer.generate_comprehensive_report(df, 'amount', 'timestamp')
    
    # Save and notify
    save_report(report)
    send_notification(report)

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(daily_analysis)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Real-Time Monitoring

```python
# Example: Real-time anomaly detection
def monitor_transactions(stream):
    analyzer = TransactionAnalyzer()
    window_size = 100  # Last 100 transactions
    
    for transaction in stream:
        # Accumulate transactions
        buffer.append(transaction)
        
        if len(buffer) >= window_size:
            df = pd.DataFrame(buffer[-window_size:])
            
            # Check for anomalies
            daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
            anomalies = analyzer.detect_spikes_and_drops(daily, 'amount_sum')
            
            if anomalies['spike_count'] > 0:
                alert_team(anomalies)
```

### Dashboard Integration

```python
# Example: Dashboard data endpoint
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/transaction-analysis')
def get_analysis():
    # Load data
    df = load_transactions()
    
    # Analyze
    analyzer = TransactionAnalyzer()
    viz_data = analyzer.generate_visualization_data(df, 'amount', 'timestamp')
    
    return jsonify(viz_data)
```

## Optional Extensions

### 1. Forecasting Models

```python
# Extension: Add ARIMA forecasting
from statsmodels.tsa.arima.model import ARIMA

class ExtendedTransactionAnalyzer(TransactionAnalyzer):
    def forecast_next_periods(self, df, value_column, periods=7):
        """Forecast next N periods using ARIMA."""
        daily = self.summarize_by_day(df, value_column, 'timestamp')
        values = daily[f'{value_column}_sum'].values
        
        model = ARIMA(values, order=(5,1,0))
        model_fit = model.fit()
        forecast = model_fit.forecast(steps=periods)
        
        return forecast
```

### 2. Seasonality Detection

```python
# Extension: Detect seasonal patterns
from statsmodels.tsa.seasonal import seasonal_decompose

class SeasonalAnalyzer(TransactionAnalyzer):
    def detect_seasonality(self, df, value_column, period=7):
        """Detect seasonal patterns in data."""
        daily = self.summarize_by_day(df, value_column, 'timestamp')
        daily = daily.set_index('date')
        
        decomposition = seasonal_decompose(
            daily[f'{value_column}_sum'],
            model='additive',
            period=period
        )
        
        return {
            'trend': decomposition.trend,
            'seasonal': decomposition.seasonal,
            'residual': decomposition.resid
        }
```

### 3. User-Defined Filters

```python
# Extension: Add custom filters
class FilterableAnalyzer(TransactionAnalyzer):
    def analyze_with_filters(self, df, value_column, filters):
        """Apply custom filters before analysis."""
        filtered_df = df.copy()
        
        for filter_func in filters:
            filtered_df = filter_func(filtered_df)
        
        return self.generate_comprehensive_report(
            filtered_df, value_column, 'timestamp'
        )

# Usage
def high_value_filter(df):
    return df[df['amount'] > 1000]

def weekday_filter(df):
    df['day'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    return df[df['day'] < 5]

analyzer = FilterableAnalyzer()
report = analyzer.analyze_with_filters(
    df, 'amount', 
    [high_value_filter, weekday_filter]
)
```

### 4. Interactive Dashboard

```python
# Extension: Create interactive dashboard with Streamlit
import streamlit as st

def create_dashboard(df):
    st.title("Transaction Analysis Dashboard")
    
    analyzer = TransactionAnalyzer()
    
    # Sidebar filters
    date_range = st.sidebar.date_input("Date Range", [df['timestamp'].min(), df['timestamp'].max()])
    
    # Filter data
    mask = (df['timestamp'] >= date_range[0]) & (df['timestamp'] <= date_range[1])
    filtered_df = df[mask]
    
    # Display metrics
    indicators = analyzer.calculate_performance_indicators(filtered_df, 'amount', 'timestamp')
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions", indicators['total_transactions'])
    col2.metric("Total Value", f"${indicators['total_value']:,.2f}")
    col3.metric("Avg Transaction", f"${indicators['average_value']:.2f}")
    
    # Charts
    viz_data = analyzer.generate_visualization_data(filtered_df, 'amount', 'timestamp')
    
    st.line_chart(pd.DataFrame({
        'Date': viz_data['time_series']['dates'],
        'Value': viz_data['time_series']['values']
    }).set_index('Date'))
```

## Performance Optimization

### For Large Datasets

1. **Chunk Processing**
   ```python
   chunk_size = 100000
   results = []
   for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
       result = analyzer.summarize_by_day(chunk, 'amount', 'timestamp')
       results.append(result)
   final_result = pd.concat(results).groupby('date').sum()
   ```

2. **Parallel Processing**
   ```python
   from multiprocessing import Pool
   
   def process_chunk(chunk):
       analyzer = TransactionAnalyzer()
       return analyzer.summarize_by_day(chunk, 'amount', 'timestamp')
   
   with Pool() as pool:
       results = pool.map(process_chunk, chunks)
   ```

3. **Memory Optimization**
   ```python
   # Use appropriate dtypes
   df['timestamp'] = pd.to_datetime(df['timestamp'])
   df['amount'] = df['amount'].astype('float32')  # Use float32 instead of float64
   ```

## Best Practices for Beginners

1. **Start Simple**: Use basic aggregations first
2. **Validate Early**: Always validate data before analysis
3. **Handle Errors**: Use try-except blocks
4. **Document**: Add comments for complex logic
5. **Test Thoroughly**: Test with edge cases

## Best Practices for Advanced Users

1. **Optimize**: Profile code and optimize bottlenecks
2. **Extend**: Create custom analyzers for specific needs
3. **Integrate**: Build automated workflows
4. **Monitor**: Set up alerting systems
5. **Scale**: Use distributed processing for very large datasets

## Troubleshooting Guide

### Issue: Performance degradation with large datasets
**Solution**: Use chunk processing or downsample data

### Issue: Memory errors
**Solution**: Process data in batches, optimize dtypes

### Issue: Incorrect anomaly detection
**Solution**: Adjust thresholds, try different methods

### Issue: Missing time periods in aggregations
**Solution**: Use forward fill or interpolation to fill gaps

## Summary

The Transaction Analysis Module provides a complete, production-ready solution for analyzing transaction data at multiple time granularities. Its modular design, comprehensive error handling, and extensibility make it suitable for both beginners learning data analysis and advanced users building automated systems.

Key strengths:
- ✅ Clean, well-commented code
- ✅ Comprehensive error handling
- ✅ Modular, reusable components
- ✅ Easy integration with larger systems
- ✅ Extensible architecture
- ✅ Beginner and expert friendly
- ✅ Production-ready quality
