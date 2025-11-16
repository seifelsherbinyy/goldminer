"""
Example usage of PromoClassifier for filtering promotional SMS messages.

This script demonstrates how to use the PromoClassifier to identify and filter
promotional/marketing messages before they enter the transaction processing pipeline.
"""
from goldminer.etl import PromoClassifier


def demo_basic_usage():
    """Demonstrate basic PromoClassifier usage."""
    print("=" * 70)
    print("DEMO 1: Basic PromoClassifier Usage")
    print("=" * 70)
    
    # Initialize classifier
    classifier = PromoClassifier()
    
    # Sample messages
    messages = [
        "Get 50% discount on all items this weekend!",
        "Your card ending 1234 was charged 250.50 EGP at Store XYZ",
        "Limited time offer: Buy 1 get 1 free!",
        "Transaction approved: 100 USD on 15/11/2024",
        "عرض خاص لفترة محدودة: خصومات على جميع المنتجات",
        "تم خصم 300 جنيه من بطاقتك في متجر كارفور"
    ]
    
    print("\nClassifying messages:\n")
    for msg in messages:
        result = classifier.classify(msg)
        status = "SKIP (Promotional)" if result.skip else "PROCESS (Transaction)"
        print(f"Status: {status:25s} | Message: {msg[:50]}...")
        if result.skip:
            print(f"  → Reason: {result.reason}")
            print(f"  → Confidence: {result.confidence}")
        print()


def demo_detailed_results():
    """Demonstrate detailed classification results."""
    print("=" * 70)
    print("DEMO 2: Detailed Classification Results")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    # Promotional message with multiple keywords
    promo_msg = "Congratulations! You've won a special gift. Enjoy exclusive rewards and discounts!"
    
    result = classifier.classify(promo_msg)
    
    print(f"\nMessage: {promo_msg}\n")
    print(f"Classification Results:")
    print(f"  Skip: {result.skip}")
    print(f"  Reason: {result.reason}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Matched Keywords: {', '.join(result.matched_keywords)}")
    print(f"  Number of Matches: {len(result.matched_keywords)}")


def demo_batch_processing():
    """Demonstrate batch processing of messages."""
    print("\n" + "=" * 70)
    print("DEMO 3: Batch Processing")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    messages = [
        "Flash sale alert: 70% off everything!",
        "Your payment of 500 SAR was successful",
        "Free gift with every purchase today",
        "ATM withdrawal: 1000 EGP from NBE ATM",
        "Win amazing prizes - enter now!",
        "Balance inquiry completed successfully"
    ]
    
    print(f"\nProcessing batch of {len(messages)} messages...\n")
    
    results = classifier.classify_batch(messages)
    
    promotional_count = sum(1 for r in results if r.skip)
    transaction_count = len(results) - promotional_count
    
    print(f"Results Summary:")
    print(f"  Total Messages: {len(messages)}")
    print(f"  Promotional: {promotional_count}")
    print(f"  Transactional: {transaction_count}")
    
    print("\nDetailed Results:")
    for i, (msg, result) in enumerate(zip(messages, results), 1):
        status = "PROMO" if result.skip else "TRANS"
        print(f"  {i}. [{status}] {msg[:40]}...")


def demo_custom_keywords():
    """Demonstrate adding custom keywords."""
    print("\n" + "=" * 70)
    print("DEMO 4: Custom Keywords")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    # Add custom keywords
    classifier.add_keywords(
        english=["clearance", "liquidation"],
        arabic=["تصفية", "نهاية الموسم"]
    )
    
    print("\nAdded custom keywords")
    print("  English: clearance, liquidation")
    print("  Arabic: تصفية, نهاية الموسم")
    
    # Test with custom keywords
    test_messages = [
        "Clearance sale - everything must go!",
        "تصفية نهاية الموسم - خصومات كبيرة"
    ]
    
    print("\nTesting custom keywords:\n")
    for msg in test_messages:
        result = classifier.classify(msg)
        print(f"Message: {msg}")
        print(f"  Detected as promotional: {result.skip}")
        if result.skip:
            print(f"  Matched keywords: {', '.join(result.matched_keywords)}")
        print()


def demo_pipeline_integration():
    """Demonstrate integration with transaction pipeline."""
    print("\n" + "=" * 70)
    print("DEMO 5: Pipeline Integration Pattern")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    # Simulated SMS messages
    incoming_messages = [
        "Your card was charged 450 EGP at Amazon",
        "Special offer: 40% discount this week!",
        "Payment of 200 USD processed successfully",
        "Win cash prizes - participate now!",
        "تم خصم 150 جنيه من حسابك"
    ]
    
    print("\nProcessing incoming messages through pipeline:\n")
    
    # Filter promotional messages
    transactional_messages = []
    promotional_messages = []
    
    for msg in incoming_messages:
        result = classifier.classify(msg)
        
        if result.skip:
            promotional_messages.append((msg, result))
            print(f"[FILTERED] {msg[:50]}...")
            print(f"  → {result.reason}\n")
        else:
            transactional_messages.append(msg)
            print(f"[ACCEPTED] {msg[:50]}...")
            print(f"  → Proceeding to transaction parser\n")
    
    print(f"\nPipeline Summary:")
    print(f"  Incoming: {len(incoming_messages)} messages")
    print(f"  Accepted: {len(transactional_messages)} transactions")
    print(f"  Filtered: {len(promotional_messages)} promotions")


def demo_borderline_cases():
    """Demonstrate handling of borderline cases."""
    print("\n" + "=" * 70)
    print("DEMO 6: Borderline Cases")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    # Messages that might be tricky to classify
    borderline_cases = [
        ("Your cashback of 50 EGP has been credited", 
         "Contains 'cashback' but is a transaction notification"),
        ("Reward points redeemed: 100 points used for payment",
         "Contains 'reward' but is a transaction"),
        ("Gift card purchase: 200 USD charged to your card",
         "Contains 'gift' but is a transaction"),
        ("Special account maintenance fee: 25 EGP",
         "Contains 'special' but is a transaction")
    ]
    
    print("\nAnalyzing borderline cases:\n")
    
    for msg, note in borderline_cases:
        result = classifier.classify(msg)
        
        print(f"Message: {msg}")
        print(f"Note: {note}")
        print(f"Classification: {'PROMOTIONAL' if result.skip else 'TRANSACTIONAL'}")
        if result.skip:
            print(f"Matched keywords: {', '.join(result.matched_keywords)}")
        print()


def demo_multilingual():
    """Demonstrate multilingual message classification."""
    print("\n" + "=" * 70)
    print("DEMO 7: Multilingual Messages")
    print("=" * 70)
    
    classifier = PromoClassifier()
    
    multilingual_messages = [
        "Special عرض خاص for our valued customers!",
        "احصل على discount of 30% today",
        "Free shipping + مجاني delivery on all orders",
        "Your transaction معاملتك was processed successfully"
    ]
    
    print("\nClassifying multilingual messages:\n")
    
    for msg in multilingual_messages:
        result = classifier.classify(msg)
        status = "PROMOTIONAL" if result.skip else "TRANSACTIONAL"
        
        print(f"Message: {msg}")
        print(f"Classification: {status}")
        if result.skip:
            print(f"Confidence: {result.confidence}")
            print(f"Keywords found: {', '.join(result.matched_keywords)}")
        print()


def main():
    """Run all demos."""
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + " " * 15 + "PromoClassifier Demo Examples" + " " * 24 + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    demo_basic_usage()
    demo_detailed_results()
    demo_batch_processing()
    demo_custom_keywords()
    demo_pipeline_integration()
    demo_borderline_cases()
    demo_multilingual()
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
