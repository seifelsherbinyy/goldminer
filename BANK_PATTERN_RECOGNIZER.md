# Bank Pattern Recognizer

## Overview

The **BankPatternRecognizer** is a powerful module for identifying banks from SMS messages by matching against known pattern fragments. It supports both exact regex pattern matching and fuzzy matching for partial overlaps, making it robust against typos and variations in SMS text.

## Features

- **Pattern Matching**: Uses regex patterns to identify banks from SMS text
- **Fuzzy Matching**: Provides partial string matching using fuzzy algorithms (via fuzzywuzzy)
- **Multilingual Support**: Handles both English and Arabic text seamlessly
- **Configurable Patterns**: Bank patterns are loaded from a YAML file that can be easily customized
- **Confidence Scores**: Returns confidence levels for matches (100 for exact, variable for fuzzy)
- **Batch Processing**: Efficiently process multiple SMS messages at once
- **Statistics Generation**: Get distribution statistics of banks in a message collection
- **Logging**: Automatically logs unmatched SMS messages for review and improvement
- **Unknown Detection**: Returns "unknown_bank" when no match is found

## Installation

The BankPatternRecognizer is included in the GoldMiner analysis module. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

Required packages:
- `pyyaml>=6.0` - For loading pattern configuration
- `fuzzywuzzy>=0.18.0` - For fuzzy string matching
- `python-Levenshtein>=0.12.0` - For faster fuzzy matching

## Quick Start

### Basic Usage

```python
from goldminer.analysis import BankPatternRecognizer

# Initialize the recognizer
recognizer = BankPatternRecognizer()

# Identify bank from a single SMS
bank_id = recognizer.identify_bank("Your HSBC card ending 1234 was charged 250 EGP")
print(bank_id)  # Output: 'HSBC'

# Unknown messages return 'unknown_bank'
bank_id = recognizer.identify_bank("Random text message")
print(bank_id)  # Output: 'unknown_bank'
```

### With Confidence Scores

```python
# Get confidence score along with bank ID
bank_id, confidence = recognizer.identify_bank(
    "HSBC transaction alert",
    return_confidence=True
)
print(f"Bank: {bank_id}, Confidence: {confidence}%")
# Output: Bank: HSBC, Confidence: 100%
```

### Batch Processing

```python
# Process multiple SMS messages at once
messages = [
    "HSBC card transaction",
    "CIB balance alert",
    "NBE withdrawal notification",
    "Unknown message"
]

bank_ids = recognizer.identify_banks_batch(messages)
print(bank_ids)
# Output: ['HSBC', 'CIB', 'NBE', 'unknown_bank']
```

### Bank Statistics

```python
# Get distribution of banks in a message collection
stats = recognizer.get_bank_statistics(messages)
print(stats)
# Output: {'HSBC': 10, 'CIB': 5, 'NBE': 3, 'unknown_bank': 2}
```

## Configuration

### Bank Patterns File

Bank patterns are stored in `bank_patterns.yaml` in the project root. The file structure is:

```yaml
HSBC:
  - "HSBC"
  - "Your HSBC card"
  - "HSBC Egypt"
  - "hsbc\\.com"

CIB:
  - "CIB"
  - "بطاقتك من CIB"
  - "Commercial International Bank"

NBE:
  - "NBE"
  - "National Bank of Egypt"
  - "البنك الأهلي"
```

Each bank ID maps to a list of patterns that can be:
- Simple strings (case-insensitive substring match)
- Regex patterns (e.g., `"hsbc\\.com"` matches "hsbc.com")
- Unicode strings (Arabic, mixed language, etc.)

### Custom Patterns File

You can use a custom patterns file:

```python
recognizer = BankPatternRecognizer(patterns_file='my_custom_patterns.yaml')
```

### Fuzzy Matching Configuration

```python
# Adjust fuzzy matching threshold (0-100)
# Higher values require closer matches
recognizer = BankPatternRecognizer(
    fuzzy_threshold=90,  # Default is 80
    enable_fuzzy=True    # Default is True
)

# Disable fuzzy matching for exact matches only
recognizer = BankPatternRecognizer(enable_fuzzy=False)
```

## API Reference

### BankPatternRecognizer Class

#### Constructor

```python
BankPatternRecognizer(
    patterns_file: Optional[str] = None,
    fuzzy_threshold: int = 80,
    enable_fuzzy: bool = True
)
```

**Parameters:**
- `patterns_file`: Path to YAML file containing bank patterns. If None, uses default `bank_patterns.yaml`
- `fuzzy_threshold`: Minimum fuzzy matching score (0-100). Default is 80
- `enable_fuzzy`: Whether to enable fuzzy matching. Default is True

#### Methods

##### identify_bank()

```python
identify_bank(sms: str, return_confidence: bool = False) -> str
```

Identify the bank from an SMS message.

**Parameters:**
- `sms`: SMS message text to analyze
- `return_confidence`: If True, returns tuple of (bank_id, confidence_score)

**Returns:**
- Bank ID string (e.g., 'HSBC', 'CIB') or 'unknown_bank'
- If return_confidence=True, returns tuple (bank_id, confidence)

**Example:**
```python
bank = recognizer.identify_bank("HSBC transaction")
# Returns: 'HSBC'

bank, conf = recognizer.identify_bank("HSBC transaction", return_confidence=True)
# Returns: ('HSBC', 100)
```

##### identify_banks_batch()

```python
identify_banks_batch(
    sms_list: List[str],
    return_confidence: bool = False
) -> List[str]
```

Identify banks from a batch of SMS messages.

**Parameters:**
- `sms_list`: List of SMS message texts
- `return_confidence`: If True, returns list of tuples (bank_id, confidence)

**Returns:**
- List of bank IDs (or tuples if return_confidence=True)

**Example:**
```python
messages = ["HSBC alert", "CIB notification"]
banks = recognizer.identify_banks_batch(messages)
# Returns: ['HSBC', 'CIB']
```

##### get_bank_statistics()

```python
get_bank_statistics(sms_list: List[str]) -> Dict[str, int]
```

Get statistics on bank distribution in a list of SMS messages.

**Parameters:**
- `sms_list`: List of SMS message texts

**Returns:**
- Dictionary mapping bank IDs to their occurrence counts

**Example:**
```python
stats = recognizer.get_bank_statistics(messages)
# Returns: {'HSBC': 2, 'CIB': 1, 'unknown_bank': 1}
```

##### reload_patterns()

```python
reload_patterns(patterns_file: Optional[str] = None) -> None
```

Reload bank patterns from file.

**Parameters:**
- `patterns_file`: Path to patterns file. If None, reloads from current file

**Example:**
```python
recognizer.reload_patterns('updated_patterns.yaml')
```

## Supported Banks

The default `bank_patterns.yaml` includes patterns for:

**Egyptian Banks:**
- HSBC
- CIB (Commercial International Bank)
- NBE (National Bank of Egypt)
- Banque Misr
- QNB ALAHLI
- Alex Bank
- Banque Du Caire
- AAIB (Arab African International Bank)
- SAIB (Societe Arabe Internationale de Banque)
- ADIB (Abu Dhabi Islamic Bank)
- Faisal Islamic Bank
- Emirates NBD
- BLOM Bank
- Credit Agricole

**International Banks:**
- Citibank
- Barclays
- Standard Chartered

**Mobile Wallets:**
- Vodafone Cash
- Etisalat Cash
- Orange Cash

**Payment Services:**
- Fawry
- Masary

You can easily add more banks by editing the `bank_patterns.yaml` file.

## Integration with SMS Loading

The BankPatternRecognizer integrates seamlessly with GoldMiner's SMS loading functionality:

```python
from goldminer.etl import load_sms_messages
from goldminer.analysis import BankPatternRecognizer

# Load SMS messages from a file
messages = load_sms_messages('sms_export.txt')

# Identify banks
recognizer = BankPatternRecognizer()
bank_ids = recognizer.identify_banks_batch(messages)

# Get statistics
stats = recognizer.get_bank_statistics(messages)
print(f"Processed {len(messages)} SMS across {len(stats)} banks")
```

## Examples

See `bank_recognizer_examples.py` for comprehensive examples including:
1. Basic bank identification
2. Confidence scores
3. Batch processing
4. Statistics generation
5. Custom patterns
6. Integration with SMS loading
7. Arabic language support

Run the examples:
```bash
python bank_recognizer_examples.py
```

## Logging

The BankPatternRecognizer automatically logs:
- **INFO**: Successful matches with bank ID and SMS preview
- **WARNING**: Unmatched SMS messages (returned as 'unknown_bank')
- **ERROR**: Configuration or pattern loading errors

Review logs to identify:
- Patterns that might need improvement
- New banks to add
- Messages that don't match any known patterns

## Best Practices

1. **Review Unknown Messages**: Regularly check logs for 'unknown_bank' messages to identify new patterns
2. **Tune Fuzzy Threshold**: Adjust `fuzzy_threshold` based on your accuracy needs (higher = stricter)
3. **Test New Patterns**: After updating patterns, run tests to ensure they work correctly
4. **Use Batch Processing**: For multiple messages, use `identify_banks_batch()` for better performance
5. **Monitor Confidence**: Use `return_confidence=True` to track matching quality
6. **Handle Edge Cases**: Empty, None, or malformed SMS are safely handled and logged

## Testing

The module includes comprehensive unit tests covering:
- Exact pattern matching
- Fuzzy matching
- Arabic text support
- Case-insensitive matching
- Edge cases (empty, None, invalid input)
- Batch processing
- Statistics generation
- Configuration validation

Run tests:
```bash
python -m unittest tests.unit.test_bank_recognizer
```

## Troubleshooting

### Issue: No matches found for valid bank SMS
**Solution**: Check if the bank's patterns are in `bank_patterns.yaml`. Add missing patterns if needed.

### Issue: Too many false positives
**Solution**: Increase `fuzzy_threshold` or disable fuzzy matching with `enable_fuzzy=False`.

### Issue: Pattern file not found
**Solution**: Ensure `bank_patterns.yaml` exists in the project root, or provide a custom path.

### Issue: Arabic text not matching
**Solution**: Ensure your patterns file is saved with UTF-8 encoding and includes Arabic patterns.

## Contributing

To add support for new banks:

1. Edit `bank_patterns.yaml`
2. Add a new bank ID with its patterns
3. Test with sample SMS messages
4. Submit a pull request

Example:
```yaml
NEW_BANK:
  - "NEW BANK"
  - "New Bank Egypt"
  - "NB-"
```

## License

Part of the GoldMiner project. See main project LICENSE for details.
