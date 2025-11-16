# CardClassifier Component

The CardClassifier component extracts card suffixes from SMS messages and maps them to account metadata. It supports both English and Arabic text patterns, handles Arabic-Indic numerals, and provides robust account lookup functionality.

## Features

- **Multi-language Support**: Extracts card suffixes from both English and Arabic SMS messages
- **Arabic-Indic Numerals**: Automatically converts Arabic-Indic numerals (٠-٩) to Western numerals (0-9)
- **Flexible Pattern Matching**: Recognizes various card suffix patterns:
  - English: "ending 1234", "card ending 1234", "card **1234", "Card 1234"
  - Arabic: "رقم 1234", "بطاقة رقم 1234", "بطاقة 1234"
- **Account Metadata Lookup**: Maps card suffixes to detailed account information
- **Fallback Handling**: Gracefully handles unknown card suffixes with default values
- **Integration with RegexParserEngine**: Enhances SMS parsing with improved card suffix extraction

## Installation

The CardClassifier is part of the goldminer analysis module:

```python
from goldminer.analysis import CardClassifier
```

## Quick Start

### Basic Card Suffix Extraction

```python
from goldminer.analysis import CardClassifier

# Extract suffix from English SMS
suffix = CardClassifier.extract_card_suffix("Transaction on card ending 1234")
print(suffix)  # Output: "1234"

# Extract suffix from Arabic SMS
suffix = CardClassifier.extract_card_suffix("بطاقة رقم ١٢٣٤")
print(suffix)  # Output: "1234" (Arabic-Indic numerals converted)

# Handle SMS without card info
suffix = CardClassifier.extract_card_suffix("Generic transaction")
print(suffix)  # Output: None
```

### Account Metadata Lookup

```python
from goldminer.analysis import CardClassifier

# Initialize classifier (loads accounts.yaml by default)
classifier = CardClassifier()

# Look up account by card suffix
account = classifier.lookup_account("1234")

print(account['account_id'])      # ACC-HSBC-001
print(account['account_type'])    # Credit
print(account['label'])           # HSBC Credit Card - Primary
print(account['is_known'])        # True

# Credit card accounts include additional fields
if account['account_type'] == 'Credit':
    print(account['interest_rate'])   # 19.99
    print(account['credit_limit'])    # 50000.00
    print(account['billing_cycle'])   # 15
```

### Complete SMS Classification

```python
from goldminer.analysis import CardClassifier

classifier = CardClassifier()

# Classify SMS in one step
result = classifier.classify_sms("HSBC: Transaction of 100 EGP on card ending 1234")

print(result['card_suffix'])      # "1234"
print(result['account_id'])       # "ACC-HSBC-001"
print(result['account_type'])     # "Credit"
print(result['is_known'])         # True
```

### Integration with RegexParserEngine

```python
from goldminer.analysis import RegexParserEngine

# CardClassifier is enabled by default
parser = RegexParserEngine(use_card_classifier=True)

sms = "HSBC: charged 100 EGP on Card **1234"
result = parser.parse_sms(sms, bank_id="HSBC")

print(result['amount'])           # "100"
print(result['currency'])         # "EGP"
print(result['card_suffix'])      # "1234" (extracted by CardClassifier)

# Disable CardClassifier for template-only extraction
parser = RegexParserEngine(use_card_classifier=False)
```

## Account Metadata Schema

The account metadata file (`accounts.yaml`) should follow this structure:

```yaml
"1234":  # Card suffix (last 4 digits)
  account_id: "ACC-HSBC-001"           # Required: Unique account identifier
  account_type: "Credit"                # Required: Credit, Debit, or Prepaid
  interest_rate: 19.99                  # Optional: For credit cards (%)
  credit_limit: 50000.00                # Optional: For credit cards
  billing_cycle: 15                     # Optional: Day of month (1-31)
  label: "HSBC Credit Card - Primary"   # Required: Human-readable label
```

### Account Types

- **Credit**: Credit card with interest rate and credit limit
- **Debit**: Debit card linked to checking/savings account
- **Prepaid**: Prepaid card with preloaded balance

## Advanced Usage

### Custom Accounts File

```python
classifier = CardClassifier(accounts_file="/path/to/custom_accounts.yaml")
```

### Reloading Accounts

```python
classifier = CardClassifier()

# Make changes to accounts.yaml...

# Reload without creating new instance
classifier.reload_accounts()
```

### Arabic-Indic Numeral Conversion

```python
from goldminer.analysis import CardClassifier

# Convert Arabic-Indic numerals
text = "بطاقة رقم ١٢٣٤"
converted = CardClassifier.convert_arabic_indic_numerals(text)
print(converted)  # "بطاقة رقم 1234"
```

## Supported Card Suffix Patterns

### English Patterns

- `ending 1234` - "Transaction on card ending 1234"
- `card ending 1234` - "HSBC card ending 1234 charged"
- `card 1234` - "HSBC card 1234 charged 100 EGP"
- `Card **1234` - "Card **1234 used"
- `****1234` - "Transaction on ****1234"

### Arabic Patterns

- `رقم 1234` - "بطاقة رقم 1234"
- `بطاقة رقم 1234` - "خصم من بطاقة رقم 1234"
- `بطاقة 1234` - "بطاقة 1234 خصم"
- `رقم ١٢٣٤` - "رقم ١٢٣٤" (with Arabic-Indic numerals)

## Error Handling

### Unknown Card Suffixes

When a card suffix is not found in the accounts metadata, the classifier returns a fallback response:

```python
classifier = CardClassifier()
result = classifier.lookup_account("9999")  # Unknown suffix

# Fallback response
print(result['account_id'])       # "unknown_9999"
print(result['account_type'])     # "Unknown"
print(result['is_known'])         # False
print(result['interest_rate'])    # None
print(result['credit_limit'])     # None
```

### Missing Account File

If the accounts file doesn't exist, the classifier initializes with an empty dictionary and logs a warning:

```python
classifier = CardClassifier(accounts_file="nonexistent.yaml")
# Logs: WARNING - Accounts file not found: nonexistent.yaml
# All lookups will return fallback responses
```

### Invalid Account Data

If the accounts file contains invalid data (missing required fields), the classifier raises a `ValueError`:

```python
# Invalid accounts.yaml:
# "1234":
#   account_type: "Credit"
#   # Missing required 'account_id' field

classifier = CardClassifier(accounts_file="invalid.yaml")
# Raises: ValueError: Account '1234' missing required field: account_id
```

## Testing

The CardClassifier includes comprehensive unit tests:

```bash
# Run CardClassifier tests
python -m unittest tests.unit.test_card_classifier -v

# Run integration tests with RegexParserEngine
python -m unittest tests.unit.test_regex_parser_engine -v
```

## Examples

See `card_classifier_demo.py` for comprehensive examples demonstrating:

1. Basic card suffix extraction
2. Account metadata lookup
3. Complete SMS classification workflow
4. Integration with RegexParserEngine
5. Arabic-Indic numeral conversion

Run the demo:

```bash
python card_classifier_demo.py
```

## API Reference

### CardClassifier Class

#### `__init__(accounts_file: Optional[str] = None)`

Initialize the CardClassifier.

**Parameters:**
- `accounts_file` (str, optional): Path to YAML file with account metadata. Defaults to `accounts.yaml` in project root.

**Raises:**
- `ValueError`: If accounts file is invalid or malformed

#### `extract_card_suffix(sms: str) -> Optional[str]`

Static method to extract card suffix from SMS text.

**Parameters:**
- `sms` (str): SMS message text

**Returns:**
- `str`: 4-digit card suffix, or `None` if not found

#### `lookup_account(card_suffix: str) -> Dict[str, Any]`

Look up account metadata by card suffix.

**Parameters:**
- `card_suffix` (str): 4-digit card suffix

**Returns:**
- `dict`: Account metadata including:
  - `account_id` (str): Account identifier
  - `account_type` (str): Credit, Debit, or Prepaid
  - `interest_rate` (float or None): Interest rate for credit cards
  - `credit_limit` (float or None): Credit limit for credit cards
  - `billing_cycle` (int or None): Billing cycle day
  - `label` (str): Human-readable label
  - `card_suffix` (str): The card suffix
  - `is_known` (bool): Whether account was found

#### `classify_sms(sms: str) -> Dict[str, Any]`

Extract card suffix and return associated account metadata.

**Parameters:**
- `sms` (str): SMS message text

**Returns:**
- `dict`: Account metadata (same as `lookup_account`)

#### `reload_accounts(accounts_file: Optional[str] = None)`

Reload account metadata from file.

**Parameters:**
- `accounts_file` (str, optional): Path to accounts file. If None, reloads from current file.

#### `convert_arabic_indic_numerals(text: str) -> str`

Static method to convert Arabic-Indic numerals to Western numerals.

**Parameters:**
- `text` (str): Text containing Arabic-Indic numerals

**Returns:**
- `str`: Text with converted numerals

## Integration with RegexParserEngine

The RegexParserEngine can use CardClassifier for enhanced card suffix extraction:

```python
parser = RegexParserEngine(use_card_classifier=True)  # Default
```

When enabled, CardClassifier is used as a fallback when template patterns don't match. This provides more robust card suffix extraction across different SMS formats.

## Best Practices

1. **Keep Account Metadata Updated**: Regularly update `accounts.yaml` with new cards and account information
2. **Use Descriptive Labels**: Make labels human-readable for better reporting and debugging
3. **Enable CardClassifier**: Keep `use_card_classifier=True` in RegexParserEngine for best results
4. **Handle Unknown Cards**: Always check `is_known` field in results and handle unknown cards appropriately
5. **Monitor Logs**: CardClassifier logs warnings for unknown suffixes and missing files

## Limitations

- Card suffixes must be exactly 4 digits
- Only supports card suffixes (last 4 digits), not full card numbers
- Account metadata must be manually maintained in YAML file
- No automatic detection of expired cards or credit limit updates

## Future Enhancements

Potential improvements for future versions:

- SQLite storage option for account metadata
- Support for card expiration dates
- Automatic credit limit tracking
- Integration with banking APIs for real-time data
- Support for 6-digit card suffixes (some banks use last 6 digits)
- Card type detection (Visa, Mastercard, etc.)
