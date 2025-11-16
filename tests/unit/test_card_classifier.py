"""Unit tests for CardClassifier."""
import unittest
import tempfile
import os
import yaml
from goldminer.analysis import CardClassifier


class TestCardClassifier(unittest.TestCase):
    """Test cases for CardClassifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary accounts file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_accounts_file = os.path.join(self.temp_dir, 'test_accounts.yaml')
        
        # Define test account data
        test_accounts = {
            '1234': {
                'account_id': 'ACC-TEST-001',
                'account_type': 'Credit',
                'interest_rate': 19.99,
                'credit_limit': 50000.00,
                'billing_cycle': 15,
                'label': 'Test Credit Card'
            },
            '5678': {
                'account_id': 'ACC-TEST-002',
                'account_type': 'Debit',
                'interest_rate': None,
                'credit_limit': None,
                'billing_cycle': None,
                'label': 'Test Debit Card'
            },
            '9012': {
                'account_id': 'ACC-TEST-003',
                'account_type': 'Prepaid',
                'interest_rate': None,
                'credit_limit': None,
                'billing_cycle': None,
                'label': 'Test Prepaid Card'
            }
        }
        
        # Write accounts to file
        with open(self.test_accounts_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_accounts, f, allow_unicode=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # Test initialization
    
    def test_initialization_default(self):
        """Test initialization with default accounts file."""
        classifier = CardClassifier()
        self.assertIsNotNone(classifier.accounts)
        self.assertIsInstance(classifier.accounts, dict)
    
    def test_initialization_custom_file(self):
        """Test initialization with custom accounts file."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        self.assertEqual(len(classifier.accounts), 3)
        self.assertIn('1234', classifier.accounts)
        self.assertIn('5678', classifier.accounts)
    
    def test_initialization_missing_file(self):
        """Test initialization with non-existent file returns empty dict."""
        non_existent_file = os.path.join(self.temp_dir, 'nonexistent.yaml')
        classifier = CardClassifier(accounts_file=non_existent_file)
        self.assertEqual(len(classifier.accounts), 0)
    
    def test_initialization_invalid_yaml(self):
        """Test initialization with invalid YAML."""
        invalid_file = os.path.join(self.temp_dir, 'invalid.yaml')
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        with self.assertRaises(ValueError):
            CardClassifier(accounts_file=invalid_file)
    
    def test_initialization_missing_required_field(self):
        """Test initialization with account missing required field."""
        invalid_accounts = {
            '1111': {
                'account_type': 'Credit',
                # Missing account_id
            }
        }
        invalid_file = os.path.join(self.temp_dir, 'invalid_accounts.yaml')
        with open(invalid_file, 'w', encoding='utf-8') as f:
            yaml.dump(invalid_accounts, f)
        
        with self.assertRaises(ValueError):
            CardClassifier(accounts_file=invalid_file)
    
    # Test extract_card_suffix
    
    def test_extract_card_suffix_english_ending(self):
        """Test extraction with English 'ending' pattern."""
        suffix = CardClassifier.extract_card_suffix("Transaction on card ending 1234")
        self.assertEqual(suffix, "1234")
    
    def test_extract_card_suffix_english_card_ending(self):
        """Test extraction with English 'card ending' pattern."""
        suffix = CardClassifier.extract_card_suffix("HSBC card ending 5678 charged")
        self.assertEqual(suffix, "5678")
    
    def test_extract_card_suffix_english_card_number(self):
        """Test extraction with English 'card' pattern."""
        suffix = CardClassifier.extract_card_suffix("HSBC card 9012 charged 100 EGP")
        self.assertEqual(suffix, "9012")
    
    def test_extract_card_suffix_english_asterisks(self):
        """Test extraction with asterisks pattern."""
        suffix = CardClassifier.extract_card_suffix("Card **1234 used")
        self.assertEqual(suffix, "1234")
        
        suffix = CardClassifier.extract_card_suffix("Card ****5678 used")
        self.assertEqual(suffix, "5678")
    
    def test_extract_card_suffix_arabic_raqm(self):
        """Test extraction with Arabic 'رقم' pattern."""
        suffix = CardClassifier.extract_card_suffix("بطاقة رقم 1234")
        self.assertEqual(suffix, "1234")
    
    def test_extract_card_suffix_arabic_bitaqa(self):
        """Test extraction with Arabic 'بطاقة' pattern."""
        suffix = CardClassifier.extract_card_suffix("بطاقة 5678 خصم")
        self.assertEqual(suffix, "5678")
    
    def test_extract_card_suffix_arabic_indic_numerals(self):
        """Test extraction with Arabic-Indic numerals."""
        suffix = CardClassifier.extract_card_suffix("بطاقة رقم ١٢٣٤")
        self.assertEqual(suffix, "1234")
        
        suffix = CardClassifier.extract_card_suffix("رقم ٥٦٧٨")
        self.assertEqual(suffix, "5678")
    
    def test_extract_card_suffix_mixed_language(self):
        """Test extraction with mixed English and Arabic."""
        suffix = CardClassifier.extract_card_suffix("HSBC بطاقة رقم 9012")
        self.assertEqual(suffix, "9012")
    
    def test_extract_card_suffix_case_insensitive(self):
        """Test that extraction is case-insensitive."""
        suffix1 = CardClassifier.extract_card_suffix("Card Ending 1234")
        suffix2 = CardClassifier.extract_card_suffix("CARD ENDING 1234")
        suffix3 = CardClassifier.extract_card_suffix("card ending 1234")
        
        self.assertEqual(suffix1, "1234")
        self.assertEqual(suffix2, "1234")
        self.assertEqual(suffix3, "1234")
    
    def test_extract_card_suffix_none_if_not_found(self):
        """Test that None is returned when no suffix is found."""
        suffix = CardClassifier.extract_card_suffix("No card info here")
        self.assertIsNone(suffix)
        
        suffix = CardClassifier.extract_card_suffix("Transaction completed")
        self.assertIsNone(suffix)
    
    def test_extract_card_suffix_invalid_length(self):
        """Test that suffixes with wrong length are rejected."""
        # Too short
        suffix = CardClassifier.extract_card_suffix("card ending 123")
        self.assertIsNone(suffix)
        
        # Too long
        suffix = CardClassifier.extract_card_suffix("card ending 12345")
        self.assertIsNone(suffix)
    
    def test_extract_card_suffix_empty_input(self):
        """Test extraction with empty or invalid input."""
        self.assertIsNone(CardClassifier.extract_card_suffix(""))
        self.assertIsNone(CardClassifier.extract_card_suffix(None))
    
    def test_extract_card_suffix_multiple_matches(self):
        """Test that first valid match is returned."""
        suffix = CardClassifier.extract_card_suffix("card ending 1234 and card 5678")
        # Should return the first match
        self.assertEqual(suffix, "1234")
    
    # Test convert_arabic_indic_numerals
    
    def test_convert_arabic_indic_numerals_basic(self):
        """Test basic Arabic-Indic numeral conversion."""
        result = CardClassifier.convert_arabic_indic_numerals("١٢٣٤")
        self.assertEqual(result, "1234")
    
    def test_convert_arabic_indic_numerals_all_digits(self):
        """Test conversion of all Arabic-Indic digits."""
        result = CardClassifier.convert_arabic_indic_numerals("٠١٢٣٤٥٦٧٨٩")
        self.assertEqual(result, "0123456789")
    
    def test_convert_arabic_indic_numerals_in_text(self):
        """Test conversion in Arabic text."""
        result = CardClassifier.convert_arabic_indic_numerals("بطاقة رقم ١٢٣٤")
        self.assertEqual(result, "بطاقة رقم 1234")
    
    def test_convert_arabic_indic_numerals_mixed(self):
        """Test conversion with mixed numerals."""
        result = CardClassifier.convert_arabic_indic_numerals("12 and ٣٤")
        self.assertEqual(result, "12 and 34")
    
    def test_convert_arabic_indic_numerals_empty(self):
        """Test conversion with empty input."""
        self.assertEqual(CardClassifier.convert_arabic_indic_numerals(""), "")
        self.assertIsNone(CardClassifier.convert_arabic_indic_numerals(None))
    
    # Test lookup_account
    
    def test_lookup_account_known_suffix(self):
        """Test lookup with known card suffix."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("1234")
        
        self.assertEqual(result['account_id'], 'ACC-TEST-001')
        self.assertEqual(result['account_type'], 'Credit')
        self.assertEqual(result['card_suffix'], '1234')
        self.assertTrue(result['is_known'])
    
    def test_lookup_account_unknown_suffix(self):
        """Test lookup with unknown card suffix."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("9999")
        
        self.assertEqual(result['account_id'], 'unknown_9999')
        self.assertEqual(result['account_type'], 'Unknown')
        self.assertEqual(result['card_suffix'], '9999')
        self.assertFalse(result['is_known'])
    
    def test_lookup_account_empty_suffix(self):
        """Test lookup with empty suffix."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("")
        
        self.assertEqual(result['account_id'], 'unknown')
        self.assertFalse(result['is_known'])
    
    def test_lookup_account_includes_all_fields(self):
        """Test that lookup includes all expected fields."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("1234")
        
        expected_fields = [
            'account_id', 'account_type', 'interest_rate',
            'credit_limit', 'billing_cycle', 'label',
            'card_suffix', 'is_known'
        ]
        
        for field in expected_fields:
            self.assertIn(field, result)
    
    def test_lookup_account_credit_card(self):
        """Test lookup for credit card account."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("1234")
        
        self.assertEqual(result['account_type'], 'Credit')
        self.assertIsNotNone(result['interest_rate'])
        self.assertIsNotNone(result['credit_limit'])
        self.assertIsNotNone(result['billing_cycle'])
    
    def test_lookup_account_debit_card(self):
        """Test lookup for debit card account."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("5678")
        
        self.assertEqual(result['account_type'], 'Debit')
        self.assertIsNone(result['interest_rate'])
        self.assertIsNone(result['credit_limit'])
    
    def test_lookup_account_prepaid_card(self):
        """Test lookup for prepaid card account."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.lookup_account("9012")
        
        self.assertEqual(result['account_type'], 'Prepaid')
        self.assertIsNone(result['interest_rate'])
        self.assertIsNone(result['credit_limit'])
    
    # Test classify_sms
    
    def test_classify_sms_with_known_card(self):
        """Test SMS classification with known card."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.classify_sms("Transaction on card ending 1234")
        
        self.assertEqual(result['account_id'], 'ACC-TEST-001')
        self.assertTrue(result['is_known'])
    
    def test_classify_sms_with_unknown_card(self):
        """Test SMS classification with unknown card."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.classify_sms("Transaction on card ending 9999")
        
        self.assertFalse(result['is_known'])
        self.assertEqual(result['card_suffix'], '9999')
    
    def test_classify_sms_no_card_suffix(self):
        """Test SMS classification when no card suffix found."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.classify_sms("Generic transaction message")
        
        self.assertFalse(result['is_known'])
        self.assertIsNone(result['card_suffix'])
        self.assertIn("No card suffix", result['label'])
    
    def test_classify_sms_arabic(self):
        """Test SMS classification with Arabic text."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        result = classifier.classify_sms("خصم من بطاقة رقم ١٢٣٤")
        
        self.assertEqual(result['account_id'], 'ACC-TEST-001')
        self.assertTrue(result['is_known'])
    
    # Test reload_accounts
    
    def test_reload_accounts_same_file(self):
        """Test reloading accounts from same file."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        initial_count = len(classifier.accounts)
        
        classifier.reload_accounts()
        
        self.assertEqual(len(classifier.accounts), initial_count)
    
    def test_reload_accounts_different_file(self):
        """Test reloading accounts from different file."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        self.assertEqual(len(classifier.accounts), 3)
        
        # Create a new file with different accounts
        new_file = os.path.join(self.temp_dir, 'new_accounts.yaml')
        new_accounts = {
            '1111': {
                'account_id': 'ACC-NEW-001',
                'account_type': 'Credit',
                'interest_rate': 20.0,
                'credit_limit': 10000.0,
                'billing_cycle': 1,
                'label': 'New Account'
            }
        }
        with open(new_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_accounts, f)
        
        classifier.reload_accounts(accounts_file=new_file)
        
        self.assertEqual(len(classifier.accounts), 1)
        self.assertIn('1111', classifier.accounts)
    
    # Integration tests
    
    def test_full_workflow_english(self):
        """Test complete workflow with English SMS."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        
        sms = "HSBC: Transaction of 100.00 EGP at Amazon on card ending 1234 on 15/11/2025"
        result = classifier.classify_sms(sms)
        
        self.assertTrue(result['is_known'])
        self.assertEqual(result['card_suffix'], '1234')
        self.assertEqual(result['account_type'], 'Credit')
        self.assertEqual(result['label'], 'Test Credit Card')
    
    def test_full_workflow_arabic(self):
        """Test complete workflow with Arabic SMS."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        
        sms = "خصم مبلغ ١٠٠ جنيه من بطاقة رقم ٥٦٧٨"
        result = classifier.classify_sms(sms)
        
        self.assertTrue(result['is_known'])
        self.assertEqual(result['card_suffix'], '5678')
        self.assertEqual(result['account_type'], 'Debit')
    
    def test_full_workflow_unknown_card(self):
        """Test complete workflow with unknown card."""
        classifier = CardClassifier(accounts_file=self.test_accounts_file)
        
        sms = "Transaction on card ending 8888"
        result = classifier.classify_sms(sms)
        
        self.assertFalse(result['is_known'])
        self.assertEqual(result['card_suffix'], '8888')
        self.assertEqual(result['account_type'], 'Unknown')


if __name__ == '__main__':
    unittest.main()
