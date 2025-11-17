"""Unit tests for AnomalyDetector."""
import unittest
from datetime import datetime, timedelta
from goldminer.analysis import AnomalyDetector


class TestAnomalyDetector(unittest.TestCase):
    """Test cases for AnomalyDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = AnomalyDetector()
    
    def test_initialization(self):
        """Test AnomalyDetector initialization."""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.high_value_percentile, 90)
        self.assertEqual(self.detector.burst_count_threshold, 3)
        self.assertEqual(self.detector.unknown_merchant_window, 100)
    
    def test_detect_high_value_anomaly(self):
        """Test high_value anomaly detection."""
        # Create history with amounts from 10 to 100
        history = [
            {'amount': i * 10, 'payee': 'Merchant A', 'date': '2024-01-01'}
            for i in range(1, 11)
        ]
        
        # Transaction with amount above 90th percentile (should be > 90)
        transaction = {
            'amount': 150,
            'payee': 'Merchant B',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('high_value', anomalies)
    
    def test_no_high_value_anomaly_normal_amount(self):
        """Test that normal amounts don't trigger high_value anomaly."""
        # Create history with amounts from 10 to 100
        history = [
            {'amount': i * 10, 'payee': 'Merchant A', 'date': '2024-01-01'}
            for i in range(1, 11)
        ]
        
        # Transaction with normal amount (50)
        transaction = {
            'amount': 50,
            'payee': 'Merchant B',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('high_value', anomalies)
    
    def test_no_high_value_with_insufficient_history(self):
        """Test that high_value detection requires minimum history."""
        # Insufficient history (less than min_history_transactions)
        history = [
            {'amount': 10, 'payee': 'Merchant A', 'date': '2024-01-01'},
            {'amount': 20, 'payee': 'Merchant A', 'date': '2024-01-02'}
        ]
        
        transaction = {
            'amount': 1000,
            'payee': 'Merchant B',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('high_value', anomalies)
    
    def test_detect_burst_frequency_anomaly(self):
        """Test burst_frequency anomaly detection."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        # Create history with multiple transactions to same merchant within 24h
        history = [
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=23)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Third transaction to same merchant (triggers burst)
        transaction = {
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('burst_frequency', anomalies)
    
    def test_no_burst_frequency_different_merchants(self):
        """Test that burst_frequency doesn't trigger for different merchants."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        history = [
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=23)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'amount': 50,
                'payee': 'Restaurant',
                'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        transaction = {
            'amount': 50,
            'payee': 'Grocery Store',
            'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('burst_frequency', anomalies)
    
    def test_no_burst_frequency_outside_time_window(self):
        """Test that burst_frequency doesn't trigger outside time window."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        # Transactions to same merchant but outside 24h window
        history = [
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=30)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=26)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        transaction = {
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('burst_frequency', anomalies)
    
    def test_detect_unknown_merchant_anomaly(self):
        """Test unknown_merchant anomaly detection."""
        # Create history with known merchants
        history = [
            {'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'},
            {'amount': 60, 'payee': 'Merchant B', 'date': '2024-01-02'},
            {'amount': 70, 'payee': 'Merchant C', 'date': '2024-01-03'},
        ]
        
        # Transaction with unknown merchant
        transaction = {
            'amount': 100,
            'payee': 'New Merchant',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('unknown_merchant', anomalies)
    
    def test_no_unknown_merchant_for_known_merchant(self):
        """Test that known merchants don't trigger unknown_merchant anomaly."""
        history = [
            {'amount': 50, 'payee': 'Coffee Shop', 'date': '2024-01-01'},
            {'amount': 60, 'payee': 'Restaurant', 'date': '2024-01-02'},
            {'amount': 70, 'payee': 'Grocery Store', 'date': '2024-01-03'},
        ]
        
        # Transaction with known merchant
        transaction = {
            'amount': 55,
            'payee': 'Coffee Shop',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('unknown_merchant', anomalies)
    
    def test_unknown_merchant_case_insensitive(self):
        """Test that unknown_merchant detection is case-insensitive."""
        history = [
            {'amount': 50, 'payee': 'Coffee Shop', 'date': '2024-01-01'},
        ]
        
        # Transaction with same merchant but different case
        transaction = {
            'amount': 55,
            'payee': 'COFFEE SHOP',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('unknown_merchant', anomalies)
    
    def test_multiple_anomalies_detected(self):
        """Test that multiple anomalies can be detected for same transaction."""
        # Small history for high_value
        history = [
            {'amount': i * 10, 'payee': 'Merchant A', 'date': '2024-01-01'}
            for i in range(1, 11)
        ]
        
        # Transaction that is both high value and from unknown merchant
        transaction = {
            'amount': 200,  # High value
            'payee': 'Unknown Merchant',  # Unknown
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('high_value', anomalies)
        self.assertIn('unknown_merchant', anomalies)
    
    def test_detect_anomalies_batch(self):
        """Test batch anomaly detection."""
        transactions = [
            {'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'},
            {'amount': 60, 'payee': 'Merchant B', 'date': '2024-01-02'},
            {'amount': 70, 'payee': 'Merchant A', 'date': '2024-01-03'},
            {'amount': 500, 'payee': 'Merchant C', 'date': '2024-01-04'},  # High value + unknown
        ]
        
        results = self.detector.detect_anomalies_batch(transactions)
        
        # Last transaction should have anomalies
        self.assertIn(3, results)
        # Unknown merchant should be detected (no previous 100 transactions)
        self.assertIn('unknown_merchant', results[3])
    
    def test_generate_report(self):
        """Test comprehensive report generation."""
        transactions = []
        
        # Create 20 normal transactions
        for i in range(20):
            transactions.append({
                'amount': 50 + i,
                'payee': f'Merchant {i % 5}',
                'date': f'2024-01-{i+1:02d}'
            })
        
        # Add anomalous transactions
        transactions.append({
            'amount': 1000,  # High value
            'payee': 'New Merchant',  # Unknown
            'date': '2024-01-21'
        })
        
        report = self.detector.generate_report(transactions)
        
        self.assertEqual(report['total_transactions'], 21)
        self.assertGreater(report['total_anomalies_detected'], 0)
        self.assertIn('anomaly_counts', report)
        self.assertIn('anomalies_by_transaction', report)
    
    def test_empty_transaction(self):
        """Test handling of empty transaction."""
        history = [{'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'}]
        transaction = {}
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertEqual(len(anomalies), 0)
    
    def test_empty_history(self):
        """Test handling of empty history."""
        history = []
        transaction = {'amount': 100, 'payee': 'Merchant A', 'date': '2024-01-01'}
        
        # Should detect unknown_merchant (no history)
        anomalies = self.detector.detect_anomalies(transaction, history)
        # With empty history, high_value won't trigger (insufficient history)
        # But unknown_merchant should trigger (empty history = all merchants unknown)
        self.assertIn('unknown_merchant', anomalies)
    
    def test_missing_amount_field(self):
        """Test handling of transaction with missing amount."""
        history = [
            {'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'},
            {'amount': 60, 'payee': 'Merchant B', 'date': '2024-01-02'},
        ]
        
        transaction = {'payee': 'Merchant C', 'date': '2024-01-15'}
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        # Should not trigger high_value (no amount)
        self.assertNotIn('high_value', anomalies)
        # Should trigger unknown_merchant
        self.assertIn('unknown_merchant', anomalies)
    
    def test_missing_merchant_field(self):
        """Test handling of transaction with missing merchant."""
        history = [{'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'}]
        
        transaction = {'amount': 100, 'date': '2024-01-15'}
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        # Should not trigger burst_frequency or unknown_merchant (no merchant)
        self.assertNotIn('burst_frequency', anomalies)
        self.assertNotIn('unknown_merchant', anomalies)
    
    def test_date_parsing_various_formats(self):
        """Test that various date formats are parsed correctly."""
        base_time = datetime(2024, 1, 15, 0, 0, 0)  # Use midnight to work with date-only formats
        
        # Test various date formats
        test_cases = [
            '2024-01-15 00:00:00',
            '2024-01-15',
            '2024-01-15T00:00:00',
        ]
        
        for date_str in test_cases:
            history = [
                {
                    'amount': 50,
                    'payee': 'Coffee Shop',
                    'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    'amount': 50,
                    'payee': 'Coffee Shop',
                    'date': (base_time - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
                }
            ]
            
            transaction = {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': date_str
            }
            
            # Should detect burst frequency regardless of date format
            anomalies = self.detector.detect_anomalies(transaction, history)
            self.assertIn('burst_frequency', anomalies, f"Failed for format: {date_str}")
    
    def test_merchant_field_alternative_names(self):
        """Test that both 'payee' and 'merchant' field names work."""
        history = [{'amount': 50, 'merchant': 'Coffee Shop', 'date': '2024-01-01'}]
        
        # Test with 'merchant' field
        transaction1 = {'amount': 55, 'merchant': 'Coffee Shop', 'date': '2024-01-15'}
        anomalies1 = self.detector.detect_anomalies(transaction1, history)
        self.assertNotIn('unknown_merchant', anomalies1)
        
        # Test with 'payee' field
        transaction2 = {'amount': 55, 'payee': 'Coffee Shop', 'date': '2024-01-15'}
        anomalies2 = self.detector.detect_anomalies(transaction2, history)
        self.assertNotIn('unknown_merchant', anomalies2)
    
    def test_percentile_boundary_value(self):
        """Test high_value detection at boundary (exactly 90th percentile)."""
        # Create 100 transactions with amounts 1-100
        history = [
            {'amount': i, 'payee': 'Merchant A', 'date': '2024-01-01'}
            for i in range(1, 101)
        ]
        
        # Transaction at exactly 90th percentile (should not trigger)
        transaction = {
            'amount': 90,
            'payee': 'Merchant B',
            'date': '2024-01-15'
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('high_value', anomalies)
        
        # Transaction just above 90th percentile (should trigger)
        transaction['amount'] = 91
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('high_value', anomalies)
    
    def test_burst_frequency_exact_threshold(self):
        """Test burst_frequency at exact threshold."""
        base_time = datetime(2024, 1, 15, 10, 0, 0)
        
        # Create exactly threshold-1 transactions (2 in history)
        history = [
            {
                'amount': 50,
                'payee': 'Coffee Shop',
                'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Second transaction (total = 2, below threshold of 3)
        transaction = {
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertNotIn('burst_frequency', anomalies)
        
        # Add one more to history and test again (total = 3, at threshold)
        history.append({
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': (base_time - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        })
        
        anomalies = self.detector.detect_anomalies(transaction, history)
        self.assertIn('burst_frequency', anomalies)


if __name__ == '__main__':
    unittest.main()
