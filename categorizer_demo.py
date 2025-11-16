"""
Demo script for the Categorizer class.

This script demonstrates the categorization of transaction records using
the Categorizer class with various merchant names and transaction types.
"""
from goldminer.etl import Categorizer, TransactionRecord


def main():
    """Demonstrate Categorizer functionality."""
    print("=" * 80)
    print("Categorizer Demo - Transaction Categorization System")
    print("=" * 80)
    print()
    
    # Initialize the categorizer
    print("Initializing Categorizer...")
    categorizer = Categorizer()
    print(f"✓ Loaded {len(categorizer.rules.get('categories', []))} category rules")
    print()
    
    # Create sample transaction records
    sample_transactions = [
        TransactionRecord(
            id='txn-001',
            payee="McDonald's",
            normalized_merchant="McDonald's",
            amount=75.50,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-002',
            payee="Carrefour Maadi",
            normalized_merchant="Carrefour Maadi",
            amount=450.00,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-003',
            payee="Uber Trip",
            normalized_merchant="Uber Trip",
            amount=35.00,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-004',
            payee="مطعم المدينة",  # Arabic: City Restaurant
            normalized_merchant="مطعم المدينة",
            amount=120.00,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-005',
            payee="Amazon.com",
            normalized_merchant="Amazon.com",
            amount=599.99,
            currency='USD'
        ),
        TransactionRecord(
            id='txn-006',
            payee="صيدلية العزبي",  # Arabic: El Ezaby Pharmacy
            normalized_merchant="صيدلية العزبي",
            amount=85.00,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-007',
            payee="Shell Gas Station",
            normalized_merchant="Shell Gas Station",
            amount=250.00,
            currency='EGP'
        ),
        TransactionRecord(
            id='txn-008',
            payee="Unknown Merchant XYZ",
            normalized_merchant="Unknown Merchant XYZ",
            amount=100.00,
            currency='EGP'
        ),
    ]
    
    print("Categorizing Sample Transactions:")
    print("-" * 80)
    
    # Categorize each transaction
    categorized_records = []
    for record in sample_transactions:
        categorized = categorizer.categorize(record)
        categorized_records.append(categorized)
        
        print(f"\nTransaction ID: {categorized.id}")
        print(f"  Merchant: {categorized.payee}")
        print(f"  Amount: {categorized.amount} {categorized.currency}")
        print(f"  Category: {categorized.category}")
        print(f"  Subcategory: {categorized.subcategory}")
        print(f"  Tags: {', '.join(categorized.tags) if categorized.tags else 'None'}")
    
    print()
    print("=" * 80)
    
    # Display statistics
    print("\nCategorization Statistics:")
    print("-" * 80)
    
    stats = categorizer.get_category_statistics(categorized_records)
    print(f"Total Transactions: {stats['total_records']}")
    print(f"Uncategorized: {stats['uncategorized_count']} ({stats['uncategorized_percentage']:.1f}%)")
    print()
    
    print("Breakdown by Category:")
    for category, info in sorted(stats['categories'].items()):
        print(f"\n  {category}: {info['count']} transaction(s)")
        for subcategory, count in sorted(info['subcategories'].items()):
            print(f"    • {subcategory}: {count}")
    
    print()
    print("=" * 80)
    
    # Demonstrate batch processing
    print("\nBatch Processing Demo:")
    print("-" * 80)
    
    batch_records = [
        TransactionRecord(id='batch-1', payee='Netflix', normalized_merchant='Netflix'),
        TransactionRecord(id='batch-2', payee='Vodafone', normalized_merchant='Vodafone'),
        TransactionRecord(id='batch-3', payee='Zara Store', normalized_merchant='Zara Store'),
        TransactionRecord(id='batch-4', payee='VOX Cinema', normalized_merchant='VOX Cinema'),
    ]
    
    batch_results = categorizer.categorize_batch(batch_records)
    
    for record in batch_results:
        print(f"• {record.payee:20s} → {record.category} / {record.subcategory}")
    
    print()
    print("=" * 80)
    
    # Demonstrate priority system
    print("\nPriority System Demo:")
    print("-" * 80)
    print("Priority: Exact Match → Fuzzy Match → Keyword Match → Fallback")
    print()
    
    priority_examples = [
        ("Amazon", "Exact match"),
        ("amazn store", "Fuzzy match"),
        ("Electronics Shop", "Keyword match"),
        ("Random Store ABC", "Fallback to Uncategorized"),
    ]
    
    for merchant, expected_match_type in priority_examples:
        record = TransactionRecord(
            id='priority-test',
            payee=merchant,
            normalized_merchant=merchant
        )
        result = categorizer.categorize(record)
        print(f"• {merchant:25s} ({expected_match_type})")
        print(f"  → {result.category} / {result.subcategory}")
    
    print()
    print("=" * 80)
    print("Demo completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
