"""Data normalization module."""
import pandas as pd
import re
from typing import List, Optional
from datetime import datetime
from goldminer.utils import setup_logger


class DataNormalizer:
    """Normalizes and standardizes data fields."""
    
    def __init__(self, config=None):
        """
        Initialize data normalizer.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Get date formats from config
        if config:
            self.date_formats = config.get('etl.date_formats', [])
        else:
            self.date_formats = [
                "%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y",
                "%Y/%m/%d", "%d/%m/%Y", "%B %d, %Y",
                "%b %d, %Y", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S"
            ]
    
    def normalize_dataframe(self, df: pd.DataFrame, 
                          strip_whitespace: bool = True,
                          lowercase_columns: bool = True) -> pd.DataFrame:
        """
        Apply general normalization to DataFrame.
        
        Args:
            df: Input DataFrame
            strip_whitespace: Whether to strip whitespace from string columns
            lowercase_columns: Whether to convert column names to lowercase
            
        Returns:
            Normalized DataFrame
        """
        df_norm = df.copy()
        
        # Normalize column names
        if lowercase_columns:
            df_norm.columns = [self._normalize_column_name(col) for col in df_norm.columns]
            self.logger.info("Normalized column names to lowercase with underscores")
        
        # Strip whitespace from string columns
        if strip_whitespace:
            for col in df_norm.select_dtypes(include=['object']).columns:
                df_norm[col] = df_norm[col].apply(
                    lambda x: x.strip() if isinstance(x, str) else x
                )
            self.logger.info("Stripped whitespace from string columns")
        
        return df_norm
    
    def _normalize_column_name(self, col_name: str) -> str:
        """
        Normalize column name to lowercase with underscores.
        
        Args:
            col_name: Original column name
            
        Returns:
            Normalized column name
        """
        # Replace spaces and special characters with underscores
        normalized = re.sub(r'[^a-zA-Z0-9]+', '_', col_name)
        # Convert to lowercase
        normalized = normalized.lower()
        # Remove leading/trailing underscores
        normalized = normalized.strip('_')
        return normalized
    
    def standardize_dates(self, df: pd.DataFrame, 
                         date_columns: Optional[List[str]] = None,
                         target_format: str = "%Y-%m-%d") -> pd.DataFrame:
        """
        Standardize date columns to a consistent format.
        
        Args:
            df: Input DataFrame
            date_columns: List of column names to standardize (if None, auto-detect)
            target_format: Target date format
            
        Returns:
            DataFrame with standardized dates
        """
        df_std = df.copy()
        
        if date_columns is None:
            # Auto-detect date columns
            date_columns = self._detect_date_columns(df_std)
        
        for col in date_columns:
            if col not in df_std.columns:
                continue
            
            self.logger.info(f"Standardizing dates in column: {col}")
            df_std[col] = df_std[col].apply(lambda x: self._parse_date(x, target_format))
        
        return df_std
    
    def _detect_date_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that likely contain dates.
        
        Args:
            df: Input DataFrame
            
        Returns:
            List of column names that likely contain dates
        """
        date_columns = []
        
        for col in df.columns:
            # Check if already datetime type
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_columns.append(col)
                continue
            
            # Check column name for date-related keywords
            col_lower = str(col).lower()
            if any(keyword in col_lower for keyword in ['date', 'time', 'timestamp', 'created', 'updated']):
                # Sample some non-null values and try to parse
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    parsed_count = sum(1 for val in sample if self._try_parse_date(val))
                    if parsed_count / len(sample) > 0.5:  # More than 50% parseable
                        date_columns.append(col)
        
        self.logger.info(f"Detected date columns: {date_columns}")
        return date_columns
    
    def _try_parse_date(self, value) -> bool:
        """
        Try to parse a value as a date.
        
        Args:
            value: Value to parse
            
        Returns:
            True if parseable, False otherwise
        """
        if pd.isna(value):
            return False
        
        value_str = str(value)
        
        for fmt in self.date_formats:
            try:
                datetime.strptime(value_str, fmt)
                return True
            except (ValueError, TypeError):
                continue
        
        # Try pandas' intelligent parsing
        try:
            pd.to_datetime(value_str)
            return True
        except:
            return False
    
    def _parse_date(self, value, target_format: str = "%Y-%m-%d"):
        """
        Parse a date value and return in target format.
        
        Args:
            value: Date value to parse
            target_format: Target format string
            
        Returns:
            Formatted date string or original value if parsing fails
        """
        if pd.isna(value):
            return None
        
        value_str = str(value)
        
        # Try each format
        for fmt in self.date_formats:
            try:
                dt = datetime.strptime(value_str, fmt)
                return dt.strftime(target_format)
            except (ValueError, TypeError):
                continue
        
        # Try pandas' intelligent parsing
        try:
            dt = pd.to_datetime(value_str)
            return dt.strftime(target_format)
        except:
            self.logger.debug(f"Could not parse date: {value}")
            return value
    
    def normalize_numeric(self, df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """
        Normalize numeric columns (remove commas, currency symbols, etc.).
        
        Args:
            df: Input DataFrame
            columns: List of column names to normalize
            
        Returns:
            DataFrame with normalized numeric columns
        """
        df_norm = df.copy()
        
        for col in columns:
            if col not in df_norm.columns:
                continue
            
            self.logger.info(f"Normalizing numeric column: {col}")
            df_norm[col] = df_norm[col].apply(self._clean_numeric)
        
        return df_norm
    
    def _clean_numeric(self, value):
        """
        Clean numeric value by removing currency symbols, commas, etc.
        
        Args:
            value: Value to clean
            
        Returns:
            Cleaned numeric value or None
        """
        if pd.isna(value):
            return None
        
        if isinstance(value, (int, float)):
            return value
        
        # Remove currency symbols, commas, and whitespace
        value_str = str(value)
        value_str = re.sub(r'[$£€¥,\s]', '', value_str)
        
        try:
            return float(value_str)
        except ValueError:
            return None
