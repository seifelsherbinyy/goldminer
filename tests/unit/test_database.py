"""Unit tests for database management."""
import unittest
import tempfile
import os
import pandas as pd
from goldminer.etl import DatabaseManager


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db_manager = DatabaseManager(self.db_path)
        
        # Create sample DataFrame
        self.df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db_manager.disconnect()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_connect_disconnect(self):
        """Test database connection and disconnection."""
        self.db_manager.connect()
        self.assertIsNotNone(self.db_manager.connection)
        
        self.db_manager.disconnect()
        self.assertIsNone(self.db_manager.connection)
    
    def test_save_and_load_dataframe(self):
        """Test saving and loading DataFrame."""
        # Save DataFrame
        self.db_manager.save_dataframe(self.df, 'test_table')
        
        # Load DataFrame
        df_loaded = self.db_manager.load_dataframe('test_table')
        
        # Verify
        self.assertEqual(len(df_loaded), len(self.df))
        self.assertListEqual(
            list(df_loaded.columns), 
            list(self.df.columns)
        )
    
    def test_list_tables(self):
        """Test listing database tables."""
        # Create tables
        self.db_manager.save_dataframe(self.df, 'table1')
        self.db_manager.save_dataframe(self.df, 'table2')
        
        # List tables
        tables = self.db_manager.list_tables()
        
        self.assertIn('table1', tables)
        self.assertIn('table2', tables)
    
    def test_get_table_info(self):
        """Test getting table information."""
        self.db_manager.save_dataframe(self.df, 'test_table')
        
        info = self.db_manager.get_table_info('test_table')
        
        self.assertIn('name', info)
        self.assertIn('row_count', info)
        self.assertIn('columns', info)
        self.assertEqual(info['row_count'], 3)
    
    def test_delete_table(self):
        """Test deleting a table."""
        self.db_manager.save_dataframe(self.df, 'test_table')
        self.db_manager.delete_table('test_table')
        
        tables = self.db_manager.list_tables()
        self.assertNotIn('test_table', tables)
    
    def test_context_manager(self):
        """Test using DatabaseManager as context manager."""
        with DatabaseManager(self.db_path) as db:
            db.save_dataframe(self.df, 'test_table')
            df_loaded = db.load_dataframe('test_table')
            self.assertEqual(len(df_loaded), len(self.df))


if __name__ == '__main__':
    unittest.main()
