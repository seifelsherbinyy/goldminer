#!/usr/bin/env python3
"""
Demonstration script for MerchantResolver functionality.

This script showcases the MerchantResolver's ability to:
- Resolve merchant names using exact matching
- Resolve merchant names using fuzzy matching
- Handle Arabic and English inputs
- Handle noisy/varied inputs
- Return confidence scores
- Provide merchant information
"""
from goldminer.utils import MerchantResolver


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def demonstrate_exact_matching():
    """Demonstrate exact merchant name matching."""
    print_section("Exact Merchant Name Matching")
    
    resolver = MerchantResolver()
    
    test_cases = [
        ("Carrefour City", "English exact match"),
        ("كارفور", "Arabic exact match"),
        ("McDonald's Egypt", "English with possessive"),
        ("ماكدونالدز", "Arabic fast food"),
        ("فودافون", "Arabic telecom"),
        ("AMAZON.COM", "Uppercase domain"),
    ]
    
    for payee, description in test_cases:
        canonical = resolver.resolve_merchant(payee)
        print(f"  {description:25} '{payee}' → '{canonical}'")


def demonstrate_fuzzy_matching():
    """Demonstrate fuzzy merchant name matching."""
    print_section("Fuzzy Matching with Confidence Scores")
    
    resolver = MerchantResolver()
    
    test_cases = [
        ("Carrefour Egyp", "Missing 't' in Egypt"),
        ("McDonalds", "Missing apostrophe"),
        ("CARREFOUR MAADI", "Location suffix"),
        ("Vodafone EG", "Country abbreviation"),
        ("Pizza Hut Egypt", "Full name with country"),
        ("UBER", "All caps"),
    ]
    
    for payee, description in test_cases:
        canonical, confidence = resolver.resolve_merchant(payee, return_confidence=True)
        if confidence:
            print(f"  {description:30} '{payee}' → '{canonical}' ({confidence:.1f}%)")
        else:
            print(f"  {description:30} '{payee}' → No match")


def demonstrate_noisy_inputs():
    """Demonstrate handling of noisy inputs."""
    print_section("Handling Noisy/Varied Inputs")
    
    resolver = MerchantResolver()
    
    test_cases = [
        ("  Carrefour City  ", "Extra whitespace"),
        ("carrefour express", "Lowercase variation"),
        ("PIZZA HUT", "All uppercase"),
        ("Jumia Online", "With descriptor"),
        ("Orange EG", "Abbreviation"),
    ]
    
    for payee, description in test_cases:
        canonical, confidence = resolver.resolve_merchant(payee, return_confidence=True)
        if confidence:
            print(f"  {description:25} '{payee}' → '{canonical}' ({confidence:.1f}%)")
        else:
            print(f"  {description:25} '{payee}' → No match")


def demonstrate_unresolvable_entries():
    """Demonstrate handling of unresolvable merchant names."""
    print_section("Unresolvable Merchant Names")
    
    resolver = MerchantResolver()
    
    test_cases = [
        "Unknown Shop XYZ",
        "Random Merchant",
        "12345",
        "A Very Different Name",
    ]
    
    print("  These payees don't match any known merchants:")
    for payee in test_cases:
        canonical, confidence = resolver.resolve_merchant(payee, return_confidence=True)
        status = "No match" if confidence is None else f"Matched with {confidence:.1f}%"
        print(f"    '{payee}' → '{canonical}' ({status})")


def demonstrate_merchant_info():
    """Demonstrate merchant information retrieval."""
    print_section("Merchant Information")
    
    resolver = MerchantResolver()
    
    merchants = ["Carrefour", "McDonald's", "Vodafone", "Uber"]
    
    for merchant in merchants:
        info = resolver.get_merchant_info(merchant)
        if info:
            print(f"\n  {merchant}:")
            print(f"    Aliases: {info['alias_count']} known variations")
            print(f"    Examples: {', '.join(info['aliases'][:5])}")
            if len(info['aliases']) > 5:
                print(f"              ... and {len(info['aliases']) - 5} more")


def demonstrate_all_merchants():
    """Demonstrate listing all canonical merchants."""
    print_section("All Canonical Merchants")
    
    resolver = MerchantResolver()
    merchants = resolver.get_all_merchants()
    
    print(f"\n  Total canonical merchants: {len(merchants)}")
    print(f"  Merchants: {', '.join(merchants)}")


def demonstrate_arabic_english_comparison():
    """Demonstrate resolution of the same merchant in Arabic and English."""
    print_section("Arabic and English Resolution Comparison")
    
    resolver = MerchantResolver()
    
    test_pairs = [
        ("كارفور", "Carrefour City"),
        ("ماكدونالدز", "McDonald's"),
        ("فودافون", "Vodafone Egypt"),
        ("اوبر", "UBER"),
        ("بيتزا هت", "Pizza Hut"),
    ]
    
    print("\n  Same merchant, different languages:")
    for arabic, english in test_pairs:
        canonical_ar = resolver.resolve_merchant(arabic)
        canonical_en = resolver.resolve_merchant(english)
        match = "✓" if canonical_ar == canonical_en else "✗"
        print(f"    {match} '{arabic}' → '{canonical_ar}'")
        print(f"      '{english}' → '{canonical_en}'")


def demonstrate_threshold_comparison():
    """Demonstrate different threshold settings."""
    print_section("Threshold Comparison")
    
    test_payee = "Carrefour Eg"  # Abbreviated Egypt
    
    thresholds = [70.0, 80.0, 85.0, 90.0, 95.0]
    
    print(f"\n  Resolving '{test_payee}' with different thresholds:\n")
    for threshold in thresholds:
        resolver = MerchantResolver(similarity_threshold=threshold)
        canonical, confidence = resolver.resolve_merchant(test_payee, return_confidence=True)
        
        if confidence:
            print(f"    Threshold {threshold:4.1f}%: '{canonical}' (confidence: {confidence:.1f}%)")
        else:
            print(f"    Threshold {threshold:4.1f}%: No match (too restrictive)")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MerchantResolver Demo - Intelligent Merchant Name Resolution".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        demonstrate_exact_matching()
        demonstrate_fuzzy_matching()
        demonstrate_noisy_inputs()
        demonstrate_unresolvable_entries()
        demonstrate_arabic_english_comparison()
        demonstrate_merchant_info()
        demonstrate_all_merchants()
        demonstrate_threshold_comparison()
        
        print("\n" + "=" * 70)
        print("  Demo completed successfully!")
        print("=" * 70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
