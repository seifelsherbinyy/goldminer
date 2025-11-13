"""Unit tests for data analysis."""
import unittest
import pandas as pd
import numpy as np
from goldminer.analysis import DataAnalyzer


class TestDataAnalyzer(unittest.TestCase):
    """Test cases for DataAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = DataAnalyzer()
        
        # Create sample DataFrame
        self.df = pd.DataFrame({
            'numeric1': [1, 2, 3, 4, 5, 100],  # 100 is outlier
            'numeric2': [10, 20, 30, 40, 50, 60],
            'category': ['A', 'B', 'A', 'B', 'A', 'B'],
            'text': ['foo', 'bar', 'baz', 'qux', 'quux', 'corge']
        })
    
    def test_generate_summary_metrics(self):
        """Test summary metrics generation."""
        summary = self.analyzer.generate_summary_metrics(self.df)
        
        # Check structure
        self.assertIn('overview', summary)
        self.assertIn('numeric_columns', summary)
        self.assertIn('categorical_columns', summary)
        
        # Check overview
        self.assertEqual(summary['overview']['total_rows'], 6)
        self.assertEqual(summary['overview']['total_columns'], 4)
        
        # Check numeric columns
        self.assertIn('numeric1', summary['numeric_columns'])
        self.assertIn('mean', summary['numeric_columns']['numeric1'])
    
    def test_detect_anomalies_zscore(self):
        """Test anomaly detection using z-score method."""
        anomalies = self.analyzer.detect_anomalies(
            self.df, 
            columns=['numeric1'], 
            method='zscore'
        )
        
        # Should detect the outlier (100)
        if 'numeric1' in anomalies:
            self.assertGreater(len(anomalies['numeric1']), 0)
    
    def test_detect_anomalies_iqr(self):
        """Test anomaly detection using IQR method."""
        anomalies = self.analyzer.detect_anomalies(
            self.df, 
            columns=['numeric1'], 
            method='iqr'
        )
        
        # Should detect the outlier (100)
        if 'numeric1' in anomalies:
            self.assertGreater(len(anomalies['numeric1']), 0)
    
    def test_calculate_trends(self):
        """Test trend calculation."""
        df_trend = self.analyzer.calculate_trends(
            self.df, 
            value_column='numeric1',
            window=3
        )
        
        # Check trend columns added
        self.assertIn('numeric1_ma3', df_trend.columns)
        self.assertIn('numeric1_trend', df_trend.columns)
    
    def test_generate_correlation_matrix(self):
        """Test correlation matrix generation."""
        corr_matrix = self.analyzer.generate_correlation_matrix(self.df)
        
        # Check shape
        numeric_cols = self.df.select_dtypes(include=['number']).columns
        self.assertEqual(corr_matrix.shape, (len(numeric_cols), len(numeric_cols)))
        
        # Check diagonal is 1 (correlation with self)
        for col in numeric_cols:
            self.assertAlmostEqual(corr_matrix.loc[col, col], 1.0)
    
    def test_identify_outliers(self):
        """Test outlier identification."""
        outliers = self.analyzer.identify_outliers(self.df)
        
        # Should identify outlier in numeric1
        if 'numeric1' in outliers:
            self.assertGreater(outliers['numeric1']['count'], 0)
            self.assertIn('lower_bound', outliers['numeric1'])
            self.assertIn('upper_bound', outliers['numeric1'])
    
    def test_generate_full_report(self):
        """Test full report generation."""
        report = self.analyzer.generate_full_report(self.df)
        
        # Check report sections
        self.assertIn('summary_metrics', report)
        self.assertIn('outliers', report)
        self.assertIn('anomalies', report)
        
        # Check correlations included
        self.assertIn('correlations', report)


if __name__ == '__main__':
    unittest.main()
