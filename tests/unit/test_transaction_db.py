"""Unit tests for TransactionDB class."""
import unittest
import tempfile
import os
import time
import sqlite3
from datetime import datetime
from goldminer.etl import TransactionDB


class TestTransactionDB(unittest.TestCase):
    """Test cases for TransactionDB class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_transactions.db')
        self.db = TransactionDB(self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.db.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
    def test_database_initialization(self):
        """Test that database and tables are created correctly."""
        # Check that connection exists
        self.assertIsNotNone(self.db.connection)
        
        # Verify tables exist
        cursor = self.db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions'
        """)
        self.assertIsNotNone(cursor.fetchone())
        
        # Verify FTS5 table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='transactions_fts'
        """)
        self.assertIsNotNone(cursor.fetchone())
    
    def test_insert_basic_transaction(self):
        """Test inserting a basic transaction."""
        transaction = {
            'date': '2024-01-15',
            'payee': 'Test Store',
            'category': 'Shopping',
            'subcategory': 'Electronics',
            'amount': 99.99,
            'account_id': 'acc_123',
            'account_type': 'credit',
            'currency': 'USD'
        }
        
        transaction_id = self.db.insert(transaction)
        
        # Verify ID was generated
        self.assertIsNotNone(transaction_id)
        self.assertTrue(len(transaction_id) > 0)
        
        # Verify transaction was inserted
        result = self.db.get_by_id(transaction_id)
        self.assertIsNotNone(result)
        self.assertEqual(result['payee'], 'Test Store')
        self.assertEqual(result['amount'], 99.99)
    
    def test_insert_with_custom_id(self):
        """Test inserting a transaction with custom ID."""
        custom_id = 'custom-uuid-12345'
        transaction = {
            'id': custom_id,
            'date': '2024-01-15',
            'payee': 'Custom Store',
            'amount': 50.00
        }
        
        returned_id = self.db.insert(transaction)
        
        self.assertEqual(returned_id, custom_id)
        result = self.db.get_by_id(custom_id)
        self.assertEqual(result['id'], custom_id)
    
    def test_insert_duplicate_detection(self):
        """Test that duplicate transactions are detected."""
        transaction = {
            'date': '2024-01-15',
            'payee': 'Duplicate Store',
            'amount': 25.00,
            'account_id': 'acc_456'
        }
        
        # First insert should succeed
        self.db.insert(transaction)
        
        # Second insert with same unique fields should raise IntegrityError
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.insert(transaction)
    
    def test_insert_with_all_fields(self):
        """Test inserting a transaction with all fields populated."""
        transaction = {
            'date': '2024-01-15',
            'payee': 'Complete Store',
            'category': 'Food',
            'subcategory': 'Restaurants',
            'amount': 45.50,
            'account_id': 'acc_789',
            'account_type': 'debit',
            'interest_rate': 0.05,
            'tags': 'dining,lunch',
            'urgency': 'high',
            'currency': 'EUR',
            'anomalies': 'unusual_time',
            'confidence': 0.95
        }
        
        transaction_id = self.db.insert(transaction)
        result = self.db.get_by_id(transaction_id)
        
        self.assertEqual(result['category'], 'Food')
        self.assertEqual(result['subcategory'], 'Restaurants')
        self.assertEqual(result['interest_rate'], 0.05)
        self.assertEqual(result['tags'], 'dining,lunch')
        self.assertEqual(result['confidence'], 0.95)
    
    def test_update_single_field(self):
        """Test updating a single field."""
        transaction = {
            'date': '2024-01-15',
            'payee': 'Update Store',
            'amount': 100.00,
            'account_id': 'acc_update'
        }
        
        transaction_id = self.db.insert(transaction)
        
        # Update category
        success = self.db.update(transaction_id, {'category': 'Updated Category'})
        self.assertTrue(success)
        
        # Verify update
        result = self.db.get_by_id(transaction_id)
        self.assertEqual(result['category'], 'Updated Category')
        self.assertEqual(result['payee'], 'Update Store')  # Other fields unchanged
    
    def test_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        transaction = {
            'date': '2024-01-15',
            'payee': 'Multi Update Store',
            'amount': 200.00,
            'account_id': 'acc_multi'
        }
        
        transaction_id = self.db.insert(transaction)
        
        # Update multiple fields
        updates = {
            'category': 'New Category',
            'subcategory': 'New Subcategory',
            'tags': 'tag1,tag2',
            'confidence': 0.88
        }
        success = self.db.update(transaction_id, updates)
        self.assertTrue(success)
        
        # Verify all updates
        result = self.db.get_by_id(transaction_id)
        self.assertEqual(result['category'], 'New Category')
        self.assertEqual(result['subcategory'], 'New Subcategory')
        self.assertEqual(result['tags'], 'tag1,tag2')
        self.assertEqual(result['confidence'], 0.88)
    
    def test_update_nonexistent_transaction(self):
        """Test updating a transaction that doesn't exist."""
        success = self.db.update('nonexistent-id', {'category': 'Test'})
        self.assertFalse(success)
    
    def test_query_all_transactions(self):
        """Test querying all transactions without filters."""
        # Insert multiple transactions
        for i in range(5):
            self.db.insert({
                'date': f'2024-01-{i+1:02d}',
                'payee': f'Store {i}',
                'amount': 10.0 * (i + 1),
                'account_id': f'acc_{i}'
            })
        
        results = self.db.query()
        self.assertEqual(len(results), 5)
    
    def test_query_by_category(self):
        """Test querying transactions by category."""
        self.db.insert({
            'date': '2024-01-01',
            'payee': 'Food Store',
            'category': 'Food',
            'amount': 30.0,
            'account_id': 'acc_food'
        })
        self.db.insert({
            'date': '2024-01-02',
            'payee': 'Gas Station',
            'category': 'Transport',
            'amount': 50.0,
            'account_id': 'acc_gas'
        })
        self.db.insert({
            'date': '2024-01-03',
            'payee': 'Restaurant',
            'category': 'Food',
            'amount': 40.0,
            'account_id': 'acc_restaurant'
        })
        
        results = self.db.query({'category': 'Food'})
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result['category'], 'Food')
    
    def test_query_by_amount_range(self):
        """Test querying transactions by amount range."""
        for i in range(5):
            self.db.insert({
                'date': f'2024-01-{i+1:02d}',
                'payee': f'Store {i}',
                'amount': 10.0 + (i * 20.0),
                'account_id': f'acc_{i}'
            })
        
        # Query for amounts between 30 and 60
        results = self.db.query({'amount_min': 30.0, 'amount_max': 60.0})
        
        self.assertTrue(len(results) >= 2)
        for result in results:
            self.assertGreaterEqual(result['amount'], 30.0)
            self.assertLessEqual(result['amount'], 60.0)
    
    def test_query_by_date_range(self):
        """Test querying transactions by date range."""
        dates = ['2024-01-01', '2024-01-15', '2024-02-01', '2024-02-15', '2024-03-01']
        for i, date in enumerate(dates):
            self.db.insert({
                'date': date,
                'payee': f'Store {i}',
                'amount': 50.0,
                'account_id': f'acc_{i}'
            })
        
        # Query for January transactions
        results = self.db.query({
            'date_from': '2024-01-01',
            'date_to': '2024-01-31'
        })
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result['date'].startswith('2024-01'))
    
    def test_query_with_list_filter(self):
        """Test querying transactions with IN clause."""
        payees = ['Store A', 'Store B', 'Store C', 'Store D']
        for i, payee in enumerate(payees):
            self.db.insert({
                'date': '2024-01-01',
                'payee': payee,
                'amount': 25.0,
                'account_id': f'acc_{i}'
            })
        
        # Query for specific payees
        results = self.db.query({'payee_in': ['Store A', 'Store C']})
        
        self.assertEqual(len(results), 2)
        payee_list = [r['payee'] for r in results]
        self.assertIn('Store A', payee_list)
        self.assertIn('Store C', payee_list)
    
    def test_full_text_search(self):
        """Test full-text search functionality using FTS5."""
        self.db.insert({
            'date': '2024-01-01',
            'payee': 'Amazon Prime',
            'category': 'Shopping',
            'tags': 'online,subscription',
            'amount': 15.0,
            'account_id': 'acc_1'
        })
        self.db.insert({
            'date': '2024-01-02',
            'payee': 'Local Grocery',
            'category': 'Food',
            'tags': 'groceries,weekly',
            'amount': 80.0,
            'account_id': 'acc_2'
        })
        self.db.insert({
            'date': '2024-01-03',
            'payee': 'Prime Restaurant',
            'category': 'Dining',
            'tags': 'dinner,special',
            'amount': 120.0,
            'account_id': 'acc_3'
        })
        
        # Search for "Prime"
        results = self.db.query({'search': 'Prime'})
        self.assertEqual(len(results), 2)
        
        # Search for "grocery"
        results = self.db.query({'search': 'Grocery'})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['payee'], 'Local Grocery')
    
    def test_count_transactions(self):
        """Test counting transactions."""
        for i in range(10):
            self.db.insert({
                'date': '2024-01-01',
                'payee': f'Store {i}',
                'category': 'Food' if i % 2 == 0 else 'Transport',
                'amount': 50.0,
                'account_id': f'acc_{i}'
            })
        
        # Count all
        total = self.db.count()
        self.assertEqual(total, 10)
        
        # Count by category
        food_count = self.db.count({'category': 'Food'})
        self.assertEqual(food_count, 5)
    
    def test_delete_transaction(self):
        """Test deleting a transaction."""
        transaction = {
            'date': '2024-01-01',
            'payee': 'Delete Me',
            'amount': 100.0,
            'account_id': 'acc_delete'
        }
        
        transaction_id = self.db.insert(transaction)
        
        # Verify it exists
        result = self.db.get_by_id(transaction_id)
        self.assertIsNotNone(result)
        
        # Delete it
        success = self.db.delete(transaction_id)
        self.assertTrue(success)
        
        # Verify it's gone
        result = self.db.get_by_id(transaction_id)
        self.assertIsNone(result)
    
    def test_delete_nonexistent_transaction(self):
        """Test deleting a transaction that doesn't exist."""
        success = self.db.delete('nonexistent-id')
        self.assertFalse(success)
    
    def test_context_manager(self):
        """Test using TransactionDB as a context manager."""
        db_path = os.path.join(self.temp_dir, 'context_test.db')
        
        with TransactionDB(db_path) as db:
            transaction_id = db.insert({
                'date': '2024-01-01',
                'payee': 'Context Store',
                'amount': 75.0,
                'account_id': 'acc_context'
            })
            
            result = db.get_by_id(transaction_id)
            self.assertIsNotNone(result)
        
        # Connection should be closed after context
        # Open new connection to verify data persists
        with TransactionDB(db_path) as db:
            result = db.get_by_id(transaction_id)
            self.assertIsNotNone(result)
            self.assertEqual(result['payee'], 'Context Store')
        
        os.remove(db_path)
    
    def test_performance_20k_rows(self):
        """Test query performance with 20K+ rows (should be under 100ms)."""
        # Insert 20,000 transactions
        print("\nInserting 20,000 transactions for performance test...")
        start_time = time.time()
        
        transactions = []
        for i in range(20000):
            transactions.append({
                'date': f'2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                'payee': f'Store {i % 100}',
                'category': ['Food', 'Transport', 'Shopping', 'Entertainment'][i % 4],
                'subcategory': f'Sub {i % 20}',
                'amount': 10.0 + (i % 1000),
                'account_id': f'acc_{i % 10}',
                'account_type': 'credit' if i % 2 == 0 else 'debit',
                'currency': 'USD',
                'confidence': 0.5 + (i % 50) / 100.0
            })
        
        # Batch insert for efficiency
        for transaction in transactions:
            self.db.insert(transaction)
        
        insert_time = time.time() - start_time
        print(f"Insert time for 20K rows: {insert_time:.2f}s")
        
        # Test query performance - simple filter
        start_time = time.time()
        results = self.db.query({'category': 'Food'})
        query_time = (time.time() - start_time) * 1000  # Convert to ms
        
        print(f"Query time (category filter): {query_time:.2f}ms")
        print(f"Results returned: {len(results)}")
        
        self.assertLess(query_time, 100, "Query should complete in under 100ms")
        self.assertGreater(len(results), 0)
        
        # Test indexed date query
        start_time = time.time()
        results = self.db.query({
            'date_from': '2024-01-01',
            'date_to': '2024-01-31'
        })
        date_query_time = (time.time() - start_time) * 1000
        
        print(f"Query time (date range): {date_query_time:.2f}ms")
        self.assertLess(date_query_time, 100, "Date range query should complete in under 100ms")
        
        # Test indexed payee query
        start_time = time.time()
        results = self.db.query({'payee': 'Store 42'})
        payee_query_time = (time.time() - start_time) * 1000
        
        print(f"Query time (payee filter): {payee_query_time:.2f}ms")
        self.assertLess(payee_query_time, 100, "Payee query should complete in under 100ms")
        
        # Test complex query with multiple filters
        start_time = time.time()
        results = self.db.query({
            'category': 'Food',
            'amount_min': 100.0,
            'amount_max': 500.0
        })
        complex_query_time = (time.time() - start_time) * 1000
        
        print(f"Query time (complex filter): {complex_query_time:.2f}ms")
        self.assertLess(complex_query_time, 100, "Complex query should complete in under 100ms")
        
        # Test full-text search performance
        # Note: FTS5 search may be slightly slower but should still be reasonable
        start_time = time.time()
        results = self.db.query({'search': 'Store'})
        fts_query_time = (time.time() - start_time) * 1000
        
        print(f"Query time (full-text search): {fts_query_time:.2f}ms")
        # FTS5 may be slightly slower, so we allow up to 150ms
        self.assertLess(fts_query_time, 150, "Full-text search should complete in reasonable time")


if __name__ == '__main__':
    unittest.main()
