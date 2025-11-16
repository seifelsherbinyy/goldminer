"""
Integration example showing PromoClassifier in an SMS processing pipeline.

This example demonstrates how to integrate PromoClassifier into a complete
SMS processing workflow that includes:
1. Loading SMS messages
2. Filtering promotional messages
3. Parsing transactions
4. Validating data
5. Storing results
"""
from goldminer.etl import PromoClassifier, load_sms_messages, FieldValidator
from typing import List, Dict, Any


def process_sms_with_promo_filter(messages: List[str]) -> Dict[str, Any]:
    """
    Process SMS messages with promotional filtering.
    
    This function demonstrates the recommended pipeline:
    1. Filter promotional messages first
    2. Parse remaining transaction messages
    3. Validate parsed data
    4. Return statistics and results
    
    Args:
        messages: List of SMS messages to process
        
    Returns:
        Dictionary with processing statistics and results
    """
    # Initialize components
    promo_classifier = PromoClassifier()
    field_validator = FieldValidator()
    
    # Statistics
    stats = {
        'total_messages': len(messages),
        'filtered_promotional': 0,
        'processed_transactions': 0,
        'validation_passed': 0,
        'validation_failed': 0
    }
    
    # Results
    filtered_promos = []
    parsed_transactions = []
    validation_results = []
    
    print(f"Processing {len(messages)} SMS messages...\n")
    
    # Step 1: Filter promotional messages
    print("=" * 60)
    print("STEP 1: Filtering Promotional Messages")
    print("=" * 60)
    
    transactional_messages = []
    
    for i, msg in enumerate(messages, 1):
        result = promo_classifier.classify(msg)
        
        if result.skip:
            # Promotional message - filter out
            stats['filtered_promotional'] += 1
            filtered_promos.append({
                'message': msg,
                'reason': result.reason,
                'confidence': result.confidence,
                'keywords': result.matched_keywords
            })
            print(f"[{i}] FILTERED: {msg[:50]}...")
            print(f"    Reason: {result.reason}")
        else:
            # Transaction message - continue processing
            transactional_messages.append(msg)
            print(f"[{i}] ACCEPTED: {msg[:50]}...")
    
    print(f"\nFiltering Summary:")
    print(f"  Promotional messages filtered: {stats['filtered_promotional']}")
    print(f"  Transaction messages accepted: {len(transactional_messages)}")
    
    # Step 2: Parse transaction messages (simplified - in real use, use RegexParserEngine)
    print("\n" + "=" * 60)
    print("STEP 2: Parsing Transaction Messages")
    print("=" * 60)
    
    for i, msg in enumerate(transactional_messages, 1):
        # In a real implementation, use RegexParserEngine here
        # For demo purposes, we'll create mock parsed data
        parsed_data = parse_transaction_mock(msg)
        parsed_transactions.append(parsed_data)
        stats['processed_transactions'] += 1
        
        print(f"[{i}] Parsed: {msg[:40]}...")
        print(f"    Amount: {parsed_data.get('amount', 'N/A')}")
        print(f"    Currency: {parsed_data.get('currency', 'N/A')}")
    
    print(f"\nParsing Summary:")
    print(f"  Successfully parsed: {stats['processed_transactions']}")
    
    # Step 3: Validate parsed transactions
    print("\n" + "=" * 60)
    print("STEP 3: Validating Parsed Transactions")
    print("=" * 60)
    
    for i, parsed_data in enumerate(parsed_transactions, 1):
        validated = field_validator.validate(parsed_data)
        validation_results.append(validated)
        
        if validated.confidence == 'high' and len(validated.warnings) == 0:
            stats['validation_passed'] += 1
            status = "VALID"
        else:
            stats['validation_failed'] += 1
            status = "WARNING"
        
        print(f"[{i}] {status}: Confidence={validated.confidence}, Warnings={len(validated.warnings)}")
        if validated.warnings:
            for warning in validated.warnings:
                print(f"    ⚠ {warning}")
    
    print(f"\nValidation Summary:")
    print(f"  Valid transactions: {stats['validation_passed']}")
    print(f"  Transactions with warnings: {stats['validation_failed']}")
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total messages processed: {stats['total_messages']}")
    print(f"Promotional messages filtered: {stats['filtered_promotional']} ({stats['filtered_promotional']/stats['total_messages']*100:.1f}%)")
    print(f"Transaction messages parsed: {stats['processed_transactions']} ({stats['processed_transactions']/stats['total_messages']*100:.1f}%)")
    print(f"Valid transactions: {stats['validation_passed']}")
    print(f"Transactions with warnings: {stats['validation_failed']}")
    
    # Return results
    return {
        'statistics': stats,
        'filtered_promotional': filtered_promos,
        'parsed_transactions': parsed_transactions,
        'validation_results': validation_results
    }


def parse_transaction_mock(message: str) -> Dict[str, Any]:
    """
    Mock transaction parser for demonstration purposes.
    
    In a real implementation, this would be replaced with RegexParserEngine.
    """
    # Simple mock parsing - just extract some basic info
    parsed = {
        'original_message': message,
        'amount': None,
        'currency': None,
        'date': None
    }
    
    # Very basic extraction (not production-ready)
    import re
    
    # Try to find amount
    amount_match = re.search(r'(\d+(?:[,.]\d{2})?)\s*(EGP|USD|EUR|SAR|جنيه|دولار)', message, re.IGNORECASE)
    if amount_match:
        parsed['amount'] = amount_match.group(1).replace(',', '')
        parsed['currency'] = amount_match.group(2).upper() if amount_match.group(2) in ['EGP', 'USD', 'EUR', 'SAR'] else amount_match.group(2)
    
    # Try to find date
    date_match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2})', message)
    if date_match:
        parsed['date'] = date_match.group(1)
    
    return parsed


def main():
    """Run the integration example."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + " " * 10 + "PromoClassifier Pipeline Integration Example" + " " * 14 + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    # Sample SMS messages (mix of promotional and transactional)
    sample_messages = [
        "Your card ending 1234 was charged 250.50 EGP at Amazon on 15/11/2024",
        "Special offer: Get 50% discount on all items this weekend only!",
        "Transaction approved: 100 USD at Starbucks on 16/11/2024",
        "Limited time offer! Free shipping on orders over 500 EGP",
        "ATM withdrawal of 1000 EGP from NBE ATM, Nasr City",
        "Win amazing prizes! Participate in our contest now",
        "Payment of 450 SAR to Netflix processed successfully on 17/11/2024",
        "Exclusive deal for you - cashback rewards on all purchases!",
        "تم خصم 300 جنيه من بطاقتك في كارفور بتاريخ 18/11/2024",
        "عرض خاص لفترة محدودة: خصومات على جميع المنتجات"
    ]
    
    # Process messages
    results = process_sms_with_promo_filter(sample_messages)
    
    # Additional analysis
    print("\n" + "=" * 60)
    print("FILTERED PROMOTIONAL MESSAGES DETAILS")
    print("=" * 60)
    
    for i, promo in enumerate(results['filtered_promotional'], 1):
        print(f"\n[{i}] Message: {promo['message'][:60]}...")
        print(f"    Confidence: {promo['confidence']}")
        print(f"    Keywords: {', '.join(promo['keywords'][:3])}")
        if len(promo['keywords']) > 3:
            print(f"              (and {len(promo['keywords']) - 3} more)")
    
    print("\n" + "=" * 60)
    print("Integration example completed!")
    print("=" * 60)
    print("\nKey Takeaways:")
    print("1. PromoClassifier filters promotional messages BEFORE parsing")
    print("2. This saves processing time and prevents promo content in transaction DB")
    print("3. Confidence levels help identify borderline cases")
    print("4. The pipeline can be customized with additional processing steps")


if __name__ == "__main__":
    main()
