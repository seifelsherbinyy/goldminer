# PromoClassifier Documentation

## Overview

The `PromoClassifier` is a component designed to identify and filter promotional/marketing SMS messages before they enter the transaction processing pipeline. It uses keyword-based classification with support for both English and Arabic languages.

## Features

- **Bilingual Support**: Detects promotional keywords in both English and Arabic
- **Configurable Keywords**: Load custom keyword sets from YAML configuration files
- **Structured Results**: Returns detailed classification results with confidence levels
- **Batch Processing**: Efficiently classify multiple messages at once
- **Flexible Integration**: Easy to integrate into existing ETL pipelines

## Installation

The PromoClassifier is part of the goldminer ETL module:

```python
from goldminer.etl import PromoClassifier, PromoResult
```

## Quick Start

### Basic Usage

```python
from goldminer.etl import PromoClassifier

# Initialize classifier
classifier = PromoClassifier()

# Classify a message
result = classifier.classify("Get 50% discount today!")

if result.skip:
    print(f"Promotional message: {result.reason}")
else:
    print("Transaction message - proceed to parser")
```

### Simple Boolean Check

```python
# Use the simple boolean method
is_promo = classifier.is_promotional("Special offer for you!")
print(f"Is promotional: {is_promo}")  # True
```

## Detailed Usage

### Classification Results

The `classify()` method returns a `PromoResult` object with detailed information:

```python
result = classifier.classify("Limited time offer: 50% off everything!")

print(f"Skip: {result.skip}")                      # True
print(f"Reason: {result.reason}")                  # "Promotional message detected..."
print(f"Confidence: {result.confidence}")          # "high"
print(f"Keywords: {result.matched_keywords}")      # ['offer', 'limited time', 'off']
```

### Confidence Levels

The classifier assigns confidence levels based on the number of matched keywords:

- **High**: 3 or more keyword matches
- **Medium**: 2 keyword matches
- **Low**: 1 keyword match

### Batch Processing

Process multiple messages efficiently:

```python
messages = [
    "Flash sale alert!",
    "Your card was charged 100 EGP",
    "Win amazing prizes!"
]

results = classifier.classify_batch(messages)

for msg, result in zip(messages, results):
    status = "PROMO" if result.skip else "TRANS"
    print(f"[{status}] {msg}")
```

## Configuration

### Using Default Keywords

By default, the classifier loads keywords from `promo_keywords.yaml` in the project root:

```python
classifier = PromoClassifier()
```

### Custom YAML File

Load keywords from a custom YAML file:

```python
classifier = PromoClassifier(keywords_file='/path/to/custom_keywords.yaml')
```

### YAML File Format

```yaml
# promo_keywords.yaml
english:
  - "offer"
  - "discount"
  - "sale"
  - "special offer"

arabic:
  - "عرض خاص"
  - "خصومات"
  - "مجاني"
```

### Runtime Keyword Management

Add or remove keywords at runtime:

```python
# Add keywords
classifier.add_keywords(
    english=["clearance", "liquidation"],
    arabic=["تصفية", "نهاية الموسم"]
)

# Remove keywords
classifier.remove_keywords(
    english=["clearance"]
)

# Get current keywords
keywords = classifier.get_keywords()
print(keywords['english'])  # List of English keywords
print(keywords['arabic'])   # List of Arabic keywords
```

## Integration with ETL Pipeline

### Filter Messages Before Parsing

```python
from goldminer.etl import PromoClassifier, load_sms_messages

# Load SMS messages
messages = load_sms_messages('sms_export.txt')

# Initialize classifier
classifier = PromoClassifier()

# Filter messages
transactional_messages = []
for msg in messages:
    result = classifier.classify(msg)
    if not result.skip:
        transactional_messages.append(msg)

print(f"Filtered {len(messages) - len(transactional_messages)} promotional messages")

# Continue with transaction parsing
# ... parse transactional_messages ...
```

### Pipeline Integration Pattern

```python
def process_sms_pipeline(messages):
    """Process SMS messages through the pipeline."""
    classifier = PromoClassifier()
    
    for msg in messages:
        # Step 1: Filter promotional messages
        promo_result = classifier.classify(msg)
        if promo_result.skip:
            print(f"Skipped: {promo_result.reason}")
            continue
        
        # Step 2: Parse transaction
        transaction = parse_transaction(msg)
        
        # Step 3: Validate transaction
        validated = validate_transaction(transaction)
        
        # Step 4: Store in database
        store_transaction(validated)
```

## Default Keywords

### English Keywords

- offer, discount, sale, enjoy, special offer
- limited time, promotion, promo, deal, deals
- save, saving, cashback, reward, rewards
- exclusive, free, gift, bonus, win, winner
- congratulations, congrats, voucher, coupon, redeem
- off, % off, percent off

### Arabic Keywords

- عرض خاص, لفترة محدودة, عروض
- توفير, مجاني, هدية
- مكافأة, مكافآت, حصري
- خصومات, استمتع, تخفيض, تخفيضات
- كاش باك, قسيمة, كوبون
- مبروك, فائز, اربح, جائزة
- وفر الآن, احصل على, فرصة

**Note**: Ambiguous keywords like "خصم" (which can mean both "discount" and "debit") are intentionally excluded to avoid false positives with transaction messages.

## Borderline Cases

Some messages contain promotional keywords but are actually transaction notifications:

```python
# These will be flagged as promotional due to keywords:
"Your cashback of 50 EGP has been credited"  # Contains "cashback"
"Reward points redeemed: 100 points"         # Contains "reward"
"Gift card purchase: 200 USD charged"        # Contains "gift"
```

The classifier is designed to be conservative and flag potential promotional content. If you need more nuanced classification, consider:

1. Adding contextual analysis
2. Using machine learning models
3. Customizing keyword lists for your specific use case

## Testing

Run the comprehensive test suite:

```bash
python -m unittest tests.unit.test_promo_classifier -v
```

Run the demo examples:

```bash
python promo_classifier_demo.py
```

## API Reference

### PromoClassifier

#### `__init__(keywords_file: Optional[str] = None)`

Initialize the classifier.

- `keywords_file`: Path to YAML file with custom keywords

#### `classify(sms: str) -> PromoResult`

Classify an SMS message.

- Returns: `PromoResult` with detailed classification information

#### `is_promotional(sms: str) -> bool`

Simple boolean check for promotional content.

- Returns: `True` if promotional, `False` otherwise

#### `classify_batch(messages: List[str]) -> List[PromoResult]`

Classify multiple messages.

- Returns: List of `PromoResult` objects

#### `add_keywords(english: List[str], arabic: List[str])`

Add custom keywords at runtime.

#### `remove_keywords(english: List[str], arabic: List[str])`

Remove keywords at runtime.

#### `get_keywords() -> Dict[str, List[str]]`

Get current keyword sets.

### PromoResult

#### Attributes

- `skip` (bool): Whether to skip this message
- `reason` (str): Reason for classification
- `matched_keywords` (List[str]): List of matched keywords
- `confidence` (str): Confidence level ('high', 'medium', 'low')

#### `to_dict() -> Dict[str, Any]`

Convert result to dictionary.

## Examples

See `promo_classifier_demo.py` for comprehensive examples including:

1. Basic usage
2. Detailed classification results
3. Batch processing
4. Custom keywords
5. Pipeline integration
6. Borderline cases
7. Multilingual messages

## Best Practices

1. **Filter Early**: Apply PromoClassifier before transaction parsing to save processing time
2. **Custom Keywords**: Tailor keyword lists to your specific message types
3. **Monitor Results**: Log filtered messages to identify patterns and adjust keywords
4. **Multilingual**: Consider adding language-specific keyword sets for your region
5. **Regular Updates**: Review and update keywords based on new promotional patterns

## Limitations

- **Keyword-Based**: Relies on predefined keywords, may miss novel promotional patterns
- **Context-Limited**: Doesn't consider message context or semantics
- **Conservative**: May flag some transaction messages that contain promotional keywords

For more sophisticated classification, consider combining PromoClassifier with:
- Machine learning models
- NLP-based semantic analysis
- Rule-based heuristics for specific transaction patterns

## Support

For issues, questions, or contributions, please refer to the main GoldMiner repository documentation.
