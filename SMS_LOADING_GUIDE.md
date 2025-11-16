# SMS Message Loading Guide

## Overview

The `load_sms_messages()` function provides a simple and robust way to load SMS messages from local files for offline processing. It supports multiple file formats and encodings, making it ideal for analyzing exported SMS data.

## Features

- **Multiple Formats**: Supports both `.txt` (one message per line) and `.json` (list of strings) formats
- **Encoding Handling**: Automatically handles UTF-8, UTF-16 (LE/BE), latin-1, and cp1252 encodings
- **Offline Operation**: Works entirely offline - no internet connection required
- **Error Resilient**: Gracefully handles encoding errors and missing files
- **Flexible Loading**: Optional parameters for file type and message limits
- **UTF-8 Output**: All messages are returned as properly decoded UTF-8 strings

## Installation

The function is part of the GoldMiner ETL package:

```python
from goldminer.etl import load_sms_messages
```

## Basic Usage

### Loading Text Files

```python
from goldminer.etl import load_sms_messages

# Load all messages from a text file
messages = load_sms_messages('sms_export.txt')
print(f"Loaded {len(messages)} messages")

# Display first few messages
for i, msg in enumerate(messages[:5], 1):
    print(f"{i}. {msg}")
```

### Loading JSON Files

```python
# Load messages from JSON file
messages = load_sms_messages('sms_export.json')
print(f"Loaded {len(messages)} messages")
```

### Limiting Message Count

```python
# Load only first 100 messages
messages = load_sms_messages('sms_export.txt', max_messages=100)
```

### Explicit File Type

```python
# Explicitly specify file type for non-standard extensions
messages = load_sms_messages('messages.data', filetype='txt')
```

## File Formats

### Text File Format (.txt)

Text files should contain one SMS message per line:

```
Hello! How are you?
Meeting at 3 PM tomorrow
Don't forget the documents
```

**Notes:**
- Empty lines are automatically filtered out
- Leading and trailing whitespace is stripped from each message
- Supports UTF-8, UTF-16, and other common encodings

### JSON File Format (.json)

JSON files should contain a list of strings:

```json
[
  "Hello! How are you?",
  "Meeting at 3 PM tomorrow",
  "Don't forget the documents"
]
```

**Notes:**
- Must be a valid JSON array of strings
- Supports UTF-8, UTF-16, and other common encodings
- Non-string values will be converted to strings

## Advanced Examples

### Processing Loaded Messages

```python
from goldminer.etl import load_sms_messages

# Load messages
messages = load_sms_messages('sms_export.txt')

# Calculate statistics
total_chars = sum(len(msg) for msg in messages)
avg_length = total_chars / len(messages) if messages else 0

print(f"Total messages: {len(messages)}")
print(f"Average length: {avg_length:.1f} characters")

# Filter messages by keyword
keyword_messages = [msg for msg in messages if 'meeting' in msg.lower()]
print(f"Messages containing 'meeting': {len(keyword_messages)}")
```

### Handling UTF-16 Encoded Files

```python
# The function automatically detects and handles UTF-16 encoding
messages = load_sms_messages('sms_utf16.txt')

# All messages are returned as UTF-8 strings
for msg in messages:
    print(msg)  # Properly decoded UTF-8
```

### Error Handling

```python
# The function returns an empty list on errors
messages = load_sms_messages('nonexistent_file.txt')
if not messages:
    print("No messages loaded - check the file path")

# Handle None filepath gracefully
messages = load_sms_messages(None)
print(messages)  # []
```

### Batch Processing Multiple Files

```python
import os
from goldminer.etl import load_sms_messages

# Process all SMS files in a directory
sms_dir = 'data/sms_exports'
all_messages = []

for filename in os.listdir(sms_dir):
    if filename.endswith(('.txt', '.json')):
        filepath = os.path.join(sms_dir, filename)
        messages = load_sms_messages(filepath)
        all_messages.extend(messages)
        print(f"Loaded {len(messages)} from {filename}")

print(f"Total messages: {len(all_messages)}")
```

## Function Reference

### `load_sms_messages(filepath, filetype, max_messages)`

Load SMS messages from a local file.

**Parameters:**
- `filepath` (str, optional): Path to the SMS file. Returns empty list if None.
- `filetype` (str, optional): File type ('txt' or 'json'). Auto-detected from extension if None.
- `max_messages` (int, optional): Maximum number of messages to load. Loads all if None.

**Returns:**
- `List[str]`: List of SMS messages as UTF-8 strings. Returns empty list on errors.

**Raises:**
- `ValueError`: If filetype is invalid or file extension is not supported.

**Example:**
```python
messages = load_sms_messages(
    filepath='sms_export.txt',
    filetype='txt',
    max_messages=100
)
```

## Supported Encodings

The function automatically tries the following encodings in order:
1. UTF-8
2. UTF-16 (with byte order mark)
3. UTF-16-LE (little-endian)
4. UTF-16-BE (big-endian)
5. Latin-1 (ISO-8859-1)
6. CP1252 (Windows-1252)

The first encoding that successfully decodes the file is used, and all messages are returned as UTF-8 strings.

## Error Handling

The function handles errors gracefully:

- **File not found**: Returns empty list and logs error
- **Invalid encoding**: Tries multiple encodings; returns empty list if all fail
- **Invalid JSON**: Returns empty list and logs error
- **Invalid filetype**: Raises `ValueError` with descriptive message
- **Unsupported extension**: Raises `ValueError` with descriptive message

All errors are logged using the GoldMiner logging system for debugging.

## Best Practices

1. **Large Files**: Use `max_messages` parameter to limit memory usage for very large files
2. **Encoding Unknown**: Let the function auto-detect encoding rather than forcing a specific one
3. **Error Checking**: Check if returned list is empty to detect errors
4. **File Validation**: Ensure files exist before calling the function
5. **Batch Processing**: Process multiple files in loops for comprehensive analysis

## Integration with GoldMiner

The `load_sms_messages()` function is designed to work seamlessly with other GoldMiner components:

```python
from goldminer.etl import load_sms_messages
import pandas as pd

# Load SMS messages
messages = load_sms_messages('sms_export.txt')

# Convert to DataFrame for analysis
df = pd.DataFrame({
    'message': messages,
    'length': [len(msg) for msg in messages]
})

# Use with GoldMiner analysis tools
# (Add your analysis code here)
```

## Troubleshooting

### No messages loaded

**Check:**
- File path is correct and file exists
- File has correct extension (.txt or .json)
- File is not empty
- File has correct format (one message per line for .txt, JSON array for .json)

### Encoding errors

**Solution:**
- The function automatically handles common encodings
- If issues persist, check that file is in a supported encoding
- Consider converting file to UTF-8 using external tools

### Memory issues with large files

**Solution:**
- Use `max_messages` parameter to load files in chunks
- Process messages incrementally rather than loading all at once

## Contributing

Contributions to improve the `load_sms_messages()` function are welcome. Please submit issues and pull requests to the [GoldMiner repository](https://github.com/seifelsherbinyy/goldminer).

## License

This function is part of the GoldMiner project and is available under the MIT License.
