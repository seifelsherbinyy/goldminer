# RegexParserEngine Documentation

## Overview

The `RegexParserEngine` is a powerful SMS parsing system that extracts structured transaction fields from bank SMS messages. It supports multiple languages (English and Arabic), handles partial matches with confidence indicators, and uses bank-specific regex templates for accurate extraction.

## Features

- **Multi-Bank Support**: Supports HSBC, CIB, NBE, QNB, and generic bank templates
- **Multi-Language**: Handles both English and Arabic SMS messages
- **Flexible Templates**: Uses YAML/JSON configuration files for easy customization
- **Confidence Indicators**: Flags low confidence when critical fields are missing
- **Batch Processing**: Parse multiple SMS messages efficiently
- **Field Extraction**: Extracts amount, currency, date, payee, transaction type, and card suffix
- **Error Handling**: Robust error handling for malformed input and partial matches
- **Extensible**: Easy to add new banks and templates

## Installation

The RegexParserEngine is part of the GoldMiner package. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from goldminer.analysis import RegexParserEngine

# Initialize parser with default templates
parser = RegexParserEngine()

# Parse an English SMS
sms = "Your HSBC card ending 1234 was charged 250.50 EGP at Store XYZ on 15/11/2024"
result = parser.parse_sms(sms, bank_id="HSBC")

print(f"Amount: {result['amount']}")           # Output: 250.50
print(f"Currency: {result['currency']}")       # Output: EGP
print(f"Card Suffix: {result['card_suffix']}")  # Output: 1234
print(f"Confidence: {result['confidence']}")   # Output: high
```

### Parse Arabic SMS

```python
# Parse an Arabic SMS
sms_ar = "تم خصم 150 جنيه من بطاقة رقم 5678 في محل ABC"
result = parser.parse_sms(sms_ar, bank_id="CIB")

print(f"Amount: {result['amount']}")      # Output: 150
print(f"Currency: {result['currency']}")  # Output: جنيه
```

### Auto-Detect Bank

```python
# Parse without specifying bank (tries all banks)
sms = "Card ending 1234 charged 100 EGP at Store"
result = parser.parse_sms(sms)

print(f"Matched Bank: {result['matched_bank']}")  # Output: auto-detected bank
```

### Batch Processing

```python
# Process multiple SMS messages at once
messages = [
    "Card ending 1234 charged 100 EGP at Store",
    "Card ending 5678 charged 200 USD",
    "Transaction of 300 EUR"
]
bank_ids = ["HSBC", "HSBC", "Generic_Bank"]

results = parser.parse_sms_batch(messages, bank_ids=bank_ids)
for result in results:
    print(f"Amount: {result['amount']}, Confidence: {result['confidence']}")
```

## API Reference

### RegexParserEngine

#### `__init__(templates_file: Optional[str] = None)`

Initialize the parser.

**Parameters:**
- `templates_file` (str, optional): Path to YAML/JSON templates file. If None, uses default templates.

**Raises:**
- `FileNotFoundError`: If templates file doesn't exist
- `ValueError`: If templates file is invalid

**Example:**
```python
# Use default templates
parser = RegexParserEngine()

# Use custom templates
parser = RegexParserEngine("/path/to/custom_templates.yaml")
```

#### `parse_sms(sms: str, bank_id: Optional[str] = None, template_name: Optional[str] = None)`

Parse an SMS message and extract transaction fields.

**Parameters:**
- `sms` (str): SMS message text to parse
- `bank_id` (str, optional): Bank identifier (e.g., 'HSBC', 'CIB'). If None, tries all banks.
- `template_name` (str, optional): Specific template name to use. If None, tries all templates for the bank.

**Returns:**
- `dict`: Dictionary containing:
  - `amount` (str or None): Transaction amount
  - `currency` (str or None): Currency code
  - `date` (str or None): Transaction date
  - `payee` (str or None): Payee/merchant name
  - `transaction_type` (str or None): Type of transaction (POS, ATM, Online, etc.)
  - `card_suffix` (str or None): Last 4 digits of card
  - `confidence` (str): Confidence level ('high', 'medium', 'low')
  - `matched_bank` (str): Bank ID that matched
  - `matched_template` (str): Template name that matched

**Example:**
```python
result = parser.parse_sms(
    "Card ending 1234 charged 100 EGP",
    bank_id="HSBC"
)
```

#### `parse_sms_batch(sms_list: List[str], bank_ids: Optional[List[str]] = None)`

Parse multiple SMS messages in batch.

**Parameters:**
- `sms_list` (List[str]): List of SMS messages
- `bank_ids` (List[str], optional): List of bank IDs corresponding to each SMS. If None, tries all banks for each SMS.

**Returns:**
- `List[dict]`: List of parsed result dictionaries

**Example:**
```python
messages = ["SMS 1", "SMS 2"]
results = parser.parse_sms_batch(messages, bank_ids=["HSBC", "CIB"])
```

#### `get_supported_banks()`

Get list of supported bank IDs.

**Returns:**
- `List[str]`: List of bank identifiers

**Example:**
```python
banks = parser.get_supported_banks()
# Output: ['HSBC', 'CIB', 'NBE', 'QNB', 'Generic_Bank']
```

#### `get_bank_templates(bank_id: str)`

Get list of template names for a specific bank.

**Parameters:**
- `bank_id` (str): Bank identifier

**Returns:**
- `List[str]`: List of template names

**Raises:**
- `ValueError`: If bank_id is not found

**Example:**
```python
templates = parser.get_bank_templates("HSBC")
# Output: ['HSBC Standard Transaction', 'HSBC Arabic Transaction']
```

#### `reload_templates(templates_file: Optional[str] = None)`

Reload parsing templates from file.

**Parameters:**
- `templates_file` (str, optional): Path to templates file. If None, reloads from current file.

**Example:**
```python
parser.reload_templates()  # Reload from same file
parser.reload_templates("/path/to/new_templates.yaml")  # Load new file
```

## Template Configuration

### Template Structure

Templates are defined in YAML or JSON format. Each bank can have multiple templates to handle different SMS formats.

```yaml
BANK_NAME:
  - name: "Template Name"
    patterns:
      amount: "regex pattern with (?P<amount>...)"
      currency: "regex pattern with (?P<currency>...)"
      date: "regex pattern with (?P<date>...)"
      payee: "regex pattern with (?P<payee>...)"
      transaction_type: "regex pattern with (?P<transaction_type>...)"
      card_suffix: "regex pattern with (?P<card_suffix>...)"
    required_fields: ["amount", "currency"]
```

### Example Template

```yaml
HSBC:
  - name: "HSBC Standard Transaction"
    patterns:
      amount: "(?:charged|debited|paid)\\s+(?P<amount>\\d+(?:[,.]\\d{2})?)"
      currency: "(?P<amount_val>\\d+(?:[,.]\\d{2})?)\\s+(?P<currency>EGP|USD|EUR)"
      date: "(?:on|date)\\s+(?P<date>\\d{2}/\\d{2}/\\d{4})"
      payee: "(?:at|from)\\s+(?P<payee>[A-Za-z0-9\\s]+?)(?:\\s+on|\\.)"
      transaction_type: "(?P<transaction_type>POS|ATM|Online)"
      card_suffix: "(?:ending|card)\\s+(?P<card_suffix>\\d{4})"
    required_fields: ["amount", "currency"]
```

### Pattern Guidelines

1. **Use Context Words**: Include context words (charged, debited, at, from) to avoid false matches
2. **Named Groups**: Each pattern must have a named group matching the field name
3. **Case Insensitive**: All patterns are matched case-insensitively
4. **Unicode Support**: Patterns support Arabic and other Unicode characters
5. **Required Fields**: Specify which fields are critical for confidence calculation

## Confidence Calculation

The parser assigns a confidence level based on extracted fields:

- **High**: All required fields + most optional fields extracted
- **Medium**: All required fields + some optional fields extracted
- **Low**: Missing required fields or very few fields extracted

Example:
```python
# High confidence - all required fields present
sms = "Card ending 1234 charged 100 EGP at Store on 15/11/2024"
result = parser.parse_sms(sms, bank_id="HSBC")
print(result['confidence'])  # Output: high

# Low confidence - missing currency (required field)
sms = "Transaction of 100"
result = parser.parse_sms(sms, bank_id="HSBC")
print(result['confidence'])  # Output: low
```

## Error Handling

The parser handles various error conditions gracefully:

```python
# Empty SMS
result = parser.parse_sms("")
print(result['confidence'])  # Output: low

# None input
result = parser.parse_sms(None)
print(result['confidence'])  # Output: low

# Invalid bank ID
result = parser.parse_sms("SMS text", bank_id="INVALID_BANK")
print(result['confidence'])  # Output: low

# No matching template
result = parser.parse_sms("Random text without transaction info", bank_id="HSBC")
print(result['confidence'])  # Output: low
```

## Supported Banks

The default templates support the following banks:

1. **HSBC** - HSBC Egypt
2. **CIB** - Commercial International Bank
3. **NBE** - National Bank of Egypt
4. **QNB** - QNB ALAHLI
5. **Generic_Bank** - Generic patterns for other banks

## Supported Languages

- **English**: Full support with context-aware patterns
- **Arabic**: Full support for Arabic text including:
  - Amount extraction (مبلغ, خصم, دفع)
  - Currency (جنيه, دولار, يورو, ريال)
  - Transaction types (صراف, شراء, سحب, تحويل)
  - Mixed language SMS messages

## Examples

### Running the Demo

A comprehensive demonstration script is included:

```bash
python regex_parser_demo.py
```

This demonstrates:
- English SMS parsing
- Arabic SMS parsing
- Mixed language SMS
- Auto-detection of banks
- Partial matches with low confidence
- Batch processing

### Real-World Examples

```python
from goldminer.analysis import RegexParserEngine

parser = RegexParserEngine()

# Example 1: Full English transaction
sms = "Dear Customer, Your HSBC card ending 1234 was charged 250.50 EGP at Amazon Store on 15/11/2024."
result = parser.parse_sms(sms, bank_id="HSBC")
# Result: amount='250.50', currency='EGP', card='1234', date='15/11/2024', confidence='high'

# Example 2: Arabic transaction
sms = "عزيزي العميل، تم خصم 150 جنيه من بطاقة رقم 5678"
result = parser.parse_sms(sms, bank_id="HSBC")
# Result: amount='150', currency='جنيه', card='5678', confidence='medium'

# Example 3: ATM withdrawal
sms = "NBE Transaction: withdrawal of 1000 EGP from ATM on 13/11/2024 card 9999"
result = parser.parse_sms(sms, bank_id="NBE")
# Result: amount='1000', currency='EGP', type='withdrawal', card='9999', confidence='high'

# Example 4: Multiple transactions
messages = [
    "Card ending 1111 charged 100 EGP",
    "Card ending 2222 charged 200 USD",
    "Card ending 3333 charged 300 EUR"
]
results = parser.parse_sms_batch(messages, bank_ids=["HSBC"] * 3)
# Results: 3 parsed transactions with extracted amounts, currencies, and cards
```

## Testing

The RegexParserEngine includes comprehensive unit tests:

```bash
# Run all tests
python -m unittest discover -s tests/unit -p "test_*.py"

# Run only RegexParserEngine tests
python -m unittest tests.unit.test_regex_parser_engine -v

# Run doctests
python -m doctest goldminer/analysis/regex_parser_engine.py -v
```

Test coverage includes:
- 37 unit tests
- 19 doctests
- English and Arabic parsing
- Confidence calculation
- Error handling
- Batch processing
- Template loading from YAML/JSON

## Extending the Parser

### Adding a New Bank

1. Open `sms_parsing_templates.yaml`
2. Add a new bank section:

```yaml
NEW_BANK:
  - name: "NEW_BANK Standard"
    patterns:
      amount: "(?:charged|paid)\\s+(?P<amount>\\d+(?:[,.]\\d{2})?)"
      currency: "(?P<amount_val>\\d+)\\s+(?P<currency>EGP|USD)"
      # ... other patterns
    required_fields: ["amount", "currency"]
```

3. Reload templates or restart:

```python
parser = RegexParserEngine()
# or
parser.reload_templates()
```

### Custom Templates

Create your own templates file:

```python
# custom_templates.yaml
MY_BANK:
  - name: "Custom Template"
    patterns:
      amount: "\\$(?P<amount>\\d+\\.\\d{2})"
      currency: "(?P<currency>USD)"
    required_fields: ["amount"]
```

Use it:

```python
parser = RegexParserEngine(templates_file="custom_templates.yaml")
```

## Troubleshooting

### Issue: Pattern not matching

**Solution**: Check that the pattern includes context words and proper escaping:
```python
# Bad: Too generic
"(?P<amount>\\d+)"

# Good: Context-aware
"(?:charged|paid)\\s+(?P<amount>\\d+(?:[,.]\\d{2})?)"
```

### Issue: Wrong field extracted

**Solution**: Ensure named groups match field names:
```python
# The pattern must use the exact field name as the named group
currency: "(?P<currency>EGP|USD)"  # Correct
currency: "(?P<curr>EGP|USD)"      # Wrong - won't extract properly
```

### Issue: Low confidence despite matching

**Solution**: Check that required fields are specified correctly in the template:
```yaml
required_fields: ["amount", "currency"]  # These must be present for high confidence
```

## Performance Considerations

- Templates are loaded once at initialization
- Regex compilation is cached by Python's `re` module
- Batch processing is more efficient than individual parsing
- Consider using specific bank_id when known to avoid trying all banks

## License

Part of the GoldMiner project. See main repository for license details.

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/seifelsherbinyy/goldminer
- Issues: https://github.com/seifelsherbinyy/goldminer/issues
