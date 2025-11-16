"""Unit tests for Categorizer."""
import unittest
import tempfile
from pathlib import Path
from goldminer.etl import Categorizer, TransactionRecord


class TestCategorizer(unittest.TestCase):
    """Test cases for Categorizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use default category_rules.yaml
        self.categorizer = Categorizer()
    
    def test_initialization_default_rules(self):
        """Test initialization with default rules file."""
        categorizer = Categorizer()
        self.assertIsNotNone(categorizer.rules)
        self.assertIn('categories', categorizer.rules)
        self.assertGreater(len(categorizer.rules['categories']), 0)
    
    def test_initialization_custom_threshold(self):
        """Test initialization with custom fuzzy threshold."""
        categorizer = Categorizer(fuzzy_threshold=85)
        self.assertEqual(categorizer.fuzzy_threshold, 85)
    
    def test_initialization_invalid_file(self):
        """Test initialization with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            Categorizer(rules_path='/nonexistent/rules.yaml')
    
    def test_exact_merchant_match(self):
        """Test exact merchant name matching."""
        record = TransactionRecord(
            id='test-1',
            payee="McDonald's",
            normalized_merchant="McDonald's"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
        self.assertIn('Dining', result.tags)
    
    def test_exact_merchant_match_case_insensitive(self):
        """Test exact merchant matching is case-insensitive."""
        record = TransactionRecord(
            id='test-2',
            payee="mcdonald's",
            normalized_merchant="mcdonald's"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_exact_merchant_match_multiple_merchants(self):
        """Test exact matching with various merchants."""
        test_cases = [
            ("Carrefour", "Food & Dining", "Groceries"),
            ("Zara", "Shopping", "Fashion & Apparel"),
            ("Uber", "Transportation", "Ride Share"),
            ("Netflix", "Entertainment", "Streaming Services"),
            ("Vodafone", "Utilities", "Telecommunications"),
        ]
        
        for merchant, expected_category, expected_subcategory in test_cases:
            with self.subTest(merchant=merchant):
                record = TransactionRecord(
                    id=f'test-{merchant}',
                    payee=merchant,
                    normalized_merchant=merchant
                )
                result = self.categorizer.categorize(record)
                self.assertEqual(result.category, expected_category)
                self.assertEqual(result.subcategory, expected_subcategory)
    
    def test_fuzzy_merchant_match(self):
        """Test fuzzy merchant name matching."""
        # Test with slightly misspelled merchant name
        record = TransactionRecord(
            id='test-3',
            payee="mcdonalds store",
            normalized_merchant="mcdonalds store"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_fuzzy_merchant_match_substring(self):
        """Test fuzzy matching with substring containment."""
        record = TransactionRecord(
            id='test-4',
            payee="Pizza Shop Downtown",
            normalized_merchant="Pizza Shop Downtown"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_fuzzy_merchant_match_below_threshold(self):
        """Test fuzzy matching fails below threshold."""
        # Create a categorizer with high threshold
        categorizer = Categorizer(fuzzy_threshold=95)
        
        record = TransactionRecord(
            id='test-5',
            payee="totally different store",
            normalized_merchant="totally different store"
        )
        
        result = categorizer.categorize(record)
        
        # Should fallback to uncategorized
        self.assertEqual(result.category, 'Uncategorized')
    
    def test_keyword_match_english(self):
        """Test keyword matching with English keywords."""
        record = TransactionRecord(
            id='test-6',
            payee="Local Restaurant Downtown",
            normalized_merchant="Local Restaurant Downtown"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_keyword_match_arabic(self):
        """Test keyword matching with Arabic keywords."""
        record = TransactionRecord(
            id='test-7',
            payee="مطعم المدينة",
            normalized_merchant="مطعم المدينة"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_keyword_match_multiple_keywords(self):
        """Test keyword matching with multiple keywords."""
        test_cases = [
            ("Supermarket Fresh", "Food & Dining", "Groceries"),
            ("Fashion Store", "Shopping", "Fashion & Apparel"),
            ("Electronics Shop", "Shopping", "Electronics"),
            ("Pharmacy Plus", "Healthcare", "Pharmacy"),
            ("Cinema Complex", "Entertainment", "Cinema & Events"),
        ]
        
        for merchant, expected_category, expected_subcategory in test_cases:
            with self.subTest(merchant=merchant):
                record = TransactionRecord(
                    id=f'test-{merchant}',
                    payee=merchant,
                    normalized_merchant=merchant
                )
                result = self.categorizer.categorize(record)
                self.assertEqual(result.category, expected_category)
                self.assertEqual(result.subcategory, expected_subcategory)
    
    def test_fallback_uncategorized(self):
        """Test fallback to uncategorized for unknown merchants."""
        record = TransactionRecord(
            id='test-8',
            payee="Unknown Merchant XYZ123",
            normalized_merchant="Unknown Merchant XYZ123"
        )
        
        result = self.categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Uncategorized')
        self.assertEqual(result.subcategory, 'General')
        self.assertIn('Uncategorized', result.tags)
    
    def test_priority_system_exact_over_fuzzy(self):
        """Test that exact match takes priority over fuzzy match."""
        # Add a record that could match both exact and fuzzy
        record = TransactionRecord(
            id='test-9',
            payee="Amazon",
            normalized_merchant="Amazon"
        )
        
        result = self.categorizer.categorize(record)
        
        # Should match exact merchant "Amazon"
        self.assertEqual(result.category, 'Shopping')
        self.assertEqual(result.subcategory, 'Electronics')
    
    def test_priority_system_fuzzy_over_keyword(self):
        """Test that fuzzy match takes priority over keyword match."""
        record = TransactionRecord(
            id='test-10',
            payee="Carrefur Market",  # Misspelled Carrefour
            normalized_merchant="Carrefur Market"
        )
        
        result = self.categorizer.categorize(record)
        
        # Should match fuzzy merchant "carrefour" rather than keyword "market"
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Groceries')
    
    def test_multiple_tags_assignment(self):
        """Test that multiple tags are assigned correctly."""
        record = TransactionRecord(
            id='test-11',
            payee="Carrefour",
            normalized_merchant="Carrefour",
            tags=['existing-tag']  # Existing tag
        )
        
        result = self.categorizer.categorize(record)
        
        # Should have both existing and new tags
        self.assertIn('existing-tag', result.tags)
        self.assertIn('Grocery', result.tags)
        self.assertIn('Household', result.tags)
    
    def test_empty_merchant_name(self):
        """Test handling of empty merchant name."""
        record = TransactionRecord(
            id='test-12',
            payee=None,
            normalized_merchant=None
        )
        
        result = self.categorizer.categorize(record)
        
        # Should fallback to uncategorized
        self.assertEqual(result.category, 'Uncategorized')
    
    def test_categorize_batch(self):
        """Test batch categorization."""
        records = [
            TransactionRecord(id='1', payee="McDonald's", normalized_merchant="McDonald's"),
            TransactionRecord(id='2', payee="Carrefour", normalized_merchant="Carrefour"),
            TransactionRecord(id='3', payee="Uber", normalized_merchant="Uber"),
            TransactionRecord(id='4', payee="Unknown", normalized_merchant="Unknown"),
        ]
        
        results = self.categorizer.categorize_batch(records)
        
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].category, 'Food & Dining')
        self.assertEqual(results[1].category, 'Food & Dining')
        self.assertEqual(results[2].category, 'Transportation')
        self.assertEqual(results[3].category, 'Uncategorized')
    
    def test_category_statistics(self):
        """Test generation of category statistics."""
        records = [
            TransactionRecord(id='1', category='Food & Dining', subcategory='Restaurants'),
            TransactionRecord(id='2', category='Food & Dining', subcategory='Groceries'),
            TransactionRecord(id='3', category='Food & Dining', subcategory='Restaurants'),
            TransactionRecord(id='4', category='Shopping', subcategory='Electronics'),
            TransactionRecord(id='5', category='Uncategorized', subcategory='General'),
        ]
        
        stats = self.categorizer.get_category_statistics(records)
        
        self.assertEqual(stats['total_records'], 5)
        self.assertEqual(stats['uncategorized_count'], 1)
        self.assertEqual(stats['uncategorized_percentage'], 20.0)
        self.assertEqual(stats['categories']['Food & Dining']['count'], 3)
        self.assertEqual(stats['categories']['Shopping']['count'], 1)
    
    def test_category_statistics_empty_list(self):
        """Test statistics with empty record list."""
        stats = self.categorizer.get_category_statistics([])
        
        self.assertEqual(stats['total_records'], 0)
        self.assertEqual(stats['uncategorized_count'], 0)
        self.assertEqual(stats['uncategorized_percentage'], 0.0)
    
    def test_arabic_merchant_name(self):
        """Test categorization with Arabic merchant names."""
        test_cases = [
            ("صيدلية العزبي", "Healthcare", "Pharmacy"),
            ("سينما فوكس", "Entertainment", "Cinema & Events"),
            ("بقالة المدينة", "Food & Dining", "Groceries"),
        ]
        
        for merchant, expected_category, expected_subcategory in test_cases:
            with self.subTest(merchant=merchant):
                record = TransactionRecord(
                    id=f'test-arabic-{merchant}',
                    payee=merchant,
                    normalized_merchant=merchant
                )
                result = self.categorizer.categorize(record)
                self.assertEqual(result.category, expected_category)
                self.assertEqual(result.subcategory, expected_subcategory)
    
    def test_mixed_language_merchant(self):
        """Test categorization with mixed English/Arabic names."""
        record = TransactionRecord(
            id='test-13',
            payee="Pharmacy صيدلية",
            normalized_merchant="Pharmacy صيدلية"
        )
        
        result = self.categorizer.categorize(record)
        
        # Should match either English or Arabic keyword
        self.assertEqual(result.category, 'Healthcare')
        self.assertEqual(result.subcategory, 'Pharmacy')
    
    def test_categorization_accuracy_real_world(self):
        """Test categorization accuracy with real-world examples."""
        # Real-world-like transaction examples
        records = [
            TransactionRecord(id='1', payee='MCDonalds Nasr City', normalized_merchant='MCDonalds Nasr City'),
            TransactionRecord(id='2', payee='CARREFOUR MAADI', normalized_merchant='CARREFOUR MAADI'),
            TransactionRecord(id='3', payee='Uber Trip', normalized_merchant='Uber Trip'),
            TransactionRecord(id='4', payee='Amazon.com Purchase', normalized_merchant='Amazon.com Purchase'),
            TransactionRecord(id='5', payee='Ezaby Pharmacy', normalized_merchant='Ezaby Pharmacy'),
            TransactionRecord(id='6', payee='VOX Cinema', normalized_merchant='VOX Cinema'),
            TransactionRecord(id='7', payee='Shell Gas Station', normalized_merchant='Shell Gas Station'),
            TransactionRecord(id='8', payee='Vodafone Recharge', normalized_merchant='Vodafone Recharge'),
        ]
        
        results = self.categorizer.categorize_batch(records)
        
        # All should be categorized (none should be Uncategorized)
        categorized_count = sum(1 for r in results if r.category != 'Uncategorized')
        self.assertGreaterEqual(categorized_count, 7)  # At least 7 out of 8 should be categorized
    
    def test_custom_rules_file(self):
        """Test initialization with custom rules file."""
        # Create a temporary rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
categories:
  - category: "Test Category"
    subcategory: "Test Subcategory"
    tags:
      - "Test"
    merchant_exact:
      - "TestMerchant"
    keywords:
      english:
        - "testword"

fallback:
  category: "Custom Uncategorized"
  subcategory: "Custom General"
  tags:
    - "Custom"
""")
            temp_file = f.name
        
        try:
            categorizer = Categorizer(rules_path=temp_file)
            
            # Test with custom rules
            record = TransactionRecord(
                id='test-custom',
                payee="TestMerchant",
                normalized_merchant="TestMerchant"
            )
            result = categorizer.categorize(record)
            
            self.assertEqual(result.category, 'Test Category')
            self.assertEqual(result.subcategory, 'Test Subcategory')
            
            # Test fallback
            record2 = TransactionRecord(
                id='test-custom-2',
                payee="Unknown",
                normalized_merchant="Unknown"
            )
            result2 = categorizer.categorize(record2)
            
            self.assertEqual(result2.category, 'Custom Uncategorized')
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_json_rules_file(self):
        """Test loading rules from JSON file."""
        # Create a temporary JSON rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            f.write("""{
  "categories": [
    {
      "category": "Test Category",
      "subcategory": "Test Subcategory",
      "tags": ["Test"],
      "merchant_exact": ["TestMerchant"],
      "keywords": {
        "english": ["testword"]
      }
    }
  ],
  "fallback": {
    "category": "Uncategorized",
    "subcategory": "General",
    "tags": ["Uncategorized"]
  }
}""")
            temp_file = f.name
        
        try:
            categorizer = Categorizer(rules_path=temp_file)
            
            record = TransactionRecord(
                id='test-json',
                payee="TestMerchant",
                normalized_merchant="TestMerchant"
            )
            result = categorizer.categorize(record)
            
            self.assertEqual(result.category, 'Test Category')
        finally:
            # Clean up
            Path(temp_file).unlink()


if __name__ == '__main__':
    unittest.main()
