"""Unit tests for RegexParserEngine."""
import unittest
import tempfile
import os
import yaml
import json
from goldminer.analysis import RegexParserEngine


class TestRegexParserEngine(unittest.TestCase):
    """Test cases for RegexParserEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary templates file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_templates_file = os.path.join(self.temp_dir, 'test_templates.yaml')
        
        # Define test templates with context-aware patterns
        test_templates = {
            'HSBC': [
                {
                    'name': 'HSBC Standard',
                    'patterns': {
                        'amount': r'(?:charged|debited|paid|amount|of)\s+(?P<amount>\d+(?:[.,]\d{2})?)',
                        'currency': r'(?P<amount_val>\d+(?:[.,]\d{2})?)\s+(?P<currency>EGP|USD|EUR)',
                        'date': r'(?:on|date)\s+(?P<date>\d{2}/\d{2}/\d{4})',
                        'payee': r'at\s+(?P<payee>[A-Za-z0-9\s]+?)(?:\s+on|\.|$)',
                        'transaction_type': r'(?P<transaction_type>POS|ATM|Online)',
                        'card_suffix': r'ending\s+(?P<card_suffix>\d{4})'
                    },
                    'required_fields': ['amount', 'currency']
                },
                {
                    'name': 'HSBC Arabic',
                    'patterns': {
                        'amount': r'(?:خصم|دفع|مبلغ)\s+(?P<amount>\d+(?:[.,]\d{2})?)',
                        'currency': r'(?P<amount_val>\d+(?:[.,]\d{2})?)\s+(?P<currency>جنيه|دولار)',
                        'date': r'(?:في|بتاريخ)\s+(?P<date>\d{2}/\d{2}/\d{4})',
                        'payee': r'في\s+(?P<payee>[\u0600-\u06FFa-zA-Z0-9\s]+?)(?:\s|$)',
                        'transaction_type': r'(?P<transaction_type>صراف|شراء)',
                        'card_suffix': r'رقم\s+(?P<card_suffix>\d{4})'
                    },
                    'required_fields': ['amount']
                }
            ],
            'CIB': [
                {
                    'name': 'CIB Standard',
                    'patterns': {
                        'amount': r'(?:charged|of|amount|Purchase|Withdrawal)\s+(?P<amount>\d+(?:[.,]\d{2})?)',
                        'currency': r'(?P<amount_val>\d+(?:[.,]\d{2})?)\s+(?P<currency>EGP|USD)',
                        'date': r'(?:on|date)\s+(?P<date>\d{2}/\d{2}/\d{4})',
                        'payee': r'from\s+(?P<payee>[A-Za-z0-9\s]+?)(?:\s|\.|,)',
                        'transaction_type': r'(?P<transaction_type>Purchase|Withdrawal)',
                        'card_suffix': r'card ending\s+(?P<card_suffix>\d{4})'
                    },
                    'required_fields': ['amount', 'currency']
                }
            ],
            'Generic_Bank': [
                {
                    'name': 'Generic',
                    'patterns': {
                        'amount': r'(?:charged|debited|amount|transaction|of|paid)\s+(?P<amount>\d+(?:[.,]\d{2})?)',
                        'currency': r'(?P<amount_val>\d+(?:[.,]\d{2})?)\s+(?P<currency>EGP|USD|EUR|GBP)',
                        'date': r'(?:on|date)\s+(?P<date>\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})',
                        'transaction_type': r'(?P<transaction_type>POS|ATM|Online|Purchase)',
                    },
                    'required_fields': ['amount']
                }
            ]
        }
        
        # Write templates to file
        with open(self.test_templates_file, 'w', encoding='utf-8') as f:
            yaml.dump(test_templates, f, allow_unicode=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization_default(self):
        """Test initialization with default templates file."""
        parser = RegexParserEngine()
        self.assertIsNotNone(parser.templates)
        self.assertGreater(len(parser.templates), 0)
    
    def test_initialization_custom_file(self):
        """Test initialization with custom templates file."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        self.assertEqual(len(parser.templates), 3)
        self.assertIn('HSBC', parser.templates)
        self.assertIn('CIB', parser.templates)
    
    def test_initialization_invalid_file(self):
        """Test initialization with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            RegexParserEngine(templates_file='/nonexistent/file.yaml')
    
    def test_parse_hsbc_english(self):
        """Test parsing HSBC English SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Your HSBC card ending 1234 was charged 250.50 EGP at Store XYZ on 15/11/2024"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '250.50')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '1234')
        self.assertEqual(result['date'], '15/11/2024')
        self.assertIn(result['payee'], ['Store XYZ', 'Store XYZ on'])
        self.assertEqual(result['confidence'], 'high')
    
    def test_parse_hsbc_arabic(self):
        """Test parsing HSBC Arabic SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "تم خصم 150 جنيه من بطاقة رقم 5678 في محل ABC"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '150')
        self.assertEqual(result['currency'], 'جنيه')
        self.assertEqual(result['card_suffix'], '5678')
        self.assertIsNotNone(result['payee'])
    
    def test_parse_cib_english(self):
        """Test parsing CIB English SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "CIB: Your card ending 9999 Purchase of 500 EGP from MERCHANT NAME."
        result = parser.parse_sms(sms, bank_id='CIB')
        
        self.assertEqual(result['amount'], '500')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '9999')
        self.assertEqual(result['transaction_type'], 'Purchase')
    
    def test_parse_without_bank_id(self):
        """Test parsing without specifying bank ID."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Card ending 1234 charged 100 EGP at Store"
        result = parser.parse_sms(sms)
        
        self.assertIsNotNone(result['matched_bank'])
        self.assertEqual(result['amount'], '100')
        self.assertEqual(result['currency'], 'EGP')
    
    def test_parse_partial_match(self):
        """Test parsing with partial information (low confidence)."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Transaction of 100"
        result = parser.parse_sms(sms, bank_id='Generic_Bank')
        
        self.assertEqual(result['amount'], '100')
        self.assertIsNone(result['currency'])
        self.assertEqual(result['confidence'], 'low')
    
    def test_parse_empty_sms(self):
        """Test parsing empty SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        result = parser.parse_sms("")
        self.assertEqual(result['confidence'], 'low')
        self.assertIsNone(result['amount'])
        
        result = parser.parse_sms("   ")
        self.assertEqual(result['confidence'], 'low')
    
    def test_parse_none_sms(self):
        """Test parsing None SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        result = parser.parse_sms(None)
        self.assertEqual(result['confidence'], 'low')
        self.assertIsNone(result['amount'])
    
    def test_parse_no_match(self):
        """Test parsing SMS that doesn't match any template."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Random text without transaction info"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['confidence'], 'low')
        self.assertIsNone(result['amount'])
    
    def test_parse_case_insensitive(self):
        """Test case-insensitive parsing."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "CARD ENDING 1234 CHARGED 100 EGP AT STORE"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '100')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '1234')
    
    def test_parse_amount_with_comma(self):
        """Test parsing amount with comma separator."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Card ending 1234 charged 1,234.56 EGP"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        # Should extract the digits before the comma
        self.assertIsNotNone(result['amount'])
    
    def test_parse_multiple_currencies(self):
        """Test parsing with different currencies."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        for currency in ['EGP', 'USD', 'EUR']:
            sms = f"Card ending 1234 charged 100 {currency}"
            result = parser.parse_sms(sms, bank_id='HSBC')
            self.assertEqual(result['currency'], currency)
    
    def test_parse_batch(self):
        """Test batch parsing of multiple SMS messages."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        messages = [
            "Card ending 1234 charged 100 EGP at Store",
            "Card ending 5678 charged 200 USD",
            "Transaction of 300 EGP"
        ]
        bank_ids = ['HSBC', 'HSBC', 'Generic_Bank']
        
        results = parser.parse_sms_batch(messages, bank_ids=bank_ids)
        
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['amount'], '100')
        self.assertEqual(results[1]['amount'], '200')
        self.assertEqual(results[2]['amount'], '300')
    
    def test_parse_batch_no_bank_ids(self):
        """Test batch parsing without bank IDs."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        messages = [
            "Card ending 1234 charged 100 EGP",
            "Transaction 200 USD"
        ]
        
        results = parser.parse_sms_batch(messages)
        
        self.assertEqual(len(results), 2)
        self.assertIsNotNone(results[0]['matched_bank'])
        self.assertIsNotNone(results[1]['matched_bank'])
    
    def test_parse_batch_mismatched_length(self):
        """Test batch parsing with mismatched bank_ids length."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        messages = ["SMS 1", "SMS 2"]
        bank_ids = ["HSBC"]  # Wrong length
        
        with self.assertRaises(ValueError):
            parser.parse_sms_batch(messages, bank_ids=bank_ids)
    
    def test_get_supported_banks(self):
        """Test getting list of supported banks."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        banks = parser.get_supported_banks()
        
        self.assertIsInstance(banks, list)
        self.assertIn('HSBC', banks)
        self.assertIn('CIB', banks)
        self.assertEqual(len(banks), 3)
    
    def test_get_bank_templates(self):
        """Test getting templates for a specific bank."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        templates = parser.get_bank_templates('HSBC')
        
        self.assertIsInstance(templates, list)
        self.assertEqual(len(templates), 2)
        self.assertIn('HSBC Standard', templates)
        self.assertIn('HSBC Arabic', templates)
    
    def test_get_bank_templates_invalid(self):
        """Test getting templates for invalid bank."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        with self.assertRaises(ValueError):
            parser.get_bank_templates('INVALID_BANK')
    
    def test_reload_templates(self):
        """Test reloading templates from file."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        initial_banks = parser.get_supported_banks()
        self.assertEqual(len(initial_banks), 3)
        
        # Modify templates file
        new_templates = {
            'TEST_BANK': [
                {
                    'name': 'Test',
                    'patterns': {
                        'amount': r'(?P<amount>\d+)'
                    },
                    'required_fields': ['amount']
                }
            ]
        }
        
        with open(self.test_templates_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_templates, f)
        
        # Reload templates
        parser.reload_templates()
        
        banks = parser.get_supported_banks()
        self.assertEqual(len(banks), 1)
        self.assertIn('TEST_BANK', banks)
    
    def test_confidence_calculation_high(self):
        """Test confidence calculation for high confidence match."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Card ending 1234 charged 100.00 EGP at Store on 15/11/2024 POS"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        # Should have high confidence with most fields extracted
        self.assertEqual(result['confidence'], 'high')
    
    def test_confidence_calculation_low(self):
        """Test confidence calculation for low confidence match."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Transaction of 100"  # Missing required currency for HSBC
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        # Should have low confidence with missing required fields
        self.assertEqual(result['confidence'], 'low')
    
    def test_specific_template_name(self):
        """Test parsing with specific template name."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "تم خصم 150 جنيه في محل ABC"
        result = parser.parse_sms(sms, bank_id='HSBC', template_name='HSBC Arabic')
        
        self.assertEqual(result['amount'], '150')
        self.assertEqual(result['matched_template'], 'HSBC Arabic')
    
    def test_mixed_language_sms(self):
        """Test parsing SMS with mixed English and Arabic."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Dear customer, تم خصم 150 جنيه from your card"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '150')
        self.assertEqual(result['currency'], 'جنيه')
    
    def test_transaction_type_extraction(self):
        """Test extraction of transaction type."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        for txn_type in ['POS', 'ATM', 'Online']:
            sms = f"Card ending 1234 {txn_type} transaction 100 EGP"
            result = parser.parse_sms(sms, bank_id='HSBC')
            self.assertEqual(result['transaction_type'], txn_type)
    
    def test_date_format_extraction(self):
        """Test extraction of different date formats."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Transaction on 15/11/2024 for 100 EGP"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['date'], '15/11/2024')
    
    def test_payee_extraction(self):
        """Test extraction of payee/merchant name."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Card ending 1234 charged 100 EGP at Amazon Store on 15/11/2024"
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertIsNotNone(result['payee'])
        self.assertIn('Amazon Store', result['payee'])
    
    def test_invalid_bank_id(self):
        """Test parsing with invalid bank ID."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Transaction 100 EGP"
        result = parser.parse_sms(sms, bank_id='INVALID_BANK')
        
        self.assertEqual(result['confidence'], 'low')
        self.assertIsNone(result['amount'])
    
    def test_long_sms_message(self):
        """Test parsing long SMS message."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        long_sms = (
            "Dear valued customer, we would like to inform you that "
            "your HSBC card ending 1234 was charged 250.00 EGP "
            "at Super Market XYZ on 15/11/2024 for a POS transaction. "
            "Thank you for using our services."
        )
        
        result = parser.parse_sms(sms=long_sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '250.00')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '1234')
    
    def test_whitespace_handling(self):
        """Test proper handling of whitespace in SMS."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "  Card  ending  1234  charged  100  EGP  "
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '100')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '1234')
    
    def test_json_template_loading(self):
        """Test loading templates from JSON file."""
        json_file = os.path.join(self.temp_dir, 'test_templates.json')
        
        templates = {
            'TEST_BANK': [
                {
                    'name': 'Test Template',
                    'patterns': {
                        'amount': r'(?P<amount>\d+)',
                        'currency': r'(?P<currency>EGP)'
                    },
                    'required_fields': ['amount']
                }
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False)
        
        parser = RegexParserEngine(templates_file=json_file)
        
        self.assertEqual(len(parser.templates), 1)
        self.assertIn('TEST_BANK', parser.templates)
    
    def test_invalid_yaml_file(self):
        """Test handling of invalid YAML file."""
        invalid_file = os.path.join(self.temp_dir, 'invalid.yaml')
        with open(invalid_file, 'w') as f:
            f.write("invalid: yaml: content: [[[")
        
        with self.assertRaises(ValueError):
            RegexParserEngine(templates_file=invalid_file)
    
    def test_invalid_json_file(self):
        """Test handling of invalid JSON file."""
        invalid_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_file, 'w') as f:
            f.write("invalid json content {{{")
        
        with self.assertRaises(ValueError):
            RegexParserEngine(templates_file=invalid_file)
    
    def test_empty_templates_file(self):
        """Test handling of empty templates file."""
        empty_file = os.path.join(self.temp_dir, 'empty.yaml')
        with open(empty_file, 'w') as f:
            f.write("")
        
        with self.assertRaises(ValueError):
            RegexParserEngine(templates_file=empty_file)
    
    def test_real_world_hsbc_english(self):
        """Test with real-world HSBC English SMS example."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "Dear Customer, Your HSBC card ending 1234 was charged 250.50 EGP at Store XYZ on 15/11/2024."
        result = parser.parse_sms(sms, bank_id='HSBC')
        
        self.assertEqual(result['amount'], '250.50')
        self.assertEqual(result['currency'], 'EGP')
        self.assertEqual(result['card_suffix'], '1234')
        self.assertEqual(result['confidence'], 'high')
    
    def test_real_world_cib_arabic(self):
        """Test with real-world CIB Arabic SMS example."""
        parser = RegexParserEngine(templates_file=self.test_templates_file)
        
        sms = "عزيزي العميل، تم خصم 150 جنيه من بطاقة رقم 5678"
        result = parser.parse_sms(sms, bank_id='HSBC')  # Using HSBC Arabic template
        
        self.assertEqual(result['amount'], '150')
        self.assertEqual(result['currency'], 'جنيه')


if __name__ == '__main__':
    unittest.main()
