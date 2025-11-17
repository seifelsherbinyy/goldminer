"""Unit tests for Categorizer load_rules functionality."""
import unittest
import tempfile
from pathlib import Path
from goldminer.etl import Categorizer, TransactionRecord


class TestCategorizerLoadRules(unittest.TestCase):
    """Test cases for Categorizer load_rules method and new rule formats."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Use default category_rules.yaml
        self.categorizer = Categorizer()
    
    def test_load_rules_with_match(self):
        """Test loading rules with exact match key."""
        # Create a temporary rules file with new format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility"]
  - match: "Careem"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility", "MENA"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: ["Uncategorized"]
""")
            temp_file = f.name
        
        try:
            # Load the new rules
            self.categorizer.load_rules(temp_file)
            
            # Test exact match
            record1 = TransactionRecord(
                id='test-1',
                payee="Uber",
                normalized_merchant="Uber"
            )
            result1 = self.categorizer.categorize(record1)
            
            self.assertEqual(result1.category, 'Transport')
            self.assertEqual(result1.subcategory, 'Ride Hailing')
            self.assertIn('Mobility', result1.tags)
            
            # Test another exact match
            record2 = TransactionRecord(
                id='test-2',
                payee="Careem",
                normalized_merchant="Careem"
            )
            result2 = self.categorizer.categorize(record2)
            
            self.assertEqual(result2.category, 'Transport')
            self.assertEqual(result2.subcategory, 'Ride Hailing')
            self.assertIn('Mobility', result2.tags)
            self.assertIn('MENA', result2.tags)
            
        finally:
            # Clean up
            Path(temp_file).unlink()
    
    def test_load_rules_with_match_regex(self):
        """Test loading rules with regex match key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match_regex: ".*Vodafone.*"
    category: "Utilities"
    subcategory: "Telecom"
    tags: ["Recharge"]
  - match_regex: "^Amazon.*"
    category: "Shopping"
    subcategory: "Online"
    tags: ["E-commerce"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            # Test regex match
            record1 = TransactionRecord(
                id='test-1',
                payee="Vodafone Egypt",
                normalized_merchant="Vodafone Egypt"
            )
            result1 = self.categorizer.categorize(record1)
            
            self.assertEqual(result1.category, 'Utilities')
            self.assertEqual(result1.subcategory, 'Telecom')
            self.assertIn('Recharge', result1.tags)
            
            # Test another regex match
            record2 = TransactionRecord(
                id='test-2',
                payee="Amazon.com",
                normalized_merchant="Amazon.com"
            )
            result2 = self.categorizer.categorize(record2)
            
            self.assertEqual(result2.category, 'Shopping')
            self.assertEqual(result2.subcategory, 'Online')
            
        finally:
            Path(temp_file).unlink()
    
    def test_load_rules_with_match_tag(self):
        """Test loading rules with tag match key."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match_tag: "subscription"
    category: "Entertainment"
    subcategory: "Streaming"
    tags: ["Recurring"]
  - match_tag: "online"
    category: "Shopping"
    subcategory: "E-commerce"
    tags: ["Internet"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            # Test tag match
            record1 = TransactionRecord(
                id='test-1',
                payee="Netflix",
                normalized_merchant="Netflix",
                tags=["subscription", "entertainment"]
            )
            result1 = self.categorizer.categorize(record1)
            
            self.assertEqual(result1.category, 'Entertainment')
            self.assertEqual(result1.subcategory, 'Streaming')
            self.assertIn('Recurring', result1.tags)
            # Original tags should be preserved
            self.assertIn('subscription', result1.tags)
            self.assertIn('entertainment', result1.tags)
            
        finally:
            Path(temp_file).unlink()
    
    def test_rule_precedence_match_over_regex(self):
        """Test that exact match takes precedence over regex match."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Exact Match"]
  - match_regex: ".*Uber.*"
    category: "Transport"
    subcategory: "General Transport"
    tags: ["Regex Match"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            record = TransactionRecord(
                id='test-1',
                payee="Uber",
                normalized_merchant="Uber"
            )
            result = self.categorizer.categorize(record)
            
            # Should match exact rule, not regex
            self.assertEqual(result.category, 'Transport')
            self.assertEqual(result.subcategory, 'Ride Hailing')
            self.assertIn('Exact Match', result.tags)
            self.assertNotIn('Regex Match', result.tags)
            
        finally:
            Path(temp_file).unlink()
    
    def test_rule_precedence_regex_over_tag(self):
        """Test that regex match takes precedence over tag match."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match_regex: ".*Netflix.*"
    category: "Entertainment"
    subcategory: "Streaming"
    tags: ["Regex Match"]
  - match_tag: "subscription"
    category: "Services"
    subcategory: "Recurring"
    tags: ["Tag Match"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            record = TransactionRecord(
                id='test-1',
                payee="Netflix Premium",
                normalized_merchant="Netflix Premium",
                tags=["subscription"]
            )
            result = self.categorizer.categorize(record)
            
            # Should match regex rule, not tag rule
            self.assertEqual(result.category, 'Entertainment')
            self.assertEqual(result.subcategory, 'Streaming')
            self.assertIn('Regex Match', result.tags)
            self.assertNotIn('Tag Match', result.tags)
            
        finally:
            Path(temp_file).unlink()
    
    def test_rule_precedence_new_format_over_legacy(self):
        """Test that new format rules take precedence over legacy format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Amazon"
    category: "Shopping"
    subcategory: "Online"
    tags: ["New Format"]

categories:
  - category: "Marketplace"
    subcategory: "Legacy"
    tags: ["Legacy Format"]
    merchant_exact:
      - "Amazon"

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            record = TransactionRecord(
                id='test-1',
                payee="Amazon",
                normalized_merchant="Amazon"
            )
            result = self.categorizer.categorize(record)
            
            # Should match new format rule
            self.assertEqual(result.category, 'Shopping')
            self.assertEqual(result.subcategory, 'Online')
            self.assertIn('New Format', result.tags)
            
        finally:
            Path(temp_file).unlink()
    
    def test_load_rules_missing_file(self):
        """Test safe fallback when file is missing."""
        # Store original rules
        original_rules = self.categorizer.rules.copy()
        
        # Try to load non-existent file
        self.categorizer.load_rules('/nonexistent/file.yaml')
        
        # Rules should remain unchanged
        self.assertEqual(self.categorizer.rules, original_rules)
    
    def test_load_rules_malformed_yaml(self):
        """Test safe fallback when YAML is malformed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Test"
    category: "Test Category"
    invalid yaml syntax here: [unclosed bracket
""")
            temp_file = f.name
        
        try:
            # Store original rules
            original_rules = self.categorizer.rules.copy()
            
            # Try to load malformed file
            self.categorizer.load_rules(temp_file)
            
            # Rules should remain unchanged
            self.assertEqual(self.categorizer.rules, original_rules)
            
        finally:
            Path(temp_file).unlink()
    
    def test_load_rules_invalid_structure(self):
        """Test safe fallback when YAML structure is invalid."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
invalid_key:
  - some data
""")
            temp_file = f.name
        
        try:
            # Store original rules
            original_rules = self.categorizer.rules.copy()
            
            # Try to load file with invalid structure
            self.categorizer.load_rules(temp_file)
            
            # Rules should remain unchanged
            self.assertEqual(self.categorizer.rules, original_rules)
            
        finally:
            Path(temp_file).unlink()
    
    def test_reload_rules_at_runtime(self):
        """Test reloading rules at runtime."""
        # Create first rules file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "TestMerchant"
    category: "Category1"
    subcategory: "Sub1"
    tags: ["Tag1"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            # Load first rules
            self.categorizer.load_rules(temp_file)
            
            record = TransactionRecord(
                id='test-1',
                payee="TestMerchant",
                normalized_merchant="TestMerchant"
            )
            result1 = self.categorizer.categorize(record)
            
            self.assertEqual(result1.category, 'Category1')
            self.assertEqual(result1.subcategory, 'Sub1')
            
            # Update the rules file
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write("""
rules:
  - match: "TestMerchant"
    category: "Category2"
    subcategory: "Sub2"
    tags: ["Tag2"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            
            # Reload rules
            self.categorizer.load_rules(temp_file)
            
            # Test with same record - should get new categorization
            result2 = self.categorizer.categorize(record)
            
            self.assertEqual(result2.category, 'Category2')
            self.assertEqual(result2.subcategory, 'Sub2')
            self.assertIn('Tag2', result2.tags)
            
        finally:
            Path(temp_file).unlink()
    
    def test_multiple_match_types_in_single_file(self):
        """Test rules file with multiple match types."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility"]
  - match_regex: ".*Vodafone.*"
    category: "Utilities"
    subcategory: "Telecom"
    tags: ["Recharge"]
  - match_tag: "subscription"
    category: "Entertainment"
    subcategory: "Streaming"
    tags: ["Recurring"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            # Test exact match
            record1 = TransactionRecord(
                id='test-1',
                payee="Uber",
                normalized_merchant="Uber"
            )
            result1 = self.categorizer.categorize(record1)
            self.assertEqual(result1.category, 'Transport')
            
            # Test regex match
            record2 = TransactionRecord(
                id='test-2',
                payee="Vodafone Egypt",
                normalized_merchant="Vodafone Egypt"
            )
            result2 = self.categorizer.categorize(record2)
            self.assertEqual(result2.category, 'Utilities')
            
            # Test tag match
            record3 = TransactionRecord(
                id='test-3',
                payee="Netflix",
                normalized_merchant="Netflix",
                tags=["subscription"]
            )
            result3 = self.categorizer.categorize(record3)
            self.assertEqual(result3.category, 'Entertainment')
            
        finally:
            Path(temp_file).unlink()
    
    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            # Test with different case
            test_cases = ["UBER", "Uber", "uber", "UbEr"]
            
            for merchant in test_cases:
                with self.subTest(merchant=merchant):
                    record = TransactionRecord(
                        id=f'test-{merchant}',
                        payee=merchant,
                        normalized_merchant=merchant
                    )
                    result = self.categorizer.categorize(record)
                    
                    self.assertEqual(result.category, 'Transport')
                    self.assertEqual(result.subcategory, 'Ride Hailing')
            
        finally:
            Path(temp_file).unlink()
    
    def test_invalid_regex_pattern(self):
        """Test handling of invalid regex pattern."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match_regex: "[invalid(regex"
    category: "Invalid"
    subcategory: "Invalid"
    tags: []
  - match: "ValidMerchant"
    category: "Valid"
    subcategory: "Valid"
    tags: ["Valid"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            # Invalid regex should be skipped, valid rules should work
            record = TransactionRecord(
                id='test-1',
                payee="ValidMerchant",
                normalized_merchant="ValidMerchant"
            )
            result = self.categorizer.categorize(record)
            
            self.assertEqual(result.category, 'Valid')
            self.assertEqual(result.subcategory, 'Valid')
            
        finally:
            Path(temp_file).unlink()
    
    def test_backward_compatibility_legacy_format(self):
        """Test that legacy format still works after adding load_rules."""
        # Use default categorizer with legacy format
        categorizer = Categorizer()
        
        # Test a merchant from the legacy rules
        record = TransactionRecord(
            id='test-1',
            payee="McDonald's",
            normalized_merchant="McDonald's"
        )
        result = categorizer.categorize(record)
        
        self.assertEqual(result.category, 'Food & Dining')
        self.assertEqual(result.subcategory, 'Restaurants')
    
    def test_tags_merge_correctly(self):
        """Test that tags from rules merge with existing tags."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write("""
rules:
  - match: "Uber"
    category: "Transport"
    subcategory: "Ride Hailing"
    tags: ["Mobility", "RideShare"]

fallback:
  category: "Uncategorized"
  subcategory: "General"
  tags: []
""")
            temp_file = f.name
        
        try:
            self.categorizer.load_rules(temp_file)
            
            record = TransactionRecord(
                id='test-1',
                payee="Uber",
                normalized_merchant="Uber",
                tags=["ExistingTag1", "ExistingTag2"]
            )
            result = self.categorizer.categorize(record)
            
            # Should have both original and new tags
            self.assertIn("ExistingTag1", result.tags)
            self.assertIn("ExistingTag2", result.tags)
            self.assertIn("Mobility", result.tags)
            self.assertIn("RideShare", result.tags)
            
        finally:
            Path(temp_file).unlink()


if __name__ == '__main__':
    unittest.main()
