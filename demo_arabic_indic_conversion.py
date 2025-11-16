#!/usr/bin/env python3
"""
Demonstration script for Arabic-Indic numeral conversion in RegexParserEngine.

This script showcases the new convert_arabic_indic_numerals() method and its
integration with SMS parsing for Arabic-language bank SMS messages.
"""

from goldminer.analysis.regex_parser_engine import RegexParserEngine


def demo_conversion_method():
    """Demonstrate the convert_arabic_indic_numerals() static method."""
    print("=" * 70)
    print("DEMO 1: Arabic-Indic Numeral Conversion Method")
    print("=" * 70)
    
    test_cases = [
        ("٠١٢٣٤٥٦٧٨٩", "All Arabic-Indic digits"),
        ("١٢٣", "Simple number"),
        ("١٥٠٫٥٠", "Decimal amount"),
        ("١٬٢٣٤٫٥٦", "Amount with thousands separator"),
        ("مبلغ ١٥٠٫٥٠ جنيه", "Arabic text with amount"),
        ("Amount: ١٥٠ EGP", "Mixed Arabic-English"),
        ("١٢٣ and 456", "Mixed Arabic-Indic and Western"),
        ("Card 1234 ABC", "Pure Latin (no conversion needed)"),
        ("٥٬٠٠٠٬٠٠٠", "Large number"),
        ("رقم: ١٢٣٤، التاريخ: ١٥/١١/٢٠٢٤", "Date with Arabic-Indic"),
    ]
    
    for text, description in test_cases:
        converted = RegexParserEngine.convert_arabic_indic_numerals(text)
        print(f"\n{description}:")
        print(f"  Input:  {text}")
        print(f"  Output: {converted}")
    
    print("\n")


def demo_sms_parsing():
    """Demonstrate SMS parsing with Arabic-Indic numerals."""
    print("=" * 70)
    print("DEMO 2: SMS Parsing with Arabic-Indic Numerals")
    print("=" * 70)
    
    parser = RegexParserEngine()
    
    test_sms = [
        {
            "sms": "تم خصم ١٥٠٫٥٠ جنيه من بطاقة رقم ٥٦٧٨",
            "bank": "HSBC",
            "description": "Arabic SMS with Arabic-Indic numerals and decimal"
        },
        {
            "sms": "Dear customer, خصم ٢٥٠ جنيه from card رقم ١٢٣٤",
            "bank": "HSBC",
            "description": "Mixed English/Arabic SMS"
        },
        {
            "sms": "خصم 300 جنيه من بطاقة رقم 9876",
            "bank": "HSBC",
            "description": "Arabic SMS with Western numerals (still works)"
        },
        {
            "sms": "خصم ١٠٠ جنيه بتاريخ ١٥/١١/٢٠٢٤",
            "bank": "HSBC",
            "description": "Arabic SMS with date in Arabic-Indic"
        },
        {
            "sms": "تم دفع ١٬٥٠٠ دولار في Amazon بتاريخ ٢٠/١١/٢٠٢٤",
            "bank": "HSBC",
            "description": "Large amount with thousands separator"
        },
    ]
    
    for i, test in enumerate(test_sms, 1):
        print(f"\nTest {i}: {test['description']}")
        print(f"SMS: {test['sms']}")
        
        result = parser.parse_sms(test['sms'], bank_id=test['bank'])
        
        print(f"Parsed Results:")
        print(f"  Amount:        {result['amount']}")
        print(f"  Currency:      {result['currency']}")
        print(f"  Card Suffix:   {result['card_suffix']}")
        print(f"  Date:          {result['date']}")
        print(f"  Payee:         {result['payee']}")
        print(f"  Confidence:    {result['confidence']}")
    
    print("\n")


def demo_batch_processing():
    """Demonstrate batch processing with mixed numeral formats."""
    print("=" * 70)
    print("DEMO 3: Batch Processing with Mixed Numeral Formats")
    print("=" * 70)
    
    parser = RegexParserEngine()
    
    messages = [
        "تم خصم ١٥٠ جنيه من بطاقة رقم ٥٦٧٨",
        "خصم ٢٥٠ جنيه في محل ABC",
        "Card ending 1234 charged 300 EGP",
        "دفع ٤٠٠٫٧٥ دولار",
    ]
    
    bank_ids = ['HSBC', 'HSBC', 'HSBC', 'HSBC']
    
    print(f"\nProcessing {len(messages)} SMS messages...\n")
    
    results = parser.parse_sms_batch(messages, bank_ids=bank_ids)
    
    for i, (msg, result) in enumerate(zip(messages, results), 1):
        print(f"Message {i}: {msg}")
        print(f"  → Amount: {result['amount']}, "
              f"Currency: {result['currency']}, "
              f"Card: {result['card_suffix']}")
    
    print("\n")


def demo_edge_cases():
    """Demonstrate handling of edge cases."""
    print("=" * 70)
    print("DEMO 4: Edge Cases and Special Scenarios")
    print("=" * 70)
    
    edge_cases = [
        ("", "Empty string"),
        (None, "None value"),
        ("   ", "Whitespace only"),
        ("مرحبا hello", "No numerals to convert"),
        ("Amount: ١٥٠٫٥٠ (pending)", "With special characters"),
        ("٠٫٠١", "Very small decimal"),
        ("٩٩٩٬٩٩٩٫٩٩", "Maximum format"),
    ]
    
    for text, description in edge_cases:
        print(f"\n{description}:")
        print(f"  Input:  {repr(text)}")
        converted = RegexParserEngine.convert_arabic_indic_numerals(text)
        print(f"  Output: {repr(converted)}")
    
    print("\n")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" Arabic-Indic Numeral Conversion Demo")
    print(" RegexParserEngine Enhancement")
    print("=" * 70)
    print()
    
    demo_conversion_method()
    demo_sms_parsing()
    demo_batch_processing()
    demo_edge_cases()
    
    print("=" * 70)
    print("Demo completed successfully!")
    print("=" * 70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ Arabic-Indic digits (٠-٩) → Western digits (0-9)")
    print("  ✓ Arabic decimal separator (٫) → Western (.)")
    print("  ✓ Arabic thousands separator (٬) → Western (,)")
    print("  ✓ Mixed-language string handling")
    print("  ✓ Automatic conversion in SMS parsing")
    print("  ✓ Batch processing support")
    print("  ✓ Edge case handling")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
