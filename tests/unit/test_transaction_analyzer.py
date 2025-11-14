"""Unit tests for TransactionAnalyzer."""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from goldminer.analysis import TransactionAnalyzer


class TestTransactionAnalyzer(unittest.TestCase):
    """Test cases for TransactionAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TransactionAnalyzer()
        
        # Create sample transaction data spanning multiple days
        dates = []
        values = []
        base_date = datetime(2024, 1, 1)
        
        # Generate 30 days of hourly data
        for day in range(30):
            for hour in range(24):
                timestamp = base_date + timedelta(days=day, hours=hour)
                dates.append(timestamp)
                # Add some pattern: higher values during business hours
                base_value = 100
                if 9 <= hour <= 17:
                    base_value = 200
                # Add some randomness
                value = base_value + np.random.randint(-20, 20)
                values.append(value)
        
        self.df = pd.DataFrame({
            'timestamp': dates,
            'amount': values
        })
        
        # Add some spikes and drops for anomaly detection
        self.df.loc[100, 'amount'] = 500  # Spike
        self.df.loc[200, 'amount'] = 10   # Drop
    
    def test_validate_dataframe(self):
        """Test DataFrame validation."""
        df, date_col = self.analyzer.validate_dataframe(self.df, 'timestamp')
        self.assertIsNotNone(df)
        self.assertEqual(date_col, 'timestamp')
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(df[date_col]))
    
    def test_validate_dataframe_auto_detect(self):
        """Test automatic date column detection."""
        df, date_col = self.analyzer.validate_dataframe(self.df)
        self.assertEqual(date_col, 'timestamp')
    
    def test_validate_dataframe_empty(self):
        """Test validation with empty DataFrame."""
        empty_df = pd.DataFrame()
        with self.assertRaises(ValueError):
            self.analyzer.validate_dataframe(empty_df)
    
    def test_summarize_by_hour(self):
        """Test hourly summarization."""
        result = self.analyzer.summarize_by_hour(
            self.df, 
            'amount', 
            'timestamp',
            aggregation='sum'
        )
        
        self.assertEqual(len(result), 24)  # 24 hours
        self.assertIn('hour', result.columns)
        self.assertIn('amount_sum', result.columns)
        self.assertIn('transaction_count', result.columns)
        self.assertTrue(all(result['hour'] == range(24)))
    
    def test_summarize_by_hour_mean(self):
        """Test hourly summarization with mean aggregation."""
        result = self.analyzer.summarize_by_hour(
            self.df,
            'amount',
            'timestamp',
            aggregation='mean'
        )
        
        self.assertIn('amount_mean', result.columns)
        # Business hours should have higher average
        business_hour_avg = result[result['hour'] == 12]['amount_mean'].iloc[0]
        night_hour_avg = result[result['hour'] == 2]['amount_mean'].iloc[0]
        self.assertGreater(business_hour_avg, night_hour_avg)
    
    def test_summarize_by_day(self):
        """Test daily summarization."""
        result = self.analyzer.summarize_by_day(
            self.df,
            'amount',
            'timestamp',
            aggregation='sum'
        )
        
        self.assertEqual(len(result), 30)  # 30 days
        self.assertIn('date', result.columns)
        self.assertIn('amount_sum', result.columns)
        self.assertIn('day_of_week', result.columns)
        self.assertIn('transaction_count', result.columns)
        
        # Each day should have 24 transactions
        self.assertTrue(all(result['transaction_count'] == 24))
    
    def test_summarize_by_month(self):
        """Test monthly summarization."""
        result = self.analyzer.summarize_by_month(
            self.df,
            'amount',
            'timestamp',
            aggregation='sum'
        )
        
        self.assertEqual(len(result), 1)  # 1 month
        self.assertIn('year_month', result.columns)
        self.assertIn('amount_sum', result.columns)
        self.assertIn('month_name', result.columns)
        self.assertIn('transaction_count', result.columns)
        self.assertEqual(result['month_name'].iloc[0], 'January')
    
    def test_detect_spikes_and_drops_zscore(self):
        """Test spike and drop detection using z-score."""
        daily_summary = self.analyzer.summarize_by_day(
            self.df,
            'amount',
            'timestamp'
        )
        
        result = self.analyzer.detect_spikes_and_drops(
            daily_summary,
            'amount_sum',
            method='zscore'
        )
        
        self.assertIn('spikes', result)
        self.assertIn('drops', result)
        self.assertIn('spike_count', result)
        self.assertIn('drop_count', result)
        self.assertEqual(result['method'], 'zscore')
    
    def test_detect_spikes_and_drops_iqr(self):
        """Test spike and drop detection using IQR."""
        daily_summary = self.analyzer.summarize_by_day(
            self.df,
            'amount',
            'timestamp'
        )
        
        result = self.analyzer.detect_spikes_and_drops(
            daily_summary,
            'amount_sum',
            method='iqr'
        )
        
        self.assertIn('spikes', result)
        self.assertIn('drops', result)
        self.assertEqual(result['method'], 'iqr')
    
    def test_calculate_moving_averages(self):
        """Test moving average calculations."""
        daily_summary = self.analyzer.summarize_by_day(
            self.df,
            'amount',
            'timestamp'
        )
        
        result = self.analyzer.calculate_moving_averages(
            daily_summary,
            'amount_sum',
            windows=[7, 14]
        )
        
        self.assertIn('amount_sum_ma7', result.columns)
        self.assertIn('amount_sum_ma14', result.columns)
        self.assertIn('amount_sum_pct_change', result.columns)
    
    def test_identify_top_periods(self):
        """Test top period identification."""
        daily_summary = self.analyzer.summarize_by_day(
            self.df,
            'amount',
            'timestamp'
        )
        
        result = self.analyzer.identify_top_periods(
            daily_summary,
            'amount_sum',
            top_n=5
        )
        
        self.assertIn('top_performers', result)
        self.assertIn('bottom_performers', result)
        self.assertIn('total_periods', result)
        self.assertEqual(len(result['top_performers']), 5)
        self.assertEqual(result['total_periods'], 30)
    
    def test_calculate_performance_indicators(self):
        """Test performance indicator calculation."""
        result = self.analyzer.calculate_performance_indicators(
            self.df,
            'amount',
            'timestamp'
        )
        
        self.assertIn('total_transactions', result)
        self.assertIn('total_value', result)
        self.assertIn('average_value', result)
        self.assertIn('median_value', result)
        self.assertIn('std_deviation', result)
        self.assertIn('min_value', result)
        self.assertIn('max_value', result)
        self.assertIn('date_range', result)
        self.assertIn('quartiles', result)
        self.assertIn('growth_rate', result)
        
        self.assertEqual(result['total_transactions'], len(self.df))
        self.assertGreater(result['total_value'], 0)
    
    def test_generate_comprehensive_report(self):
        """Test comprehensive report generation."""
        result = self.analyzer.generate_comprehensive_report(
            self.df,
            'amount',
            'timestamp'
        )
        
        self.assertIn('overview', result)
        self.assertIn('hourly_analysis', result)
        self.assertIn('daily_analysis', result)
        self.assertIn('monthly_analysis', result)
        
        # Check overview
        self.assertIn('total_transactions', result['overview'])
        
        # Check hourly analysis
        if 'error' not in result['hourly_analysis']:
            self.assertIn('summary', result['hourly_analysis'])
            self.assertIn('peak_hour', result['hourly_analysis'])
        
        # Check daily analysis
        if 'error' not in result['daily_analysis']:
            self.assertIn('summary', result['daily_analysis'])
            self.assertIn('anomalies', result['daily_analysis'])
    
    def test_generate_visualization_data(self):
        """Test visualization data generation."""
        result = self.analyzer.generate_visualization_data(
            self.df,
            'amount',
            'timestamp'
        )
        
        self.assertIn('time_series', result)
        self.assertIn('hourly_distribution', result)
        self.assertIn('monthly_trends', result)
        
        # Check time series data
        self.assertIn('dates', result['time_series'])
        self.assertIn('values', result['time_series'])
        self.assertIn('moving_average_7', result['time_series'])
        
        # Check hourly distribution
        self.assertEqual(len(result['hourly_distribution']['hours']), 24)
        
        # Check monthly trends
        self.assertGreater(len(result['monthly_trends']['months']), 0)
    
    def test_invalid_column_handling(self):
        """Test handling of invalid column names."""
        with self.assertRaises(ValueError):
            self.analyzer.summarize_by_hour(
                self.df,
                'nonexistent_column',
                'timestamp'
            )
    
    def test_invalid_aggregation_method(self):
        """Test handling of invalid aggregation methods."""
        with self.assertRaises(ValueError):
            self.analyzer.summarize_by_day(
                self.df,
                'amount',
                'timestamp',
                aggregation='invalid_method'
            )
    
    def test_empty_dataframe_after_validation(self):
        """Test handling when all dates are invalid."""
        df_invalid = pd.DataFrame({
            'timestamp': [None, None, None],
            'amount': [100, 200, 300]
        })
        
        with self.assertRaises(ValueError):
            self.analyzer.validate_dataframe(df_invalid, 'timestamp')


if __name__ == '__main__':
    unittest.main()
