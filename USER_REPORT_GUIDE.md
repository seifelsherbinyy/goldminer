# User Report Generation Guide

## Overview

The `generate_user_report` function creates polished Excel workbooks containing comprehensive financial transaction reports with embedded charts and professional formatting.

## Features

### Three Sheet Layout

1. **Transactions Sheet**
   - All parsed transaction rows with complete metadata
   - Tagged data fields (id, date, payee, category, amount, etc.)
   - Bold, colored headers with centered alignment
   - Frozen top row for easy scrolling
   - Auto-adjusted column widths
   - Currency formatting for amounts
   - Date formatting (YYYY-MM-DD)
   - Red highlighting for anomaly rows
   - Auto-filters enabled

2. **Anomalies Sheet**
   - Filtered view of flagged transactions only
   - All rows highlighted in red for quick identification
   - Includes anomaly type in the 'anomalies' column
   - Same professional formatting as Transactions sheet
   - Auto-filters enabled

3. **Summary Sheet**
   - Monthly transaction summary with totals, averages, and counts
   - Category breakdown by month (pivoted table)
   - Top 5 merchants by total spending
   - Three embedded charts (see below)

### Embedded Charts

All charts are created using `xlsxwriter.Chart()` for professional visualizations:

1. **Monthly Spend Line Chart**
   - Shows spending trends over time
   - Line chart with clear axis labels
   - Helps identify spending patterns and seasonal variations

2. **Category Breakdown Pie Chart**
   - Visualizes spending distribution across categories
   - Includes percentage labels
   - Makes it easy to see where money is going

3. **Merchant Bar Chart (Top 5)**
   - Horizontal bar chart of top 5 merchants by spending
   - Helps identify major vendors
   - Useful for expense analysis

## Installation

Ensure you have the required dependencies:

```bash
pip install xlsxwriter>=3.1.0 pandas>=2.0.0
```

## Usage

### Basic Example

```python
from goldminer.etl import generate_user_report

# Your transaction data
transactions = [
    {
        'id': 'TXN001',
        'date': '2024-01-15',
        'payee': 'Coffee Shop',
        'category': 'Food & Dining',
        'amount': 5.50,
        'currency': 'USD',
        'account_id': 'ACC-001',
        'account_type': 'Credit',
        'anomalies': '',
        'confidence': 'high'
    },
    # ... more transactions
]

# Generate the report
generate_user_report(transactions, 'financial_report.xlsx')
```

### Complete Example with 100 Transactions

See the included `user_report_demo.py` script for a complete working example that generates 100 sample transactions and creates a comprehensive report.

```bash
python user_report_demo.py
```

This will create a file called `user_financial_report.xlsx` with all features demonstrated.

## Transaction Data Structure

Each transaction dictionary should contain the following fields:

### Required Fields

- `date` (str): Transaction date in YYYY-MM-DD format
- `amount` (float): Transaction amount

### Recommended Fields

- `id` (str): Unique transaction identifier
- `payee` (str): Merchant or payee name
- `category` (str): Transaction category
- `subcategory` (str): Sub-category
- `currency` (str): Currency code (e.g., 'USD')
- `account_id` (str): Account identifier
- `account_type` (str): Account type (e.g., 'Credit', 'Debit')
- `tags` (str): Tags or labels
- `anomalies` (str): Anomaly flags (empty string if none)
- `confidence` (str): Confidence level

The function handles missing fields gracefully, so not all fields are strictly required.

## API Reference

### `generate_user_report(transactions, output_path)`

Generate a polished Excel user report with transactions, anomalies, and summary sheets.

**Parameters:**
- `transactions` (List[dict]): List of transaction dictionaries
- `output_path` (str): Output filename for the Excel workbook (will add .xlsx if missing)

**Raises:**
- `ValueError`: If transactions list is empty
- `IOError`: If unable to write to the specified file

**Returns:**
- None (writes file to disk)

## Output File Validation

The generated workbook is compatible with:
- Microsoft Excel 365
- Microsoft Excel 2016+
- LibreOffice Calc
- Google Sheets (with some chart limitations)

### File Characteristics

- Format: Microsoft Excel 2007+ (.xlsx)
- Typical file size: 15-30 KB for 100 transactions
- Charts: Embedded directly in the Summary sheet
- Encoding: UTF-8 compatible

## Testing

The implementation includes comprehensive test coverage:

```bash
# Run all tests for generate_user_report
python -m unittest tests.unit.test_generate_user_report

# Run specific test
python -m unittest tests.unit.test_generate_user_report.TestGenerateUserReport.test_generate_user_report_basic
```

Test suite includes:
- Basic report generation with 100 transactions
- Empty transaction list handling
- Missing columns handling
- UTF-8 compatibility
- Anomaly highlighting
- Chart generation
- Workbook integrity validation
- File size verification

## Formatting Details

### Color Scheme

- Header background: #366092 (blue)
- Header text: White
- Anomaly highlight: #FFC7CE (red/pink)
- Regular cells: White with borders

### Font and Style

- Headers: Bold, 11pt, centered
- Title: Bold, 14pt
- Subtitle: Bold, 12pt
- Data cells: Regular, bordered

### Column Widths

Automatically adjusted based on content:
- ID columns: 12 characters
- Date columns: 12 characters
- Payee/Merchant columns: 25 characters
- Category columns: 18 characters
- Amount columns: 12 characters
- Other columns: 15 characters (default)

Maximum width: 50 characters

## Performance Notes

- Typical generation time: < 1 second for 100 transactions
- Memory usage: ~10-20 MB for 100 transactions
- Recommended maximum: 10,000 transactions per report
- For larger datasets, consider splitting into multiple reports

## Comparison with XLSXExporter

The repository also includes an `XLSXExporter` class that uses `openpyxl` for chart generation. Key differences:

| Feature | generate_user_report | XLSXExporter |
|---------|---------------------|--------------|
| Chart Library | xlsxwriter | openpyxl |
| Auto-filters | Yes | No |
| Top Merchants Chart | Yes | No |
| Read Existing Files | No | Yes (via openpyxl) |
| API Style | Function | Class |

Choose `generate_user_report` for:
- Simple, one-time report generation
- When xlsxwriter charts are preferred
- When you need auto-filters

Choose `XLSXExporter` for:
- When you need to read/modify existing Excel files
- Object-oriented approach
- When openpyxl is already in use

## Troubleshooting

### File Already Exists Error

If you get a permission error, ensure the file isn't open in Excel:

```python
import os
if os.path.exists('report.xlsx'):
    os.remove('report.xlsx')
generate_user_report(transactions, 'report.xlsx')
```

### Missing xlsxwriter Module

```bash
pip install xlsxwriter>=3.1.0
```

### Invalid Date Format

Ensure dates are in YYYY-MM-DD format:

```python
from datetime import datetime

# Convert various date formats
transaction['date'] = datetime.strptime(
    transaction['date'], '%m/%d/%Y'
).strftime('%Y-%m-%d')
```

### Charts Not Appearing

Verify that you have transactions spanning multiple months and categories:

```python
# Check date range
dates = [t['date'] for t in transactions]
print(f"Date range: {min(dates)} to {max(dates)}")

# Check categories
categories = set(t.get('category', '') for t in transactions)
print(f"Categories: {categories}")
```

## Examples

See the following files for complete working examples:

1. `user_report_demo.py` - Standalone demo with 100 sample transactions
2. `tests/unit/test_generate_user_report.py` - Comprehensive test suite with various scenarios

## License

Part of the GoldMiner ETL pipeline. See repository LICENSE for details.

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review this guide
3. Open an issue in the repository
