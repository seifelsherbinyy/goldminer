"""
Parquet Exporter module for exporting transaction data to Parquet files.

This module provides the ParquetExporter class for creating optimized Parquet files
with proper schema optimization, compression, and metadata suitable for data analytics.
"""
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from goldminer.utils import setup_logger


class ParquetExporter:
    """
    Exports transaction data to optimized Parquet files.
    
    Features:
    - Schema optimization (categorical for tags, dictionary encoding for payees)
    - Compression (snappy or brotli)
    - Partitioning by year/month
    - Metadata in file footer (export timestamp, user ID, number of rows)
    - Compatible with downstream tools (Spark, Polars, DuckDB)
    - Consistent schema across exports
    """
    
    def __init__(self):
        """Initialize the Parquet exporter."""
        self.logger = setup_logger(__name__)
        self.logger.info("ParquetExporter initialized")
    
    def export_to_parquet(
        self, 
        transactions: List[Dict[str, Any]], 
        filepath: str,
        compression: str = 'snappy',
        partition_cols: Optional[List[str]] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Export transactions to a Parquet file with optimized schema and metadata.
        
        Args:
            transactions: List of transaction dictionaries with keys like:
                - id, date, amount, currency, payee, category, subcategory,
                  tags, account_id, account_type, interest_rate, urgency, confidence
            filepath: Output filepath for the Parquet file
            compression: Compression algorithm ('snappy', 'brotli', 'gzip', 'zstd', or 'none')
            partition_cols: Optional list of columns to partition by (e.g., ['year', 'month'])
            user_id: Optional user ID to include in metadata
            
        Raises:
            ValueError: If transactions list is empty or filepath is invalid
            IOError: If unable to write to the specified file
        """
        if not transactions:
            raise ValueError("Cannot export empty transaction list")
        
        if not filepath.endswith('.parquet'):
            filepath += '.parquet'
        
        self.logger.info(f"Exporting {len(transactions)} transactions to {filepath}")
        
        # Convert to DataFrame
        df = pd.DataFrame(transactions)
        
        # Normalize and optimize schema
        df = self._optimize_schema(df)
        
        # Add partitioning columns if needed
        if partition_cols:
            df = self._add_partition_columns(df)
        
        # Convert to PyArrow table with optimized schema
        table = self._create_arrow_table(df)
        
        # Add custom metadata
        metadata = self._create_metadata(len(transactions), user_id)
        table = table.replace_schema_metadata(metadata)
        
        # Write to Parquet file
        try:
            if partition_cols:
                # Partitioned write
                pq.write_to_dataset(
                    table,
                    root_path=filepath.replace('.parquet', ''),
                    partition_cols=partition_cols,
                    compression=compression,
                    use_dictionary=True,
                    write_statistics=True
                )
                self.logger.info(f"Successfully exported to partitioned dataset at {filepath.replace('.parquet', '')}")
            else:
                # Single file write
                pq.write_table(
                    table,
                    filepath,
                    compression=compression,
                    use_dictionary=True,
                    write_statistics=True
                )
                self.logger.info(f"Successfully exported to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to write Parquet file: {e}")
            raise IOError(f"Unable to write to file {filepath}: {e}")
    
    def _optimize_schema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize DataFrame schema for efficient Parquet storage.
        
        Optimizations:
        - Convert category, subcategory, account_type, urgency, confidence to categorical
        - Convert tags to string (will use dictionary encoding)
        - Ensure proper data types for numeric and string fields
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with optimized schema
        """
        df_optimized = df.copy()
        
        # Define categorical columns (low cardinality)
        categorical_cols = ['category', 'subcategory', 'account_type', 'urgency', 'confidence', 'currency']
        
        for col in categorical_cols:
            if col in df_optimized.columns:
                df_optimized[col] = df_optimized[col].astype('category')
                self.logger.debug(f"Converted {col} to categorical")
        
        # Ensure string types for high-cardinality text fields
        # These will benefit from dictionary encoding in Parquet
        string_cols = ['id', 'payee', 'normalized_merchant', 'account_id']
        for col in string_cols:
            if col in df_optimized.columns and df_optimized[col].dtype != 'object':
                df_optimized[col] = df_optimized[col].astype(str)
        
        # Handle tags - convert list to string representation for Parquet compatibility
        if 'tags' in df_optimized.columns:
            df_optimized['tags'] = df_optimized['tags'].apply(
                lambda x: ','.join(x) if isinstance(x, list) else (str(x) if pd.notna(x) else '')
            )
            df_optimized['tags'] = df_optimized['tags'].astype('category')
            self.logger.debug("Converted tags to categorical string")
        
        # Ensure numeric types
        if 'amount' in df_optimized.columns:
            df_optimized['amount'] = pd.to_numeric(df_optimized['amount'], errors='coerce')
        
        if 'interest_rate' in df_optimized.columns:
            df_optimized['interest_rate'] = pd.to_numeric(df_optimized['interest_rate'], errors='coerce')
        
        # Ensure date is in proper format
        if 'date' in df_optimized.columns:
            df_optimized['date'] = pd.to_datetime(df_optimized['date'], errors='coerce')
        
        self.logger.info("Schema optimization complete")
        return df_optimized
    
    def _add_partition_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add year and month columns for partitioning.
        
        Args:
            df: Input DataFrame
            
        Returns:
            DataFrame with year and month columns added
        """
        df_with_partitions = df.copy()
        
        if 'date' in df_with_partitions.columns:
            # Ensure date is datetime
            df_with_partitions['date'] = pd.to_datetime(df_with_partitions['date'], errors='coerce')
            
            # Add year and month columns
            df_with_partitions['year'] = df_with_partitions['date'].dt.year
            df_with_partitions['month'] = df_with_partitions['date'].dt.month
            
            self.logger.debug("Added year and month partition columns")
        else:
            self.logger.warning("No date column found for partitioning")
        
        return df_with_partitions
    
    def _create_arrow_table(self, df: pd.DataFrame) -> pa.Table:
        """
        Create PyArrow table from DataFrame with explicit schema.
        
        This ensures consistent schema across exports and proper type handling.
        
        Args:
            df: Input DataFrame
            
        Returns:
            PyArrow Table
        """
        # Build schema dynamically based on available columns
        schema_fields = []
        
        # Define expected field types
        field_types = {
            'id': pa.string(),
            'date': pa.timestamp('ms'),
            'amount': pa.float64(),
            'currency': pa.dictionary(pa.int8(), pa.string()),
            'payee': pa.string(),
            'normalized_merchant': pa.string(),
            'category': pa.dictionary(pa.int8(), pa.string()),
            'subcategory': pa.dictionary(pa.int8(), pa.string()),
            'tags': pa.dictionary(pa.int8(), pa.string()),
            'account_id': pa.string(),
            'account_type': pa.dictionary(pa.int8(), pa.string()),
            'interest_rate': pa.float64(),
            'urgency': pa.dictionary(pa.int8(), pa.string()),
            'confidence': pa.dictionary(pa.int8(), pa.string()),
            'year': pa.int32(),
            'month': pa.int32()
        }
        
        # Build schema from available columns
        for col in df.columns:
            if col in field_types:
                schema_fields.append(pa.field(col, field_types[col]))
            else:
                # Infer type for unknown columns
                schema_fields.append(pa.field(col, pa.from_numpy_dtype(df[col].dtype)))
        
        schema = pa.schema(schema_fields)
        
        # Convert DataFrame to PyArrow table
        table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
        
        self.logger.debug(f"Created PyArrow table with schema: {schema}")
        return table
    
    def _create_metadata(self, num_rows: int, user_id: Optional[str] = None) -> Dict[bytes, bytes]:
        """
        Create custom metadata for Parquet file footer.
        
        Args:
            num_rows: Number of rows in the export
            user_id: Optional user ID
            
        Returns:
            Dictionary of metadata key-value pairs (as bytes)
        """
        export_timestamp = datetime.now(timezone.utc).isoformat()
        
        metadata = {
            b'export_timestamp': export_timestamp.encode('utf-8'),
            b'num_rows': str(num_rows).encode('utf-8'),
            b'exporter': b'GoldMiner ParquetExporter v1.0',
            b'schema_version': b'1.0'
        }
        
        if user_id:
            metadata[b'user_id'] = user_id.encode('utf-8')
        
        self.logger.debug(f"Created metadata with {len(metadata)} entries")
        return metadata
    
    def get_schema_info(self, filepath: str) -> Dict[str, Any]:
        """
        Get schema information from a Parquet file.
        
        Useful for validating schema consistency across runs.
        
        Args:
            filepath: Path to Parquet file
            
        Returns:
            Dictionary with schema information
        """
        try:
            # Read schema without loading full data
            parquet_file = pq.ParquetFile(filepath)
            schema = parquet_file.schema_arrow
            metadata = parquet_file.schema_arrow.metadata
            
            schema_info = {
                'num_columns': len(schema),
                'column_names': schema.names,
                'column_types': {name: str(schema.field(name).type) for name in schema.names},
                'metadata': {k.decode('utf-8'): v.decode('utf-8') for k, v in metadata.items()} if metadata else {},
                'num_row_groups': parquet_file.num_row_groups
            }
            
            self.logger.info(f"Retrieved schema info from {filepath}")
            return schema_info
        except Exception as e:
            self.logger.error(f"Failed to read schema from {filepath}: {e}")
            raise
    
    def validate_compatibility(self, filepath: str) -> Dict[str, bool]:
        """
        Validate that the Parquet file can be read by common tools.
        
        Tests compatibility with:
        - PyArrow
        - Pandas
        - Polars (if available)
        
        Args:
            filepath: Path to Parquet file
            
        Returns:
            Dictionary with compatibility results
        """
        results = {}
        
        # Test PyArrow
        try:
            table = pq.read_table(filepath)
            results['pyarrow'] = True
            self.logger.info("PyArrow compatibility: OK")
        except Exception as e:
            results['pyarrow'] = False
            self.logger.warning(f"PyArrow compatibility failed: {e}")
        
        # Test Pandas
        try:
            df = pd.read_parquet(filepath)
            results['pandas'] = True
            self.logger.info("Pandas compatibility: OK")
        except Exception as e:
            results['pandas'] = False
            self.logger.warning(f"Pandas compatibility failed: {e}")
        
        # Test Polars (optional)
        try:
            import polars as pl
            df_polars = pl.read_parquet(filepath)
            results['polars'] = True
            self.logger.info("Polars compatibility: OK")
        except ImportError:
            results['polars'] = None  # Not installed
            self.logger.info("Polars not installed, skipping compatibility check")
        except Exception as e:
            results['polars'] = False
            self.logger.warning(f"Polars compatibility failed: {e}")
        
        return results
