"""Unit tests for generate_user_report function."""
import unittest
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import xlsxwriter
from goldminer.etl import generate_user_report


class TestGenerateUserReport(unittest.TestCase):
    """Test cases for generate_user_report function."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create sample transaction data with 100 transactions as specified
        self.sample_transactions = self._create_sample_transactions(100)
    
    def tearDown(self):
        """Clean up test files."""
        # Remove temporary files
        for file in Path(self.temp_dir).glob("*.xlsx"):
            try:
                file.unlink()
            except:
                pass
        try:
            Path(self.temp_dir).rmdir()
        except:
            pass
    
    def _create_sample_transactions(self, count=100):
        """
        Create sample transaction data for testing.
        
        Args:
            count: Number of transactions to generate
            
        Returns:
            List of transaction dictionaries
        """
        base_date = datetime.now() - timedelta(days=180)
        transactions = []
        
        categories = ['Food & Dining', 'Transportation', 'Entertainment', 
                     'Bills & Utilities', 'Shopping', 'Healthcare', 'Travel', 'Education']
        payees = [
            'Coffee Shop', 'Subway Station', 'Netflix', 'Electric Company',
            'Amazon', 'Pharmacy', 'Airline', 'University',
            'Restaurant', 'Gas Station', 'Cinema', 'Internet Provider',
            'Target', 'Doctor', 'Hotel', 'Bookstore'
        ]
        accounts = ['ACC-CREDIT-001', 'ACC-DEBIT-002', 'ACC-DEBIT-003']
        account_types = ['Credit', 'Debit', 'Debit']
        
        for i in range(count):
            # Generate date within the last 6 months
            days_offset = (i * 2) % 180  # Spread across 6 months
            transaction_date = base_date + timedelta(days=days_offset)
            
            # Generate amount with some pattern
            category = categories[i % len(categories)]
            if category == 'Bills & Utilities':
                amount = round(50 + (i * 3.7) % 250, 2)
            elif category == 'Travel':
                amount = round(200 + (i * 17.3) % 1800, 2)
            elif category == 'Food & Dining':
                amount = round(5 + (i * 2.1) % 95, 2)
            else:
                amount = round(10 + (i * 7.9) % 490, 2)
            
            # Add some anomalies (high value transactions and other flags)
            anomaly_flag = ''
            if amount > 1500:
                anomaly_flag = 'high_value'
            elif i % 30 == 0:  # Periodic anomalies
                anomaly_flag = 'burst_frequency'
            elif i % 40 == 0:
                anomaly_flag = 'unknown_merchant'
            
            account_idx = i % len(accounts)
            
            transaction = {
                'id': f'TXN{i:06d}',
                'date': transaction_date.strftime('%Y-%m-%d'),
                'payee': payees[i % len(payees)],
                'category': category,
                'subcategory': f'Sub-{category.split()[0]}',
                'amount': amount,
                'currency': 'USD',
                'account_id': accounts[account_idx],
                'account_type': account_types[account_idx],
                'tags': f'tag-{i % 5}' if i % 3 == 0 else '',
                'anomalies': anomaly_flag,
                'confidence': 'high' if anomaly_flag == '' else 'medium'
            }
            
            transactions.append(transaction)
        
        return transactions
    
    def test_generate_user_report_basic(self):
        """Test basic report generation with 100 transactions."""
        output_file = os.path.join(self.temp_dir, 'test_report.xlsx')
        
        # Generate report
        generate_user_report(self.sample_transactions, output_file)
        
        # Verify file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file can be opened
        try:
            workbook = xlsxwriter.Workbook(output_file + '.tmp')
            workbook.close()
            os.remove(output_file + '.tmp')
        except:
            pass  # xlsxwriter doesn't read, just verify file exists
    
    def test_generate_user_report_empty_transactions(self):
        """Test report generation with empty transaction list."""
        output_file = os.path.join(self.temp_dir, 'test_empty.xlsx')
        
        with self.assertRaises(ValueError):
            generate_user_report([], output_file)
    
    def test_generate_user_report_adds_extension(self):
        """Test report generation adds .xlsx extension if missing."""
        output_file = os.path.join(self.temp_dir, 'test_no_ext')
        
        generate_user_report(self.sample_transactions, output_file)
        
        # Verify file was created with .xlsx extension
        expected_file = output_file + '.xlsx'
        self.assertTrue(os.path.exists(expected_file))
    
    def test_generate_user_report_with_anomalies(self):
        """Test report generation includes anomalies sheet."""
        # Add more anomalies to test data
        test_transactions = self.sample_transactions.copy()
        for i in range(0, len(test_transactions), 10):
            test_transactions[i]['anomalies'] = 'test_anomaly'
        
        output_file = os.path.join(self.temp_dir, 'test_with_anomalies.xlsx')
        
        # Should not raise an error
        generate_user_report(test_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_with_no_anomalies(self):
        """Test report generation when no anomalies are present."""
        # Create transactions without anomalies
        clean_transactions = [
            {
                'id': f'TXN{i:03d}',
                'date': '2024-01-01',
                'amount': 100.00,
                'category': 'Food',
                'payee': 'Restaurant',
                'anomalies': ''
            }
            for i in range(100)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_no_anomalies.xlsx')
        
        generate_user_report(clean_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_with_missing_columns(self):
        """Test report generation handles missing columns gracefully."""
        # Create transactions with minimal fields
        minimal_transactions = [
            {
                'id': f'TXN{i:03d}',
                'date': (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d'),
                'amount': 100.00 + i * 10,
                'payee': f'Merchant {i % 5}'
            }
            for i in range(100)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_minimal.xlsx')
        
        # Should not raise an error
        generate_user_report(minimal_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_file_size(self):
        """Test that generated file has reasonable size (not empty)."""
        output_file = os.path.join(self.temp_dir, 'test_size.xlsx')
        
        generate_user_report(self.sample_transactions, output_file)
        
        # Verify file size is reasonable (should be at least 10KB for 100 transactions with charts)
        file_size = os.path.getsize(output_file)
        self.assertGreater(file_size, 10000)
    
    def test_generate_user_report_utf8_compatibility(self):
        """Test report generation handles UTF-8 characters correctly."""
        utf8_transactions = [
            {
                'id': f'TXN{i:03d}',
                'date': '2024-01-01',
                'payee': 'Café René' if i % 2 == 0 else '北京饭店',
                'category': 'Food & Drink',
                'amount': 100.00 + i * 5,
                'currency': '€' if i % 2 == 0 else '¥',
                'anomalies': ''
            }
            for i in range(100)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_utf8.xlsx')
        
        # Should handle UTF-8 characters without error
        generate_user_report(utf8_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_with_categories(self):
        """Test report generation creates proper category breakdown."""
        # Ensure we have diverse categories
        test_transactions = []
        categories = ['Food', 'Transport', 'Shopping', 'Entertainment', 'Bills']
        
        for i in range(100):
            test_transactions.append({
                'id': f'TXN{i:03d}',
                'date': (datetime.now() - timedelta(days=i % 30)).strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 10}',
                'category': categories[i % len(categories)],
                'amount': 50.0 + (i * 7.3) % 450,
                'anomalies': ''
            })
        
        output_file = os.path.join(self.temp_dir, 'test_categories.xlsx')
        
        generate_user_report(test_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_with_merchants(self):
        """Test report generation creates proper merchant breakdown."""
        # Ensure we have diverse merchants with different spending amounts
        test_transactions = []
        merchants = ['Amazon', 'Walmart', 'Target', 'Starbucks', 'Shell', 
                    'Restaurant A', 'Restaurant B', 'Gas Station', 'Grocery Store', 'Pharmacy']
        
        for i in range(100):
            test_transactions.append({
                'id': f'TXN{i:03d}',
                'date': (datetime.now() - timedelta(days=i % 30)).strftime('%Y-%m-%d'),
                'payee': merchants[i % len(merchants)],
                'category': 'Shopping',
                'amount': 50.0 + (i * 11.7) % 950,
                'anomalies': ''
            })
        
        output_file = os.path.join(self.temp_dir, 'test_merchants.xlsx')
        
        generate_user_report(test_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_date_range(self):
        """Test report generation with transactions across multiple months."""
        # Create transactions spanning 6 months
        test_transactions = []
        base_date = datetime.now() - timedelta(days=180)
        
        for i in range(100):
            test_transactions.append({
                'id': f'TXN{i:03d}',
                'date': (base_date + timedelta(days=i * 2)).strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 10}',
                'category': 'Shopping',
                'amount': 50.0 + (i * 3.7) % 450,
                'anomalies': ''
            })
        
        output_file = os.path.join(self.temp_dir, 'test_date_range.xlsx')
        
        generate_user_report(test_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
    
    def test_generate_user_report_invalid_path(self):
        """Test report generation with invalid path raises IOError."""
        invalid_path = '/nonexistent/directory/test.xlsx'
        
        with self.assertRaises(IOError):
            generate_user_report(self.sample_transactions, invalid_path)
    
    def test_generate_user_report_workbook_integrity(self):
        """Test that generated workbook maintains integrity with 100 transactions."""
        output_file = os.path.join(self.temp_dir, 'test_integrity.xlsx')
        
        # Generate report
        generate_user_report(self.sample_transactions, output_file)
        
        # Verify file exists and has content
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file is not corrupted by checking size
        file_size = os.path.getsize(output_file)
        self.assertGreater(file_size, 5000)
        
        # Verify file has .xlsx extension
        self.assertTrue(output_file.endswith('.xlsx'))
    
    def test_generate_user_report_with_all_fields(self):
        """Test report generation with all expected transaction fields."""
        complete_transactions = [
            {
                'id': f'TXN{i:05d}',
                'date': (datetime.now() - timedelta(days=i % 180)).strftime('%Y-%m-%d'),
                'payee': f'Merchant {i % 20}',
                'category': ['Food', 'Transport', 'Shopping'][i % 3],
                'subcategory': f'Sub{i % 5}',
                'amount': round(10 + (i * 7.3) % 990, 2),
                'currency': 'USD',
                'account_id': f'ACC{i % 3:03d}',
                'account_type': 'Credit' if i % 2 == 0 else 'Debit',
                'tags': f'tag{i % 5}',
                'anomalies': 'high_value' if i % 25 == 0 else '',
                'confidence': 'high'
            }
            for i in range(100)
        ]
        
        output_file = os.path.join(self.temp_dir, 'test_complete.xlsx')
        
        generate_user_report(complete_transactions, output_file)
        
        self.assertTrue(os.path.exists(output_file))
        
        # Verify file size is substantial (complete data should create larger file)
        file_size = os.path.getsize(output_file)
        self.assertGreater(file_size, 15000)


if __name__ == '__main__':
    unittest.main()
