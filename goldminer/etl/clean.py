"""Data cleaning module for handling duplicates and data quality."""
import pandas as pd
from typing import List, Optional, Dict, Any
from goldminer.utils import setup_logger


class DataCleaner:
    """Handles data cleaning including duplicate removal."""
    
    def __init__(self, config=None):
        """
        Initialize data cleaner.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
    
    def remove_duplicates(self, df: pd.DataFrame, 
                         subset: Optional[List[str]] = None,
                         keep: str = 'first') -> pd.DataFrame:
        """
        Remove duplicate rows from DataFrame.
        
        Args:
            df: Input DataFrame
            subset: Column names to consider for identifying duplicates
                   (if None, use all columns)
            keep: Which duplicates to keep ('first', 'last', False for remove all)
            
        Returns:
            DataFrame with duplicates removed
        """
        initial_rows = len(df)
        
        df_clean = df.drop_duplicates(subset=subset, keep=keep)
        
        removed_count = initial_rows - len(df_clean)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} duplicate rows")
        else:
            self.logger.info("No duplicates found")
        
        return df_clean
    
    def handle_missing_values(self, df: pd.DataFrame,
                            strategy: str = 'drop',
                            fill_value: Any = None,
                            columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Handle missing values in DataFrame.
        
        Args:
            df: Input DataFrame
            strategy: Strategy for handling missing values
                     ('drop', 'fill', 'forward_fill', 'backward_fill')
            fill_value: Value to use when strategy is 'fill'
            columns: Specific columns to process (if None, process all)
            
        Returns:
            DataFrame with missing values handled
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.columns.tolist()
        
        initial_nulls = df_clean[columns].isnull().sum().sum()
        
        if strategy == 'drop':
            df_clean = df_clean.dropna(subset=columns)
            self.logger.info(f"Dropped rows with missing values in {columns}")
        elif strategy == 'fill':
            df_clean[columns] = df_clean[columns].fillna(fill_value)
            self.logger.info(f"Filled missing values with {fill_value}")
        elif strategy == 'forward_fill':
            df_clean[columns] = df_clean[columns].fillna(method='ffill')
            self.logger.info("Applied forward fill to missing values")
        elif strategy == 'backward_fill':
            df_clean[columns] = df_clean[columns].fillna(method='bfill')
            self.logger.info("Applied backward fill to missing values")
        else:
            self.logger.warning(f"Unknown strategy: {strategy}")
        
        final_nulls = df_clean[columns].isnull().sum().sum()
        self.logger.info(f"Reduced null values from {initial_nulls} to {final_nulls}")
        
        return df_clean
    
    def remove_outliers(self, df: pd.DataFrame,
                       columns: List[str],
                       method: str = 'iqr',
                       threshold: float = 1.5) -> pd.DataFrame:
        """
        Remove outliers from numeric columns.
        
        Args:
            df: Input DataFrame
            columns: List of numeric columns to check for outliers
            method: Method for outlier detection ('iqr' or 'zscore')
            threshold: Threshold for outlier detection
                      (IQR multiplier for 'iqr', z-score for 'zscore')
            
        Returns:
            DataFrame with outliers removed
        """
        df_clean = df.copy()
        initial_rows = len(df_clean)
        
        for col in columns:
            if col not in df_clean.columns:
                continue
            
            if not pd.api.types.is_numeric_dtype(df_clean[col]):
                self.logger.warning(f"Column {col} is not numeric, skipping outlier removal")
                continue
            
            if method == 'iqr':
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - threshold * IQR
                upper_bound = Q3 + threshold * IQR
                
                mask = (df_clean[col] >= lower_bound) & (df_clean[col] <= upper_bound)
                df_clean = df_clean[mask]
                
            elif method == 'zscore':
                mean = df_clean[col].mean()
                std = df_clean[col].std()
                z_scores = ((df_clean[col] - mean) / std).abs()
                df_clean = df_clean[z_scores <= threshold]
        
        removed_count = initial_rows - len(df_clean)
        if removed_count > 0:
            self.logger.info(f"Removed {removed_count} outlier rows")
        
        return df_clean
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate data quality report.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary containing data quality metrics
        """
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "duplicate_rows": df.duplicated().sum(),
            "columns": {}
        }
        
        for col in df.columns:
            col_report = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float(df[col].isnull().sum() / len(df) * 100),
                "unique_count": int(df[col].nunique()),
                "unique_percentage": float(df[col].nunique() / len(df) * 100)
            }
            
            # Add numeric-specific metrics
            if pd.api.types.is_numeric_dtype(df[col]):
                col_report["zero_count"] = int((df[col] == 0).sum())
                col_report["negative_count"] = int((df[col] < 0).sum())
            
            quality_report["columns"][col] = col_report
        
        self.logger.info("Generated data quality report")
        return quality_report
    
    def clean_text_columns(self, df: pd.DataFrame, 
                          columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Clean text columns by removing extra whitespace and special characters.
        
        Args:
            df: Input DataFrame
            columns: List of columns to clean (if None, clean all text columns)
            
        Returns:
            DataFrame with cleaned text columns
        """
        df_clean = df.copy()
        
        if columns is None:
            columns = df_clean.select_dtypes(include=['object']).columns.tolist()
        
        for col in columns:
            if col not in df_clean.columns:
                continue
            
            df_clean[col] = df_clean[col].apply(self._clean_text)
            self.logger.debug(f"Cleaned text in column: {col}")
        
        return df_clean
    
    def _clean_text(self, value):
        """
        Clean a single text value.
        
        Args:
            value: Text value to clean
            
        Returns:
            Cleaned text value
        """
        if pd.isna(value):
            return value
        
        if not isinstance(value, str):
            value = str(value)
        
        # Remove extra whitespace
        value = ' '.join(value.split())
        
        return value
