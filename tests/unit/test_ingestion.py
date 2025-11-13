"""Unit tests for data ingestion."""
import unittest
import tempfile
import os
import pandas as pd
from goldminer.etl import DataIngestion


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


if __name__ == '__main__':
    unittest.main()
