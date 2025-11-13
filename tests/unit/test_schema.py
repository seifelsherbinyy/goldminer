"""Unit tests for schema inference."""
import unittest
import pandas as pd
from goldminer.etl import SchemaInference


class TestSchemaInference(unittest.TestCase):
    """Test cases for SchemaInference class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.schema_inference = SchemaInference()
        
        # Create sample DataFrame
        self.df = pd.DataFrame({
            'integer_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'string_col': ['a', 'b', 'c', 'd', 'e'],
            'date_col': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05']
        })
    
    def test_infer_schema(self):
        """Test schema inference."""
        schema = self.schema_inference.infer_schema(self.df)
        
        # Check schema structure
        self.assertIn('columns', schema)
        self.assertIn('row_count', schema)
        self.assertIn('column_count', schema)
        
        # Check row and column counts
        self.assertEqual(schema['row_count'], 5)
        self.assertEqual(schema['column_count'], 4)
        
        # Check column information
        self.assertIn('integer_col', schema['columns'])
        col_info = schema['columns']['integer_col']
        self.assertIn('dtype', col_info)
        self.assertIn('null_count', col_info)
        self.assertIn('inferred_type', col_info)
    
    def test_infer_column_type(self):
        """Test column type inference."""
        # Integer column
        int_type = self.schema_inference._infer_column_type(self.df['integer_col'])
        self.assertEqual(int_type, 'integer')
        
        # Float column
        float_type = self.schema_inference._infer_column_type(self.df['float_col'])
        self.assertEqual(float_type, 'numeric')
        
        # String column
        str_type = self.schema_inference._infer_column_type(self.df['string_col'])
        self.assertEqual(str_type, 'text')
    
    def test_suggest_data_types(self):
        """Test data type suggestions."""
        suggestions = self.schema_inference.suggest_data_types(self.df)
        
        self.assertIsInstance(suggestions, dict)
        self.assertIn('integer_col', suggestions)
        self.assertIn('float_col', suggestions)
    
    def test_apply_schema(self):
        """Test applying schema to DataFrame."""
        schema = {'integer_col': 'float64', 'string_col': 'str'}
        df_applied = self.schema_inference.apply_schema(self.df, schema)
        
        self.assertEqual(str(df_applied['integer_col'].dtype), 'float64')


if __name__ == '__main__':
    unittest.main()
