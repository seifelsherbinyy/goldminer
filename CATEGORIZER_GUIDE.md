# Transaction Categorizer

The **Categorizer** is a sophisticated transaction categorization system that automatically assigns categories, subcategories, and tags to transaction records based on merchant names, keywords, and patterns.

## Features

- **Priority-Based Matching System**: Implements a 4-tier priority system for accurate categorization
  1. Exact merchant name match
  2. Fuzzy merchant name match
  3. Keyword match (English and Arabic)
  4. Fallback to "Uncategorized"

- **Multi-Language Support**: Full support for both English and Arabic keywords and merchant names

- **Multiple Fuzzy Matching Algorithms**: Uses token_sort_ratio, token_set_ratio, and partial_ratio for robust fuzzy matching

- **Flexible Tag System**: Supports assignment of multiple tags to transactions

- **Batch Processing**: Efficiently categorize multiple transactions at once

- **Statistics Generation**: Generate comprehensive statistics about categorization results

## Installation

The Categorizer is part of the goldminer ETL pipeline. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- `fuzzywuzzy>=0.18.0`
- `python-Levenshtein>=0.12.0`
- `pyyaml>=6.0`

## Quick Start

```python
from goldminer.etl import Categorizer, TransactionRecord

# Initialize the categorizer
categorizer = Categorizer()

# Create a transaction record
record = TransactionRecord(
    id='txn-001',
    payee="McDonald's",
    normalized_merchant="McDonald's",
    amount=75.50,
    currency='EGP'
)

# Categorize the transaction
categorized = categorizer.categorize(record)

print(f"Category: {categorized.category}")
print(f"Subcategory: {categorized.subcategory}")
print(f"Tags: {categorized.tags}")
```

## Usage

### Basic Categorization

```python
from goldminer.etl import Categorizer, TransactionRecord

# Initialize with default rules
categorizer = Categorizer()

# Create a transaction record
record = TransactionRecord(
    id='txn-001',
    payee='Carrefour',
    normalized_merchant='Carrefour'
)

# Categorize
result = categorizer.categorize(record)
# Result: Food & Dining / Groceries
```

### Custom Rules File

```python
# Use a custom category rules file
categorizer = Categorizer(rules_path='/path/to/custom_rules.yaml')
```

### Adjusting Fuzzy Matching Threshold

```python
# Set a higher threshold for more strict matching (default: 80)
categorizer = Categorizer(fuzzy_threshold=85)
```

### Batch Processing

```python
# Categorize multiple records at once
records = [
    TransactionRecord(id='1', payee='Netflix', normalized_merchant='Netflix'),
    TransactionRecord(id='2', payee='Uber', normalized_merchant='Uber'),
    TransactionRecord(id='3', payee='Amazon', normalized_merchant='Amazon'),
]

results = categorizer.categorize_batch(records)
```

### Category Statistics

```python
# Get statistics about categorized transactions
stats = categorizer.get_category_statistics(categorized_records)

print(f"Total: {stats['total_records']}")
print(f"Uncategorized: {stats['uncategorized_count']}")
print(f"Categories: {stats['categories']}")
```

## Category Rules

Categories are defined in `category_rules.yaml` with the following structure:

```yaml
categories:
  - category: "Food & Dining"
    subcategory: "Restaurants"
    tags:
      - "Dining"
    merchant_exact:
      - "McDonald's"
      - "KFC"
    merchant_fuzzy:
      - "mcdonalds"
      - "kfc"
    keywords:
      english:
        - "restaurant"
        - "food"
      arabic:
        - "مطعم"
        - "طعام"

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags:
    - "Uncategorized"
```

### Built-in Categories

The default `category_rules.yaml` includes 19 comprehensive categories:

1. **Food & Dining**
   - Restaurants
   - Groceries

2. **Shopping**
   - Fashion & Apparel
   - Electronics
   - Online Shopping

3. **Transportation**
   - Ride Share
   - Fuel

4. **Entertainment**
   - Streaming Services
   - Cinema & Events

5. **Healthcare**
   - Pharmacy
   - Medical Services

6. **Utilities**
   - Telecommunications
   - Bills

7. **Travel**
   - Flights
   - Hotels

8. **Education**
   - Tuition & Courses

9. **Financial Services**
   - Bank Fees
   - ATM Withdrawal

10. **Personal Care**
    - Beauty & Salon

## Priority System

The categorizer uses a priority-based matching system:

### 1. Exact Merchant Match (Highest Priority)
Matches merchant names exactly (case-insensitive):
```python
"McDonald's" → Food & Dining / Restaurants
```

### 2. Fuzzy Merchant Match
Uses multiple fuzzy algorithms for similar names:
```python
"Carrefour Maadi" → Food & Dining / Groceries (matches "carrefour")
"mcdonalds" → Food & Dining / Restaurants (matches "McDonald's")
```

### 3. Keyword Match
Searches for keywords in merchant name:
```python
"Local Restaurant" → Food & Dining / Restaurants (keyword: "restaurant")
"مطعم المدينة" → Food & Dining / Restaurants (keyword: "مطعم")
```

### 4. Fallback (Lowest Priority)
When no match is found:
```python
"Unknown Store XYZ" → Uncategorized / General
```

## Multi-Language Support

The categorizer supports both English and Arabic:

### English Example
```python
record = TransactionRecord(
    id='en-1',
    payee='Pharmacy Plus'
)
result = categorizer.categorize(record)
# Category: Healthcare / Pharmacy
```

### Arabic Example
```python
record = TransactionRecord(
    id='ar-1',
    payee='صيدلية العزبي'
)
result = categorizer.categorize(record)
# Category: Healthcare / Pharmacy
```

### Mixed Language
```python
record = TransactionRecord(
    id='mixed-1',
    payee='Pharmacy صيدلية'
)
result = categorizer.categorize(record)
# Category: Healthcare / Pharmacy
```

## Fuzzy Matching

The categorizer uses three fuzzy matching algorithms:

1. **token_sort_ratio**: Sorts tokens before comparing
2. **token_set_ratio**: Compares token sets, ignoring duplicates
3. **partial_ratio**: Finds best match within strings

The highest score from all algorithms is used, ensuring robust matching:

```python
"Carrefour Maadi" matches "carrefour" with 100% confidence (token_set_ratio)
"Pizza Hut Downtown" matches "pizza" with 90% confidence (substring + boost)
```

## Testing

Run the comprehensive test suite:

```bash
# Run categorizer tests
python -m unittest tests.unit.test_categorizer -v

# Run all tests
python -m unittest discover tests/unit -v
```

The test suite includes:
- 25+ test cases covering all functionality
- Exact, fuzzy, and keyword matching tests
- Arabic and English language tests
- Priority system verification
- Real-world transaction examples
- Edge cases and error handling

## Demo

Run the demo script to see the categorizer in action:

```bash
python categorizer_demo.py
```

The demo demonstrates:
- Basic categorization
- Batch processing
- Priority system
- Multi-language support
- Statistics generation

## API Reference

### Categorizer Class

#### `__init__(rules_path=None, fuzzy_threshold=80)`
Initialize the categorizer.

**Parameters:**
- `rules_path` (str, optional): Path to YAML/JSON rules file. Defaults to `category_rules.yaml`
- `fuzzy_threshold` (int, optional): Minimum fuzzy match score (0-100). Default: 80

#### `categorize(record: TransactionRecord) -> TransactionRecord`
Categorize a single transaction record.

**Parameters:**
- `record` (TransactionRecord): Transaction to categorize

**Returns:**
- TransactionRecord with category, subcategory, and tags populated

#### `categorize_batch(records: List[TransactionRecord]) -> List[TransactionRecord]`
Categorize multiple transaction records.

**Parameters:**
- `records` (List[TransactionRecord]): List of transactions to categorize

**Returns:**
- List of categorized TransactionRecord objects

#### `get_category_statistics(records: List[TransactionRecord]) -> Dict[str, Any]`
Generate statistics about categorization results.

**Parameters:**
- `records` (List[TransactionRecord]): List of categorized transactions

**Returns:**
- Dictionary with statistics including:
  - `total_records`: Total number of records
  - `uncategorized_count`: Number of uncategorized records
  - `uncategorized_percentage`: Percentage uncategorized
  - `categories`: Breakdown by category and subcategory

## Custom Rules

Create a custom rules file to add your own categories:

```yaml
categories:
  - category: "My Category"
    subcategory: "My Subcategory"
    tags:
      - "Custom Tag"
    merchant_exact:
      - "Exact Merchant Name"
    merchant_fuzzy:
      - "fuzzy match"
    keywords:
      english:
        - "keyword"
      arabic:
        - "كلمة مفتاحية"

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags:
    - "Uncategorized"
```

Then load it:

```python
categorizer = Categorizer(rules_path='/path/to/custom_rules.yaml')
```

## Performance

The categorizer is optimized for performance:

- **Single transaction**: < 1ms per categorization
- **Batch processing**: Efficient processing of hundreds of transactions
- **Memory efficient**: Rules loaded once at initialization
- **Lazy evaluation**: Only evaluates rules as needed based on priority

## Best Practices

1. **Use normalized merchant names**: Always populate the `normalized_merchant` field for best results
2. **Adjust fuzzy threshold**: Lower threshold (e.g., 75) for more matches, higher (e.g., 85) for stricter matching
3. **Custom rules for specific needs**: Create custom rules for your specific merchant ecosystem
4. **Batch processing**: Use `categorize_batch()` for multiple transactions
5. **Monitor statistics**: Use `get_category_statistics()` to track categorization accuracy

## Limitations

- Fuzzy matching may incorrectly match very similar merchant names
- Keywords must be predefined in rules file
- No automatic learning or adaptation
- Performance may degrade with very large rule sets (1000+ rules)

## Contributing

To add new categories or improve matching:

1. Edit `category_rules.yaml` to add new categories
2. Add corresponding test cases in `tests/unit/test_categorizer.py`
3. Run tests to ensure no regressions
4. Submit a pull request

## License

Part of the GoldMiner ETL pipeline. See main repository for license details.

## Support

For issues, questions, or contributions, please refer to the main GoldMiner repository.
