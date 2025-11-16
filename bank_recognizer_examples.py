"""
Example usage of BankPatternRecognizer for identifying banks from SMS messages.

This script demonstrates how to use the BankPatternRecognizer class to:
1. Identify banks from individual SMS messages
2. Process batches of SMS messages
3. Get bank statistics from a collection of messages
4. Use confidence scores for matching
"""
from goldminer.analysis import BankPatternRecognizer
from goldminer.etl import load_sms_messages


def example_basic_usage():
    """Demonstrate basic bank identification."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Bank Identification")
    print("=" * 70)
    
    # Initialize the recognizer
    recognizer = BankPatternRecognizer()
    
    # Sample SMS messages
    sample_messages = [
        "Dear customer, Your HSBC card ending 1234 was charged 250.00 EGP at Store XYZ",
        "CIB: Your account balance is 5,000.00 EGP. Thank you for banking with us.",
        "NBE - Transaction alert: Withdrawal of 1,000 EGP from ATM on 15/11/2025",
        "تم الخصم من بطاقتك من CIB بمبلغ 500 جنيه",
        "Your transaction has been processed successfully",
        "QNB ALAHLI: Purchase of 350 EGP approved at Merchant ABC",
    ]
    
    print("\nIdentifying banks from SMS messages:\n")
    for sms in sample_messages:
        bank_id = recognizer.identify_bank(sms)
        print(f"Bank: {bank_id:20s} | SMS: {sms[:60]}...")
    
    print()


def example_with_confidence():
    """Demonstrate bank identification with confidence scores."""
    print("=" * 70)
    print("EXAMPLE 2: Bank Identification with Confidence Scores")
    print("=" * 70)
    
    recognizer = BankPatternRecognizer()
    
    sample_messages = [
        "HSBC card transaction approved",
        "Your CIB account was updated",
        "Message from your bank",
    ]
    
    print("\nIdentifying banks with confidence scores:\n")
    for sms in sample_messages:
        bank_id, confidence = recognizer.identify_bank(sms, return_confidence=True)
        print(f"Bank: {bank_id:20s} | Confidence: {confidence:3d}% | SMS: {sms}")
    
    print()


def example_batch_processing():
    """Demonstrate batch processing of SMS messages."""
    print("=" * 70)
    print("EXAMPLE 3: Batch Processing")
    print("=" * 70)
    
    recognizer = BankPatternRecognizer()
    
    # Simulate loading multiple SMS messages
    messages = [
        "HSBC: Transaction 1",
        "HSBC: Transaction 2",
        "CIB: Balance inquiry",
        "NBE: Withdrawal alert",
        "QNB ALAHLI: Purchase notification",
        "Unknown bank message",
        "Commercial International Bank alert",
    ]
    
    print(f"\nProcessing {len(messages)} SMS messages in batch...\n")
    
    # Process all messages at once
    bank_ids = recognizer.identify_banks_batch(messages)
    
    # Display results
    for sms, bank in zip(messages, bank_ids):
        print(f"{bank:20s} | {sms}")
    
    print()


def example_statistics():
    """Demonstrate getting bank statistics."""
    print("=" * 70)
    print("EXAMPLE 4: Bank Statistics")
    print("=" * 70)
    
    recognizer = BankPatternRecognizer()
    
    # Simulate a month of SMS messages
    messages = [
        "HSBC card charged",
        "HSBC balance inquiry",
        "HSBC transaction alert",
        "CIB withdrawal",
        "CIB deposit",
        "NBE transfer",
        "QNB ALAHLI purchase",
        "Random message 1",
        "Random message 2",
    ]
    
    print(f"\nAnalyzing {len(messages)} SMS messages...\n")
    
    # Get statistics
    stats = recognizer.get_bank_statistics(messages)
    
    print("Bank Distribution:")
    print("-" * 40)
    for bank, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(messages)) * 100
        print(f"{bank:20s} | {count:3d} messages ({percentage:5.1f}%)")
    
    print()


def example_custom_patterns():
    """Demonstrate using custom patterns file."""
    print("=" * 70)
    print("EXAMPLE 5: Custom Patterns")
    print("=" * 70)
    
    # You can create a custom patterns file and pass it to the recognizer
    # recognizer = BankPatternRecognizer(patterns_file='custom_patterns.yaml')
    
    # Or use the default patterns with custom settings
    recognizer = BankPatternRecognizer(
        fuzzy_threshold=90,  # Higher threshold for stricter matching
        enable_fuzzy=True
    )
    
    print(f"\nRecognizer configured with:")
    print(f"- Fuzzy threshold: {recognizer.fuzzy_threshold}")
    print(f"- Fuzzy matching enabled: {recognizer.enable_fuzzy}")
    print(f"- Number of banks: {len(recognizer.bank_patterns)}")
    
    print()


def example_with_loaded_sms():
    """Demonstrate integration with load_sms_messages function."""
    print("=" * 70)
    print("EXAMPLE 6: Integration with SMS Loading")
    print("=" * 70)
    
    # Note: This example shows the pattern, but requires an actual SMS file
    # Uncomment and provide a real file path to test
    
    # Load SMS messages from file
    # messages = load_sms_messages('path/to/sms_export.txt')
    
    # For demonstration, use sample messages
    messages = [
        "HSBC: Your card was charged 100 EGP",
        "CIB: Balance is 5000 EGP",
        "NBE withdrawal alert",
    ]
    
    print(f"\nProcessing {len(messages)} SMS messages loaded from file...\n")
    
    # Initialize recognizer
    recognizer = BankPatternRecognizer()
    
    # Identify banks
    bank_ids = recognizer.identify_banks_batch(messages)
    
    # Display results
    for sms, bank in zip(messages, bank_ids):
        print(f"{bank:20s} | {sms[:60]}")
    
    # Get statistics
    stats = recognizer.get_bank_statistics(messages)
    
    print("\nBank Statistics:")
    for bank, count in stats.items():
        print(f"  {bank}: {count} message(s)")
    
    print()


def example_arabic_support():
    """Demonstrate Arabic language support."""
    print("=" * 70)
    print("EXAMPLE 7: Arabic Language Support")
    print("=" * 70)
    
    recognizer = BankPatternRecognizer()
    
    arabic_messages = [
        "تم الخصم من بطاقتك من CIB بمبلغ 200 جنيه",
        "البنك الأهلي: تم السحب من حسابك",
        "بنك قطر الوطني: عملية شراء بمبلغ 150 جنيه",
        "Dear customer, بطاقتك من HSBC تم استخدامها",
    ]
    
    print("\nIdentifying banks from Arabic SMS messages:\n")
    for sms in arabic_messages:
        bank_id = recognizer.identify_bank(sms)
        print(f"Bank: {bank_id:20s} | SMS: {sms}")
    
    print()


def main():
    """Run all examples."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  BankPatternRecognizer - Example Usage".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Run examples
    example_basic_usage()
    example_with_confidence()
    example_batch_processing()
    example_statistics()
    example_custom_patterns()
    example_with_loaded_sms()
    example_arabic_support()
    
    print("=" * 70)
    print("Examples completed successfully!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
