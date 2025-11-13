"""Unit tests for data cleaning."""
import unittest
import pandas as pd
import numpy as np
from goldminer.etl import DataCleaner


class TestDataCleaner(unittest.TestCase):
    """Test cases for DataCleaner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cleaner = DataCleaner()
        
        # Create sample DataFrame with duplicates
        self.df = pd.DataFrame({
            'col1': [1, 2, 2, 3, 4],
            'col2': ['a', 'b', 'b', 'c', 'd']
        })
    
    def test_remove_duplicates(self):
        """Test duplicate removal."""
        df_clean = self.cleaner.remove_duplicates(self.df)
        
        # Should remove one duplicate row
        self.assertEqual(len(df_clean), 4)
        
        # Check no duplicates remain
        self.assertEqual(df_clean.duplicated().sum(), 0)
    
    def test_handle_missing_values_drop(self):
        """Test handling missing values with drop strategy."""
        df_nulls = pd.DataFrame({
            'col1': [1, 2, None, 4],
            'col2': ['a', 'b', 'c', 'd']
        })
        
        df_clean = self.cleaner.handle_missing_values(df_nulls, strategy='drop')
        
        # Should drop row with null
        self.assertEqual(len(df_clean), 3)
    
    def test_handle_missing_values_fill(self):
        """Test handling missing values with fill strategy."""
        df_nulls = pd.DataFrame({
            'col1': [1, 2, None, 4],
            'col2': ['a', 'b', 'c', 'd']
        })
        
        df_clean = self.cleaner.handle_missing_values(
            df_nulls, 
            strategy='fill', 
            fill_value=0
        )
        
        # Should fill nulls with 0
        self.assertEqual(df_clean['col1'].isnull().sum(), 0)
    
    def test_remove_outliers_iqr(self):
        """Test outlier removal using IQR method."""
        df_outliers = pd.DataFrame({
            'values': [1, 2, 3, 4, 5, 100]  # 100 is outlier
        })
        
        df_clean = self.cleaner.remove_outliers(
            df_outliers, 
            columns=['values'], 
            method='iqr'
        )
        
        # Should remove outlier
        self.assertLess(len(df_clean), len(df_outliers))
    
    def test_validate_data_quality(self):
        """Test data quality validation."""
        report = self.cleaner.validate_data_quality(self.df)
        
        # Check report structure
        self.assertIn('total_rows', report)
        self.assertIn('total_columns', report)
        self.assertIn('duplicate_rows', report)
        self.assertIn('columns', report)
        
        # Check specific values
        self.assertEqual(report['total_rows'], 5)
        self.assertEqual(report['total_columns'], 2)
    
    def test_clean_text_columns(self):
        """Test text column cleaning."""
        df_text = pd.DataFrame({
            'text': ['  hello  world  ', 'test   data', 'value']
        })
        
        df_clean = self.cleaner.clean_text_columns(df_text)
        
        # Check extra whitespace is removed
        self.assertEqual(df_clean['text'].iloc[0], 'hello world')


if __name__ == '__main__':
    unittest.main()
