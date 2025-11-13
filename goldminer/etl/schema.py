"""Schema inference module."""
import pandas as pd
from typing import Dict, Any, List
from goldminer.utils import setup_logger


class SchemaInference:
    """Infers and manages schemas for data sources."""
    
    def __init__(self, config=None):
        """
        Initialize schema inference.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
    
    def infer_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Infer schema from DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary containing schema information
        """
        self.logger.info("Inferring schema from DataFrame")
        
        schema = {
            "columns": {},
            "row_count": len(df),
            "column_count": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum()
        }
        
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "null_percentage": float(df[col].isnull().sum() / len(df) * 100),
                "unique_count": int(df[col].nunique()),
                "inferred_type": self._infer_column_type(df[col])
            }
            
            # Add sample values
            non_null_values = df[col].dropna()
            if len(non_null_values) > 0:
                col_info["sample_values"] = non_null_values.head(3).tolist()
            
            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(df[col]):
                col_info["stats"] = {
                    "min": float(df[col].min()) if not df[col].isnull().all() else None,
                    "max": float(df[col].max()) if not df[col].isnull().all() else None,
                    "mean": float(df[col].mean()) if not df[col].isnull().all() else None,
                    "median": float(df[col].median()) if not df[col].isnull().all() else None,
                    "std": float(df[col].std()) if not df[col].isnull().all() else None
                }
            
            schema["columns"][col] = col_info
        
        self.logger.info(f"Schema inferred: {schema['column_count']} columns, {schema['row_count']} rows")
        return schema
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """
        Infer semantic type of a column.
        
        Args:
            series: Pandas Series
            
        Returns:
            Inferred type as string
        """
        # Check if numeric
        if pd.api.types.is_numeric_dtype(series):
            if pd.api.types.is_integer_dtype(series):
                return "integer"
            return "numeric"
        
        # Check if datetime
        if pd.api.types.is_datetime64_any_dtype(series):
            return "datetime"
        
        # Check if boolean
        if pd.api.types.is_bool_dtype(series):
            return "boolean"
        
        # For object types, try to infer more
        if series.dtype == 'object':
            # Try to detect dates in string format
            non_null = series.dropna()
            if len(non_null) > 0:
                sample = non_null.head(10)
                try:
                    pd.to_datetime(sample)
                    return "date_string"
                except:
                    pass
            
            # Check if categorical (low cardinality)
            unique_ratio = series.nunique() / len(series)
            if unique_ratio < 0.05 and series.nunique() < 50:
                return "categorical"
            
            return "text"
        
        return "unknown"
    
    def suggest_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Suggest optimal data types for DataFrame columns.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary mapping column names to suggested types
        """
        suggestions = {}
        
        for col in df.columns:
            inferred_type = self._infer_column_type(df[col])
            
            if inferred_type == "date_string":
                suggestions[col] = "datetime64"
            elif inferred_type == "categorical":
                suggestions[col] = "category"
            elif inferred_type == "integer" and df[col].min() >= 0:
                # Use unsigned int for non-negative integers
                max_val = df[col].max()
                if max_val < 256:
                    suggestions[col] = "uint8"
                elif max_val < 65536:
                    suggestions[col] = "uint16"
                else:
                    suggestions[col] = "uint32"
            else:
                suggestions[col] = str(df[col].dtype)
        
        return suggestions
    
    def apply_schema(self, df: pd.DataFrame, schema: Dict[str, str]) -> pd.DataFrame:
        """
        Apply schema to DataFrame.
        
        Args:
            df: Input DataFrame
            schema: Dictionary mapping column names to data types
            
        Returns:
            DataFrame with applied schema
        """
        df_copy = df.copy()
        
        for col, dtype in schema.items():
            if col in df_copy.columns:
                try:
                    if dtype.startswith("datetime"):
                        df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
                    else:
                        df_copy[col] = df_copy[col].astype(dtype)
                    self.logger.debug(f"Applied type {dtype} to column {col}")
                except Exception as e:
                    self.logger.warning(f"Could not apply type {dtype} to column {col}: {str(e)}")
        
        return df_copy
