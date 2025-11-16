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


if __name__ == '__main__':
    unittest.main()
