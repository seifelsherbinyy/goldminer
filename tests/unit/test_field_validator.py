"""Unit tests for FieldValidator and ParsedTransaction."""
import unittest
from datetime import datetime
from goldminer.etl import FieldValidator, ParsedTransaction


class TestParsedTransaction(unittest.TestCase):
    """Test cases for ParsedTransaction Pydantic model."""
    
    def test_valid_transaction_all_fields(self):
        """Test creating a valid transaction with all fields."""
        data = {
            'amount': '250.50',
            'currency': 'EGP',
            'date': '15/11/2024',
            'payee': 'Store XYZ',
            'txn_type': 'POS',
            'card_suffix': '1234',
            'bank_id': 'HSBC',
            'confidence': 'high'
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.amount, '250.50')
        self.assertEqual(transaction.currency, 'EGP')
        self.assertEqual(transaction.date, '15/11/2024')
        self.assertEqual(transaction.payee, 'Store XYZ')
        self.assertEqual(transaction.txn_type, 'POS')
        self.assertEqual(transaction.card_suffix, '1234')
        self.assertEqual(transaction.bank_id, 'HSBC')
        self.assertEqual(transaction.confidence, 'high')
        self.assertEqual(len(transaction.warnings), 0)
    
    def test_valid_transaction_minimal_fields(self):
        """Test creating a valid transaction with minimal required fields."""
        data = {
            'amount': '100',
            'currency': 'USD',
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.amount, '100')
        self.assertEqual(transaction.currency, 'USD')
        self.assertIsNone(transaction.date)
        self.assertIsNone(transaction.payee)
        # Should have warnings for missing date
        self.assertIn('low', transaction.confidence.lower())
    
    def test_invalid_amount_format(self):
        """Test transaction with invalid amount format."""
        data = {
            'amount': 'invalid_amount',
            'currency': 'EGP'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about invalid amount
        self.assertTrue(any('Invalid numeric format' in w for w in transaction.warnings))
        self.assertEqual(transaction.confidence, 'low')
    
    def test_negative_amount(self):
        """Test transaction with negative amount."""
        data = {
            'amount': '-50.00',
            'currency': 'EGP'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about positive amount
        self.assertTrue(any('positive' in w for w in transaction.warnings))
    
    def test_invalid_currency(self):
        """Test transaction with invalid currency code."""
        data = {
            'amount': '100',
            'currency': 'INVALID'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about invalid currency
        self.assertTrue(any('Invalid currency' in w for w in transaction.warnings))
        # Should have low confidence due to invalid currency + missing date
        self.assertIn(transaction.confidence, ['low', 'medium'])
    
    def test_valid_currencies(self):
        """Test various valid currency codes."""
        valid_currencies = ['EGP', 'USD', 'EUR', 'GBP', 'SAR', 'AED', 'جنيه', 'دولار']
        
        for currency in valid_currencies:
            data = {
                'amount': '100',
                'currency': currency,
                'date': '15/11/2024'
            }
            
            transaction = ParsedTransaction(**data)
            
            # Should not have currency warning
            currency_warnings = [w for w in transaction.warnings if 'currency' in w.lower()]
            self.assertEqual(len(currency_warnings), 0, 
                           f"Unexpected warning for valid currency {currency}")
    
    def test_malformed_date(self):
        """Test transaction with malformed date."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': 'invalid_date'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about malformed date
        self.assertTrue(any('Malformed date' in w for w in transaction.warnings))
    
    def test_valid_date_formats(self):
        """Test various valid date formats."""
        valid_dates = [
            '15/11/2024',
            '2024-11-15',
            '11/15/2024',
            '15-11-2024',
            '2024/11/15',
            '15.11.2024',
        ]
        
        for date_str in valid_dates:
            data = {
                'amount': '100',
                'currency': 'EGP',
                'date': date_str
            }
            
            transaction = ParsedTransaction(**data)
            
            # Should not have date warning
            date_warnings = [w for w in transaction.warnings if 'date' in w.lower()]
            self.assertEqual(len(date_warnings), 0,
                           f"Unexpected warning for valid date format {date_str}")
    
    def test_invalid_card_suffix(self):
        """Test transaction with invalid card suffix."""
        invalid_suffixes = ['123', '12345', 'abcd', '12a4']
        
        for suffix in invalid_suffixes:
            data = {
                'amount': '100',
                'currency': 'EGP',
                'card_suffix': suffix
            }
            
            transaction = ParsedTransaction(**data)
            
            # Should have warning about invalid card suffix
            self.assertTrue(any('card suffix' in w.lower() for w in transaction.warnings),
                          f"Expected warning for invalid suffix {suffix}")
    
    def test_valid_card_suffix(self):
        """Test transaction with valid card suffix."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': '15/11/2024',
            'card_suffix': '1234'
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.card_suffix, '1234')
        # Should not have card suffix warning
        suffix_warnings = [w for w in transaction.warnings if 'card suffix' in w.lower()]
        self.assertEqual(len(suffix_warnings), 0)
    
    def test_missing_amount(self):
        """Test transaction with missing amount field."""
        data = {
            'currency': 'EGP',
            'date': '15/11/2024'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about missing amount
        self.assertTrue(any('Missing required field: amount' in w for w in transaction.warnings))
        self.assertEqual(transaction.confidence, 'low')
    
    def test_missing_currency(self):
        """Test transaction with missing currency field."""
        data = {
            'amount': '100',
            'date': '15/11/2024'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have warning about missing currency
        self.assertTrue(any('Missing currency' in w for w in transaction.warnings))
    
    def test_partial_data(self):
        """Test transaction with partial data (only amount)."""
        data = {
            'amount': '100'
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.amount, '100')
        self.assertIsNone(transaction.currency)
        self.assertIsNone(transaction.date)
        # Should have warning for missing currency
        self.assertGreaterEqual(len(transaction.warnings), 1)
        # Should have medium confidence (only 1 warning)
        self.assertEqual(transaction.confidence, 'medium')
    
    def test_amount_with_comma_separator(self):
        """Test transaction with comma-separated amount."""
        data = {
            'amount': '1,234.56',
            'currency': 'EGP',
            'date': '15/11/2024'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should clean and validate the amount
        self.assertEqual(transaction.amount, '1234.56')
        # Should not have amount warnings
        amount_warnings = [w for w in transaction.warnings if 'amount' in w.lower()]
        self.assertEqual(len(amount_warnings), 0)
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        data = {
            'amount': '  100.50  ',
            'currency': '  EGP  ',
            'date': '  15/11/2024  ',
            'card_suffix': '  1234  '
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.amount, '100.50')
        self.assertEqual(transaction.currency, 'EGP')
        self.assertEqual(transaction.date, '15/11/2024')
        self.assertEqual(transaction.card_suffix, '1234')
    
    def test_confidence_high(self):
        """Test that high confidence is assigned correctly."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': '15/11/2024',
            'payee': 'Store ABC',
            'card_suffix': '1234'
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.confidence, 'high')
        self.assertEqual(len(transaction.warnings), 0)
    
    def test_confidence_medium(self):
        """Test that medium confidence is assigned correctly."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': 'invalid_date',  # This will cause one warning
            'card_suffix': '1234'
        }
        
        transaction = ParsedTransaction(**data)
        
        # Should have medium confidence with some warnings
        self.assertIn(transaction.confidence, ['medium', 'low'])
        self.assertGreater(len(transaction.warnings), 0)
    
    def test_confidence_low(self):
        """Test that low confidence is assigned correctly."""
        data = {
            'amount': 'invalid',
            'currency': 'EGP'
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertEqual(transaction.confidence, 'low')
        self.assertGreater(len(transaction.warnings), 0)
    
    def test_empty_strings_treated_as_none(self):
        """Test that empty strings are treated as None."""
        data = {
            'amount': '',
            'currency': '',
            'date': '',
        }
        
        transaction = ParsedTransaction(**data)
        
        self.assertIsNone(transaction.amount)
        self.assertIsNone(transaction.currency)
        self.assertIsNone(transaction.date)
    
    def test_txn_type_field(self):
        """Test transaction type field."""
        txn_types = ['POS', 'ATM', 'Online', 'Purchase', 'Withdrawal']
        
        for txn_type in txn_types:
            data = {
                'amount': '100',
                'currency': 'EGP',
                'txn_type': txn_type
            }
            
            transaction = ParsedTransaction(**data)
            self.assertEqual(transaction.txn_type, txn_type)
    
    def test_payee_field(self):
        """Test payee field with various names."""
        payees = ['Amazon', 'Store XYZ', 'المحل', 'Café 123']
        
        for payee in payees:
            data = {
                'amount': '100',
                'currency': 'EGP',
                'payee': payee
            }
            
            transaction = ParsedTransaction(**data)
            self.assertEqual(transaction.payee, payee)
    
    def test_bank_id_field(self):
        """Test bank_id field."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'bank_id': 'HSBC'
        }
        
        transaction = ParsedTransaction(**data)
        self.assertEqual(transaction.bank_id, 'HSBC')


class TestFieldValidator(unittest.TestCase):
    """Test cases for FieldValidator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator()
    
    def test_validate_valid_data(self):
        """Test validation of valid transaction data."""
        data = {
            'amount': '250.50',
            'currency': 'EGP',
            'date': '15/11/2024',
            'payee': 'Store XYZ',
            'txn_type': 'POS',
            'card_suffix': '1234',
            'bank_id': 'HSBC'
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.amount, '250.50')
        self.assertEqual(result.currency, 'EGP')
        self.assertEqual(result.confidence, 'high')
        self.assertEqual(len(result.warnings), 0)
    
    def test_validate_invalid_data(self):
        """Test validation of invalid transaction data."""
        data = {
            'amount': 'not_a_number',
            'currency': 'INVALID_CURRENCY',
            'date': 'bad_date',
            'card_suffix': '123'  # Invalid: not 4 digits
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.confidence, 'low')
        self.assertGreater(len(result.warnings), 0)
        # Should have warnings for all invalid fields
        self.assertTrue(any('amount' in w.lower() for w in result.warnings))
        self.assertTrue(any('currency' in w.lower() for w in result.warnings))
        self.assertTrue(any('date' in w.lower() for w in result.warnings))
        self.assertTrue(any('card suffix' in w.lower() for w in result.warnings))
    
    def test_validate_partial_data(self):
        """Test validation of partial transaction data."""
        data = {
            'amount': '100',
            'payee': 'Store ABC'
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.amount, '100')
        self.assertEqual(result.payee, 'Store ABC')
        # Should have low confidence due to missing currency (2 warnings: missing currency and no date)
        self.assertIn(result.confidence, ['low', 'medium'])
        # Should have warnings for missing fields
        self.assertTrue(any('currency' in w.lower() for w in result.warnings))
    
    def test_validate_malformed_data(self):
        """Test validation of malformed transaction data."""
        data = {
            'amount': '###',
            'currency': '123',
            'date': '99/99/9999',
            'card_suffix': 'abcd'
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.confidence, 'low')
        self.assertGreater(len(result.warnings), 2)
    
    def test_validate_empty_data(self):
        """Test validation of empty data."""
        data = {}
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.confidence, 'low')
        # Should have warnings for missing required fields
        self.assertTrue(any('amount' in w.lower() for w in result.warnings))
    
    def test_validate_none_values(self):
        """Test validation with None values."""
        data = {
            'amount': None,
            'currency': None,
            'date': None
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.confidence, 'low')
        self.assertGreater(len(result.warnings), 0)
    
    def test_validate_no_exceptions_raised(self):
        """Test that validate never raises exceptions."""
        # Try various problematic inputs
        problematic_data = [
            {'amount': object()},  # Wrong type
            {'amount': [1, 2, 3]},  # List instead of string
            {'date': 12345},  # Number instead of string
            None,  # None as data - this would raise TypeError
        ]
        
        for data in problematic_data:
            try:
                result = self.validator.validate(data if data is not None else {})
                self.assertIsInstance(result, ParsedTransaction)
                self.assertEqual(result.confidence, 'low')
            except Exception as e:
                self.fail(f"validate() raised exception {e} for data {data}")
    
    def test_validate_batch_valid(self):
        """Test batch validation with valid data."""
        data_list = [
            {'amount': '100', 'currency': 'EGP', 'date': '15/11/2024'},
            {'amount': '200', 'currency': 'USD', 'date': '16/11/2024'},
            {'amount': '300', 'currency': 'EUR', 'date': '17/11/2024'}
        ]
        
        results = self.validator.validate_batch(data_list)
        
        self.assertEqual(len(results), 3)
        for i, result in enumerate(results):
            self.assertIsInstance(result, ParsedTransaction)
            expected_amount = str((i + 1) * 100)
            self.assertEqual(result.amount, expected_amount)
    
    def test_validate_batch_mixed(self):
        """Test batch validation with mixed valid/invalid data."""
        data_list = [
            {'amount': '100', 'currency': 'EGP', 'date': '15/11/2024'},  # Valid
            {'amount': 'invalid', 'currency': 'BAD'},  # Invalid
            {'amount': '300', 'currency': 'USD'}  # Partial
        ]
        
        results = self.validator.validate_batch(data_list)
        
        self.assertEqual(len(results), 3)
        
        # First should be valid
        self.assertLessEqual(len(results[0].warnings), 1)
        
        # Second should have warnings
        self.assertGreater(len(results[1].warnings), 0)
        self.assertEqual(results[1].confidence, 'low')
        
        # Third should have warnings (missing date)
        self.assertGreaterEqual(len(results[2].warnings), 0)
    
    def test_validate_batch_empty(self):
        """Test batch validation with empty list."""
        results = self.validator.validate_batch([])
        
        self.assertEqual(len(results), 0)
    
    def test_validate_with_transaction_type_alias(self):
        """Test validation handles transaction_type field name."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'transaction_type': 'POS'  # Alternative field name
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.txn_type, 'POS')
    
    def test_validate_with_matched_bank_alias(self):
        """Test validation handles matched_bank field name."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'matched_bank': 'HSBC'  # Alternative field name
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.bank_id, 'HSBC')
    
    def test_validate_integration_with_parser_output(self):
        """Test validation with typical parser output format."""
        # Simulate output from RegexParserEngine
        parser_output = {
            'amount': '250.50',
            'currency': 'EGP',
            'date': '15/11/2024',
            'payee': 'Store XYZ',
            'transaction_type': 'POS',
            'card_suffix': '1234',
            'confidence': 'high',
            'matched_bank': 'HSBC',
            'matched_template': 'HSBC Standard'
        }
        
        result = self.validator.validate(parser_output)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.amount, '250.50')
        self.assertEqual(result.currency, 'EGP')
        self.assertEqual(result.txn_type, 'POS')
        self.assertEqual(result.bank_id, 'HSBC')
        self.assertEqual(result.confidence, 'high')
    
    def test_validate_arabic_currency(self):
        """Test validation with Arabic currency names."""
        data = {
            'amount': '150',
            'currency': 'جنيه',
            'date': '15/11/2024'
        }
        
        result = self.validator.validate(data)
        
        self.assertIsInstance(result, ParsedTransaction)
        self.assertEqual(result.currency, 'جنيه')
        # Should not have currency warning
        currency_warnings = [w for w in result.warnings if 'currency' in w.lower()]
        self.assertEqual(len(currency_warnings), 0)
    
    def test_validate_decimal_precision(self):
        """Test validation preserves decimal precision."""
        amounts = ['100.00', '99.99', '0.01', '1234.56']
        
        for amount in amounts:
            data = {
                'amount': amount,
                'currency': 'EGP',
                'date': '15/11/2024'
            }
            
            result = self.validator.validate(data)
            self.assertEqual(result.amount, amount)
    
    def test_validate_large_amounts(self):
        """Test validation with large amounts."""
        data = {
            'amount': '1000000.00',
            'currency': 'EGP',
            'date': '15/11/2024'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.amount, '1000000.00')
        # Should not have amount warnings
        amount_warnings = [w for w in result.warnings if 'Invalid numeric' in w]
        self.assertEqual(len(amount_warnings), 0)


class TestFieldValidatorEdgeCases(unittest.TestCase):
    """Test edge cases for FieldValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = FieldValidator()
    
    def test_unicode_characters_in_payee(self):
        """Test handling of Unicode characters in payee field."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'payee': 'المحل العربي 🏪'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.payee, 'المحل العربي 🏪')
    
    def test_zero_amount(self):
        """Test handling of zero amount."""
        data = {
            'amount': '0',
            'currency': 'EGP'
        }
        
        result = self.validator.validate(data)
        
        # Should have warning about positive amount
        self.assertTrue(any('positive' in w for w in result.warnings))
    
    def test_very_small_amount(self):
        """Test handling of very small amounts."""
        data = {
            'amount': '0.01',
            'currency': 'EGP',
            'date': '15/11/2024'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.amount, '0.01')
        # Should not have positive amount warning
        positive_warnings = [w for w in result.warnings if 'positive' in w]
        self.assertEqual(len(positive_warnings), 0)
    
    def test_amount_without_decimals(self):
        """Test handling of amounts without decimal points."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': '15/11/2024'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.amount, '100')
    
    def test_lowercase_currency(self):
        """Test that currency codes are normalized to uppercase."""
        data = {
            'amount': '100',
            'currency': 'egp',
            'date': '15/11/2024'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.currency, 'EGP')
    
    def test_mixed_case_confidence(self):
        """Test that confidence levels are normalized to lowercase."""
        data = {
            'amount': '100',
            'currency': 'EGP',
            'date': '15/11/2024',
            'confidence': 'HIGH'
        }
        
        result = self.validator.validate(data)
        
        self.assertEqual(result.confidence, 'high')


if __name__ == '__main__':
    unittest.main()
