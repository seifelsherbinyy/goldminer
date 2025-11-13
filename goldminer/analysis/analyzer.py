"""Data analysis module for metrics, trends, and anomaly detection."""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from goldminer.utils import setup_logger


class DataAnalyzer:
    """Provides analysis capabilities for processed data."""
    
    def __init__(self, config=None):
        """
        Initialize data analyzer.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Get analysis configuration
        if config:
            self.zscore_threshold = config.get('analysis.anomaly_detection.zscore_threshold', 3.0)
            self.iqr_multiplier = config.get('analysis.anomaly_detection.iqr_multiplier', 1.5)
            self.trend_window = config.get('analysis.trend_window', 7)
        else:
            self.zscore_threshold = 3.0
            self.iqr_multiplier = 1.5
            self.trend_window = 7
    
    def generate_summary_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for DataFrame.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary containing summary metrics
        """
        self.logger.info("Generating summary metrics")
        
        summary = {
            "overview": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024)
            },
            "numeric_columns": {},
            "categorical_columns": {},
            "date_columns": {}
        }
        
        # Analyze numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            summary["numeric_columns"][col] = {
                "count": int(df[col].count()),
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "25%": float(df[col].quantile(0.25)),
                "50%": float(df[col].median()),
                "75%": float(df[col].quantile(0.75)),
                "max": float(df[col].max()),
                "null_count": int(df[col].isnull().sum())
            }
        
        # Analyze categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            top_values = df[col].value_counts().head(5).to_dict()
            summary["categorical_columns"][col] = {
                "unique_count": int(df[col].nunique()),
                "null_count": int(df[col].isnull().sum()),
                "top_values": {str(k): int(v) for k, v in top_values.items()}
            }
        
        # Analyze date columns
        date_cols = df.select_dtypes(include=['datetime64']).columns
        for col in date_cols:
            summary["date_columns"][col] = {
                "min_date": str(df[col].min()),
                "max_date": str(df[col].max()),
                "date_range_days": int((df[col].max() - df[col].min()).days),
                "null_count": int(df[col].isnull().sum())
            }
        
        self.logger.info(f"Generated metrics for {len(df.columns)} columns")
        return summary
    
    def detect_anomalies(self, df: pd.DataFrame, 
                        columns: Optional[List[str]] = None,
                        method: str = 'zscore') -> Dict[str, pd.DataFrame]:
        """
        Detect anomalies in numeric columns.
        
        Args:
            df: Input DataFrame
            columns: List of columns to check (if None, check all numeric)
            method: Method for anomaly detection ('zscore' or 'iqr')
            
        Returns:
            Dictionary mapping column names to DataFrames of anomalies
        """
        self.logger.info(f"Detecting anomalies using {method} method")
        
        if columns is None:
            columns = df.select_dtypes(include=['number']).columns.tolist()
        
        anomalies = {}
        
        for col in columns:
            if col not in df.columns or not pd.api.types.is_numeric_dtype(df[col]):
                continue
            
            if method == 'zscore':
                anomaly_mask = self._detect_anomalies_zscore(df[col])
            elif method == 'iqr':
                anomaly_mask = self._detect_anomalies_iqr(df[col])
            else:
                self.logger.warning(f"Unknown method: {method}")
                continue
            
            if anomaly_mask.any():
                anomalies[col] = df[anomaly_mask].copy()
                anomalies[col]['anomaly_column'] = col
                self.logger.info(f"Found {anomaly_mask.sum()} anomalies in column '{col}'")
        
        return anomalies
    
    def _detect_anomalies_zscore(self, series: pd.Series) -> pd.Series:
        """
        Detect anomalies using z-score method.
        
        Args:
            series: Input series
            
        Returns:
            Boolean series indicating anomalies
        """
        mean = series.mean()
        std = series.std()
        
        if std == 0:
            return pd.Series([False] * len(series), index=series.index)
        
        z_scores = np.abs((series - mean) / std)
        return z_scores > self.zscore_threshold
    
    def _detect_anomalies_iqr(self, series: pd.Series) -> pd.Series:
        """
        Detect anomalies using IQR method.
        
        Args:
            series: Input series
            
        Returns:
            Boolean series indicating anomalies
        """
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - self.iqr_multiplier * IQR
        upper_bound = Q3 + self.iqr_multiplier * IQR
        
        return (series < lower_bound) | (series > upper_bound)
    
    def calculate_trends(self, df: pd.DataFrame,
                        value_column: str,
                        date_column: Optional[str] = None,
                        window: Optional[int] = None) -> pd.DataFrame:
        """
        Calculate trends over time using moving averages.
        
        Args:
            df: Input DataFrame
            value_column: Column containing values to analyze
            date_column: Column containing dates (if None, auto-detect)
            window: Window size for moving average (if None, use config)
            
        Returns:
            DataFrame with trend calculations
        """
        if window is None:
            window = self.trend_window
        
        df_trend = df.copy()
        
        # Auto-detect date column if not provided
        if date_column is None:
            date_cols = df_trend.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                date_column = date_cols[0]
            else:
                self.logger.warning("No date column found, using row index")
        
        # Sort by date if available
        if date_column and date_column in df_trend.columns:
            df_trend = df_trend.sort_values(date_column)
        
        # Calculate moving average
        df_trend[f'{value_column}_ma{window}'] = df_trend[value_column].rolling(
            window=window, min_periods=1
        ).mean()
        
        # Calculate trend direction
        df_trend[f'{value_column}_trend'] = df_trend[f'{value_column}_ma{window}'].diff()
        
        self.logger.info(f"Calculated trends for column '{value_column}' with window={window}")
        return df_trend
    
    def generate_correlation_matrix(self, df: pd.DataFrame,
                                   columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Generate correlation matrix for numeric columns.
        
        Args:
            df: Input DataFrame
            columns: List of columns to include (if None, use all numeric)
            
        Returns:
            Correlation matrix DataFrame
        """
        if columns is None:
            columns = df.select_dtypes(include=['number']).columns.tolist()
        
        correlation_matrix = df[columns].corr()
        self.logger.info(f"Generated correlation matrix for {len(columns)} columns")
        
        return correlation_matrix
    
    def identify_outliers(self, df: pd.DataFrame,
                         columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Identify outliers and provide statistics.
        
        Args:
            df: Input DataFrame
            columns: List of columns to check (if None, check all numeric)
            
        Returns:
            Dictionary with outlier information
        """
        if columns is None:
            columns = df.select_dtypes(include=['number']).columns.tolist()
        
        outlier_report = {}
        
        for col in columns:
            if col not in df.columns:
                continue
            
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.iqr_multiplier * IQR
            upper_bound = Q3 + self.iqr_multiplier * IQR
            
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                outlier_report[col] = {
                    "count": int(outlier_count),
                    "percentage": float(outlier_count / len(df) * 100),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "outlier_values": df[outlier_mask][col].tolist()[:10]  # First 10
                }
        
        self.logger.info(f"Identified outliers in {len(outlier_report)} columns")
        return outlier_report
    
    def generate_full_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Dictionary containing full analysis report
        """
        self.logger.info("Generating comprehensive analysis report")
        
        report = {
            "summary_metrics": self.generate_summary_metrics(df),
            "outliers": self.identify_outliers(df),
            "anomalies": {}
        }
        
        # Add anomaly detection
        anomalies = self.detect_anomalies(df)
        for col, anomaly_df in anomalies.items():
            report["anomalies"][col] = {
                "count": len(anomaly_df),
                "sample": anomaly_df.head(5).to_dict('records')
            }
        
        # Add correlation matrix for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric_cols) > 1:
            report["correlations"] = self.generate_correlation_matrix(df).to_dict()
        
        self.logger.info("Analysis report generated successfully")
        return report
