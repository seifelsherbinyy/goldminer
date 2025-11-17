# ParquetExporter Guide

## Overview

The `ParquetExporter` class provides an efficient way to export transaction data to Apache Parquet format. Parquet is a columnar storage format that offers excellent compression ratios and is optimized for analytical queries.

## Features

- **Schema Optimization**: Automatically optimizes column types for storage efficiency
  - Categorical encoding for low-cardinality columns
  - Dictionary encoding for high-cardinality text columns
  - Proper data types for numeric and temporal fields

- **Compression**: Supports multiple compression algorithms
  - Snappy (default): Fast compression with good ratio
  - Brotli: Better compression ratio, slower
  - Gzip, Zstd: Other options available

- **Partitioning**: Organize data by year/month for efficient querying
  - Improves query performance on date ranges
  - Reduces I/O by reading only relevant partitions

- **Metadata**: Rich metadata in file footer
  - Export timestamp
  - User ID
  - Number of rows
  - Exporter version and schema version

- **Compatibility**: Works with popular data tools
  - PyArrow
  - Pandas
  - Polars
  - Apache Spark
  - DuckDB

## Installation

Add to your requirements.txt:
```
pyarrow>=14.0.1
```

## Basic Usage

```python
from goldminer.etl import ParquetExporter

# Initialize exporter
exporter = ParquetExporter()

# Prepare transaction data
transactions = [
    {
        'id': 'TXN001',
        'date': '2025-01-15',
        'payee': 'Coffee Shop',
        'amount': 5.50,
        'currency': 'USD',
        'category': 'Food',
        'subcategory': 'Dining',
        'account_id': 'ACC001',
        'account_type': 'Credit',
        'tags': ['morning', 'caffeine'],
        'urgency': 'normal',
        'confidence': 'high'
    },
    # ... more transactions
]

# Export to Parquet
exporter.export_to_parquet(
    transactions=transactions,
    filepath='transactions.parquet'
)
```

## Advanced Usage

### Using Compression

```python
# Use Brotli for better compression
exporter.export_to_parquet(
    transactions=transactions,
    filepath='transactions.parquet',
    compression='brotli'
)
```

### Partitioning by Date

```python
# Partition by year and month
exporter.export_to_parquet(
    transactions=transactions,
    filepath='transactions.parquet',
    partition_cols=['year', 'month']
)
```

This creates a directory structure:
```
transactions/
  year=2025/
    month=1/
      part-0.parquet
    month=2/
      part-0.parquet
```

### Adding Custom Metadata

```python
# Include user ID in metadata
exporter.export_to_parquet(
    transactions=transactions,
    filepath='transactions.parquet',
    user_id='user_12345'
)
```

### Validating Schema Consistency

```python
# Get schema information
schema_info = exporter.get_schema_info('transactions.parquet')
print(f"Columns: {schema_info['column_names']}")
print(f"Types: {schema_info['column_types']}")
print(f"Metadata: {schema_info['metadata']}")
```

### Checking Compatibility

```python
# Validate file can be read by common tools
results = exporter.validate_compatibility('transactions.parquet')
print(f"PyArrow: {results['pyarrow']}")
print(f"Pandas: {results['pandas']}")
print(f"Polars: {results['polars']}")
```

## Reading Parquet Files

### With Pandas

```python
import pandas as pd

df = pd.read_parquet('transactions.parquet')
print(df.head())
```

### With PyArrow

```python
import pyarrow.parquet as pq

table = pq.read_table('transactions.parquet')
df = table.to_pandas()
```

### With Polars

```python
import polars as pl

df = pl.read_parquet('transactions.parquet')
print(df.head())
```

### Reading Partitioned Data

```python
import pandas as pd

# Read all partitions
df = pd.read_parquet('transactions/')

# Read specific partitions
df = pd.read_parquet(
    'transactions/',
    filters=[('year', '=', 2025), ('month', '=', 1)]
)
```

## Schema Optimization Details

The exporter automatically optimizes the schema:

| Column Type | Storage Type | Optimization |
|------------|--------------|--------------|
| category, subcategory | Dictionary | Categorical encoding |
| account_type, urgency | Dictionary | Categorical encoding |
| confidence, currency | Dictionary | Categorical encoding |
| tags | Dictionary | Categorical encoding (comma-separated) |
| payee, merchant | String | Dictionary encoding in Parquet |
| id, account_id | String | Plain encoding |
| amount, interest_rate | Float64 | Standard numeric |
| date | Timestamp | Millisecond precision |
| year, month | Int32 | Standard integer |

## Performance Tips

1. **Use compression**: Snappy offers good balance between speed and size
2. **Partition large datasets**: By year/month for time-series data
3. **Use filters when reading**: Only read needed partitions
4. **Batch writes**: Write in larger batches when possible
5. **Consider row groups**: Default settings work well for most cases

## Comparison with Other Formats

| Feature | Parquet | CSV | Excel |
|---------|---------|-----|-------|
| Compression | Excellent | None | Fair |
| Query Speed | Fast | Slow | N/A |
| Schema | Built-in | None | Inferred |
| Size | Small | Large | Medium |
| Analytics Tools | Yes | Limited | No |

## Troubleshooting

### Large file sizes
- Use compression (brotli for best ratio)
- Check for duplicate data
- Consider partitioning

### Slow reads
- Use appropriate filters
- Check partition strategy
- Consider columnar reading

### Schema mismatches
- Use `get_schema_info()` to verify
- Ensure consistent data types
- Check TransactionRecord schema

## See Also

- [XLSXExporter Guide](XLSX_EXPORTER_GUIDE.md)
- [Schema Normalizer](goldminer/etl/schema_normalizer.py)
- [Transaction Record Schema](goldminer/etl/schema_normalizer.py#TransactionRecord)
- [Apache Parquet Documentation](https://parquet.apache.org/docs/)
- [PyArrow Documentation](https://arrow.apache.org/docs/python/)
