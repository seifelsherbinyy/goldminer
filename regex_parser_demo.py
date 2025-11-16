"""
RegexParserEngine demonstration script.

This script demonstrates the usage of RegexParserEngine for parsing
transaction SMS messages in both English and Arabic.
"""

from goldminer.analysis import RegexParserEngine


def print_result(sms, result):
    """Print parsing result in a formatted way."""
    print(f"\nSMS: {sms}")
    print("-" * 80)
    print(f"  Amount:           {result.get('amount', 'N/A')}")
    print(f"  Currency:         {result.get('currency', 'N/A')}")
    print(f"  Date:             {result.get('date', 'N/A')}")
    print(f"  Payee:            {result.get('payee', 'N/A')}")
    print(f"  Transaction Type: {result.get('transaction_type', 'N/A')}")
    print(f"  Card Suffix:      {result.get('card_suffix', 'N/A')}")
    print(f"  Confidence:       {result.get('confidence', 'N/A')}")
    print(f"  Matched Bank:     {result.get('matched_bank', 'N/A')}")
    print(f"  Matched Template: {result.get('matched_template', 'N/A')}")


def main():
    """Run the demonstration."""
    print("=" * 80)
    print("RegexParserEngine Demonstration")
    print("=" * 80)
    
    # Initialize the parser
    parser = RegexParserEngine()
    
    print(f"\nLoaded templates for {len(parser.get_supported_banks())} banks:")
    print(", ".join(parser.get_supported_banks()))
    
    # English SMS Examples
    print("\n" + "=" * 80)
    print("ENGLISH SMS EXAMPLES")
    print("=" * 80)
    
    english_examples = [
        ("HSBC", "Your HSBC card ending 1234 was charged 250.50 EGP at Amazon Store on 15/11/2024"),
        ("CIB", "CIB: Your card ending 5678 Purchase of 500.00 EGP from CARREFOUR on 14/11/2024."),
        ("NBE", "NBE Transaction: withdrawal of 1000 EGP from ATM on 13/11/2024 card 9999"),
        ("QNB", "QNB ALAHLI: Your card ending 4444 was charged 75.25 EGP at Gas Station on 12/11/2024"),
        ("Generic_Bank", "Transaction charged 100 EGP at Store on 10/11/2024"),
    ]
    
    for bank_id, sms in english_examples:
        result = parser.parse_sms(sms, bank_id=bank_id)
        print_result(sms, result)
    
    # Arabic SMS Examples
    print("\n" + "=" * 80)
    print("ARABIC SMS EXAMPLES")
    print("=" * 80)
    
    arabic_examples = [
        ("HSBC", "عزيزي العميل، تم خصم 150 جنيه من بطاقة رقم 1234 في محل الإلكترونيات"),
        ("CIB", "CIB: تم خصم 300 جنيه من بطاقتك في تاجر كارفور"),
        ("NBE", "البنك الأهلي: تم سحب 500 جنيه من صراف آلي بطاقة 8888"),
        ("Generic_Bank", "تم خصم 200 جنيه في المحل"),
    ]
    
    for bank_id, sms in arabic_examples:
        result = parser.parse_sms(sms, bank_id=bank_id)
        print_result(sms, result)
    
    # Mixed Language Example
    print("\n" + "=" * 80)
    print("MIXED LANGUAGE EXAMPLE")
    print("=" * 80)
    
    mixed_sms = "Dear customer, تم خصم 125.75 جنيه from your HSBC card"
    result = parser.parse_sms(mixed_sms, bank_id="HSBC")
    print_result(mixed_sms, result)
    
    # Auto-detect bank
    print("\n" + "=" * 80)
    print("AUTO-DETECT BANK (No bank_id specified)")
    print("=" * 80)
    
    auto_detect_sms = "Transaction charged 50 EGP at Cafe"
    result = parser.parse_sms(auto_detect_sms)
    print_result(auto_detect_sms, result)
    
    # Partial match with low confidence
    print("\n" + "=" * 80)
    print("PARTIAL MATCH (Low Confidence)")
    print("=" * 80)
    
    partial_sms = "Transaction of 25"
    result = parser.parse_sms(partial_sms, bank_id="Generic_Bank")
    print_result(partial_sms, result)
    
    # Batch processing
    print("\n" + "=" * 80)
    print("BATCH PROCESSING EXAMPLE")
    print("=" * 80)
    
    batch_sms = [
        "Card ending 1111 charged 100 EGP",
        "Card ending 2222 charged 200 USD",
        "Card ending 3333 charged 300 EUR"
    ]
    bank_ids = ["HSBC", "HSBC", "HSBC"]
    
    print("\nProcessing batch of 3 SMS messages...")
    results = parser.parse_sms_batch(batch_sms, bank_ids=bank_ids)
    
    for i, (sms, result) in enumerate(zip(batch_sms, results), 1):
        print(f"\n[{i}] {sms}")
        print(f"    Amount: {result['amount']}, Currency: {result['currency']}, "
              f"Card: {result['card_suffix']}, Confidence: {result['confidence']}")
    
    print("\n" + "=" * 80)
    print("Demonstration Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
