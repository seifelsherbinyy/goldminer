"""Unit tests for data ingestion."""
import unittest
import tempfile
import os
import json
import pandas as pd
from goldminer.etl import DataIngestion, load_sms_messages


class TestDataIngestion(unittest.TestCase):
    """Test cases for DataIngestion class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.ingestion = DataIngestion()
        
        # Create sample CSV file
        self.csv_path = os.path.join(self.temp_dir, 'test.csv')
        df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
        df.to_csv(self.csv_path, index=False)
        
        # Create sample Excel file
        self.excel_path = os.path.join(self.temp_dir, 'test.xlsx')
        df.to_excel(self.excel_path, index=False)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_read_csv(self):
        """Test reading CSV files."""
        df = self.ingestion.read_csv(self.csv_path)
        
        self.assertEqual(len(df), 3)
        self.assertIn('col1', df.columns)
        self.assertIn('col2', df.columns)
    
    def test_read_excel(self):
        """Test reading Excel files."""
        df = self.ingestion.read_excel(self.excel_path)
        
        self.assertEqual(len(df), 3)
        self.assertIn('col1', df.columns)
        self.assertIn('col2', df.columns)
    
    def test_ingest_file(self):
        """Test ingesting a single file."""
        # Test CSV
        df_csv = self.ingestion.ingest_file(self.csv_path)
        self.assertIn('_source_file', df_csv.columns)
        self.assertEqual(df_csv['_source_file'].iloc[0], 'test.csv')
        
        # Test Excel
        df_excel = self.ingestion.ingest_file(self.excel_path)
        self.assertIn('_source_file', df_excel.columns)
        self.assertEqual(df_excel['_source_file'].iloc[0], 'test.xlsx')
    
    def test_ingest_directory(self):
        """Test ingesting all files from a directory."""
        dataframes = self.ingestion.ingest_directory(self.temp_dir)
        
        # Should find both CSV and Excel files
        self.assertEqual(len(dataframes), 2)
        
        # Each should have source file column
        for df in dataframes:
            self.assertIn('_source_file', df.columns)


class TestLoadSMSMessages(unittest.TestCase):
    """Test cases for load_sms_messages function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_txt_file_utf8(self):
        """Test loading SMS messages from UTF-8 .txt file."""
        # Create sample text file with UTF-8 encoding
        txt_path = os.path.join(self.temp_dir, 'sms.txt')
        messages_data = [
            'Hello, this is message 1',
            'This is message 2 with emoji 😊',
            'Message 3 here'
        ]
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(messages_data))
        
        # Load messages
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'Hello, this is message 1')
        self.assertIn('😊', messages[1])
    
    def test_load_txt_file_utf16(self):
        """Test loading SMS messages from UTF-16 encoded .txt file."""
        # Create sample text file with UTF-16 encoding
        txt_path = os.path.join(self.temp_dir, 'sms_utf16.txt')
        messages_data = [
            'UTF-16 message 1',
            'UTF-16 message 2',
            'UTF-16 message 3'
        ]
        with open(txt_path, 'w', encoding='utf-16') as f:
            f.write('\n'.join(messages_data))
        
        # Load messages
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'UTF-16 message 1')
        self.assertEqual(messages[2], 'UTF-16 message 3')
    
    def test_load_json_file(self):
        """Test loading SMS messages from .json file."""
        # Create sample JSON file
        json_path = os.path.join(self.temp_dir, 'sms.json')
        messages_data = [
            'JSON message 1',
            'JSON message 2',
            'JSON message 3 with special chars: äöü'
        ]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False)
        
        # Load messages
        messages = load_sms_messages(json_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'JSON message 1')
        self.assertIn('äöü', messages[2])
    
    def test_load_json_file_utf16(self):
        """Test loading SMS messages from UTF-16 encoded .json file."""
        # Create sample JSON file with UTF-16 encoding
        json_path = os.path.join(self.temp_dir, 'sms_utf16.json')
        messages_data = [
            'UTF-16 JSON message 1',
            'UTF-16 JSON message 2'
        ]
        with open(json_path, 'w', encoding='utf-16') as f:
            json.dump(messages_data, f, ensure_ascii=False)
        
        # Load messages
        messages = load_sms_messages(json_path)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], 'UTF-16 JSON message 1')
    
    def test_max_messages_parameter(self):
        """Test max_messages parameter limits returned messages."""
        # Create text file with many messages
        txt_path = os.path.join(self.temp_dir, 'many_sms.txt')
        messages_data = [f'Message {i}' for i in range(1, 101)]
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(messages_data))
        
        # Load with max_messages limit
        messages = load_sms_messages(txt_path, max_messages=10)
        
        self.assertEqual(len(messages), 10)
        self.assertEqual(messages[0], 'Message 1')
        self.assertEqual(messages[9], 'Message 10')
    
    def test_explicit_filetype_parameter(self):
        """Test explicitly specifying filetype parameter."""
        # Create file with non-standard extension
        file_path = os.path.join(self.temp_dir, 'messages.data')
        messages_data = ['Message 1', 'Message 2']
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(messages_data))
        
        # Load with explicit filetype
        messages = load_sms_messages(file_path, filetype='txt')
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], 'Message 1')
    
    def test_empty_lines_filtered(self):
        """Test that empty lines in .txt files are filtered out."""
        # Create text file with empty lines
        txt_path = os.path.join(self.temp_dir, 'sms_with_empty.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Message 1\n\n\nMessage 2\n\n')
        
        # Load messages
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], 'Message 1')
        self.assertEqual(messages[1], 'Message 2')
    
    def test_file_not_found(self):
        """Test handling of non-existent file."""
        messages = load_sms_messages('nonexistent_file.txt')
        self.assertEqual(messages, [])
    
    def test_no_filepath_provided(self):
        """Test handling of None filepath."""
        messages = load_sms_messages(None)
        self.assertEqual(messages, [])
    
    def test_invalid_filetype(self):
        """Test handling of invalid filetype."""
        txt_path = os.path.join(self.temp_dir, 'test.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Test')
        
        with self.assertRaises(ValueError):
            load_sms_messages(txt_path, filetype='xml')
    
    def test_unsupported_extension(self):
        """Test handling of unsupported file extension."""
        file_path = os.path.join(self.temp_dir, 'test.xml')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('<messages/>')
        
        with self.assertRaises(ValueError):
            load_sms_messages(file_path)
    
    def test_json_not_a_list(self):
        """Test handling of JSON file that doesn't contain a list."""
        json_path = os.path.join(self.temp_dir, 'invalid.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({'messages': ['test']}, f)
        
        messages = load_sms_messages(json_path)
        self.assertEqual(messages, [])
    
    def test_whitespace_stripping(self):
        """Test that whitespace is properly stripped from messages."""
        txt_path = os.path.join(self.temp_dir, 'whitespace.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('  Message with leading space\n')
            f.write('Message with trailing space  \n')
            f.write('  Message with both  ')
        
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'Message with leading space')
        self.assertEqual(messages[1], 'Message with trailing space')
        self.assertEqual(messages[2], 'Message with both')
    
    def test_unicode_normalization(self):
        """Test that Unicode RTL marks and invisible characters are removed."""
        txt_path = os.path.join(self.temp_dir, 'unicode.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            # Include messages with various invisible Unicode characters
            f.write('Message with RTL mark\u200e here\n')
            f.write('Text\u200f with\u200f multiple marks\n')
            f.write('Zero\u200b width\u200b space\n')
            f.write('Zero\u200c width\u200d joiner\n')
            f.write('\ufeffBOM character at start')
        
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 5)
        # Verify invisible characters are removed
        self.assertEqual(messages[0], 'Message with RTL mark here')
        self.assertEqual(messages[1], 'Text with multiple marks')
        self.assertEqual(messages[2], 'Zero width space')
        self.assertEqual(messages[3], 'Zero width joiner')
        self.assertEqual(messages[4], 'BOM character at start')
    
    def test_multiple_spaces_normalized(self):
        """Test that multiple consecutive spaces are replaced with single space."""
        txt_path = os.path.join(self.temp_dir, 'spaces.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Multiple   spaces   here\n')
            f.write('Even    more     spaces\n')
            f.write('Tab\t\tcharacters   and  spaces')
        
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'Multiple spaces here')
        self.assertEqual(messages[1], 'Even more spaces')
        # Note: Tabs are preserved by strip(), but multiple spaces are normalized
        self.assertIn('Tab', messages[2])
    
    def test_duplicate_removal(self):
        """Test that duplicate messages are removed."""
        txt_path = os.path.join(self.temp_dir, 'duplicates.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Unique message 1\n')
            f.write('Duplicate message\n')
            f.write('Unique message 2\n')
            f.write('Duplicate message\n')
            f.write('Duplicate message\n')
            f.write('Unique message 3')
        
        messages = load_sms_messages(txt_path)
        
        # Should have only 4 unique messages
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[0], 'Unique message 1')
        self.assertEqual(messages[1], 'Duplicate message')
        self.assertEqual(messages[2], 'Unique message 2')
        self.assertEqual(messages[3], 'Unique message 3')
        
        # Verify no duplicates in result
        self.assertEqual(len(messages), len(set(messages)))
    
    def test_duplicate_removal_after_sanitization(self):
        """Test that duplicates are identified after sanitization."""
        txt_path = os.path.join(self.temp_dir, 'sanitized_duplicates.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            # These should all become the same after sanitization
            f.write('Hello World\n')
            f.write('  Hello World  \n')
            f.write('Hello\u200e World\n')
            f.write('Hello   World\n')
            f.write('Unique message')
        
        messages = load_sms_messages(txt_path)
        
        # Should have only 2 unique messages after sanitization
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], 'Hello World')
        self.assertEqual(messages[1], 'Unique message')
    
    def test_sanitization_preserves_valid_content(self):
        """Test that sanitization preserves valid message content."""
        txt_path = os.path.join(self.temp_dir, 'valid_content.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Email: test@example.com\n')
            f.write('URL: https://example.com/path\n')
            f.write('Price: $99.99 for 2 items\n')
            f.write('Emoji message 😊🎉👍\n')
            f.write('Special chars: !@#$%^&*()')
        
        messages = load_sms_messages(txt_path)
        
        self.assertEqual(len(messages), 5)
        self.assertIn('test@example.com', messages[0])
        self.assertIn('https://example.com/path', messages[1])
        self.assertIn('$99.99', messages[2])
        self.assertIn('😊', messages[3])
        self.assertIn('!@#$%^&*()', messages[4])
    
    def test_empty_messages_filtered_after_sanitization(self):
        """Test that messages that become empty after sanitization are filtered."""
        txt_path = os.path.join(self.temp_dir, 'empty_after_sanitization.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('Valid message\n')
            f.write('\u200e\u200f\u200b\n')  # Only invisible characters
            f.write('   \n')  # Only spaces
            f.write('Another valid message')
        
        messages = load_sms_messages(txt_path)
        
        # Should only have 2 valid messages
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], 'Valid message')
        self.assertEqual(messages[1], 'Another valid message')
    
    def test_json_duplicate_removal(self):
        """Test that duplicate removal works for JSON files."""
        json_path = os.path.join(self.temp_dir, 'duplicates.json')
        messages_data = [
            'Message 1',
            'Message 2',
            'Message 1',  # Duplicate
            'Message 3',
            'Message 2'   # Duplicate
        ]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f)
        
        messages = load_sms_messages(json_path)
        
        # Should have only 3 unique messages
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'Message 1')
        self.assertEqual(messages[1], 'Message 2')
        self.assertEqual(messages[2], 'Message 3')
    
    def test_json_unicode_normalization(self):
        """Test Unicode normalization in JSON files."""
        json_path = os.path.join(self.temp_dir, 'unicode.json')
        messages_data = [
            'Text\u200e with RTL',
            'Multiple\u200b\u200binvisible chars',
            '\ufeffWith BOM'
        ]
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(messages_data, f, ensure_ascii=False)
        
        messages = load_sms_messages(json_path)
        
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0], 'Text with RTL')
        self.assertEqual(messages[1], 'Multipleinvisible chars')
        self.assertEqual(messages[2], 'With BOM')


if __name__ == '__main__':
    unittest.main()
