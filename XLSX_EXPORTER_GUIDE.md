# XLSXExporter Guide

## Overview

The `XLSXExporter` class provides a comprehensive solution for exporting transaction data to well-formatted Excel workbooks. It creates professional, user-friendly Excel files with multiple sheets, formatting, and charts suitable for non-technical users.

## Features

### Multi-Sheet Workbook Structure

The exporter creates three sheets in each workbook:

1. **Transactions Sheet**: Full row-level transaction data
2. **Monthly Summary Sheet**: Aggregated totals by category and account
3. **Anomalies Sheet**: Only transactions with anomaly flags

### Professional Formatting

- **Styled Headers**: Bold text with colored background
- **Frozen Panes**: Top row frozen for easy scrolling
- **Auto-Adjusted Widths**: Column widths automatically adjusted based on content
- **Currency Formatting**: Amount columns formatted as currency (e.g., $1,234.56)
- **Conditional Formatting**: Dynamic urgency-based highlighting:
  - **High Urgency**: Red fill with bold white text
  - **Medium Urgency**: Yellow fill
  - **Normal/Low Urgency**: Green tint
- **Anomaly Borders**: Bold red borders for rows with anomaly flags
- **Dynamic Application**: Formatting applied based on cell content (not hardcoded row indices)

### Charts and Visualizations

The Monthly Summary sheet includes three charts:

1. **Pie Chart**: Category spending distribution
2. **Bar Chart**: Monthly spending trends
3. **Line Chart**: Cumulative spending over time

### UTF-8 Compatibility

Full support for international characters, ensuring compatibility with global data.

## Installation

The XLSXExporter requires `openpyxl`, which is included in GoldMiner's requirements:

```bash
pip install -r requirements.txt
```

## Basic Usage

### Simple Export

```python
from goldminer.etl import XLSXExporter

# Create sample transactions
transactions = [
    {
        'id': 'TXN001',
        'date': '2024-01-15',
        'payee': 'Coffee Shop',
        'category': 'Food & Dining',
        'amount': 4.50,
        'currency': 'USD',
        'account_id': 'ACC001',
        'anomalies': ''
    },
    {
        'id': 'TXN002',
        'date': '2024-01-16',
        'payee': 'Gas Station',
        'category': 'Transportation',
        'amount': 45.00,
        'currency': 'USD',
        'account_id': 'ACC001',
        'anomalies': ''
    }
]

# Export to Excel
exporter = XLSXExporter()
exporter.export_to_excel(transactions, 'my_transactions.xlsx')
```

### Export from Database

```python
from goldminer.etl import TransactionDB, XLSXExporter

# Query transactions from database
db = TransactionDB("data/processed/transactions.db")
transactions = db.query()

# Convert to list of dictionaries
transaction_dicts = [dict(txn) for txn in transactions]

# Export
exporter = XLSXExporter()
exporter.export_to_excel(transaction_dicts, 'database_export.xlsx')

db.close()
```

### Export Filtered Data

```python
from goldminer.etl import TransactionDB, XLSXExporter

# Query only high-value transactions
db = TransactionDB("data/processed/transactions.db")
high_value_txns = db.query(filters={'amount_min': 1000})

# Convert and export
transaction_dicts = [dict(txn) for txn in high_value_txns]
exporter = XLSXExporter()
exporter.export_to_excel(transaction_dicts, 'high_value_transactions.xlsx')

db.close()
```

## Transaction Data Structure

The XLSXExporter expects transactions as a list of dictionaries with the following fields:

### Required Fields

- `id`: Transaction ID (string)
- `date`: Transaction date in 'YYYY-MM-DD' format (string)
- `amount`: Transaction amount (float)

### Optional Fields

- `payee`: Merchant/payee name (string)
- `category`: Transaction category (string)
- `subcategory`: Transaction subcategory (string)
- `currency`: Currency code (string, default: 'USD')
- `account_id`: Account identifier (string)
- `account_type`: Account type (string, e.g., 'Credit', 'Debit')
- `urgency`: Transaction urgency level (string: 'high', 'medium', 'normal', or 'low')
- `tags`: Transaction tags (string)
- `anomalies`: Anomaly flags (string, comma-separated values like 'high_value', 'burst_frequency', 'unknown_merchant')
- `confidence`: Confidence score (float or string)

### Example Transaction

```python
{
    'id': 'TXN123456',
    'date': '2024-01-15',
    'payee': 'Amazon',
    'category': 'Shopping',
    'subcategory': 'Electronics',
    'amount': 299.99,
    'currency': 'USD',
    'account_id': 'ACC-CREDIT-001',
    'account_type': 'Credit',
    'urgency': 'normal',
    'tags': 'online,electronics',
    'anomalies': 'high_value',
    'confidence': 'high'
}
```

## Sheet Details

### Transactions Sheet

Contains all transaction data with the following columns:

- id
- date
- payee
- category
- subcategory
- amount (currency formatted)
- currency
- account_id
- account_type
- urgency
- tags
- anomalies
- confidence

**Features**:
- Header row frozen for scrolling
- Conditional formatting based on urgency level:
  - High urgency: Red fill with bold white text
  - Medium urgency: Yellow fill
  - Normal/Low urgency: Green tint
- Bold red borders for rows with anomaly flags
- Amount columns with currency formatting

### Monthly Summary Sheet

Aggregated data by month including:

1. **Monthly Totals Section**:
   - Month
   - Total amount
   - Average amount
   - Transaction count

2. **Category Breakdown Section**:
   - Spending by category for each month

3. **Charts**:
   - Pie chart showing category distribution
   - Bar chart showing monthly trends
   - Line chart showing cumulative spending

### Anomalies Sheet

Contains only transactions with anomaly flags, displayed with:
- All relevant transaction fields including urgency
- Conditional formatting based on urgency level
- Bold red borders for all anomaly rows (since all rows have anomalies)
- Same formatting as Transactions sheet

## Conditional Formatting

The XLSXExporter now includes advanced conditional formatting features that dynamically highlight transactions based on their urgency level and anomaly status.

### Urgency-Based Formatting

Transactions are automatically formatted based on their urgency level:

- **High Urgency** (`urgency='high'`):
  - Red background fill (#FF0000)
  - Bold white text for high visibility
  - Applied to transactions with amounts ≥ $10,000 or critical flags

- **Medium Urgency** (`urgency='medium'`):
  - Yellow background fill (#FFFF00)
  - Standard text formatting
  - Applied to transactions with amounts ≥ $5,000 (for credit cards)

- **Normal/Low Urgency** (`urgency='normal'` or `urgency='low'`):
  - Light green tint (#C6EFCE)
  - Standard text formatting
  - Applied to regular transactions

### Anomaly Border Formatting

Transactions with anomaly flags receive bold red borders:

- **Border Style**: Thick red border (#FF0000) on all sides
- **Applied To**: Any transaction with non-empty `anomalies` field
- **Common Anomaly Types**:
  - `high_value`: Unusually large transaction amounts
  - `burst_frequency`: Rapid succession of transactions
  - `unknown_merchant`: Unrecognized merchant/payee
  - `duplicate`: Potential duplicate transaction

### Dynamic Application

Conditional formatting is applied dynamically using openpyxl's `CellIsRule`:

- Formatting rules are based on cell content, not hardcoded row indices
- Works correctly with any number of transactions (tested with 1K+ records)
- Automatically adapts to filtered or sorted data
- Applied to entire rows for consistent visualization

### Example with Conditional Formatting

```python
from goldminer.etl import XLSXExporter

# Transactions with urgency and anomaly flags
transactions = [
    {
        'id': 'TXN001',
        'date': '2024-01-15',
        'payee': 'Large Purchase Store',
        'category': 'Shopping',
        'amount': 15000.00,
        'urgency': 'high',  # Will get red fill with bold white text
        'anomalies': 'high_value'  # Will get red borders
    },
    {
        'id': 'TXN002',
        'date': '2024-01-16',
        'payee': 'Monthly Bill',
        'category': 'Bills',
        'amount': 7500.00,
        'urgency': 'medium',  # Will get yellow fill
        'anomalies': ''
    },
    {
        'id': 'TXN003',
        'date': '2024-01-17',
        'payee': 'Coffee Shop',
        'category': 'Food',
        'amount': 5.50,
        'urgency': 'normal',  # Will get green tint
        'anomalies': ''
    }
]

exporter = XLSXExporter()
exporter.export_to_excel(transactions, 'formatted_transactions.xlsx')
```

### Helper Functions

The exporter includes helper functions for consistent formatting:

- `_apply_row_urgency_formatting()`: Applies urgency formatting to entire rows
- `_apply_anomaly_borders()`: Applies red borders to anomaly rows
- `_apply_urgency_formatting()`: Applies urgency formatting to specific columns

These functions ensure consistent styling across all sheets and simplify maintenance.

## Advanced Usage

### Custom Styling

While the XLSXExporter provides default styling, you can create a custom exporter by extending the class:

```python
from goldminer.etl import XLSXExporter
from openpyxl.styles import Font, PatternFill

class CustomExporter(XLSXExporter):
    def __init__(self):
        super().__init__()
        # Override styles
        self.header_fill = PatternFill(
            start_color="4472C4",
            end_color="4472C4",
            fill_type="solid"
        )
        self.anomaly_fill = PatternFill(
            start_color="FFD966",
            end_color="FFD966",
            fill_type="solid"
        )

# Use custom exporter
exporter = CustomExporter()
exporter.export_to_excel(transactions, 'custom_export.xlsx')
```

### Handling Missing Data

The exporter gracefully handles missing fields:

```python
# Transactions with minimal data
minimal_transactions = [
    {'id': 'TXN001', 'date': '2024-01-15', 'amount': 50.00},
    {'id': 'TXN002', 'date': '2024-01-16', 'amount': 75.00}
]

exporter = XLSXExporter()
exporter.export_to_excel(minimal_transactions, 'minimal_export.xlsx')
# Works! Missing columns are simply not included
```

### Large Datasets

The exporter efficiently handles large datasets:

```python
from goldminer.etl import TransactionDB, XLSXExporter

db = TransactionDB()
# Query large dataset
transactions = db.query(limit=10000)

transaction_dicts = [dict(txn) for txn in transactions]

exporter = XLSXExporter()
exporter.export_to_excel(transaction_dicts, 'large_export.xlsx')
```

## Integration with ETL Pipeline

### Export After Pipeline Run

```python
from goldminer.config import ConfigManager
from goldminer.etl import ETLPipeline, TransactionDB, XLSXExporter

# Run ETL pipeline
config = ConfigManager()
pipeline = ETLPipeline(config)
df = pipeline.run_pipeline(
    source_path='data/raw',
    table_name='unified_data',
    is_directory=True
)

# Query from database
db = TransactionDB()
transactions = db.query()
transaction_dicts = [dict(txn) for txn in transactions]

# Export to Excel
exporter = XLSXExporter()
exporter.export_to_excel(transaction_dicts, 'pipeline_export.xlsx')

db.close()
```

### Periodic Exports

```python
from goldminer.etl import TransactionDB, XLSXExporter
from datetime import datetime

def export_monthly_report():
    """Export monthly transaction report."""
    db = TransactionDB()
    
    # Get current month's transactions
    current_month = datetime.now().strftime('%Y-%m')
    transactions = db.query(filters={'date_from': f'{current_month}-01'})
    
    # Export
    transaction_dicts = [dict(txn) for txn in transactions]
    filename = f'monthly_report_{current_month}.xlsx'
    
    exporter = XLSXExporter()
    exporter.export_to_excel(transaction_dicts, filename)
    
    db.close()
    return filename

# Call periodically (e.g., via cron job)
report_file = export_monthly_report()
print(f"Generated report: {report_file}")
```

## Error Handling

### Empty Transaction List

```python
exporter = XLSXExporter()

try:
    exporter.export_to_excel([], 'empty.xlsx')
except ValueError as e:
    print(f"Error: {e}")
    # Output: Error: Cannot export empty transaction list
```

### Invalid Filename

```python
try:
    exporter.export_to_excel(transactions, '/invalid/path/file.xlsx')
except IOError as e:
    print(f"Error writing file: {e}")
```

### Missing Required Fields

```python
# Transactions missing 'amount' field
incomplete_transactions = [
    {'id': 'TXN001', 'date': '2024-01-15'}
]

exporter = XLSXExporter()
# Will export but Monthly Summary may have limited data
exporter.export_to_excel(incomplete_transactions, 'incomplete.xlsx')
```

## Best Practices

1. **Use Descriptive Filenames**: Include date/time in filenames for easy identification
   ```python
   from datetime import datetime
   filename = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
   ```

2. **Close Database Connections**: Always close database connections after querying
   ```python
   db = TransactionDB()
   transactions = db.query()
   db.close()  # Important!
   ```

3. **Handle Large Datasets**: For very large datasets, consider filtering or pagination
   ```python
   # Export in batches
   batch_size = 5000
   for offset in range(0, total_count, batch_size):
       transactions = db.query(limit=batch_size, offset=offset)
       # Process batch
   ```

4. **Validate Data**: Ensure data quality before export
   ```python
   # Filter out invalid transactions
   valid_transactions = [
       t for t in transactions
       if t.get('date') and t.get('amount') is not None
   ]
   ```

5. **Log Exports**: Keep track of exports for auditing
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   exporter = XLSXExporter()
   exporter.export_to_excel(transactions, filename)
   logger.info(f"Exported {len(transactions)} transactions to {filename}")
   ```

## Demo Scripts

### Basic Demo

Run the basic demo to see XLSXExporter in action:

```bash
python xlsx_exporter_demo.py
```

This generates sample data and creates `demo_transactions_export.xlsx`.

### Conditional Formatting Demo

Run the conditional formatting demo to see the new features:

```bash
python xlsx_conditional_formatting_demo.py
```

This creates `demo_conditional_formatting_export.xlsx` with:
- 1200+ transactions with mixed urgency levels
- Various anomaly types (high_value, burst_frequency, unknown_merchant, duplicate)
- Full conditional formatting applied to both Transactions and Anomalies sheets

The demo output shows statistics on urgency distribution and anomaly counts.

### Integration Demo

Run the integration demo to see database integration:

```bash
python xlsx_exporter_integration_example.py
```

This creates a sample database, queries it, and exports to Excel.

## Troubleshooting

### Issue: "Cannot export empty transaction list"

**Solution**: Ensure your transaction list is not empty before calling `export_to_excel()`.

### Issue: Charts not appearing

**Cause**: Missing or insufficient data for chart generation.
**Solution**: Ensure transactions span multiple months and have category information.

### Issue: Column widths too narrow/wide

**Cause**: Auto-adjustment based on content length.
**Solution**: The exporter caps column widths at 50 characters. For custom widths, extend the class and override `_auto_adjust_column_widths()`.

### Issue: Memory errors with large datasets

**Cause**: Loading entire dataset into memory.
**Solution**: Process data in batches or filter unnecessary columns.

## API Reference

### XLSXExporter Class

#### `__init__()`

Initialize the XLSX exporter with default styling.

```python
exporter = XLSXExporter()
```

#### `export_to_excel(transactions, filename)`

Export transactions to Excel workbook.

**Parameters**:
- `transactions` (List[Dict]): List of transaction dictionaries
- `filename` (str): Output filename (`.xlsx` extension added if missing)

**Raises**:
- `ValueError`: If transactions list is empty
- `IOError`: If unable to write to file

**Returns**: None

**Example**:
```python
exporter.export_to_excel(transactions, 'output.xlsx')
```

## Contributing

To contribute improvements to XLSXExporter:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

XLSXExporter is part of the GoldMiner project and is available under the MIT License.
