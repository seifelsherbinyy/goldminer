"""
Transaction Analysis Module for Time-Series Transaction Data.

This module provides comprehensive analysis capabilities for transaction datasets
including hourly, daily, and monthly aggregations, anomaly detection, trend analysis,
and visualization support.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from goldminer.utils import setup_logger


class TransactionAnalyzer:
    """
    Comprehensive transaction analyzer for time-series data.
    
    This class provides methods to analyze transaction data at different time granularities
    (hourly, daily, monthly), detect anomalies, calculate trends, and identify 
    top-performing periods.
    """
    
    def __init__(self, config=None):
        """
        Initialize transaction analyzer.
        
        Args:
            config: Configuration manager instance (optional)
        """
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Get configuration or use defaults
        if config:
            self.zscore_threshold = config.get('analysis.anomaly_detection.zscore_threshold', 3.0)
            self.iqr_multiplier = config.get('analysis.anomaly_detection.iqr_multiplier', 1.5)
            self.trend_window = config.get('analysis.trend_window', 7)
        else:
            self.zscore_threshold = 3.0
            self.iqr_multiplier = 1.5
            self.trend_window = 7
    
    def validate_dataframe(self, df: pd.DataFrame, date_column: Optional[str] = None) -> Tuple[pd.DataFrame, str]:
        """
        Validate and prepare DataFrame for analysis.
        
        Args:
            df: Input DataFrame
            date_column: Name of the date/timestamp column (auto-detected if None)
            
        Returns:
            Tuple of (validated DataFrame, date column name)
            
        Raises:
            ValueError: If DataFrame is empty or no date column found
        """
        if df is None or df.empty:
            raise ValueError("DataFrame is empty or None")
        
        # Auto-detect date column if not provided
        if date_column is None:
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) == 0:
                # Try to find string columns that might be dates
                for col in df.columns:
                    try:
                        pd.to_datetime(df[col], errors='coerce')
                        if df[col].notna().sum() > 0:
                            date_column = col
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                            break
                    except:
                        continue
            else:
                date_column = date_cols[0]
        
        if date_column is None or date_column not in df.columns:
            raise ValueError(f"Date column '{date_column}' not found in DataFrame")
        
        # Ensure date column is datetime type
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
        
        # Remove rows with invalid dates
        initial_count = len(df)
        df = df[df[date_column].notna()].copy()
        removed_count = initial_count - len(df)
        
        if removed_count > 0:
            self.logger.warning(f"Removed {removed_count} rows with invalid dates")
        
        if df.empty:
            raise ValueError("No valid data remaining after date validation")
        
        self.logger.info(f"Validated DataFrame: {len(df)} rows, date column: '{date_column}'")
        return df, date_column
    
    def summarize_by_hour(self, df: pd.DataFrame, 
                         value_column: str,
                         date_column: Optional[str] = None,
                         aggregation: str = 'sum') -> pd.DataFrame:
        """
        Summarize transactions by hour of day.
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            aggregation: Aggregation method ('sum', 'mean', 'count', 'min', 'max')
            
        Returns:
            DataFrame with hourly summaries
        """
        df, date_column = self.validate_dataframe(df, date_column)
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        # Extract hour from timestamp
        df_copy = df.copy()
        df_copy['hour'] = df_copy[date_column].dt.hour
        
        # Aggregate by hour
        if aggregation == 'sum':
            hourly_data = df_copy.groupby('hour')[value_column].sum()
        elif aggregation == 'mean':
            hourly_data = df_copy.groupby('hour')[value_column].mean()
        elif aggregation == 'count':
            hourly_data = df_copy.groupby('hour')[value_column].count()
        elif aggregation == 'min':
            hourly_data = df_copy.groupby('hour')[value_column].min()
        elif aggregation == 'max':
            hourly_data = df_copy.groupby('hour')[value_column].max()
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        # Create result DataFrame with all 24 hours
        result = pd.DataFrame({
            'hour': range(24),
            f'{value_column}_{aggregation}': 0.0
        })
        
        # Fill in actual values
        for hour, value in hourly_data.items():
            result.loc[result['hour'] == hour, f'{value_column}_{aggregation}'] = value
        
        result['transaction_count'] = df_copy.groupby('hour').size().reindex(range(24), fill_value=0).values
        
        self.logger.info(f"Generated hourly summary with {aggregation} aggregation")
        return result
    
    def summarize_by_day(self, df: pd.DataFrame,
                        value_column: str,
                        date_column: Optional[str] = None,
                        aggregation: str = 'sum') -> pd.DataFrame:
        """
        Summarize transactions by day.
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            aggregation: Aggregation method ('sum', 'mean', 'count', 'min', 'max')
            
        Returns:
            DataFrame with daily summaries
        """
        df, date_column = self.validate_dataframe(df, date_column)
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        # Extract date (without time)
        df_copy = df.copy()
        df_copy['date'] = df_copy[date_column].dt.date
        
        # Aggregate by date
        if aggregation == 'sum':
            daily_data = df_copy.groupby('date')[value_column].sum()
        elif aggregation == 'mean':
            daily_data = df_copy.groupby('date')[value_column].mean()
        elif aggregation == 'count':
            daily_data = df_copy.groupby('date')[value_column].count()
        elif aggregation == 'min':
            daily_data = df_copy.groupby('date')[value_column].min()
        elif aggregation == 'max':
            daily_data = df_copy.groupby('date')[value_column].max()
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        # Create result DataFrame
        result = pd.DataFrame({
            'date': daily_data.index,
            f'{value_column}_{aggregation}': daily_data.values
        })
        
        # Add transaction count
        result['transaction_count'] = df_copy.groupby('date').size().values
        
        # Add day of week
        result['day_of_week'] = pd.to_datetime(result['date']).dt.day_name()
        
        # Sort by date
        result = result.sort_values('date').reset_index(drop=True)
        
        self.logger.info(f"Generated daily summary for {len(result)} days with {aggregation} aggregation")
        return result
    
    def summarize_by_month(self, df: pd.DataFrame,
                          value_column: str,
                          date_column: Optional[str] = None,
                          aggregation: str = 'sum') -> pd.DataFrame:
        """
        Summarize transactions by month.
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            aggregation: Aggregation method ('sum', 'mean', 'count', 'min', 'max')
            
        Returns:
            DataFrame with monthly summaries
        """
        df, date_column = self.validate_dataframe(df, date_column)
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        # Extract year-month
        df_copy = df.copy()
        df_copy['year'] = df_copy[date_column].dt.year
        df_copy['month'] = df_copy[date_column].dt.month
        df_copy['year_month'] = df_copy[date_column].dt.to_period('M')
        
        # Aggregate by year-month
        if aggregation == 'sum':
            monthly_data = df_copy.groupby('year_month')[value_column].sum()
        elif aggregation == 'mean':
            monthly_data = df_copy.groupby('year_month')[value_column].mean()
        elif aggregation == 'count':
            monthly_data = df_copy.groupby('year_month')[value_column].count()
        elif aggregation == 'min':
            monthly_data = df_copy.groupby('year_month')[value_column].min()
        elif aggregation == 'max':
            monthly_data = df_copy.groupby('year_month')[value_column].max()
        else:
            raise ValueError(f"Unknown aggregation method: {aggregation}")
        
        # Create result DataFrame
        result = pd.DataFrame({
            'year_month': monthly_data.index.astype(str),
            f'{value_column}_{aggregation}': monthly_data.values
        })
        
        # Add additional metrics
        result['transaction_count'] = df_copy.groupby('year_month').size().values
        result['year'] = df_copy.groupby('year_month')['year'].first().values
        result['month'] = df_copy.groupby('year_month')['month'].first().values
        result['month_name'] = pd.to_datetime(result['year'].astype(str) + '-' + 
                                              result['month'].astype(str) + '-01').dt.month_name()
        
        # Sort by year-month
        result = result.sort_values('year_month').reset_index(drop=True)
        
        self.logger.info(f"Generated monthly summary for {len(result)} months with {aggregation} aggregation")
        return result
    
    def detect_spikes_and_drops(self, df: pd.DataFrame,
                               value_column: str,
                               threshold: Optional[float] = None,
                               method: str = 'zscore') -> Dict[str, Any]:
        """
        Detect unusual spikes or drops in transaction values.
        
        Args:
            df: Input DataFrame (already aggregated, e.g., daily or hourly)
            value_column: Column containing values to analyze
            threshold: Threshold for anomaly detection (uses default if None)
            method: Detection method ('zscore' or 'iqr')
            
        Returns:
            Dictionary containing spike and drop information
        """
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        if threshold is None:
            threshold = self.zscore_threshold if method == 'zscore' else self.iqr_multiplier
        
        values = df[value_column].values
        
        if method == 'zscore':
            mean = np.mean(values)
            std = np.std(values)
            
            if std == 0:
                self.logger.warning("Standard deviation is 0, cannot detect anomalies")
                return {'spikes': [], 'drops': [], 'method': method}
            
            z_scores = (values - mean) / std
            spike_mask = z_scores > threshold
            drop_mask = z_scores < -threshold
            
        elif method == 'iqr':
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            
            upper_bound = Q3 + threshold * IQR
            lower_bound = Q1 - threshold * IQR
            
            spike_mask = values > upper_bound
            drop_mask = values < lower_bound
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Identify spikes and drops
        spikes = []
        drops = []
        
        for idx in np.where(spike_mask)[0]:
            spike_info = {
                'index': int(idx),
                'value': float(values[idx])
            }
            # Add additional columns if they exist
            for col in df.columns:
                if col != value_column:
                    spike_info[col] = df.iloc[idx][col]
                    if isinstance(spike_info[col], (pd.Timestamp, datetime)):
                        spike_info[col] = str(spike_info[col])
            spikes.append(spike_info)
        
        for idx in np.where(drop_mask)[0]:
            drop_info = {
                'index': int(idx),
                'value': float(values[idx])
            }
            # Add additional columns if they exist
            for col in df.columns:
                if col != value_column:
                    drop_info[col] = df.iloc[idx][col]
                    if isinstance(drop_info[col], (pd.Timestamp, datetime)):
                        drop_info[col] = str(drop_info[col])
            drops.append(drop_info)
        
        result = {
            'spikes': spikes,
            'drops': drops,
            'spike_count': len(spikes),
            'drop_count': len(drops),
            'method': method,
            'threshold': float(threshold)
        }
        
        self.logger.info(f"Detected {len(spikes)} spikes and {len(drops)} drops using {method} method")
        return result
    
    def calculate_moving_averages(self, df: pd.DataFrame,
                                  value_column: str,
                                  windows: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Calculate moving averages for different window sizes.
        
        Args:
            df: Input DataFrame (sorted by time)
            value_column: Column containing values
            windows: List of window sizes (default: [7, 14, 30])
            
        Returns:
            DataFrame with moving averages added
        """
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        if windows is None:
            windows = [7, 14, 30]
        
        result = df.copy()
        
        for window in windows:
            ma_col = f'{value_column}_ma{window}'
            result[ma_col] = result[value_column].rolling(
                window=window, 
                min_periods=1
            ).mean()
        
        # Calculate overall trend (percentage change)
        result[f'{value_column}_pct_change'] = result[value_column].pct_change() * 100
        
        self.logger.info(f"Calculated moving averages with windows: {windows}")
        return result
    
    def identify_top_periods(self, df: pd.DataFrame,
                            value_column: str,
                            top_n: int = 10,
                            period_type: str = 'all') -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify top-performing periods.
        
        Args:
            df: Input DataFrame with time aggregations
            value_column: Column containing values
            top_n: Number of top periods to return
            period_type: Type of period ('all', 'positive', 'negative')
            
        Returns:
            Dictionary containing top and bottom performing periods
        """
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        # Sort by value
        sorted_df = df.sort_values(value_column, ascending=False)
        
        # Get top performers
        top_periods = []
        for idx, row in sorted_df.head(top_n).iterrows():
            period_info = {'value': float(row[value_column])}
            for col in df.columns:
                if col != value_column:
                    val = row[col]
                    if isinstance(val, (pd.Timestamp, datetime)):
                        period_info[col] = str(val)
                    elif isinstance(val, (np.integer, np.floating)):
                        period_info[col] = float(val)
                    else:
                        period_info[col] = val
            top_periods.append(period_info)
        
        # Get bottom performers if requested
        bottom_periods = []
        if period_type in ['all', 'negative']:
            for idx, row in sorted_df.tail(top_n).iterrows():
                period_info = {'value': float(row[value_column])}
                for col in df.columns:
                    if col != value_column:
                        val = row[col]
                        if isinstance(val, (pd.Timestamp, datetime)):
                            period_info[col] = str(val)
                        elif isinstance(val, (np.integer, np.floating)):
                            period_info[col] = float(val)
                        else:
                            period_info[col] = val
                bottom_periods.append(period_info)
        
        result = {
            'top_performers': top_periods,
            'bottom_performers': bottom_periods[::-1] if bottom_periods else [],
            'total_periods': len(df)
        }
        
        self.logger.info(f"Identified top {top_n} performing periods")
        return result
    
    def calculate_performance_indicators(self, df: pd.DataFrame,
                                         value_column: str,
                                         date_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive performance indicators.
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            
        Returns:
            Dictionary with performance metrics
        """
        df, date_column = self.validate_dataframe(df, date_column)
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in DataFrame")
        
        values = df[value_column].values
        
        indicators = {
            'total_transactions': int(len(df)),
            'total_value': float(np.sum(values)),
            'average_value': float(np.mean(values)),
            'median_value': float(np.median(values)),
            'std_deviation': float(np.std(values)),
            'min_value': float(np.min(values)),
            'max_value': float(np.max(values)),
            'value_range': float(np.max(values) - np.min(values)),
            'coefficient_of_variation': float(np.std(values) / np.mean(values)) if np.mean(values) != 0 else 0,
            'date_range': {
                'start': str(df[date_column].min()),
                'end': str(df[date_column].max()),
                'days': int((df[date_column].max() - df[date_column].min()).days)
            },
            'quartiles': {
                'q1': float(np.percentile(values, 25)),
                'q2': float(np.percentile(values, 50)),
                'q3': float(np.percentile(values, 75))
            }
        }
        
        # Calculate growth rate if data spans multiple periods
        if len(df) > 1:
            df_sorted = df.sort_values(date_column)
            first_value = df_sorted[value_column].iloc[0]
            last_value = df_sorted[value_column].iloc[-1]
            
            if first_value != 0:
                indicators['growth_rate'] = float((last_value - first_value) / first_value * 100)
            else:
                indicators['growth_rate'] = None
        
        self.logger.info("Calculated comprehensive performance indicators")
        return indicators
    
    def generate_comprehensive_report(self, df: pd.DataFrame,
                                     value_column: str,
                                     date_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive analysis report for transaction data.
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            
        Returns:
            Dictionary containing complete analysis report
        """
        self.logger.info("Generating comprehensive transaction analysis report")
        
        df, date_column = self.validate_dataframe(df, date_column)
        
        report = {
            'overview': self.calculate_performance_indicators(df, value_column, date_column),
            'hourly_analysis': {},
            'daily_analysis': {},
            'monthly_analysis': {},
            'anomalies': {},
            'trends': {}
        }
        
        # Hourly analysis
        try:
            hourly_summary = self.summarize_by_hour(df, value_column, date_column)
            report['hourly_analysis'] = {
                'summary': hourly_summary.to_dict('records'),
                'peak_hour': int(hourly_summary.loc[hourly_summary[f'{value_column}_sum'].idxmax(), 'hour']),
                'lowest_hour': int(hourly_summary.loc[hourly_summary[f'{value_column}_sum'].idxmin(), 'hour'])
            }
        except Exception as e:
            self.logger.warning(f"Could not complete hourly analysis: {e}")
            report['hourly_analysis'] = {'error': str(e)}
        
        # Daily analysis
        try:
            daily_summary = self.summarize_by_day(df, value_column, date_column)
            daily_with_ma = self.calculate_moving_averages(daily_summary, f'{value_column}_sum')
            
            report['daily_analysis'] = {
                'summary': daily_with_ma.to_dict('records')[:30],  # First 30 days
                'anomalies': self.detect_spikes_and_drops(daily_summary, f'{value_column}_sum'),
                'top_days': self.identify_top_periods(daily_summary, f'{value_column}_sum', top_n=5)
            }
        except Exception as e:
            self.logger.warning(f"Could not complete daily analysis: {e}")
            report['daily_analysis'] = {'error': str(e)}
        
        # Monthly analysis
        try:
            monthly_summary = self.summarize_by_month(df, value_column, date_column)
            monthly_with_ma = self.calculate_moving_averages(monthly_summary, f'{value_column}_sum', windows=[3, 6])
            
            report['monthly_analysis'] = {
                'summary': monthly_with_ma.to_dict('records'),
                'anomalies': self.detect_spikes_and_drops(monthly_summary, f'{value_column}_sum'),
                'top_months': self.identify_top_periods(monthly_summary, f'{value_column}_sum', top_n=5)
            }
        except Exception as e:
            self.logger.warning(f"Could not complete monthly analysis: {e}")
            report['monthly_analysis'] = {'error': str(e)}
        
        self.logger.info("Comprehensive report generation completed")
        return report
    
    def generate_visualization_data(self, df: pd.DataFrame,
                                   value_column: str,
                                   date_column: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate data formatted for visualization (charts, graphs).
        
        Args:
            df: Input DataFrame
            value_column: Column containing transaction values
            date_column: Column containing timestamps
            
        Returns:
            Dictionary with data formatted for various chart types
        """
        df, date_column = self.validate_dataframe(df, date_column)
        
        # Daily time series
        daily_summary = self.summarize_by_day(df, value_column, date_column)
        daily_with_ma = self.calculate_moving_averages(daily_summary, f'{value_column}_sum')
        
        # Hourly distribution
        hourly_summary = self.summarize_by_hour(df, value_column, date_column)
        
        # Monthly trends
        monthly_summary = self.summarize_by_month(df, value_column, date_column)
        
        viz_data = {
            'time_series': {
                'dates': [str(d) for d in daily_summary['date'].tolist()],
                'values': daily_summary[f'{value_column}_sum'].tolist(),
                'moving_average_7': daily_with_ma[f'{value_column}_sum_ma7'].tolist() if f'{value_column}_sum_ma7' in daily_with_ma.columns else []
            },
            'hourly_distribution': {
                'hours': hourly_summary['hour'].tolist(),
                'values': hourly_summary[f'{value_column}_sum'].tolist()
            },
            'monthly_trends': {
                'months': monthly_summary['year_month'].tolist(),
                'values': monthly_summary[f'{value_column}_sum'].tolist(),
                'transaction_counts': monthly_summary['transaction_count'].tolist()
            }
        }
        
        self.logger.info("Generated visualization data")
        return viz_data
