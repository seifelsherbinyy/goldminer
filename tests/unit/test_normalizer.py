"""Unit tests for data normalization."""
import unittest
import pandas as pd
from goldminer.etl import DataNormalizer


class TestDataNormalizer(unittest.TestCase):
    """Test cases for DataNormalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = DataNormalizer()
        
        # Create sample DataFrame
        self.df = pd.DataFrame({
            'Column One': ['  test  ', 'data', '  value  '],
            'COLUMN_TWO': [100, 200, 300],
            'Date Field': ['2024-01-01', '01/15/2024', '2024-03-01']
        })
    
    def test_normalize_column_name(self):
        """Test column name normalization."""
        # Test with spaces
        normalized = self.normalizer._normalize_column_name('Column One')
        self.assertEqual(normalized, 'column_one')
        
        # Test with underscores
        normalized = self.normalizer._normalize_column_name('COLUMN_TWO')
        self.assertEqual(normalized, 'column_two')
        
        # Test with special characters
        normalized = self.normalizer._normalize_column_name('Column@#$One')
        self.assertEqual(normalized, 'column_one')
    
    def test_normalize_dataframe(self):
        """Test DataFrame normalization."""
        df_norm = self.normalizer.normalize_dataframe(self.df)
        
        # Check column names are lowercase
        for col in df_norm.columns:
            self.assertEqual(col, col.lower())
        
        # Check whitespace is stripped
        self.assertEqual(df_norm['column_one'].iloc[0], 'test')
    
    def test_standardize_dates(self):
        """Test date standardization."""
        df_dates = self.normalizer.standardize_dates(
            self.df, 
            date_columns=['Date Field']
        )
        
        # All dates should be in YYYY-MM-DD format
        self.assertTrue(all('-' in str(d) for d in df_dates['Date Field']))
    
    def test_parse_date(self):
        """Test date parsing."""
        # Test standard format
        result = self.normalizer._parse_date('2024-01-01')
        self.assertEqual(result, '2024-01-01')
        
        # Test alternate format
        result = self.normalizer._parse_date('01/15/2024')
        self.assertEqual(result, '2024-01-15')
    
    def test_normalize_numeric(self):
        """Test numeric normalization."""
        df = pd.DataFrame({
            'amount': ['$100', '£200.50', '1,234.56']
        })
        
        df_norm = self.normalizer.normalize_numeric(df, ['amount'])
        
        # Check numeric values are cleaned
        self.assertIsInstance(df_norm['amount'].iloc[0], (int, float, type(None)))


if __name__ == '__main__':
    unittest.main()
