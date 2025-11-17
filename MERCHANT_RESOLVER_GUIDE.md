# MerchantResolver Guide

## Overview

The `MerchantResolver` is a powerful utility class that resolves merchant/payee names to their canonical forms using intelligent fuzzy matching. It's designed to handle variations in merchant names, including typos, case differences, language variations (Arabic and English), and partial matches.

## Features

- **RapidFuzz-based Fuzzy Matching**: Uses RapidFuzz library for accurate and fast string similarity matching
- **Two-Stage Matching**: 
  1. Exact match (case-insensitive) for perfect aliases
  2. Fuzzy match for similar names above a configurable threshold
- **Multi-Language Support**: Handles both Arabic (العربية) and English merchant names seamlessly
- **Configurable Threshold**: Default 85% similarity threshold, customizable per instance
- **Confidence Scores**: Optional return of confidence scores (0-100) for matches
- **Comprehensive Logging**: Logs matching details and unresolvable entries for debugging
- **Helper Methods**: Additional utilities for merchant information and exploration

## Installation

The MerchantResolver is included in the GoldMiner package. Ensure you have the required dependencies:

```bash
pip install rapidfuzz>=3.0.0
```

This is already included in the `requirements.txt` file.

## Quick Start

### Basic Usage

```python
from goldminer.utils import MerchantResolver

# Initialize the resolver
resolver = MerchantResolver()

# Resolve a merchant name
canonical = resolver.resolve_merchant("Carrefour City")
print(canonical)  # Output: "Carrefour"

# Resolve with confidence score
canonical, confidence = resolver.resolve_merchant(
    "CARREFOUR MAADI",
    return_confidence=True
)
print(f"{canonical} ({confidence}%)")  # Output: "Carrefour (100.0%)"
```

### Arabic Support

```python
# Resolve Arabic merchant names
canonical = resolver.resolve_merchant("كارفور")
print(canonical)  # Output: "Carrefour"

canonical = resolver.resolve_merchant("ماكدونالدز")
print(canonical)  # Output: "McDonald's"

canonical = resolver.resolve_merchant("فودافون")
print(canonical)  # Output: "Vodafone"
```

## API Reference

### Initialization

```python
MerchantResolver(
    aliases_path: Optional[str] = None,
    similarity_threshold: float = 85.0
)
```

**Parameters:**
- `aliases_path` (str, optional): Path to YAML file containing merchant aliases. If None, uses default `merchant_aliases.yaml` in project root.
- `similarity_threshold` (float): Minimum similarity score (0-100) for fuzzy matching. Default is 85.0 (85%).

**Raises:**
- `FileNotFoundError`: If aliases file doesn't exist
- `ValueError`: If aliases file is invalid or threshold is out of range (0-100)

**Example:**
```python
# Use default configuration
resolver = MerchantResolver()

# Use custom threshold (more restrictive)
resolver = MerchantResolver(similarity_threshold=90.0)

# Use custom aliases file
resolver = MerchantResolver(aliases_path='/path/to/custom_aliases.yaml')
```

### resolve_merchant()

```python
resolve_merchant(
    payee: str,
    return_confidence: bool = False
) -> Union[str, Tuple[str, Optional[float]]]
```

Resolve a payee string to a canonical merchant name.

**Parameters:**
- `payee` (str): The payee/merchant string to resolve
- `return_confidence` (bool): If True, return tuple of (canonical_name, confidence_score)

**Returns:**
- If `return_confidence` is False: The canonical merchant name (str), or original payee if no match
- If `return_confidence` is True: Tuple of (canonical_name, confidence_score) where score is 0-100, or (original_payee, None) if no match

**Examples:**
```python
# Simple resolution
result = resolver.resolve_merchant("Carrefour City")
print(result)  # "Carrefour"

# With confidence score
result, score = resolver.resolve_merchant("Carrefour Egyp", return_confidence=True)
print(f"{result}: {score}%")  # "Carrefour: 92.3%"

# Unmatched merchant
result, score = resolver.resolve_merchant("Unknown Shop", return_confidence=True)
print(f"{result}: {score}")  # "Unknown Shop: None"
```

### get_merchant_info()

```python
get_merchant_info(canonical_name: str) -> Optional[Dict[str, Any]]
```

Get information about a canonical merchant name.

**Parameters:**
- `canonical_name` (str): The canonical merchant name

**Returns:**
- Dictionary containing merchant info (canonical name, aliases, alias_count), or None if not found

**Example:**
```python
info = resolver.get_merchant_info("Carrefour")
print(info)
# {
#     'canonical': 'Carrefour',
#     'aliases': ['كارفور', 'carrefour eg', 'carrefour city', ...],
#     'alias_count': 6
# }
```

### get_all_merchants()

```python
get_all_merchants() -> List[str]
```

Get a list of all canonical merchant names.

**Returns:**
- Sorted list of canonical merchant names

**Example:**
```python
merchants = resolver.get_all_merchants()
print(merchants)
# ['Amazon', 'Careem', 'Carrefour', 'Electric Company', ...]
```

## Configuration File Format

The `merchant_aliases.yaml` file defines merchant aliases in the following format:

```yaml
merchants:
  - canonical: "Carrefour"
    aliases:
      - "كارفور"
      - "Carrefour EG"
      - "Carrefour City"
      - "Carrefour Market"
      - "CARREFOUR MAADI"
      
  - canonical: "McDonald's"
    aliases:
      - "ماكدونالدز"
      - "McDonalds"
      - "MC DONALDS"
      - "McDonald's Egypt"
```

**Structure:**
- `merchants`: List of merchant entries
- `canonical`: The canonical (standard) name for the merchant
- `aliases`: List of known variations and aliases for the merchant

## Use Cases

### 1. Transaction Data Normalization

Normalize merchant names in transaction data for consistent reporting:

```python
import pandas as pd
from goldminer.utils import MerchantResolver

# Load transaction data
df = pd.read_csv('transactions.csv')

# Initialize resolver
resolver = MerchantResolver()

# Normalize merchant names
df['canonical_merchant'] = df['payee'].apply(resolver.resolve_merchant)
```

### 2. Merchant Recognition with Confidence

Identify merchants and flag low-confidence matches for review:

```python
def resolve_with_review_flag(payee: str) -> dict:
    resolver = MerchantResolver()
    canonical, confidence = resolver.resolve_merchant(
        payee,
        return_confidence=True
    )
    
    return {
        'original': payee,
        'canonical': canonical,
        'confidence': confidence,
        'needs_review': confidence is None or confidence < 90
    }

result = resolve_with_review_flag("Carrefour Egyp")
print(result)
# {'original': 'Carrefour Egyp', 'canonical': 'Carrefour', 
#  'confidence': 92.3, 'needs_review': False}
```

### 3. Multi-Language Transaction Processing

Handle transactions from mixed-language sources:

```python
transactions = [
    "كارفور",           # Arabic
    "Carrefour City",   # English
    "CARREFOUR MAADI",  # English uppercase
]

resolver = MerchantResolver()
for txn in transactions:
    canonical = resolver.resolve_merchant(txn)
    print(f"{txn:20} -> {canonical}")
```

Output:
```
كارفور              -> Carrefour
Carrefour City       -> Carrefour
CARREFOUR MAADI      -> Carrefour
```

### 4. Batch Processing with Logging

Process large datasets with detailed logging:

```python
from goldminer.utils import MerchantResolver, setup_logger

# Setup logging
logger = setup_logger(__name__, log_file='merchant_resolution.log')

# Initialize resolver
resolver = MerchantResolver()

# Process transactions
unmatched = []
matched = []

for payee in payees:
    canonical, confidence = resolver.resolve_merchant(
        payee,
        return_confidence=True
    )
    
    if confidence is None:
        unmatched.append(payee)
        logger.warning(f"Unmatched merchant: {payee}")
    else:
        matched.append((payee, canonical, confidence))
        logger.info(f"Matched: {payee} -> {canonical} ({confidence}%)")

print(f"Matched: {len(matched)}, Unmatched: {len(unmatched)}")
```

## Best Practices

### 1. Choose Appropriate Threshold

The similarity threshold affects matching behavior:
- **85-90%**: Balanced (recommended) - catches most variations with few false positives
- **70-84%**: Lenient - more matches but higher risk of false positives
- **91-100%**: Strict - fewer false positives but may miss valid variations

```python
# For noisy data with many variations
lenient_resolver = MerchantResolver(similarity_threshold=80.0)

# For clean data requiring high precision
strict_resolver = MerchantResolver(similarity_threshold=92.0)
```

### 2. Handle Edge Cases

Always handle None, empty strings, and unmatched merchants:

```python
def safe_resolve(payee: str, resolver: MerchantResolver) -> str:
    if not payee:
        return "Unknown"
    
    canonical, confidence = resolver.resolve_merchant(
        payee,
        return_confidence=True
    )
    
    # Flag low-confidence matches
    if confidence and confidence < 85:
        return f"{canonical} [LOW_CONF]"
    elif confidence is None:
        return f"{payee} [UNKNOWN]"
    
    return canonical
```

### 3. Maintain the Aliases File

Regularly update `merchant_aliases.yaml` with new merchants and variations:
- Add new merchants as they appear in your data
- Include common misspellings and variations
- Add both Arabic and English names where applicable
- Keep aliases lowercase for better matching

### 4. Monitor Unmatched Merchants

Track and analyze unmatched merchants to improve your aliases:

```python
from collections import Counter

unmatched = []
for payee in all_payees:
    canonical, confidence = resolver.resolve_merchant(
        payee,
        return_confidence=True
    )
    if confidence is None:
        unmatched.append(payee)

# Find most common unmatched merchants
counter = Counter(unmatched)
print("Top unmatched merchants:")
for merchant, count in counter.most_common(10):
    print(f"  {merchant}: {count} occurrences")
```

## Performance Considerations

- **Initialization**: Loading aliases is done once during initialization
- **Exact Matching**: O(1) lookup time (dictionary lookup)
- **Fuzzy Matching**: O(n) where n is the number of aliases (typically very fast with RapidFuzz)
- **Memory**: Minimal - stores aliases in memory (~100KB for 1000 aliases)

## Troubleshooting

### Issue: Low Matching Rate

**Solution:**
1. Lower the similarity threshold: `MerchantResolver(similarity_threshold=80.0)`
2. Add more aliases to `merchant_aliases.yaml`
3. Check for data quality issues (encoding, special characters)

### Issue: Too Many False Positives

**Solution:**
1. Increase the similarity threshold: `MerchantResolver(similarity_threshold=90.0)`
2. Review and refine aliases to be more specific
3. Use confidence scores to flag uncertain matches

### Issue: Arabic Text Not Matching

**Solution:**
1. Ensure the YAML file is saved with UTF-8 encoding
2. Verify Arabic aliases are correctly formatted
3. Check for Arabic text normalization issues in your data

## Examples

See `merchant_resolver_demo.py` for comprehensive examples covering:
- Exact and fuzzy matching
- Arabic and English resolution
- Noisy input handling
- Confidence score usage
- Merchant information retrieval
- Threshold comparisons

Run the demo:
```bash
python merchant_resolver_demo.py
```

## Contributing

To add new merchants to the aliases file:

1. Edit `merchant_aliases.yaml`
2. Add a new entry under `merchants:`
3. Include the canonical name and all known aliases
4. Test the changes:
   ```python
   resolver = MerchantResolver()
   result = resolver.resolve_merchant("Your New Alias")
   print(result)  # Should return the canonical name
   ```

## Security Considerations

- The MerchantResolver has been tested with CodeQL and no security vulnerabilities were found
- Input validation is performed on all payee strings
- YAML loading uses `yaml.safe_load()` to prevent code injection
- No external API calls or network access is required

## License

This component is part of the GoldMiner project and is available under the MIT License.
