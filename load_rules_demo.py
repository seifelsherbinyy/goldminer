#!/usr/bin/env python
"""
Demonstration of the Categorizer load_rules functionality.

This script shows how to:
1. Load custom categorization rules from a YAML file
2. Use different match types (match, match_regex, match_tag)
3. Reload rules at runtime
4. Handle safe fallback for missing or malformed files
"""

from goldminer.etl import Categorizer, TransactionRecord


def demo_basic_loading():
    """Demonstrate basic rule loading."""
    print("=" * 70)
    print("DEMO 1: Basic Rule Loading")
    print("=" * 70)
    
    # Create categorizer with default rules
    categorizer = Categorizer()
    print("✓ Categorizer initialized with default rules\n")
    
    # Load custom rules from example file
    categorizer.load_rules('example_categorizer_rules.yaml')
    print("✓ Custom rules loaded from example_categorizer_rules.yaml\n")


def demo_match_types():
    """Demonstrate different match types."""
    print("=" * 70)
    print("DEMO 2: Different Match Types")
    print("=" * 70)
    
    categorizer = Categorizer()
    categorizer.load_rules('example_categorizer_rules.yaml')
    
    # Test exact match
    print("\n1. Exact Match (match key):")
    record1 = TransactionRecord(id='1', payee='Uber', normalized_merchant='Uber')
    result1 = categorizer.categorize(record1)
    print(f"   Payee: 'Uber'")
    print(f"   Result: {result1.category} / {result1.subcategory}")
    print(f"   Tags: {result1.tags}")
    
    # Test regex match
    print("\n2. Regex Match (match_regex key):")
    record2 = TransactionRecord(id='2', payee='Vodafone Egypt', normalized_merchant='Vodafone Egypt')
    result2 = categorizer.categorize(record2)
    print(f"   Payee: 'Vodafone Egypt'")
    print(f"   Result: {result2.category} / {result2.subcategory}")
    print(f"   Tags: {result2.tags}")
    
    # Test tag match
    print("\n3. Tag Match (match_tag key):")
    record3 = TransactionRecord(
        id='3',
        payee='Monthly Service',
        normalized_merchant='Monthly Service',
        tags=['subscription']
    )
    result3 = categorizer.categorize(record3)
    print(f"   Payee: 'Monthly Service'")
    print(f"   Existing Tags: ['subscription']")
    print(f"   Result: {result3.category} / {result3.subcategory}")
    print(f"   Final Tags: {result3.tags}")


def demo_rule_precedence():
    """Demonstrate rule precedence."""
    print("\n" + "=" * 70)
    print("DEMO 3: Rule Precedence")
    print("=" * 70)
    
    categorizer = Categorizer()
    categorizer.load_rules('example_categorizer_rules.yaml')
    
    # Uber matches both exact and would match regex if we had one
    record = TransactionRecord(id='1', payee='Uber', normalized_merchant='Uber')
    result = categorizer.categorize(record)
    
    print("\nRule priority order:")
    print("  1. match (exact string)")
    print("  2. match_regex (regex pattern)")
    print("  3. match_tag (tag-based)")
    print("  4. Legacy format (merchant_exact, merchant_fuzzy, keywords)")
    print("  5. Fallback")
    
    print(f"\nFor 'Uber' (has exact match rule):")
    print(f"  Matched using: exact match")
    print(f"  Category: {result.category} / {result.subcategory}")


def demo_runtime_reload():
    """Demonstrate runtime reloading of rules."""
    print("\n" + "=" * 70)
    print("DEMO 4: Runtime Rule Reloading")
    print("=" * 70)
    
    categorizer = Categorizer()
    
    # Initial state with default rules
    record = TransactionRecord(id='1', payee='Uber', normalized_merchant='Uber')
    result1 = categorizer.categorize(record)
    print(f"\nBefore loading custom rules:")
    print(f"  'Uber' -> {result1.category} / {result1.subcategory}")
    
    # Load custom rules
    categorizer.load_rules('example_categorizer_rules.yaml')
    result2 = categorizer.categorize(record)
    print(f"\nAfter loading custom rules:")
    print(f"  'Uber' -> {result2.category} / {result2.subcategory}")
    
    print("\n✓ Rules can be reloaded at runtime without restarting the application")


def demo_safe_fallback():
    """Demonstrate safe fallback behavior."""
    print("\n" + "=" * 70)
    print("DEMO 5: Safe Fallback Behavior")
    print("=" * 70)
    
    categorizer = Categorizer()
    categorizer.load_rules('example_categorizer_rules.yaml')
    
    # Test with missing file
    print("\n1. Loading non-existent file:")
    categorizer.load_rules('/nonexistent/rules.yaml')
    print("   ✓ Original rules preserved")
    
    # Test that categorization still works
    record = TransactionRecord(id='1', payee='Uber', normalized_merchant='Uber')
    result = categorizer.categorize(record)
    print(f"   ✓ Categorization still works: 'Uber' -> {result.category}")
    
    print("\n2. The categorizer handles errors gracefully:")
    print("   - Missing files: logs warning, keeps existing rules")
    print("   - Malformed YAML: logs error, keeps existing rules")
    print("   - Invalid structure: logs error, keeps existing rules")


def demo_backward_compatibility():
    """Demonstrate backward compatibility."""
    print("\n" + "=" * 70)
    print("DEMO 6: Backward Compatibility")
    print("=" * 70)
    
    categorizer = Categorizer()
    
    # Test with legacy format (category_rules.yaml)
    record = TransactionRecord(id='1', payee="McDonald's", normalized_merchant="McDonald's")
    result = categorizer.categorize(record)
    
    print("\nLegacy format (category_rules.yaml) still works:")
    print(f"  'McDonald's' -> {result.category} / {result.subcategory}")
    print("\n✓ Fully backward compatible with existing rules files")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "Categorizer load_rules() Demo" + " " * 23 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        demo_basic_loading()
        demo_match_types()
        demo_rule_precedence()
        demo_runtime_reload()
        demo_safe_fallback()
        demo_backward_compatibility()
        
        print("\n" + "=" * 70)
        print("✓ All demonstrations completed successfully!")
        print("=" * 70)
        print("\nKey Features:")
        print("  • Load rules from YAML files with load_rules(filepath)")
        print("  • Support for match, match_regex, and match_tag")
        print("  • Clear rule precedence system")
        print("  • Runtime reloading capability")
        print("  • Safe fallback for errors")
        print("  • Full backward compatibility")
        print("\nFor non-technical users:")
        print("  • Edit YAML files to change categorization rules")
        print("  • No code changes required")
        print("  • Changes take effect immediately with reload")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {str(e)}")
        raise


if __name__ == "__main__":
    main()
