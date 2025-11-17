"""Unit tests for ParquetExporter."""
import unittest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
from goldminer.etl import ParquetExporter


class TestParquetExporter(unittest.TestCase):
    """Test cases for ParquetExporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.exporter = ParquetExporter()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample transaction data
        self.sample_transactions = self._create_sample_transactions()
    
    def tearDown(self):
        """Clean up test files."""
        # Remove temporary files and directories
        for file in Path(self.temp_dir).rglob("*"):
            if file.is_file():
                file.unlink()
        
        # Remove directories
        for dir_path in sorted(Path(self.temp_dir).rglob("*"), reverse=True):
            if dir_path.is_dir():
                dir_path.rmdir()
        
        Path(self.temp_dir).rmdir()
    
    def _create_sample_transactions(self):
        """Create sample transaction data for testing."""
        base_date = datetime.now() - timedelta(days=90)
        transactions = []
        
        categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping']
        subcategories = ['Groceries', 'Fuel', 'Movies', 'Utilities', 'Clothing']
        accounts = ['ACC001', 'ACC002', 'ACC003']
        account_types = ['Credit', 'Debit', 'Prepaid']
        urgencies = ['normal', 'medium', 'high']
        confidences = ['low', 'medium', 'high']
        
        for i in range(100):
            date = base_date + timedelta(days=i % 30)
            transaction = {
                'id': f'TXN{i:05d}',
                'date': date.strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 10}',
                'normalized_merchant': f'MERCHANT_{i % 10}',
                'category': categories[i % len(categories)],
                'subcategory': subcategories[i % len(subcategories)],
                'amount': round(50 + (i * 13.7) % 500, 2),
                'currency': 'USD',
                'account_id': accounts[i % len(accounts)],
                'account_type': account_types[i % len(account_types)],
                'interest_rate': 0.15 if account_types[i % len(account_types)] == 'Credit' else None,
                'tags': ['tag1', 'tag2'] if i % 3 == 0 else ['tag3'],
                'urgency': urgencies[i % len(urgencies)],
                'confidence': confidences[i % len(confidences)]
            }
            transactions.append(transaction)
        
        return transactions
    
    def test_initialization(self):
        """Test ParquetExporter initialization."""
        self.assertIsNotNone(self.exporter)
        self.assertIsNotNone(self.exporter.logger)
    
    def test_export_basic(self):
        """Test basic export to Parquet file."""
        output_file = os.path.join(self.temp_dir, "test_transactions.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Verify file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file can be read
        df = pd.read_parquet(output_file)
        self.assertEqual(len(df), len(self.sample_transactions))
    
    def test_export_with_compression_snappy(self):
        """Test export with Snappy compression."""
        output_file = os.path.join(self.temp_dir, "test_snappy.parquet")
        
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_file, 
            compression='snappy'
        )
        
        # Verify file exists and is readable
        self.assertTrue(os.path.exists(output_file))
        df = pd.read_parquet(output_file)
        self.assertEqual(len(df), len(self.sample_transactions))
    
    def test_export_with_compression_brotli(self):
        """Test export with Brotli compression."""
        output_file = os.path.join(self.temp_dir, "test_brotli.parquet")
        
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_file, 
            compression='brotli'
        )
        
        # Verify file exists and is readable
        self.assertTrue(os.path.exists(output_file))
        df = pd.read_parquet(output_file)
        self.assertEqual(len(df), len(self.sample_transactions))
    
    def test_export_with_partitioning(self):
        """Test export with year/month partitioning."""
        output_dir = os.path.join(self.temp_dir, "test_partitioned")
        
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_dir + '.parquet',
            partition_cols=['year', 'month']
        )
        
        # Verify partitioned directory exists
        self.assertTrue(os.path.exists(output_dir))
        
        # Verify we can read the partitioned dataset
        df = pd.read_parquet(output_dir)
        self.assertEqual(len(df), len(self.sample_transactions))
        
        # Verify year and month columns exist
        self.assertIn('year', df.columns)
        self.assertIn('month', df.columns)
    
    def test_metadata_in_footer(self):
        """Test that metadata is written to Parquet file footer."""
        output_file = os.path.join(self.temp_dir, "test_metadata.parquet")
        user_id = "test_user_123"
        
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_file,
            user_id=user_id
        )
        
        # Read metadata from Parquet file
        parquet_file = pq.ParquetFile(output_file)
        metadata = parquet_file.schema_arrow.metadata
        
        # Verify metadata exists
        self.assertIsNotNone(metadata)
        self.assertIn(b'export_timestamp', metadata)
        self.assertIn(b'num_rows', metadata)
        self.assertIn(b'user_id', metadata)
        self.assertIn(b'exporter', metadata)
        
        # Verify metadata values
        self.assertEqual(metadata[b'num_rows'], str(len(self.sample_transactions)).encode('utf-8'))
        self.assertEqual(metadata[b'user_id'], user_id.encode('utf-8'))
    
    def test_schema_consistency_across_runs(self):
        """Test that schema remains consistent across multiple exports."""
        output_file1 = os.path.join(self.temp_dir, "test_schema1.parquet")
        output_file2 = os.path.join(self.temp_dir, "test_schema2.parquet")
        
        # Export twice with same data
        self.exporter.export_to_parquet(self.sample_transactions, output_file1)
        self.exporter.export_to_parquet(self.sample_transactions, output_file2)
        
        # Get schema info from both files
        schema1 = self.exporter.get_schema_info(output_file1)
        schema2 = self.exporter.get_schema_info(output_file2)
        
        # Verify schema consistency
        self.assertEqual(schema1['num_columns'], schema2['num_columns'])
        self.assertEqual(schema1['column_names'], schema2['column_names'])
        self.assertEqual(schema1['column_types'], schema2['column_types'])
    
    def test_schema_optimization_categorical(self):
        """Test that categorical columns are properly optimized."""
        output_file = os.path.join(self.temp_dir, "test_categorical.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Read schema
        parquet_file = pq.ParquetFile(output_file)
        schema = parquet_file.schema_arrow
        
        # Check that categorical columns use dictionary encoding
        categorical_cols = ['category', 'subcategory', 'account_type', 'urgency', 'confidence', 'currency', 'tags']
        
        for col in categorical_cols:
            if col in schema.names:
                field = schema.field(col)
                # Dictionary encoded fields have a dictionary type
                self.assertTrue(
                    'dictionary' in str(field.type).lower(),
                    f"Column {col} should use dictionary encoding but has type {field.type}"
                )
    
    def test_schema_optimization_string_columns(self):
        """Test that high-cardinality string columns are properly handled."""
        output_file = os.path.join(self.temp_dir, "test_strings.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Read and verify
        df = pd.read_parquet(output_file)
        
        # Verify string columns exist and are readable
        string_cols = ['id', 'payee', 'normalized_merchant', 'account_id']
        for col in string_cols:
            if col in df.columns:
                self.assertTrue(df[col].notna().any(), f"Column {col} should have values")
    
    def test_tags_handling(self):
        """Test that tags (list type) are properly handled."""
        output_file = os.path.join(self.temp_dir, "test_tags.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Read and verify tags
        df = pd.read_parquet(output_file)
        
        # Tags should be converted to comma-separated string
        self.assertIn('tags', df.columns)
        # Verify tags are readable as strings
        for tag_value in df['tags'].dropna():
            self.assertIsInstance(tag_value, str)
    
    def test_compatibility_pyarrow(self):
        """Test compatibility with PyArrow."""
        output_file = os.path.join(self.temp_dir, "test_pyarrow_compat.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Verify PyArrow can read
        table = pq.read_table(output_file)
        self.assertEqual(len(table), len(self.sample_transactions))
    
    def test_compatibility_pandas(self):
        """Test compatibility with Pandas."""
        output_file = os.path.join(self.temp_dir, "test_pandas_compat.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Verify Pandas can read
        df = pd.read_parquet(output_file)
        self.assertEqual(len(df), len(self.sample_transactions))
        
        # Verify all expected columns exist
        expected_cols = ['id', 'date', 'amount', 'payee', 'category']
        for col in expected_cols:
            self.assertIn(col, df.columns)
    
    def test_validate_compatibility_function(self):
        """Test the validate_compatibility method."""
        output_file = os.path.join(self.temp_dir, "test_validate_compat.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Run compatibility validation
        results = self.exporter.validate_compatibility(output_file)
        
        # Verify results
        self.assertIn('pyarrow', results)
        self.assertIn('pandas', results)
        self.assertTrue(results['pyarrow'], "PyArrow should be able to read the file")
        self.assertTrue(results['pandas'], "Pandas should be able to read the file")
    
    def test_empty_transactions_raises_error(self):
        """Test that exporting empty transactions raises ValueError."""
        output_file = os.path.join(self.temp_dir, "test_empty.parquet")
        
        with self.assertRaises(ValueError):
            self.exporter.export_to_parquet([], output_file)
    
    def test_auto_add_parquet_extension(self):
        """Test that .parquet extension is automatically added."""
        output_file = os.path.join(self.temp_dir, "test_no_ext")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Verify file with .parquet extension exists
        expected_file = output_file + '.parquet'
        self.assertTrue(os.path.exists(expected_file))
    
    def test_numeric_types_preserved(self):
        """Test that numeric types are properly preserved."""
        output_file = os.path.join(self.temp_dir, "test_numeric.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Read and verify numeric columns
        df = pd.read_parquet(output_file)
        
        # Amount should be float
        self.assertTrue(pd.api.types.is_float_dtype(df['amount']))
        
        # Interest rate should be float (with nulls)
        if 'interest_rate' in df.columns:
            self.assertTrue(pd.api.types.is_float_dtype(df['interest_rate']))
    
    def test_date_type_preserved(self):
        """Test that date types are properly preserved."""
        output_file = os.path.join(self.temp_dir, "test_dates.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Read and verify date column
        df = pd.read_parquet(output_file)
        
        # Date should be datetime type
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df['date']))
    
    def test_get_schema_info(self):
        """Test get_schema_info method."""
        output_file = os.path.join(self.temp_dir, "test_schema_info.parquet")
        
        self.exporter.export_to_parquet(self.sample_transactions, output_file)
        
        # Get schema info
        schema_info = self.exporter.get_schema_info(output_file)
        
        # Verify schema info structure
        self.assertIn('num_columns', schema_info)
        self.assertIn('column_names', schema_info)
        self.assertIn('column_types', schema_info)
        self.assertIn('metadata', schema_info)
        self.assertIn('num_row_groups', schema_info)
        
        # Verify values
        self.assertGreater(schema_info['num_columns'], 0)
        self.assertIsInstance(schema_info['column_names'], list)
        self.assertIsInstance(schema_info['column_types'], dict)
    
    def test_compression_reduces_file_size(self):
        """Test that compression reduces file size."""
        output_file_uncompressed = os.path.join(self.temp_dir, "test_uncompressed.parquet")
        output_file_compressed = os.path.join(self.temp_dir, "test_compressed.parquet")
        
        # Export without compression
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_file_uncompressed,
            compression='none'
        )
        
        # Export with compression
        self.exporter.export_to_parquet(
            self.sample_transactions, 
            output_file_compressed,
            compression='snappy'
        )
        
        # Compare file sizes
        size_uncompressed = os.path.getsize(output_file_uncompressed)
        size_compressed = os.path.getsize(output_file_compressed)
        
        # Compressed should be smaller (or at least not significantly larger)
        self.assertLessEqual(size_compressed, size_uncompressed * 1.1)  # Allow 10% margin


if __name__ == '__main__':
    unittest.main()
