# Categorizer load_rules() Method - User Guide

## Overview

The `load_rules()` method allows you to load and reload categorization rules from YAML configuration files at runtime. This enables non-technical users to customize categorization behavior without modifying code.

## Features

- **Multiple Match Types**: Support for exact match, regex patterns, and tag-based matching
- **Runtime Reloading**: Update rules without restarting your application
- **Safe Fallback**: Gracefully handles missing or malformed files
- **Rule Precedence**: Clear priority system for conflict resolution
- **Backward Compatible**: Works seamlessly with existing rule formats

## Basic Usage

```python
from goldminer.etl import Categorizer

# Initialize categorizer
categorizer = Categorizer()

# Load custom rules from a YAML file
categorizer.load_rules('my_custom_rules.yaml')

# Categorize transactions as usual
result = categorizer.categorize(transaction)

# Reload rules at runtime (e.g., after editing the file)
categorizer.load_rules('my_custom_rules.yaml')
```

## Rule Format

### New Format (Recommended)

The new format uses `match`, `match_regex`, and `match_tag` keys:

```yaml
rules:
  # Exact string matching
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility"]
  
  # Regex pattern matching
  - match_regex: ".*Vodafone.*"
    category: "Utilities"
    subcategory: "Telecom"
    tags: ["Recharge"]
  
  # Tag-based matching
  - match_tag: "subscription"
    category: "Entertainment"
    subcategory: "Streaming"
    tags: ["Recurring"]

# Fallback for unmatched transactions
fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
```

### Match Types Explained

#### 1. `match` - Exact String Match
Matches merchant names exactly (case-insensitive).

**Example:**
```yaml
- match: "Uber"
  category: "Transport"
  subcategory: "Ride Hailing"
  tags: ["Mobility"]
```

**Matches:**
- "Uber"
- "uber" 
- "UBER"

**Does NOT match:**
- "Uber Eats"
- "Super Uber"

#### 2. `match_regex` - Regex Pattern Match
Matches merchant names using regular expressions (case-insensitive).

**Example:**
```yaml
- match_regex: ".*Vodafone.*"
  category: "Utilities"
  subcategory: "Telecom"
  tags: ["Recharge"]
```

**Matches:**
- "Vodafone"
- "Vodafone Egypt"
- "Vodafone Store 123"

**Common Patterns:**
- `".*keyword.*"` - Contains keyword anywhere
- `"^keyword"` - Starts with keyword
- `"keyword$"` - Ends with keyword
- `"word1.*word2"` - Contains word1 followed by word2
- `"word1|word2"` - Contains either word1 or word2

#### 3. `match_tag` - Tag-Based Match
Matches transactions that already have a specific tag.

**Example:**
```yaml
- match_tag: "subscription"
  category: "Entertainment"
  subcategory: "Streaming"
  tags: ["Recurring"]
```

**Use Case:** Useful when tags are added by other parts of your system and you want to categorize based on those tags.

## Rule Precedence

When multiple rules could match a transaction, they are evaluated in this order:

1. **New format `match`** (exact string)
2. **New format `match_regex`** (regex pattern)
3. **New format `match_tag`** (tag-based)
4. **Legacy format `merchant_exact`** (exact merchant)
5. **Legacy format `merchant_fuzzy`** (fuzzy merchant)
6. **Legacy format `keywords`** (keyword matching)
7. **Fallback** (uncategorized)

The first matching rule wins and stops further evaluation.

## Safe Fallback Behavior

The `load_rules()` method implements safe fallback for error scenarios:

### Missing File
```python
categorizer.load_rules('/nonexistent/file.yaml')
# Logs: WARNING - Rules file not found. Keeping existing rules.
# Original rules remain intact
```

### Malformed YAML
```yaml
rules:
  - match: "Test"
    invalid syntax [
```
```python
categorizer.load_rules('malformed.yaml')
# Logs: ERROR - YAML parsing error. Keeping existing rules.
# Original rules remain intact
```

### Invalid Structure
```yaml
wrong_key:
  - some data
```
```python
categorizer.load_rules('invalid.yaml')
# Logs: ERROR - Invalid rules format. Keeping existing rules.
# Original rules remain intact
```

## Runtime Reloading

You can reload rules at any time without restarting your application:

```python
# Initial load
categorizer.load_rules('rules_v1.yaml')

# Process some transactions
results = categorizer.categorize_batch(transactions)

# Edit rules_v1.yaml or switch to a different file
categorizer.load_rules('rules_v2.yaml')

# New rules take effect immediately
results = categorizer.categorize_batch(more_transactions)
```

**Use Cases:**
- A/B testing different categorization strategies
- Seasonal rule adjustments
- User-specific customizations
- Hot-reloading in development

## Backward Compatibility

The new format coexists with the legacy format. You can:

1. **Use only new format:**
```yaml
rules:
  - match: "Uber"
    category: "Transport"
    # ...
```

2. **Use only legacy format:**
```yaml
categories:
  - category: "Food & Dining"
    merchant_exact: ["McDonald's"]
    # ...
```

3. **Mix both formats:**
```yaml
rules:
  - match: "Uber"
    category: "Transport"
    # ...

categories:
  - category: "Food & Dining"
    merchant_exact: ["McDonald's"]
    # ...
```

When mixing formats, new format rules have priority.

## Complete Example

See `example_categorizer_rules.yaml` for a complete working example:

```yaml
rules:
  # Ride sharing services
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility"]
  
  - match: "Careem"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility", "MENA"]
  
  # Telecom providers (any variant)
  - match_regex: ".*Vodafone.*"
    category: "Utilities"
    subcategory: "Telecom"
    tags: ["Recharge", "Mobile"]
  
  # Online shopping
  - match_regex: "^Amazon.*"
    category: "Shopping"
    subcategory: "Online Shopping"
    tags: ["E-commerce"]
  
  # Subscription services
  - match_tag: "subscription"
    category: "Entertainment"
    subcategory: "Streaming"
    tags: ["Recurring"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: ["Uncategorized"]
```

## Best Practices

1. **Start Simple**: Begin with exact matches, add regex only when needed
2. **Test Patterns**: Validate regex patterns before deploying
3. **Document Intent**: Add comments explaining why rules exist
4. **Version Control**: Keep rule files in version control
5. **Backup**: Keep a backup before major changes
6. **Incremental Changes**: Make small changes and test frequently
7. **Use Fallback**: Always define a fallback category

## Common Regex Patterns

```yaml
# Match anything containing "pharmacy"
- match_regex: ".*[Pp]harmacy.*"

# Match Starbucks or Costa
- match_regex: ".*Starbucks.*|.*Costa.*"

# Match any Amazon variant
- match_regex: "^Amazon(\.com|\.eg|\.ae)?.*"

# Match phone numbers
- match_regex: ".*\\d{3}-\\d{3}-\\d{4}.*"

# Match Arabic text
- match_regex: ".*[\u0600-\u06FF]+.*"
```

## Troubleshooting

### Rules Not Taking Effect
- Check that `load_rules()` was called after initialization
- Verify YAML syntax is correct
- Check log output for error messages

### Wrong Category Applied
- Check rule precedence - earlier rules win
- Verify merchant name matches your pattern
- Test regex patterns at https://regex101.com

### Performance Issues
- Use exact matches when possible (faster than regex)
- Avoid overly complex regex patterns
- Consider caching frequently used patterns

## For Non-Technical Users

To edit categorization rules:

1. Open the YAML file in a text editor
2. Find the rule you want to change
3. Edit the category, subcategory, or tags
4. Save the file
5. Reload rules in the application (or restart)

**Important:**
- Keep the file structure intact
- Use spaces, not tabs, for indentation
- Match string values must be in quotes
- Test one change at a time

## Advanced Usage

### Dynamic Rule Selection
```python
# Load different rules based on user preference
if user.country == 'EG':
    categorizer.load_rules('rules_egypt.yaml')
elif user.country == 'AE':
    categorizer.load_rules('rules_uae.yaml')
else:
    categorizer.load_rules('rules_default.yaml')
```

### Rule Validation
```python
import yaml

def validate_rules(filepath):
    """Validate rules file before loading."""
    try:
        with open(filepath, 'r') as f:
            rules = yaml.safe_load(f)
        
        # Check structure
        if 'rules' not in rules and 'categories' not in rules:
            return False, "Missing 'rules' or 'categories' key"
        
        # Check each rule has required fields
        for rule in rules.get('rules', []):
            if not any(k in rule for k in ['match', 'match_regex', 'match_tag']):
                return False, f"Rule missing match type: {rule}"
        
        return True, "Valid"
    except Exception as e:
        return False, str(e)

# Use validation before loading
valid, message = validate_rules('my_rules.yaml')
if valid:
    categorizer.load_rules('my_rules.yaml')
else:
    print(f"Invalid rules file: {message}")
```

## See Also

- `example_categorizer_rules.yaml` - Complete example file
- `load_rules_demo.py` - Interactive demonstration
- `test_categorizer_load_rules.py` - Test cases showing all features
- `CATEGORIZER_GUIDE.md` - General categorizer documentation
