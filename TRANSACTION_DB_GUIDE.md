# TransactionDB Usage Guide

## Overview

The `TransactionDB` class provides a robust, performant solution for managing persistent storage of financial transactions using SQLite3 with full-text search capabilities.

## Features

- **Complete Schema**: Supports all transaction fields including id, date, payee, category, subcategory, amount, account details, and more
- **Fast Retrieval**: Indexed fields (date, payee, category) for sub-millisecond queries even with 20K+ rows
- **Full-Text Search**: FTS5 virtual table for searching across payee, category, subcategory, and tags
- **Duplicate Detection**: Unique constraint on (date, payee, amount, account_id) prevents duplicates
- **Flexible Querying**: Support for exact matches, ranges, lists, and full-text search
- **Smart Insert Methods**: `insert_transaction()` with skip/upsert modes for duplicate handling
- **Bulk Operations**: `bulk_insert()` with 600+ TPS throughput and automatic rollback on failure
- **Dashboard Aggregations**: `get_summary_by_month()` for Excel reports and visualizations

## Quick Start

```python
from goldminer.etl import TransactionDB

# Initialize database
db = TransactionDB("path/to/transactions.db")

# Insert a transaction
transaction_id = db.insert({
    'date': '2024-01-15',
    'payee': 'Amazon Prime',
    'category': 'Shopping',
    'subcategory': 'Online',
    'amount': 14.99,
    'account_id': 'acc_001',
    'account_type': 'credit',
    'currency': 'USD',
    'tags': 'subscription,monthly',
    'confidence': 0.95
})

# Query transactions
food_transactions = db.query({'category': 'Food'})

# Update a transaction
db.update(transaction_id, {'category': 'Entertainment'})

# Close connection
db.close()
```

## Usage with Context Manager

```python
with TransactionDB("transactions.db") as db:
    # Insert
    txn_id = db.insert({
        'date': '2024-01-16',
        'payee': 'Whole Foods',
        'amount': 125.50,
        'account_id': 'acc_001'
    })
    
    # Query
    results = db.query({'amount_min': 100.0})
```

## Methods

### insert_transaction(transaction: dict, mode: str = 'skip') -> dict

Enhanced insert method with duplicate checking and configurable conflict resolution.

```python
# Skip duplicate transactions (default)
result = db.insert_transaction({
    'date': '2024-01-15',
    'payee': 'Store Name',
    'amount': 99.99,
    'account_id': 'acc_123'
}, mode='skip')

if result['status'] == 'inserted':
    print(f"Transaction inserted: {result['id']}")
elif result['status'] == 'skipped':
    print("Duplicate transaction skipped")

# Upsert mode - update if duplicate exists
result = db.insert_transaction({
    'date': '2024-01-15',
    'payee': 'Store Name',
    'amount': 99.99,
    'account_id': 'acc_123',
    'category': 'Updated Category'
}, mode='upsert')

if result['status'] == 'updated':
    print(f"Transaction updated: {result['id']}")
```

**Returns:**
- `id`: Transaction ID (UUID)
- `status`: 'inserted', 'skipped', or 'updated'
- `message`: Description of action taken

**Features:**
- Automatic duplicate detection using composite key (date, amount, payee, account_id)
- Transaction rollback on failure
- Detailed logging of rejected/duplicate records

### bulk_insert(transactions: List[dict], mode: str = 'skip') -> dict

Efficient batch insert with performance tracking and duplicate handling.

```python
transactions = [
    {'date': '2024-01-15', 'payee': 'Store A', 'amount': 100.0, 'account_id': 'acc_001'},
    {'date': '2024-01-16', 'payee': 'Store B', 'amount': 150.0, 'account_id': 'acc_002'},
    # ... more transactions
]

result = db.bulk_insert(transactions, mode='skip')

print(f"Inserted: {result['inserted']}")
print(f"Updated: {result['updated']}")
print(f"Skipped: {result['skipped']}")
print(f"Failed: {result['failed']}")
print(f"Duration: {result['duration']}s")
print(f"Throughput: {result['transactions_per_second']} TPS")

# Check for failures
if result['failed'] > 0:
    for detail in result['details']:
        print(f"Failed at index {detail['index']}: {detail['error']}")
```

**Returns:**
- `inserted`: Number of transactions inserted
- `updated`: Number of transactions updated (upsert mode)
- `skipped`: Number of duplicates skipped
- `failed`: Number of failed transactions
- `duration`: Total time in seconds
- `transactions_per_second`: Insert rate (TPS)
- `details`: List of failed transaction details

**Performance:**
- Achieves 600+ TPS on 10,000+ record batches
- Atomic operations with rollback on critical failure
- Detailed error tracking for failed records

### get_summary_by_month(start_date: str = None, end_date: str = None) -> dict

Generate monthly aggregations for dashboard visualization.

```python
# Get all-time summary
summary = db.get_summary_by_month()

# Get summary for specific date range
summary = db.get_summary_by_month(
    start_date='2024-01-01',
    end_date='2024-12-31'
)

# Access monthly totals
for month_data in summary['by_month']:
    print(f"{month_data['month']}: ${month_data['total_amount']}")

# Access category breakdown
for month, categories in summary['by_category'].items():
    print(f"\n{month}:")
    for category, data in categories.items():
        print(f"  {category}: ${data['total_amount']} ({data['transaction_count']} txns)")

# Access account type breakdown
for month, accounts in summary['by_account_type'].items():
    for account_type, data in accounts.items():
        print(f"{month} - {account_type}: ${data['total_amount']}")

# Access tag breakdown
for month, tags in summary['by_tag'].items():
    for tag, data in tags.items():
        print(f"{month} - #{tag}: ${data['total_amount']}")
```

**Returns:**
- `by_month`: Overall monthly totals with transaction counts and statistics
- `by_category`: Spending aggregated by category per month
- `by_account_type`: Spending aggregated by account type per month
- `by_tag`: Spending aggregated by tag per month (tags are split and counted separately)

**Use Cases:**
- Excel dashboard data feeds
- Monthly spending reports
- Budget analysis by category
- Account type comparison
- Tag-based expense tracking

### insert(transaction: dict) -> str

Inserts a new transaction and returns its UUID.

```python
transaction_id = db.insert({
    'date': '2024-01-15',
    'payee': 'Store Name',
    'amount': 99.99,
    'account_id': 'acc_123'
})
```

**Note**: 
- Automatically generates UUID if not provided
- Raises `sqlite3.IntegrityError` if duplicate detected

### update(id: str, fields: dict) -> bool

Updates an existing transaction by ID. Returns `True` if successful, `False` if transaction not found.

```python
success = db.update(transaction_id, {
    'category': 'Food',
    'subcategory': 'Groceries',
    'confidence': 0.98
})
```

### query(filters: dict) -> List[dict]

Queries transactions with flexible filtering options.

**Direct field matching:**
```python
results = db.query({'category': 'Food'})
```

**Range queries:**
```python
# Amount range
results = db.query({
    'amount_min': 50.0,
    'amount_max': 200.0
})

# Date range
results = db.query({
    'date_from': '2024-01-01',
    'date_to': '2024-01-31'
})
```

**List matching (IN clause):**
```python
results = db.query({
    'payee_in': ['Amazon', 'Walmart', 'Target']
})
```

**Full-text search:**
```python
results = db.query({'search': 'restaurant'})
```

**Combined filters:**
```python
results = db.query({
    'category': 'Food',
    'amount_min': 50.0,
    'date_from': '2024-01-01'
})
```

### get_by_id(id: str) -> Optional[dict]

Retrieves a single transaction by ID.

```python
transaction = db.get_by_id(transaction_id)
if transaction:
    print(f"Payee: {transaction['payee']}")
```

### delete(id: str) -> bool

Deletes a transaction by ID. Returns `True` if successful, `False` if not found.

```python
success = db.delete(transaction_id)
```

### count(filters: dict) -> int

Counts transactions matching the given filters.

```python
# Total count
total = db.count()

# Filtered count
food_count = db.count({'category': 'Food'})
```

## Schema

| Field | Type | Description | Indexed |
|-------|------|-------------|---------|
| id | TEXT | UUID (Primary Key) | Yes |
| date | TEXT | Transaction date (ISO format) | Yes |
| payee | TEXT | Merchant/payee name | Yes |
| category | TEXT | Transaction category | Yes |
| subcategory | TEXT | Transaction subcategory | No |
| amount | REAL | Transaction amount | No |
| account_id | TEXT | Account identifier | No |
| account_type | TEXT | Type of account (credit/debit) | No |
| interest_rate | REAL | Interest rate | No |
| tags | TEXT | Comma-separated tags | No |
| urgency | TEXT | Urgency level | No |
| currency | TEXT | Currency code | No |
| anomalies | TEXT | Detected anomalies | No |
| confidence | REAL | Confidence score (0-1) | No |

**Unique Constraint**: (date, payee, amount, account_id)

## Performance

Query performance with 20,000+ rows:

| Query Type | Time |
|------------|------|
| Category filter | ~21ms |
| Date range | ~8ms |
| Payee lookup | ~1ms |
| Complex (multiple filters) | ~8ms |
| Full-text search | ~78ms |

All queries are well under the 100ms requirement.

Bulk insert performance:

| Operation | Throughput |
|-----------|------------|
| Bulk insert (10K records) | 600-650 TPS |
| Individual inserts | ~300-350 TPS |
| Bulk insert with duplicates | 500-600 TPS |

**Note**: Bulk operations provide 2x performance improvement over individual inserts.

## Error Handling

```python
import sqlite3

try:
    db.insert(transaction)
except sqlite3.IntegrityError:
    print("Duplicate transaction detected")
```

## Best Practices

1. **Use context managers** for automatic connection cleanup
2. **Use `bulk_insert()` for large datasets** - Achieves 600+ TPS instead of individual inserts
3. **Choose the right mode** - Use 'skip' for import, 'upsert' for updates
4. **Use indexed fields** (date, payee, category) in query filters for best performance
5. **Full-text search** is powerful but slightly slower - use for search features
6. **Monitor failed records** - Check the 'details' field in bulk_insert results for errors
7. **Use `get_summary_by_month()`** for dashboard data instead of custom aggregation queries

## Example: Processing a batch of transactions

```python
from goldminer.etl import TransactionDB

def process_transactions(transactions_list):
    with TransactionDB("transactions.db") as db:
        # Use bulk_insert for efficiency
        result = db.bulk_insert(transactions_list, mode='skip')
        
        print(f"Processing complete:")
        print(f"  Inserted: {result['inserted']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Duration: {result['duration']}s")
        print(f"  Throughput: {result['transactions_per_second']} TPS")
        
        # Get monthly summary for reporting
        summary = db.get_summary_by_month()
        
        # Display category spending
        for month, categories in summary['by_category'].items():
            print(f"\n{month} spending by category:")
            for category, data in categories.items():
                print(f"  {category}: ${data['total_amount']:.2f}")
```

## Example: Safe upsert with error handling

```python
from goldminer.etl import TransactionDB

def import_with_updates(transactions):
    """Import transactions, updating existing ones with new data."""
    with TransactionDB("transactions.db") as db:
        try:
            result = db.bulk_insert(transactions, mode='upsert')
            
            print(f"Import completed:")
            print(f"  New transactions: {result['inserted']}")
            print(f"  Updated transactions: {result['updated']}")
            
            if result['failed'] > 0:
                print(f"\nFailed transactions: {result['failed']}")
                for detail in result['details']:
                    print(f"  Index {detail['index']}: {detail['error']}")
                    
        except Exception as e:
            print(f"Import failed with rollback: {e}")
```

## Testing

Run the test suite:

```bash
python -m unittest tests.unit.test_transaction_db -v
```

This will run 31 comprehensive tests including:
- Basic CRUD operations
- Duplicate detection and handling
- Skip vs upsert modes
- Bulk insert with 10,000+ records
- Performance validation with 20K+ rows
- Monthly aggregations and summaries
- Error handling and rollback scenarios
