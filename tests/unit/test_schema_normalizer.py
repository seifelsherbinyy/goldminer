"""Unit tests for SchemaNormalizer and TransactionRecord."""
import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from goldminer.etl import SchemaNormalizer, TransactionRecord, ParsedTransaction, FieldValidator


class TestTransactionRecord(unittest.TestCase):
    """Test cases for TransactionRecord dataclass."""
    
    def test_transaction_record_creation(self):
        """Test creating a TransactionRecord with all fields."""
        record = TransactionRecord(
            id='test-id-123',
            date='2024-11-15',
            amount=250.50,
            currency='EGP',
            payee='Test Store',
            normalized_merchant='TEST STORE',
            category='Shopping',
            subcategory='Electronics',
            tags=['POS', 'HSBC'],
            account_id='ACC-HSBC-001',
            account_type='Credit',
            interest_rate=19.99,
            urgency='normal',
            confidence='high'
        )
        
        self.assertEqual(record.id, 'test-id-123')
        self.assertEqual(record.date, '2024-11-15')
        self.assertEqual(record.amount, 250.50)
        self.assertEqual(record.currency, 'EGP')
        self.assertEqual(record.payee, 'Test Store')
        self.assertEqual(record.account_type, 'Credit')
        self.assertEqual(record.interest_rate, 19.99)
        self.assertEqual(len(record.tags), 2)
    
    def test_transaction_record_minimal(self):
        """Test creating a TransactionRecord with minimal fields."""
        record = TransactionRecord(id='test-id')
        
        self.assertEqual(record.id, 'test-id')
        self.assertIsNone(record.date)
        self.assertIsNone(record.amount)
        self.assertEqual(record.confidence, 'low')
        self.assertEqual(record.urgency, 'normal')
        self.assertEqual(len(record.tags), 0)


class TestSchemaNormalizer(unittest.TestCase):
    """Test cases for SchemaNormalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock CardClassifier to avoid file system dependencies
        self.mock_classifier = Mock()
        self.mock_classifier.lookup_account.return_value = {
            'account_id': 'ACC-HSBC-001',
            'account_type': 'Credit',
            'interest_rate': 19.99,
            'credit_limit': 50000.00,
            'billing_cycle': 15,
            'label': 'HSBC Credit Card - Primary',
            'card_suffix': '1234',
            'is_known': True
        }
        
        self.normalizer = SchemaNormalizer(card_classifier=self.mock_classifier)
    
    def test_normalize_complete_transaction(self):
        """Test normalizing a complete ParsedTransaction."""
        parsed = ParsedTransaction(
            amount='250.50',
            currency='EGP',
            date='15/11/2024',
            payee='Test Store',
            txn_type='POS',
            card_suffix='1234',
            bank_id='HSBC',
            confidence='high'
        )
        
        record = self.normalizer.normalize(parsed)
        
        # Check ID is generated
        self.assertIsNotNone(record.id)
        self.assertTrue(len(record.id) > 0)
        
        # Check date normalization
        self.assertEqual(record.date, '2024-11-15')
        
        # Check amount conversion
        self.assertEqual(record.amount, 250.50)
        self.assertIsInstance(record.amount, float)
        
        # Check text normalization
        self.assertEqual(record.currency, 'EGP')
        self.assertEqual(record.payee, 'Test Store')
        
        # Check metadata attachment
        self.assertEqual(record.account_id, 'ACC-HSBC-001')
        self.assertEqual(record.account_type, 'Credit')
        self.assertEqual(record.interest_rate, 19.99)
        
        # Check confidence is preserved
        self.assertEqual(record.confidence, 'high')
        
        # Check tags
        self.assertIn('POS', record.tags)
        self.assertIn('HSBC', record.tags)
    
    def test_normalize_partial_transaction(self):
        """Test normalizing a partial ParsedTransaction."""
        parsed = ParsedTransaction(
            amount='100',
            currency='USD'
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertIsNotNone(record.id)
        self.assertEqual(record.amount, 100.0)
        self.assertEqual(record.currency, 'USD')
        self.assertIsNone(record.date)
        self.assertIsNone(record.payee)
    
    def test_normalize_date_formats(self):
        """Test date normalization from various formats to ISO 8601."""
        test_cases = [
            ('15/11/2024', '2024-11-15'),
            ('2024-11-15', '2024-11-15'),
            ('11/15/2024', '2024-11-15'),
            ('15-11-2024', '2024-11-15'),
            ('2024/11/15', '2024-11-15'),
            ('15.11.2024', '2024-11-15'),
        ]
        
        for input_date, expected_output in test_cases:
            result = self.normalizer._normalize_date(input_date)
            self.assertEqual(result, expected_output, 
                           f"Failed to normalize {input_date} to {expected_output}, got {result}")
    
    def test_normalize_date_with_time(self):
        """Test date normalization strips time and returns date only."""
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP',
            date='15/11/2024 14:30:45'
        )
        
        record = self.normalizer.normalize(parsed)
        self.assertEqual(record.date, '2024-11-15')
    
    def test_normalize_date_invalid(self):
        """Test date normalization with invalid date."""
        result = self.normalizer._normalize_date('invalid-date')
        self.assertIsNone(result)
        
        result = self.normalizer._normalize_date('99/99/9999')
        self.assertIsNone(result)
    
    def test_normalize_date_none(self):
        """Test date normalization with None."""
        result = self.normalizer._normalize_date(None)
        self.assertIsNone(result)
        
        result = self.normalizer._normalize_date('')
        self.assertIsNone(result)
    
    def test_safe_float_cast_valid(self):
        """Test safe float casting with valid values."""
        test_cases = [
            ('100', 100.0),
            ('250.50', 250.50),
            ('1,234.56', 1234.56),
            ('  50.00  ', 50.00),
            ('0.01', 0.01),
            ('10000', 10000.0),
        ]
        
        for input_val, expected in test_cases:
            result = self.normalizer._safe_float_cast(input_val)
            self.assertEqual(result, expected,
                           f"Failed to cast {input_val} to {expected}, got {result}")
    
    def test_safe_float_cast_invalid(self):
        """Test safe float casting with invalid values."""
        test_cases = [
            'invalid',
            'abc123',
            '12.34.56',
            '',
            '   ',
        ]
        
        for input_val in test_cases:
            result = self.normalizer._safe_float_cast(input_val)
            self.assertIsNone(result, f"Expected None for {input_val}, got {result}")
    
    def test_safe_float_cast_none(self):
        """Test safe float casting with None."""
        result = self.normalizer._safe_float_cast(None)
        self.assertIsNone(result)
    
    def test_safe_float_cast_numeric_types(self):
        """Test safe float casting with numeric types."""
        self.assertEqual(self.normalizer._safe_float_cast(100), 100.0)
        self.assertEqual(self.normalizer._safe_float_cast(50.5), 50.5)
    
    def test_normalize_text_basic(self):
        """Test text normalization with basic strings."""
        test_cases = [
            ('  Test  ', 'Test'),
            ('Test   Store', 'Test Store'),
            ('  Multiple   Spaces  ', 'Multiple Spaces'),
            ('Normal Text', 'Normal Text'),
        ]
        
        for input_text, expected in test_cases:
            result = self.normalizer._normalize_text(input_text)
            self.assertEqual(result, expected,
                           f"Failed to normalize '{input_text}' to '{expected}', got '{result}'")
    
    def test_normalize_text_unicode(self):
        """Test text normalization with Unicode characters."""
        # Test Arabic text
        arabic = '  المحل العربي  '
        result = self.normalizer._normalize_text(arabic)
        self.assertEqual(result, 'المحل العربي')
        
        # Test with emoji
        emoji_text = 'Store 🏪'
        result = self.normalizer._normalize_text(emoji_text)
        self.assertEqual(result, 'Store 🏪')
    
    def test_normalize_text_none_and_empty(self):
        """Test text normalization with None and empty strings."""
        self.assertIsNone(self.normalizer._normalize_text(None))
        self.assertIsNone(self.normalizer._normalize_text(''))
        self.assertIsNone(self.normalizer._normalize_text('   '))
    
    def test_account_metadata_attachment(self):
        """Test account metadata is correctly attached."""
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP',
            card_suffix='1234'
        )
        
        record = self.normalizer.normalize(parsed)
        
        # Verify lookup was called
        self.mock_classifier.lookup_account.assert_called_with('1234')
        
        # Verify metadata attached
        self.assertEqual(record.account_id, 'ACC-HSBC-001')
        self.assertEqual(record.account_type, 'Credit')
        self.assertEqual(record.interest_rate, 19.99)
    
    def test_account_metadata_no_card_suffix(self):
        """Test account metadata when no card suffix provided."""
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP'
        )
        
        record = self.normalizer.normalize(parsed)
        
        # Verify lookup was not called
        self.mock_classifier.lookup_account.assert_not_called()
        
        # Verify metadata is None
        self.assertIsNone(record.account_id)
        self.assertIsNone(record.account_type)
        self.assertIsNone(record.interest_rate)
    
    def test_account_metadata_unknown_card(self):
        """Test account metadata with unknown card suffix."""
        # Mock returns empty/unknown data
        self.mock_classifier.lookup_account.return_value = {
            'account_id': 'unknown_9999',
            'account_type': 'Unknown',
            'interest_rate': None,
        }
        
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP',
            card_suffix='9999'
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertEqual(record.account_id, 'unknown_9999')
        self.assertEqual(record.account_type, 'Unknown')
        self.assertIsNone(record.interest_rate)
    
    def test_urgency_determination(self):
        """Test urgency determination based on amount and account type."""
        # High urgency - large amount
        urgency = self.normalizer._determine_urgency(15000.0, 'Debit')
        self.assertEqual(urgency, 'high')
        
        # Medium urgency - credit card with significant amount
        urgency = self.normalizer._determine_urgency(7500.0, 'Credit')
        self.assertEqual(urgency, 'medium')
        
        # Normal urgency - small amount
        urgency = self.normalizer._determine_urgency(100.0, 'Debit')
        self.assertEqual(urgency, 'normal')
        
        # Normal urgency - credit card with small amount
        urgency = self.normalizer._determine_urgency(100.0, 'Credit')
        self.assertEqual(urgency, 'normal')
        
        # Normal urgency - None amount
        urgency = self.normalizer._determine_urgency(None, 'Credit')
        self.assertEqual(urgency, 'normal')
    
    def test_default_values_population(self):
        """Test default values are populated for missing data."""
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP'
        )
        
        record = self.normalizer.normalize(parsed)
        
        # Check defaults
        self.assertEqual(record.category, 'Uncategorized')
        self.assertEqual(record.subcategory, 'General')
        self.assertEqual(record.urgency, 'normal')
    
    def test_tag_extraction(self):
        """Test tags are extracted from parsed transaction."""
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP',
            txn_type='POS',
            bank_id='HSBC'
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertIn('POS', record.tags)
        self.assertIn('HSBC', record.tags)
    
    def test_tag_extraction_with_warnings(self):
        """Test warning tag is added when transaction has warnings."""
        parsed = ParsedTransaction(
            amount='invalid',
            currency='EGP'
        )
        
        record = self.normalizer.normalize(parsed)
        
        # Should have has-warnings tag
        self.assertIn('has-warnings', record.tags)
    
    def test_normalize_batch(self):
        """Test batch normalization of multiple transactions."""
        parsed_list = [
            ParsedTransaction(amount='100', currency='EGP', date='15/11/2024'),
            ParsedTransaction(amount='200', currency='USD', date='16/11/2024'),
            ParsedTransaction(amount='300', currency='EUR', date='17/11/2024'),
        ]
        
        records = self.normalizer.normalize_batch(parsed_list)
        
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].amount, 100.0)
        self.assertEqual(records[1].amount, 200.0)
        self.assertEqual(records[2].amount, 300.0)
        
        self.assertEqual(records[0].date, '2024-11-15')
        self.assertEqual(records[1].date, '2024-11-16')
        self.assertEqual(records[2].date, '2024-11-17')
    
    def test_normalize_batch_empty(self):
        """Test batch normalization with empty list."""
        records = self.normalizer.normalize_batch([])
        self.assertEqual(len(records), 0)
    
    def test_generate_id_uniqueness(self):
        """Test that generated IDs are unique."""
        id1 = self.normalizer._generate_id()
        id2 = self.normalizer._generate_id()
        
        self.assertNotEqual(id1, id2)
        self.assertTrue(len(id1) > 0)
        self.assertTrue(len(id2) > 0)
    
    def test_merchant_normalization(self):
        """Test merchant normalization from payee."""
        payee = '  Test Store  '
        merchant = self.normalizer._normalize_merchant(payee)
        
        self.assertEqual(merchant, 'Test Store')
    
    def test_merchant_normalization_none(self):
        """Test merchant normalization with None."""
        merchant = self.normalizer._normalize_merchant(None)
        self.assertIsNone(merchant)
    
    def test_confidence_preservation(self):
        """Test that confidence from parsed transaction is preserved."""
        test_cases = ['high', 'medium', 'low']
        
        for confidence in test_cases:
            parsed = ParsedTransaction(
                amount='100',
                currency='EGP',
                confidence=confidence
            )
            
            record = self.normalizer.normalize(parsed)
            self.assertEqual(record.confidence, confidence)
    
    def test_integration_with_field_validator(self):
        """Test integration with FieldValidator output."""
        validator = FieldValidator()
        
        # Simulate validator output
        data = {
            'amount': '250.50',
            'currency': 'EGP',
            'date': '15/11/2024',
            'payee': 'Test Store',
            'transaction_type': 'POS',
            'card_suffix': '1234',
            'matched_bank': 'HSBC'
        }
        
        parsed = validator.validate(data)
        record = self.normalizer.normalize(parsed)
        
        # Verify full pipeline
        self.assertEqual(record.amount, 250.50)
        self.assertEqual(record.date, '2024-11-15')
        self.assertEqual(record.currency, 'EGP')
        self.assertEqual(record.payee, 'Test Store')
        self.assertIn('POS', record.tags)
    
    def test_whitespace_handling_in_amount(self):
        """Test whitespace is properly handled in amount conversion."""
        parsed = ParsedTransaction(
            amount='  1,234.56  ',
            currency='EGP'
        )
        
        record = self.normalizer.normalize(parsed)
        self.assertEqual(record.amount, 1234.56)
    
    def test_empty_string_handling(self):
        """Test empty strings are handled as None."""
        parsed = ParsedTransaction(
            amount='',
            currency='',
            date=''
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertIsNone(record.amount)
        self.assertIsNone(record.currency)
        self.assertIsNone(record.date)
    
    def test_large_amounts(self):
        """Test handling of large transaction amounts."""
        parsed = ParsedTransaction(
            amount='1000000.00',
            currency='EGP',
            date='15/11/2024'
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertEqual(record.amount, 1000000.0)
        self.assertEqual(record.urgency, 'high')
    
    def test_very_small_amounts(self):
        """Test handling of very small amounts."""
        parsed = ParsedTransaction(
            amount='0.01',
            currency='EGP',
            date='15/11/2024'
        )
        
        record = self.normalizer.normalize(parsed)
        
        self.assertEqual(record.amount, 0.01)


class TestSchemaNormalizerEdgeCases(unittest.TestCase):
    """Test edge cases for SchemaNormalizer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_classifier = Mock()
        self.mock_classifier.lookup_account.return_value = {}
        self.normalizer = SchemaNormalizer(card_classifier=self.mock_classifier)
    
    def test_normalize_with_account_lookup_exception(self):
        """Test normalization when account lookup raises exception."""
        self.mock_classifier.lookup_account.side_effect = Exception("Lookup error")
        
        parsed = ParsedTransaction(
            amount='100',
            currency='EGP',
            card_suffix='1234'
        )
        
        # Should not raise exception
        record = self.normalizer.normalize(parsed)
        
        # Should have None metadata
        self.assertIsNone(record.account_id)
        self.assertIsNone(record.account_type)
    
    def test_normalize_batch_with_error(self):
        """Test batch normalization handles errors gracefully."""
        # Create a scenario that causes an error
        self.mock_classifier.lookup_account.side_effect = Exception("Error")
        
        parsed_list = [
            ParsedTransaction(amount='100', currency='EGP', card_suffix='1234'),
        ]
        
        records = self.normalizer.normalize_batch(parsed_list)
        
        # Should still return a list with same length
        self.assertEqual(len(records), 1)
        # Record should exist even if there was an error
        self.assertIsNotNone(records[0])
    
    def test_unicode_normalization_nfc(self):
        """Test Unicode NFC normalization."""
        # Create text with combining characters
        text = 'café'  # May be represented as 'cafe\u0301'
        normalized = self.normalizer._normalize_text(text)
        
        # Should be normalized to NFC form
        self.assertEqual(normalized, 'café')
    
    def test_arabic_text_normalization(self):
        """Test normalization preserves Arabic text."""
        arabic = 'متجر الإلكترونيات'
        normalized = self.normalizer._normalize_text(arabic)
        
        self.assertEqual(normalized, 'متجر الإلكترونيات')
    
    def test_mixed_language_text(self):
        """Test normalization with mixed language text."""
        mixed = 'Store المحل'
        normalized = self.normalizer._normalize_text(mixed)
        
        self.assertEqual(normalized, 'Store المحل')


if __name__ == '__main__':
    unittest.main()
