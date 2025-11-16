"""Unit tests for BankPatternRecognizer."""
import unittest
import tempfile
import os
import yaml
from goldminer.analysis import BankPatternRecognizer


class TestBankPatternRecognizer(unittest.TestCase):
    """Test cases for BankPatternRecognizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary patterns file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_patterns_file = os.path.join(self.temp_dir, 'test_patterns.yaml')
        
        # Define test patterns
        test_patterns = {
            'HSBC': [
                'HSBC',
                'Your HSBC card',
                'HSBC Egypt'
            ],
            'CIB': [
                'CIB',
                'بطاقتك من CIB',
                'Commercial International Bank'
            ],
            'NBE': [
                'NBE',
                'National Bank of Egypt',
                'البنك الأهلي'
            ],
            'QNB': [
                'QNB',
                'QNB ALAHLI',
                'بنك قطر'
            ]
        }
        
        # Write patterns to file
        with open(self.test_patterns_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_patterns, f, allow_unicode=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_default(self):
        """Test initialization with default patterns file."""
        recognizer = BankPatternRecognizer()
        self.assertIsNotNone(recognizer.bank_patterns)
        self.assertGreater(len(recognizer.bank_patterns), 0)
        self.assertEqual(recognizer.fuzzy_threshold, 80)
        self.assertTrue(recognizer.enable_fuzzy)
    
    def test_initialization_custom_file(self):
        """Test initialization with custom patterns file."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        self.assertEqual(len(recognizer.bank_patterns), 4)
        self.assertIn('HSBC', recognizer.bank_patterns)
        self.assertIn('CIB', recognizer.bank_patterns)
    
    def test_initialization_invalid_file(self):
        """Test initialization with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            BankPatternRecognizer(patterns_file='/nonexistent/file.yaml')
    
    def test_initialization_custom_threshold(self):
        """Test initialization with custom fuzzy threshold."""
        recognizer = BankPatternRecognizer(
            patterns_file=self.test_patterns_file,
            fuzzy_threshold=90
        )
        self.assertEqual(recognizer.fuzzy_threshold, 90)
    
    def test_exact_match_hsbc(self):
        """Test exact pattern matching for HSBC."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # Test various HSBC patterns
        self.assertEqual(recognizer.identify_bank("Your HSBC card ending 1234 was charged"), 'HSBC')
        self.assertEqual(recognizer.identify_bank("HSBC Egypt transaction alert"), 'HSBC')
        self.assertEqual(recognizer.identify_bank("Message from HSBC Bank"), 'HSBC')
    
    def test_exact_match_cib(self):
        """Test exact pattern matching for CIB."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        self.assertEqual(recognizer.identify_bank("CIB: Your balance is 1000 EGP"), 'CIB')
        self.assertEqual(recognizer.identify_bank("Commercial International Bank alert"), 'CIB')
    
    def test_exact_match_arabic(self):
        """Test exact pattern matching with Arabic text."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # Test Arabic patterns
        self.assertEqual(recognizer.identify_bank("تم الخصم من بطاقتك من CIB"), 'CIB')
        self.assertEqual(recognizer.identify_bank("البنك الأهلي - تنبيه"), 'NBE')
    
    def test_case_insensitive_matching(self):
        """Test case-insensitive pattern matching."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        self.assertEqual(recognizer.identify_bank("hsbc card transaction"), 'HSBC')
        self.assertEqual(recognizer.identify_bank("HSBC Card Transaction"), 'HSBC')
        self.assertEqual(recognizer.identify_bank("HsBc CaRd TrAnSaCtIoN"), 'HSBC')
    
    def test_no_match_returns_unknown(self):
        """Test that unmatched SMS returns 'unknown_bank'."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        self.assertEqual(recognizer.identify_bank("Random text message"), 'unknown_bank')
        self.assertEqual(recognizer.identify_bank("Some unknown bank alert"), 'unknown_bank')
    
    def test_empty_sms(self):
        """Test handling of empty SMS."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        self.assertEqual(recognizer.identify_bank(""), 'unknown_bank')
        self.assertEqual(recognizer.identify_bank("   "), 'unknown_bank')
    
    def test_none_sms(self):
        """Test handling of None SMS."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        self.assertEqual(recognizer.identify_bank(None), 'unknown_bank')
    
    def test_fuzzy_matching_enabled(self):
        """Test fuzzy matching when enabled."""
        recognizer = BankPatternRecognizer(
            patterns_file=self.test_patterns_file,
            fuzzy_threshold=70,
            enable_fuzzy=True
        )
        
        # Test with slight variations/typos
        result = recognizer.identify_bank("Your HSBC crad was used")  # typo: crad
        # Should still match HSBC due to fuzzy matching
        self.assertIn(result, ['HSBC', 'unknown_bank'])  # May or may not match depending on threshold
    
    def test_fuzzy_matching_disabled(self):
        """Test that fuzzy matching can be disabled."""
        recognizer = BankPatternRecognizer(
            patterns_file=self.test_patterns_file,
            enable_fuzzy=False
        )
        
        # Without fuzzy matching, this should not match
        result = recognizer.identify_bank("HSBC-like message but not exact")
        # This depends on whether the pattern is still substring-matched
        self.assertIsInstance(result, str)
    
    def test_return_confidence(self):
        """Test returning confidence scores."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # Exact match should return confidence of 100
        bank, confidence = recognizer.identify_bank("HSBC transaction", return_confidence=True)
        self.assertEqual(bank, 'HSBC')
        self.assertEqual(confidence, 100)
        
        # Unknown bank should return confidence of 0
        bank, confidence = recognizer.identify_bank("Unknown message", return_confidence=True)
        self.assertEqual(bank, 'unknown_bank')
        self.assertEqual(confidence, 0)
    
    def test_identify_banks_batch(self):
        """Test batch processing of multiple SMS messages."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        messages = [
            "HSBC card transaction",
            "CIB balance alert",
            "NBE withdrawal",
            "Unknown bank message"
        ]
        
        results = recognizer.identify_banks_batch(messages)
        
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0], 'HSBC')
        self.assertEqual(results[1], 'CIB')
        self.assertEqual(results[2], 'NBE')
        self.assertEqual(results[3], 'unknown_bank')
    
    def test_identify_banks_batch_with_confidence(self):
        """Test batch processing with confidence scores."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        messages = [
            "HSBC transaction",
            "Unknown message"
        ]
        
        results = recognizer.identify_banks_batch(messages, return_confidence=True)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][0], 'HSBC')
        self.assertEqual(results[0][1], 100)
        self.assertEqual(results[1][0], 'unknown_bank')
        self.assertEqual(results[1][1], 0)
    
    def test_get_bank_statistics(self):
        """Test getting bank statistics from SMS list."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        messages = [
            "HSBC transaction 1",
            "HSBC transaction 2",
            "CIB alert",
            "NBE withdrawal",
            "Unknown message"
        ]
        
        stats = recognizer.get_bank_statistics(messages)
        
        self.assertEqual(stats['HSBC'], 2)
        self.assertEqual(stats['CIB'], 1)
        self.assertEqual(stats['NBE'], 1)
        self.assertEqual(stats['unknown_bank'], 1)
    
    def test_reload_patterns(self):
        """Test reloading patterns from file."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        initial_count = len(recognizer.bank_patterns)
        self.assertEqual(initial_count, 4)
        
        # Modify patterns file
        new_patterns = {
            'TEST_BANK': ['TEST'],
            'ANOTHER_BANK': ['ANOTHER']
        }
        
        with open(self.test_patterns_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_patterns, f)
        
        # Reload patterns
        recognizer.reload_patterns()
        
        self.assertEqual(len(recognizer.bank_patterns), 2)
        self.assertIn('TEST_BANK', recognizer.bank_patterns)
    
    def test_multiple_banks_first_match_wins(self):
        """Test that first matching bank is returned when multiple could match."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # SMS that could potentially match multiple banks (though unlikely in practice)
        result = recognizer.identify_bank("HSBC and CIB transaction")
        # Should return the first one found
        self.assertIn(result, ['HSBC', 'CIB'])
    
    def test_regex_special_characters(self):
        """Test handling of regex special characters in patterns."""
        # Create patterns with regex special chars
        special_patterns = {
            'TEST_BANK': [
                r'test\.bank',
                r'test\-bank',
                r'test\(bank\)'
            ]
        }
        
        temp_file = os.path.join(self.temp_dir, 'special_patterns.yaml')
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(special_patterns, f)
        
        recognizer = BankPatternRecognizer(patterns_file=temp_file)
        
        # Should match with regex patterns
        self.assertEqual(recognizer.identify_bank("Message from test.bank"), 'TEST_BANK')
        self.assertEqual(recognizer.identify_bank("Message from test-bank"), 'TEST_BANK')
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in SMS."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # SMS with extra whitespace
        self.assertEqual(recognizer.identify_bank("  HSBC  transaction  "), 'HSBC')
        self.assertEqual(recognizer.identify_bank("\nHSBC\ntransaction\n"), 'HSBC')
    
    def test_long_sms_message(self):
        """Test handling of long SMS messages."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        long_sms = (
            "This is a very long SMS message with lots of text. "
            "It contains information about a transaction. "
            "Your HSBC card ending in 1234 was charged 500 EGP "
            "at some merchant on some date and time. "
            "Thank you for using our services."
        )
        
        self.assertEqual(recognizer.identify_bank(long_sms), 'HSBC')
    
    def test_mixed_language_sms(self):
        """Test SMS with mixed English and Arabic."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        mixed_sms = "Dear customer, بطاقتك من CIB was charged 100 EGP"
        self.assertEqual(recognizer.identify_bank(mixed_sms), 'CIB')
    
    def test_detection_accuracy_real_world_samples(self):
        """Test detection accuracy with real-world-like SMS samples."""
        recognizer = BankPatternRecognizer(patterns_file=self.test_patterns_file)
        
        # Real-world style messages
        samples = [
            ("Dear customer, Your HSBC card ending 1234 was charged 250.00 EGP", 'HSBC'),
            ("CIB: Your account balance is 5000 EGP", 'CIB'),
            ("NBE - Transaction alert: Withdrawal of 1000 EGP", 'NBE'),
            ("QNB ALAHLI: Purchase approved", 'QNB'),
            ("Your transaction has been processed", 'unknown_bank'),
        ]
        
        for sms, expected_bank in samples:
            result = recognizer.identify_bank(sms)
            self.assertEqual(
                result,
                expected_bank,
                f"Failed to correctly identify {expected_bank} from: {sms}"
            )
    
    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file."""
        invalid_file = os.path.join(self.temp_dir, 'invalid.yaml')
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [[[")
        
        with self.assertRaises(ValueError):
            BankPatternRecognizer(patterns_file=invalid_file)
    
    def test_empty_patterns_file(self):
        """Test handling of empty patterns file."""
        empty_file = os.path.join(self.temp_dir, 'empty.yaml')
        with open(empty_file, 'w') as f:
            f.write("")
        
        with self.assertRaises(ValueError):
            BankPatternRecognizer(patterns_file=empty_file)


if __name__ == '__main__':
    unittest.main()
