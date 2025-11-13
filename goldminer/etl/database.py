"""Database management module for SQLite."""
import sqlite3
import pandas as pd
import os
from typing import Optional, List, Dict, Any
from goldminer.utils import setup_logger


class DatabaseManager:
    """Manages SQLite database operations."""
    
    def __init__(self, db_path: str = "data/processed/goldminer.db", config=None):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
            config: Configuration manager instance
        """
        self.db_path = db_path
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize connection
        self.connection = None
    
    def connect(self):
        """Establish database connection."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.logger.info(f"Connected to database: {self.db_path}")
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Disconnected from database")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def save_dataframe(self, df: pd.DataFrame, 
                      table_name: str,
                      if_exists: str = 'replace') -> None:
        """
        Save DataFrame to database table.
        
        Args:
            df: DataFrame to save
            table_name: Name of table
            if_exists: How to behave if table exists ('fail', 'replace', 'append')
        """
        self.connect()
        
        try:
            df.to_sql(table_name, self.connection, if_exists=if_exists, index=False)
            self.logger.info(f"Saved {len(df)} rows to table '{table_name}'")
        except Exception as e:
            self.logger.error(f"Error saving to database: {str(e)}")
            raise
    
    def load_dataframe(self, table_name: str, 
                      query: Optional[str] = None) -> pd.DataFrame:
        """
        Load DataFrame from database table.
        
        Args:
            table_name: Name of table to load
            query: Optional SQL query (if None, loads entire table)
            
        Returns:
            DataFrame containing table data
        """
        self.connect()
        
        try:
            if query is None:
                query = f"SELECT * FROM {table_name}"
            
            df = pd.read_sql_query(query, self.connection)
            self.logger.info(f"Loaded {len(df)} rows from table '{table_name}'")
            return df
        except Exception as e:
            self.logger.error(f"Error loading from database: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """
        Execute SQL query and return results.
        
        Args:
            query: SQL query string
            params: Optional query parameters
            
        Returns:
            List of result tuples
        """
        self.connect()
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            self.connection.commit()
            return results
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            raise
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        self.connect()
        
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor = self.connection.cursor()
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        
        self.logger.info(f"Found {len(tables)} tables in database")
        return tables
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table.
        
        Args:
            table_name: Name of table
            
        Returns:
            Dictionary containing table information
        """
        self.connect()
        
        # Get column information
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        table_info = {
            "name": table_name,
            "row_count": row_count,
            "columns": [
                {
                    "name": col[1],
                    "type": col[2],
                    "nullable": not col[3],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        }
        
        return table_info
    
    def delete_table(self, table_name: str) -> None:
        """
        Delete a table from the database.
        
        Args:
            table_name: Name of table to delete
        """
        self.connect()
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.connection.commit()
            self.logger.info(f"Deleted table '{table_name}'")
        except Exception as e:
            self.logger.error(f"Error deleting table: {str(e)}")
            raise
    
    def create_index(self, table_name: str, column_name: str, 
                    index_name: Optional[str] = None) -> None:
        """
        Create an index on a table column.
        
        Args:
            table_name: Name of table
            column_name: Name of column to index
            index_name: Optional name for the index
        """
        self.connect()
        
        if index_name is None:
            index_name = f"idx_{table_name}_{column_name}"
        
        try:
            query = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})"
            self.connection.execute(query)
            self.connection.commit()
            self.logger.info(f"Created index '{index_name}' on {table_name}({column_name})")
        except Exception as e:
            self.logger.error(f"Error creating index: {str(e)}")
            raise
