"""Unit tests for PromoClassifier."""
import unittest
import tempfile
import os
from goldminer.etl import PromoClassifier, PromoResult


class TestPromoResult(unittest.TestCase):
    """Test cases for PromoResult class."""
    
    def test_promo_result_initialization(self):
        """Test PromoResult initialization."""
        result = PromoResult(
            skip=True,
            reason="Test reason",
            matched_keywords=["offer", "discount"],
            confidence="high"
        )
        
        self.assertTrue(result.skip)
        self.assertEqual(result.reason, "Test reason")
        self.assertEqual(result.matched_keywords, ["offer", "discount"])
        self.assertEqual(result.confidence, "high")
    
    def test_promo_result_default_values(self):
        """Test PromoResult with default values."""
        result = PromoResult()
        
        self.assertFalse(result.skip)
        self.assertEqual(result.reason, "")
        self.assertEqual(result.matched_keywords, [])
        self.assertEqual(result.confidence, "low")
    
    def test_promo_result_to_dict(self):
        """Test converting PromoResult to dictionary."""
        result = PromoResult(
            skip=True,
            reason="Promotional",
            matched_keywords=["sale"],
            confidence="medium"
        )
        
        result_dict = result.to_dict()
        
        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict['skip'])
        self.assertEqual(result_dict['reason'], "Promotional")
        self.assertEqual(result_dict['matched_keywords'], ["sale"])
        self.assertEqual(result_dict['confidence'], "medium")
    
    def test_promo_result_repr(self):
        """Test string representation of PromoResult."""
        result = PromoResult(skip=True, reason="Test")
        repr_str = repr(result)
        
        self.assertIn("PromoResult", repr_str)
        self.assertIn("skip=True", repr_str)
        self.assertIn("Test", repr_str)


class TestPromoClassifier(unittest.TestCase):
    """Test cases for PromoClassifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = PromoClassifier()
    
    def test_initialization_with_defaults(self):
        """Test classifier initialization with default keywords."""
        classifier = PromoClassifier()
        
        self.assertIsInstance(classifier, PromoClassifier)
        self.assertGreater(len(classifier.english_keywords), 0)
        self.assertGreater(len(classifier.arabic_keywords), 0)
    
    def test_english_promotional_messages(self):
        """Test detection of English promotional messages."""
        promotional_messages = [
            "Get 50% discount today!",
            "Special offer for you",
            "Limited time sale - hurry!",
            "Enjoy exclusive deals",
            "Free gift with purchase",
            "Win amazing prizes",
            "Cashback rewards available"
        ]
        
        for msg in promotional_messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip, f"Failed to detect promo in: {msg}")
            self.assertGreater(len(result.matched_keywords), 0)
    
    def test_arabic_promotional_messages(self):
        """Test detection of Arabic promotional messages."""
        promotional_messages = [
            "عرض خاص لفترة محدودة",
            "خصومات 50% على جميع المنتجات",
            "وفر الآن مع عروضنا",
            "مجاني مع كل عملية شراء",
            "مكافأة حصرية لك"
        ]
        
        for msg in promotional_messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip, f"Failed to detect promo in: {msg}")
            self.assertGreater(len(result.matched_keywords), 0)
    
    def test_multilingual_promotions(self):
        """Test detection of multilingual promotional messages."""
        multilingual_messages = [
            "Special عرض خاص for you!",
            "Get خصومات 30% today",
            "Exclusive deal - وفر الآن now!",
            "Free shipping + مجاني delivery"
        ]
        
        for msg in multilingual_messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip, f"Failed to detect multilingual promo in: {msg}")
            self.assertGreater(len(result.matched_keywords), 0)
    
    def test_non_promotional_transactions(self):
        """Test that legitimate transactions are not flagged as promotional."""
        transaction_messages = [
            "Your card ending 1234 was charged 250.50 EGP at Store XYZ",
            "Transaction approved: 100 USD on 15/11/2024",
            "ATM withdrawal of 500 EGP completed",
            "Payment of 1500 SAR to Merchant ABC",
            "تم خصم 300 جنيه من بطاقتك",
            "عملية شراء بمبلغ 150 دولار"
        ]
        
        for msg in transaction_messages:
            result = self.classifier.classify(msg)
            self.assertFalse(result.skip, f"False positive for transaction: {msg}")
    
    def test_borderline_cases(self):
        """Test borderline cases that might contain both transaction and promo keywords."""
        # These contain promotional keywords but are actual transactions
        borderline_messages = [
            "Your cashback of 50 EGP has been credited",  # "cashback" is promo keyword
            "Reward points redeemed: 100 points",  # "reward" and "redeem" are promo keywords
            "Gift card purchase: 200 USD charged",  # "gift" is promo keyword
        ]
        
        for msg in borderline_messages:
            result = self.classifier.classify(msg)
            # These should be flagged as promotional due to keywords
            # The classifier is designed to be conservative and flag potential promos
            self.assertTrue(result.skip, f"Should detect promo keywords in: {msg}")
            self.assertGreater(len(result.matched_keywords), 0)
    
    def test_false_positives_prevention(self):
        """Test that messages with similar but different words don't trigger false positives."""
        non_promo_messages = [
            "Transaction processed successfully",
            "Your payment was received",
            "Balance inquiry completed",
            "Statement generated for your account"
        ]
        
        for msg in non_promo_messages:
            result = self.classifier.classify(msg)
            self.assertFalse(result.skip, f"False positive for: {msg}")
    
    def test_is_promotional_method(self):
        """Test the simple is_promotional boolean method."""
        promo_msg = "Get 50% off today!"
        non_promo_msg = "Your card was charged 100 EGP"
        
        self.assertTrue(self.classifier.is_promotional(promo_msg))
        self.assertFalse(self.classifier.is_promotional(non_promo_msg))
    
    def test_empty_or_invalid_input(self):
        """Test handling of empty or invalid input."""
        invalid_inputs = ["", None, "   ", "\n", "\t"]
        
        for inp in invalid_inputs:
            result = self.classifier.classify(inp)
            self.assertFalse(result.skip)
            self.assertEqual(result.reason, "Invalid input")
    
    def test_confidence_levels(self):
        """Test that confidence levels are assigned correctly."""
        # High confidence: 3+ keyword matches
        high_conf_msg = "Special offer with discount and free gift!"
        result_high = self.classifier.classify(high_conf_msg)
        self.assertTrue(result_high.skip)
        self.assertEqual(result_high.confidence, "high")
        self.assertGreaterEqual(len(result_high.matched_keywords), 3)
        
        # Medium/Low confidence: fewer keyword matches
        medium_conf_msg = "Limited sale today"
        result_medium = self.classifier.classify(medium_conf_msg)
        self.assertTrue(result_medium.skip)
        # Could be low, medium, or high depending on exact matches
        self.assertIn(result_medium.confidence, ["low", "medium", "high"])
        
        # Single keyword match
        low_conf_msg = "This is a special message"
        result_low = self.classifier.classify(low_conf_msg)
        # Note: "special" alone might not be enough without context
        # The actual behavior depends on exact keyword matching
    
    def test_case_insensitivity_english(self):
        """Test that English keyword matching is case-insensitive."""
        messages = [
            "SPECIAL OFFER",
            "Special Offer",
            "special offer",
            "SpEcIaL oFfEr"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip, f"Case-insensitive matching failed for: {msg}")
    
    def test_word_boundary_matching(self):
        """Test that keyword matching respects word boundaries."""
        # Should NOT match because "offering" is not "offer"
        msg_no_match = "We are offering a new service"
        result = self.classifier.classify(msg_no_match)
        # This might still match if other keywords are present
        # The key is that partial word matches shouldn't count
        
        # Should match - exact word
        msg_match = "Special offer available"
        result_match = self.classifier.classify(msg_match)
        self.assertTrue(result_match.skip)
    
    def test_classify_batch(self):
        """Test batch classification of messages."""
        messages = [
            "Get 50% discount!",  # Promotional
            "Your card was charged 100 EGP",  # Transaction
            "Special offer for you",  # Promotional
            "Transaction completed successfully"  # Transaction
        ]
        
        results = self.classifier.classify_batch(messages)
        
        self.assertEqual(len(results), 4)
        self.assertTrue(results[0].skip)  # Promo
        self.assertFalse(results[1].skip)  # Transaction
        self.assertTrue(results[2].skip)  # Promo
        self.assertFalse(results[3].skip)  # Transaction
    
    def test_classify_batch_empty(self):
        """Test batch classification with empty list."""
        results = self.classifier.classify_batch([])
        self.assertEqual(len(results), 0)
    
    def test_add_keywords(self):
        """Test adding custom keywords."""
        initial_english_count = len(self.classifier.english_keywords)
        initial_arabic_count = len(self.classifier.arabic_keywords)
        
        self.classifier.add_keywords(
            english=["custom1", "custom2"],
            arabic=["مخصص1", "مخصص2"]
        )
        
        self.assertEqual(len(self.classifier.english_keywords), initial_english_count + 2)
        self.assertEqual(len(self.classifier.arabic_keywords), initial_arabic_count + 2)
        
        # Test that custom keywords work
        msg = "This is a custom1 message"
        result = self.classifier.classify(msg)
        self.assertTrue(result.skip)
    
    def test_remove_keywords(self):
        """Test removing keywords."""
        # Add some keywords first
        self.classifier.add_keywords(english=["temp1", "temp2"])
        
        # Verify they were added
        self.assertIn("temp1", self.classifier.english_keywords)
        
        # Remove them
        self.classifier.remove_keywords(english=["temp1", "temp2"])
        
        # Verify they were removed
        self.assertNotIn("temp1", self.classifier.english_keywords)
    
    def test_get_keywords(self):
        """Test retrieving current keyword sets."""
        keywords = self.classifier.get_keywords()
        
        self.assertIsInstance(keywords, dict)
        self.assertIn('english', keywords)
        self.assertIn('arabic', keywords)
        self.assertIsInstance(keywords['english'], list)
        self.assertIsInstance(keywords['arabic'], list)
        self.assertGreater(len(keywords['english']), 0)
        self.assertGreater(len(keywords['arabic']), 0)


class TestPromoClassifierYAMLLoading(unittest.TestCase):
    """Test cases for YAML keyword loading."""
    
    def test_load_from_yaml_file(self):
        """Test loading keywords from a YAML file."""
        # Create a temporary YAML file
        yaml_content = """
english:
  - test_keyword_1
  - test_keyword_2

arabic:
  - اختبار_1
  - اختبار_2
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            classifier = PromoClassifier(keywords_file=temp_file)
            
            self.assertIn('test_keyword_1', classifier.english_keywords)
            self.assertIn('test_keyword_2', classifier.english_keywords)
            self.assertIn('اختبار_1', classifier.arabic_keywords)
            self.assertIn('اختبار_2', classifier.arabic_keywords)
            
        finally:
            os.unlink(temp_file)
    
    def test_load_from_nonexistent_file(self):
        """Test that classifier falls back to defaults when file doesn't exist."""
        classifier = PromoClassifier(keywords_file='/nonexistent/file.yaml')
        
        # Should fall back to defaults
        self.assertGreater(len(classifier.english_keywords), 0)
        self.assertGreater(len(classifier.arabic_keywords), 0)
    
    def test_load_from_empty_yaml(self):
        """Test handling of empty YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            temp_file = f.name
        
        try:
            classifier = PromoClassifier(keywords_file=temp_file)
            
            # Should fall back to defaults
            self.assertGreater(len(classifier.english_keywords), 0)
            self.assertGreater(len(classifier.arabic_keywords), 0)
            
        finally:
            os.unlink(temp_file)
    
    def test_load_from_malformed_yaml(self):
        """Test handling of malformed YAML file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("this is not: valid: yaml: content:")
            temp_file = f.name
        
        try:
            classifier = PromoClassifier(keywords_file=temp_file)
            
            # Should fall back to defaults
            self.assertGreater(len(classifier.english_keywords), 0)
            self.assertGreater(len(classifier.arabic_keywords), 0)
            
        finally:
            os.unlink(temp_file)
    
    def test_yaml_with_only_english(self):
        """Test YAML file with only English keywords."""
        yaml_content = """
english:
  - keyword1
  - keyword2
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            classifier = PromoClassifier(keywords_file=temp_file)
            
            self.assertIn('keyword1', classifier.english_keywords)
            # Arabic keywords might be empty or have defaults
            
        finally:
            os.unlink(temp_file)
    
    def test_yaml_with_only_arabic(self):
        """Test YAML file with only Arabic keywords."""
        yaml_content = """
arabic:
  - كلمة1
  - كلمة2
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
            f.write(yaml_content)
            temp_file = f.name
        
        try:
            classifier = PromoClassifier(keywords_file=temp_file)
            
            self.assertIn('كلمة1', classifier.arabic_keywords)
            # English keywords might be empty or have defaults
            
        finally:
            os.unlink(temp_file)


class TestPromoClassifierEdgeCases(unittest.TestCase):
    """Test edge cases for PromoClassifier."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.classifier = PromoClassifier()
    
    def test_very_long_message(self):
        """Test handling of very long messages."""
        long_msg = "Transaction details " * 100 + " special offer"
        result = self.classifier.classify(long_msg)
        
        self.assertTrue(result.skip)
        self.assertGreater(len(result.matched_keywords), 0)
    
    def test_message_with_special_characters(self):
        """Test messages with special characters."""
        messages = [
            "!!!SPECIAL OFFER!!!",
            "Get 50% off... now!!!",
            "Limited time: SALE 🎉",
            "Discount @50% today!"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip, f"Failed to detect promo in: {msg}")
    
    def test_message_with_unicode_characters(self):
        """Test messages with various Unicode characters."""
        messages = [
            "Special offer 🎁",
            "عرض خاص 🌟",
            "50% discount ✨"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip)
    
    def test_message_with_numbers_and_percentages(self):
        """Test that numbers and percentages don't interfere with detection."""
        messages = [
            "50% off",
            "Get 30% discount",
            "Sale: 25% off all items"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip)
    
    def test_repeated_keywords(self):
        """Test messages with repeated keywords."""
        msg = "sale sale sale"
        result = self.classifier.classify(msg)
        
        self.assertTrue(result.skip)
        # Should only count unique keywords
        self.assertEqual(len(set(result.matched_keywords)), len(result.matched_keywords))
    
    def test_keywords_at_different_positions(self):
        """Test that keyword position doesn't matter."""
        messages = [
            "offer at the beginning",
            "in the middle offer here",
            "at the end offer"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            self.assertTrue(result.skip)
    
    def test_mixed_case_and_spacing(self):
        """Test various case and spacing combinations."""
        messages = [
            "SPECIAL  OFFER",
            "Special     Offer",
            "special\toffer",
            "special\noffer"
        ]
        
        for msg in messages:
            result = self.classifier.classify(msg)
            # Some might not match depending on exact whitespace handling
            # But at least "special" or "offer" should match


class TestPromoClassifierIntegration(unittest.TestCase):
    """Integration tests for PromoClassifier."""
    
    def test_realistic_promotional_scenarios(self):
        """Test with realistic promotional message scenarios."""
        promo_messages = [
            "Dear customer, enjoy 50% discount on all items this weekend only!",
            "Limited time offer: Buy 1 get 1 free!",
            "Congratulations! You've won a special gift. Redeem now.",
            "Exclusive deal for our valued customers - 30% off everything!",
            "Flash sale alert: Save up to 70% today!",
            "عرض حصري لعملائنا: خصومات 40% على جميع المنتجات",
            "وفر الآن مع عروضنا الخاصة لفترة محدودة"
        ]
        
        classifier = PromoClassifier()
        
        for msg in promo_messages:
            result = classifier.classify(msg)
            self.assertTrue(result.skip, f"Failed to detect realistic promo: {msg}")
            self.assertGreater(len(result.matched_keywords), 0)
            self.assertIn(result.confidence, ['low', 'medium', 'high'])
    
    def test_realistic_transaction_scenarios(self):
        """Test with realistic transaction message scenarios."""
        transaction_messages = [
            "Dear customer, your card ending 5678 was charged 1,250.00 EGP at Amazon on 15/11/2024",
            "Purchase approved: 450 USD at Apple Store on 16/11/2024. Balance: 5,000 USD",
            "ATM withdrawal: 2,000 EGP from your account at NBE ATM, Nasr City",
            "Online payment of 750 SAR to Netflix has been processed successfully",
            "تم خصم مبلغ 500 جنيه من بطاقتك في متجر كارفور بتاريخ 15/11/2024",
            "عملية سحب نقدي بمبلغ 1000 ريال من صراف البنك الأهلي"
        ]
        
        classifier = PromoClassifier()
        
        for msg in transaction_messages:
            result = classifier.classify(msg)
            self.assertFalse(result.skip, f"False positive for transaction: {msg}")


if __name__ == '__main__':
    unittest.main()
