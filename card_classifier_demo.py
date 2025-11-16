#!/usr/bin/env python3
"""
Demonstration of CardClassifier component for extracting card suffixes
and mapping them to account metadata.

This script shows:
1. Basic card suffix extraction from English and Arabic SMS
2. Account metadata lookup by card suffix
3. Complete SMS classification workflow
4. Integration with RegexParserEngine
"""

from goldminer.analysis import CardClassifier, RegexParserEngine


def print_section(title):
    """Print a formatted section title."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_extraction():
    """Demonstrate basic card suffix extraction."""
    print_section("Basic Card Suffix Extraction")
    
    test_cases = [
        "Transaction on card ending 1234",
        "HSBC card **5678 charged 100 EGP",
        "بطاقة رقم ١٢٣٤",
        "خصم من بطاقة ٥٦٧٨",
        "Card 9012 used at Amazon",
        "No card information here",
    ]
    
    for sms in test_cases:
        suffix = CardClassifier.extract_card_suffix(sms)
        print(f"\nSMS: {sms}")
        print(f"Extracted Suffix: {suffix if suffix else 'None'}")


def demo_account_lookup():
    """Demonstrate account metadata lookup."""
    print_section("Account Metadata Lookup")
    
    classifier = CardClassifier()
    
    test_suffixes = ["1234", "5678", "9999"]  # 9999 is unknown
    
    for suffix in test_suffixes:
        print(f"\n--- Looking up card suffix: {suffix} ---")
        account = classifier.lookup_account(suffix)
        
        print(f"Account ID: {account['account_id']}")
        print(f"Account Type: {account['account_type']}")
        print(f"Label: {account['label']}")
        print(f"Is Known: {account['is_known']}")
        
        if account['account_type'] == 'Credit':
            print(f"Interest Rate: {account['interest_rate']}%")
            print(f"Credit Limit: ${account['credit_limit']:,.2f}")
            print(f"Billing Cycle: Day {account['billing_cycle']}")


def demo_sms_classification():
    """Demonstrate complete SMS classification workflow."""
    print_section("Complete SMS Classification")
    
    classifier = CardClassifier()
    
    test_messages = [
        "HSBC: Transaction of 150.00 EGP on card ending 1234",
        "CIB: Debit of 200 EGP from card 5678",
        "خصم مبلغ ١٠٠ جنيه من بطاقة رقم ٤٣٢١",
        "Generic transaction with card **9999",
        "Transaction without card info",
    ]
    
    for sms in test_messages:
        print(f"\n--- Classifying SMS ---")
        print(f"SMS: {sms}")
        
        result = classifier.classify_sms(sms)
        
        print(f"\nExtracted Card Suffix: {result['card_suffix']}")
        print(f"Account ID: {result['account_id']}")
        print(f"Account Type: {result['account_type']}")
        print(f"Label: {result['label']}")
        print(f"Is Known Account: {result['is_known']}")


def demo_regex_parser_integration():
    """Demonstrate integration with RegexParserEngine."""
    print_section("Integration with RegexParserEngine")
    
    # Create parser with CardClassifier enabled (default)
    parser_enabled = RegexParserEngine(use_card_classifier=True)
    parser_disabled = RegexParserEngine(use_card_classifier=False)
    
    # Test SMS that CardClassifier can extract but template might miss
    test_sms = "HSBC: charged 100 EGP on Card **1234 at Amazon"
    
    print(f"\nTest SMS: {test_sms}\n")
    
    # Parse with CardClassifier enabled
    print("--- With CardClassifier Enabled ---")
    result_enabled = parser_enabled.parse_sms(test_sms, bank_id="HSBC")
    print(f"Amount: {result_enabled['amount']}")
    print(f"Currency: {result_enabled['currency']}")
    print(f"Card Suffix: {result_enabled['card_suffix']}")
    print(f"Confidence: {result_enabled['confidence']}")
    
    # Parse with CardClassifier disabled
    print("\n--- With CardClassifier Disabled ---")
    result_disabled = parser_disabled.parse_sms(test_sms, bank_id="HSBC")
    print(f"Amount: {result_disabled['amount']}")
    print(f"Currency: {result_disabled['currency']}")
    print(f"Card Suffix: {result_disabled['card_suffix']}")
    print(f"Confidence: {result_disabled['confidence']}")


def demo_arabic_indic_conversion():
    """Demonstrate Arabic-Indic numeral conversion."""
    print_section("Arabic-Indic Numeral Conversion")
    
    test_cases = [
        "١٢٣٤",
        "بطاقة رقم ٥٦٧٨",
        "مبلغ ١٢٣٫٤٥ جنيه",
        "٠١٢٣٤٥٦٧٨٩",
    ]
    
    for text in test_cases:
        converted = CardClassifier.convert_arabic_indic_numerals(text)
        print(f"\nOriginal: {text}")
        print(f"Converted: {converted}")


def main():
    """Run all demonstrations."""
    print("\n" + "█" * 70)
    print("  CardClassifier Component Demonstration")
    print("█" * 70)
    
    try:
        demo_basic_extraction()
        demo_account_lookup()
        demo_sms_classification()
        demo_regex_parser_integration()
        demo_arabic_indic_conversion()
        
        print("\n" + "█" * 70)
        print("  Demonstration Complete!")
        print("█" * 70 + "\n")
        
    except Exception as e:
        print(f"\nError during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
