# Anomaly Detector Guide

## Overview

The `AnomalyDetector` class identifies unusual patterns in transaction data using three configurable detection rules. It's designed to integrate seamlessly into the GoldMiner ETL pipeline for real-time transaction monitoring.

## Features

### Detection Rules

1. **High Value Anomaly** (`high_value`)
   - Detects transactions with amounts above the user's historical percentile
   - Default: 90th percentile
   - Requires minimum 10 historical transactions for reliable detection
   - Uses pandas efficient percentile calculation

2. **Burst Frequency Anomaly** (`burst_frequency`)
   - Detects when the same merchant is used too frequently
   - Default: ≥ 3 transactions within 24 hours
   - Uses time-window based analysis
   - Case-insensitive merchant matching

3. **Unknown Merchant Anomaly** (`unknown_merchant`)
   - Detects transactions to merchants not seen in recent history
   - Default: Checks last 100 transactions
   - Case-insensitive matching
   - Configurable history window

## Installation

The AnomalyDetector is included in GoldMiner. Make sure you have installed all dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Configure detection thresholds in `anomaly_config.yaml`:

```yaml
anomaly_detection:
  high_value:
    percentile: 90  # Detect amounts above 90th percentile
    min_history_transactions: 10  # Minimum history needed
  
  burst_frequency:
    count_threshold: 3  # Number of transactions to trigger
    time_window_hours: 24  # Time window in hours
  
  unknown_merchant:
    history_window: 100  # Look back at last N transactions
  
  enabled_rules:
    - high_value
    - burst_frequency
    - unknown_merchant
  
  caching:
    enabled: true
    max_cache_size: 1000
```

## Usage

### Basic Usage

```python
from goldminer.analysis import AnomalyDetector

# Initialize detector
detector = AnomalyDetector()

# Prepare transaction and history
transaction = {
    'amount': 1500,
    'payee': 'New Store',
    'date': '2024-01-15'
}

history = [
    {'amount': 50, 'payee': 'Coffee Shop', 'date': '2024-01-01'},
    {'amount': 60, 'payee': 'Restaurant', 'date': '2024-01-02'},
    # ... more historical transactions
]

# Detect anomalies
anomalies = detector.detect_anomalies(transaction, history)
print(f"Anomalies detected: {anomalies}")
# Output: ['high_value', 'unknown_merchant']
```

### Batch Processing

```python
# Process multiple transactions at once
transactions = [
    {'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'},
    {'amount': 60, 'payee': 'Merchant B', 'date': '2024-01-02'},
    {'amount': 500, 'payee': 'Merchant C', 'date': '2024-01-03'},
]

# Each transaction is checked against all previous ones
results = detector.detect_anomalies_batch(transactions)

for idx, anomaly_list in results.items():
    print(f"Transaction {idx}: {anomaly_list}")
```

### Generate Comprehensive Report

```python
# Generate detailed report
report = detector.generate_report(transactions)

print(f"Total transactions: {report['total_transactions']}")
print(f"Anomalies detected: {report['total_anomalies_detected']}")
print(f"Anomaly rate: {report['anomaly_rate']:.2%}")
print(f"Breakdown: {report['anomaly_counts']}")
```

### Integration with ETL Pipeline

```python
from goldminer.etl import ETLPipeline
from goldminer.config import ConfigManager

# Initialize pipeline
config = ConfigManager()
pipeline = ETLPipeline(config)

# Run pipeline with anomaly detection enabled
df = pipeline.run_pipeline(
    source_path='data/raw/transactions.csv',
    table_name='transactions',
    detect_anomalies=True  # Enable anomaly detection
)

# Check results
if 'anomalies' in df.columns:
    anomaly_rows = df[df['anomalies'].notna()]
    print(f"Detected {len(anomaly_rows)} anomalous transactions")
```

### Using the CLI

```bash
# Run pipeline with anomaly detection
python cli.py run data/raw/transactions.csv --detect-anomalies

# Run on directory with anomaly detection and analysis
python cli.py run data/raw/ --directory --detect-anomalies --analyze
```

## Field Name Mapping

The detector automatically handles various field naming conventions:

| Standard Field | Alternative Names |
|---------------|------------------|
| `amount` | `Amount`, `transaction_amount`, `value` |
| `payee` | `Payee`, `merchant`, `Merchant`, `description` |
| `date` | `Date`, `transaction_date`, `timestamp`, `Timestamp` |

## Date Format Support

The detector supports multiple date formats:
- `YYYY-MM-DD` (e.g., `2024-01-15`)
- `YYYY-MM-DD HH:MM:SS` (e.g., `2024-01-15 10:30:00`)
- `YYYY/MM/DD`
- `DD/MM/YYYY`
- `MM/DD/YYYY`
- `YYYY-MM-DDTHH:MM:SS` (ISO 8601)
- `YYYY-MM-DDTHH:MM:SS.ffffff` (with microseconds)

## Performance Considerations

### Efficient Percentile Calculation
- Uses pandas vectorized operations for percentile calculations
- Avoids repeated calculations through efficient data structures

### Batch Processing
- Process multiple transactions in a single call
- Reduces overhead for large datasets

### Caching (Optional)
- Enable caching in configuration for repeated queries
- Configurable cache size limit

### Memory Usage
- Efficient memory usage through pandas DataFrames
- Handles large transaction histories (tested with 10,000+ transactions)

## Examples

### Example 1: High Value Detection

```python
detector = AnomalyDetector()

# Historical transactions: $10 to $100
history = [
    {'amount': i * 10, 'payee': 'Store', 'date': '2024-01-01'}
    for i in range(1, 11)
]

# Test transaction: $150 (above 90th percentile)
transaction = {'amount': 150, 'payee': 'Store', 'date': '2024-01-15'}
anomalies = detector.detect_anomalies(transaction, history)
# Output: ['high_value']
```

### Example 2: Burst Frequency Detection

```python
from datetime import datetime, timedelta

detector = AnomalyDetector()
base_time = datetime(2024, 1, 15, 10, 0, 0)

# Two recent transactions to same merchant
history = [
    {
        'amount': 50,
        'payee': 'Coffee Shop',
        'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
    },
    {
        'amount': 50,
        'payee': 'Coffee Shop',
        'date': (base_time - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
    }
]

# Third transaction (triggers burst)
transaction = {
    'amount': 50,
    'payee': 'Coffee Shop',
    'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
}
anomalies = detector.detect_anomalies(transaction, history)
# Output: ['burst_frequency']
```

### Example 3: Unknown Merchant Detection

```python
detector = AnomalyDetector()

# Known merchants
history = [
    {'amount': 50, 'payee': 'Coffee Shop', 'date': '2024-01-01'},
    {'amount': 60, 'payee': 'Restaurant ABC', 'date': '2024-01-02'},
]

# Unknown merchant
transaction = {'amount': 100, 'payee': 'New Store', 'date': '2024-01-15'}
anomalies = detector.detect_anomalies(transaction, history)
# Output: ['unknown_merchant']
```

### Example 4: Multiple Anomalies

```python
detector = AnomalyDetector()

history = [
    {'amount': i * 10, 'payee': 'Regular Store', 'date': '2024-01-01'}
    for i in range(1, 11)
]

# Transaction with multiple issues
transaction = {
    'amount': 500,  # High value
    'payee': 'Suspicious Store',  # Unknown merchant
    'date': '2024-01-15'
}
anomalies = detector.detect_anomalies(transaction, history)
# Output: ['high_value', 'unknown_merchant']
```

## Testing

Run the test suite:

```bash
# Run all anomaly detector tests
python -m unittest tests.unit.test_anomaly_detector -v

# Run all tests
python -m unittest discover tests -v
```

Run the demonstration script:

```bash
python anomaly_detector_demo.py
```

## Error Handling

The detector includes robust error handling:

- **Invalid transaction format**: Returns empty list, logs warning
- **Missing required fields**: Skips that specific detection rule
- **Insufficient history**: Returns no anomaly for rules requiring minimum data
- **Date parsing errors**: Logs warning, continues with other rules
- **Exception during detection**: Logs error, returns partial results

## Custom Configuration

Create a custom configuration file:

```python
# Load custom config
detector = AnomalyDetector(config_path='custom_anomaly_config.yaml')
```

Example custom configuration:

```yaml
anomaly_detection:
  high_value:
    percentile: 95  # More strict: 95th percentile
    min_history_transactions: 20  # Require more history
  
  burst_frequency:
    count_threshold: 5  # Require 5 transactions
    time_window_hours: 12  # Within 12 hours
  
  unknown_merchant:
    history_window: 50  # Check last 50 only
  
  enabled_rules:
    - high_value  # Only enable high_value detection
```

## Best Practices

1. **Minimum History**: Ensure sufficient transaction history for accurate percentile calculation (minimum 10 transactions recommended)

2. **Time Zones**: Use consistent time zones across all date fields to avoid false positives in burst detection

3. **Merchant Naming**: Normalize merchant names in your data source for better matching (the detector handles basic case normalization)

4. **Thresholds**: Tune thresholds based on your specific use case and false positive rate

5. **Performance**: Use batch processing for large datasets instead of single transaction detection

6. **Integration**: Enable anomaly detection selectively based on data volume and processing requirements

## Limitations

- **Sequential Processing**: Batch processing treats transactions sequentially (transaction N uses transactions 0 to N-1 as history)
- **Merchant Matching**: Basic string matching; doesn't handle merchant aliases or variations
- **Time Windows**: Fixed time windows; doesn't account for patterns like weekly cycles
- **Single User**: Designed for single-user transaction history; multi-user scenarios require separate processing

## API Reference

### AnomalyDetector Class

#### `__init__(config_path: Optional[str] = None)`
Initialize the detector with optional custom configuration.

#### `detect_anomalies(transaction: dict, history: List[dict]) -> List[str]`
Detect anomalies in a single transaction.
- **Returns**: List of anomaly type strings (e.g., `['high_value', 'unknown_merchant']`)

#### `detect_anomalies_batch(transactions: List[dict]) -> Dict[int, List[str]]`
Detect anomalies in a batch of transactions.
- **Returns**: Dictionary mapping transaction indices to anomaly lists

#### `generate_report(transactions: List[dict]) -> Dict[str, Any]`
Generate comprehensive anomaly detection report.
- **Returns**: Report dictionary with statistics and detected anomalies

## Support

For issues or questions:
1. Check the test suite: `tests/unit/test_anomaly_detector.py`
2. Run the demo: `python anomaly_detector_demo.py`
3. Review logs for detailed information

## Version History

- **v1.0** (2024-11): Initial release with three detection rules
  - High value detection
  - Burst frequency detection
  - Unknown merchant detection
