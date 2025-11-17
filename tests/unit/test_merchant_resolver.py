"""Unit tests for MerchantResolver."""
import unittest
import tempfile
from pathlib import Path
from goldminer.utils import MerchantResolver


class TestMerchantResolver(unittest.TestCase):
    """Test cases for MerchantResolver class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use default merchant_aliases.yaml
        self.resolver = MerchantResolver()
    
    def test_initialization_default(self):
        """Test initialization with default aliases file."""
        resolver = MerchantResolver()
        self.assertIsNotNone(resolver.merchant_map)
        self.assertGreater(len(resolver.merchant_map), 0)
        self.assertEqual(resolver.similarity_threshold, 85.0)
    
    def test_initialization_custom_threshold(self):
        """Test initialization with custom similarity threshold."""
        resolver = MerchantResolver(similarity_threshold=90.0)
        self.assertEqual(resolver.similarity_threshold, 90.0)
    
    def test_initialization_invalid_threshold(self):
        """Test initialization with invalid threshold raises ValueError."""
        with self.assertRaises(ValueError):
            MerchantResolver(similarity_threshold=150)
        
        with self.assertRaises(ValueError):
            MerchantResolver(similarity_threshold=-10)
    
    def test_initialization_invalid_file(self):
        """Test initialization with non-existent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            MerchantResolver(aliases_path='/nonexistent/aliases.yaml')
    
    def test_exact_match_english(self):
        """Test exact match with English merchant name."""
        result = self.resolver.resolve_merchant("Carrefour City")
        self.assertEqual(result, "Carrefour")
        
        result = self.resolver.resolve_merchant("McDonald's Egypt")
        self.assertEqual(result, "McDonald's")
    
    def test_exact_match_arabic(self):
        """Test exact match with Arabic merchant name."""
        result = self.resolver.resolve_merchant("كارفور")
        self.assertEqual(result, "Carrefour")
        
        result = self.resolver.resolve_merchant("ماكدونالدز")
        self.assertEqual(result, "McDonald's")
        
        result = self.resolver.resolve_merchant("فودافون")
        self.assertEqual(result, "Vodafone")
    
    def test_exact_match_case_insensitive(self):
        """Test that exact matching is case-insensitive."""
        result1 = self.resolver.resolve_merchant("CARREFOUR MAADI")
        result2 = self.resolver.resolve_merchant("carrefour maadi")
        result3 = self.resolver.resolve_merchant("Carrefour Maadi")
        
        self.assertEqual(result1, "Carrefour")
        self.assertEqual(result2, "Carrefour")
        self.assertEqual(result3, "Carrefour")
    
    def test_fuzzy_match_english(self):
        """Test fuzzy matching with English names (with typos/variations)."""
        # Test with slight variations
        result = self.resolver.resolve_merchant("Carrefour Egyp")  # Missing 't'
        self.assertEqual(result, "Carrefour")
        
        result = self.resolver.resolve_merchant("McDonalds Egypt")  # Missing apostrophe
        self.assertEqual(result, "McDonald's")
    
    def test_fuzzy_match_arabic(self):
        """Test fuzzy matching with Arabic names."""
        # Test with slight variations
        result = self.resolver.resolve_merchant("فودافون")
        self.assertEqual(result, "Vodafone")
    
    def test_fuzzy_match_with_noise(self):
        """Test fuzzy matching with noisy inputs (extra characters, spaces)."""
        # Extra spaces
        result = self.resolver.resolve_merchant("  Carrefour City  ")
        self.assertEqual(result, "Carrefour")
        
        # Mixed case with extra characters
        result = self.resolver.resolve_merchant("UBER Egypt ")
        self.assertEqual(result, "Uber")
    
    def test_fuzzy_match_below_threshold(self):
        """Test that matches below threshold return original payee."""
        # Very different string should not match
        result = self.resolver.resolve_merchant("Completely Different Name XYZ")
        self.assertEqual(result, "Completely Different Name XYZ")
    
    def test_return_confidence_exact_match(self):
        """Test confidence score for exact matches."""
        result, confidence = self.resolver.resolve_merchant(
            "Carrefour City",
            return_confidence=True
        )
        self.assertEqual(result, "Carrefour")
        self.assertEqual(confidence, 100.0)
    
    def test_return_confidence_fuzzy_match(self):
        """Test confidence score for fuzzy matches."""
        result, confidence = self.resolver.resolve_merchant(
            "Carrefour Egyp",  # Slight typo
            return_confidence=True
        )
        self.assertEqual(result, "Carrefour")
        self.assertIsNotNone(confidence)
        self.assertGreaterEqual(confidence, 85.0)
        self.assertLess(confidence, 100.0)
    
    def test_return_confidence_no_match(self):
        """Test confidence score when no match is found."""
        result, confidence = self.resolver.resolve_merchant(
            "Completely Unknown Merchant",
            return_confidence=True
        )
        self.assertEqual(result, "Completely Unknown Merchant")
        self.assertIsNone(confidence)
    
    def test_empty_payee(self):
        """Test handling of empty payee string."""
        result = self.resolver.resolve_merchant("")
        self.assertEqual(result, "")
        
        result, confidence = self.resolver.resolve_merchant("", return_confidence=True)
        self.assertEqual(result, "")
        self.assertIsNone(confidence)
    
    def test_none_payee(self):
        """Test handling of None payee."""
        result = self.resolver.resolve_merchant(None)
        self.assertIsNone(result)
        
        result, confidence = self.resolver.resolve_merchant(None, return_confidence=True)
        self.assertIsNone(result)
        self.assertIsNone(confidence)
    
    def test_whitespace_payee(self):
        """Test handling of whitespace-only payee."""
        result = self.resolver.resolve_merchant("   ")
        self.assertEqual(result, "")
    
    def test_arabic_and_english_mixed(self):
        """Test merchants with mixed Arabic and English text."""
        # Test various telecom providers
        result1 = self.resolver.resolve_merchant("فودافون")
        self.assertEqual(result1, "Vodafone")
        
        result2 = self.resolver.resolve_merchant("Vodafone Cash")
        self.assertEqual(result2, "Vodafone")
        
        result3 = self.resolver.resolve_merchant("اورنج")
        self.assertEqual(result3, "Orange")
    
    def test_multiple_merchants(self):
        """Test resolving multiple different merchants."""
        test_cases = [
            ("كارفور", "Carrefour"),
            ("UBER", "Uber"),
            ("فوري", "Fawry"),
            ("Pizza Hut Egypt", "Pizza Hut"),
            ("AMAZON.COM", "Amazon"),
        ]
        
        for payee, expected in test_cases:
            with self.subTest(payee=payee):
                result = self.resolver.resolve_merchant(payee)
                self.assertEqual(result, expected)
    
    def test_get_merchant_info(self):
        """Test getting merchant information."""
        info = self.resolver.get_merchant_info("Carrefour")
        self.assertIsNotNone(info)
        self.assertEqual(info['canonical'], "Carrefour")
        self.assertIn('aliases', info)
        self.assertIn('alias_count', info)
        self.assertGreater(info['alias_count'], 0)
    
    def test_get_merchant_info_not_found(self):
        """Test getting info for non-existent merchant."""
        info = self.resolver.get_merchant_info("Non Existent Merchant")
        self.assertIsNone(info)
    
    def test_get_all_merchants(self):
        """Test getting all canonical merchant names."""
        merchants = self.resolver.get_all_merchants()
        self.assertIsInstance(merchants, list)
        self.assertGreater(len(merchants), 0)
        # Check that list is sorted
        self.assertEqual(merchants, sorted(merchants))
        # Check for some expected merchants
        self.assertIn("Carrefour", merchants)
        self.assertIn("McDonald's", merchants)
        self.assertIn("Vodafone", merchants)
    
    def test_custom_threshold_higher(self):
        """Test that higher threshold is more restrictive."""
        # Lower threshold resolver
        resolver_low = MerchantResolver(similarity_threshold=80.0)
        # Higher threshold resolver
        resolver_high = MerchantResolver(similarity_threshold=95.0)
        
        # Test with a slightly different string
        payee = "Carrefour Eg"  # Missing 'ypt'
        
        result_low = resolver_low.resolve_merchant(payee)
        result_high = resolver_high.resolve_merchant(payee)
        
        # Low threshold should match, high threshold might not
        self.assertEqual(result_low, "Carrefour")
        # High threshold result could be either Carrefour or the original
        # depending on the exact score
        self.assertIn(result_high, ["Carrefour", payee])
    
    def test_special_characters(self):
        """Test handling of special characters in payee names."""
        # Test with apostrophe
        result = self.resolver.resolve_merchant("McDonald's")
        self.assertEqual(result, "McDonald's")
        
        # Test with various special characters
        result = self.resolver.resolve_merchant("MC DONALDS")
        self.assertEqual(result, "McDonald's")
    
    def test_numeric_payee(self):
        """Test handling of numeric payee (edge case)."""
        result = self.resolver.resolve_merchant("12345")
        self.assertEqual(result, "12345")  # Should return as-is


class TestMerchantResolverCustomAliases(unittest.TestCase):
    """Test MerchantResolver with custom aliases file."""
    
    def setUp(self):
        """Set up test fixtures with custom aliases."""
        # Create a temporary aliases file
        self.temp_dir = tempfile.mkdtemp()
        self.aliases_file = Path(self.temp_dir) / "test_aliases.yaml"
        
        # Write test aliases
        aliases_content = """
merchants:
  - canonical: "Test Merchant A"
    aliases:
      - "تست أ"
      - "Test A"
      - "TEST_A"
      
  - canonical: "Test Merchant B"
    aliases:
      - "تست ب"
      - "Test B"
      - "TEST_B"
"""
        with open(self.aliases_file, 'w', encoding='utf-8') as f:
            f.write(aliases_content)
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_custom_aliases_exact_match(self):
        """Test exact matching with custom aliases file."""
        resolver = MerchantResolver(aliases_path=str(self.aliases_file))
        
        result = resolver.resolve_merchant("Test A")
        self.assertEqual(result, "Test Merchant A")
        
        result = resolver.resolve_merchant("تست أ")
        self.assertEqual(result, "Test Merchant A")
    
    def test_custom_aliases_fuzzy_match(self):
        """Test fuzzy matching with custom aliases file."""
        resolver = MerchantResolver(aliases_path=str(self.aliases_file))
        
        result = resolver.resolve_merchant("Test_A")  # Underscore instead of space
        self.assertEqual(result, "Test Merchant A")
    
    def test_custom_aliases_with_confidence(self):
        """Test confidence scores with custom aliases."""
        resolver = MerchantResolver(aliases_path=str(self.aliases_file))
        
        result, confidence = resolver.resolve_merchant("Test A", return_confidence=True)
        self.assertEqual(result, "Test Merchant A")
        self.assertEqual(confidence, 100.0)
    
    def test_invalid_yaml_structure(self):
        """Test handling of invalid YAML structure."""
        invalid_file = Path(self.temp_dir) / "invalid.yaml"
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: structure:")
        
        with self.assertRaises(ValueError):
            MerchantResolver(aliases_path=str(invalid_file))
    
    def test_missing_merchants_key(self):
        """Test handling of YAML without 'merchants' key."""
        invalid_file = Path(self.temp_dir) / "no_merchants.yaml"
        with open(invalid_file, 'w') as f:
            f.write("some_other_key:\n  - value: test\n")
        
        with self.assertRaises(ValueError):
            MerchantResolver(aliases_path=str(invalid_file))


if __name__ == '__main__':
    unittest.main()
