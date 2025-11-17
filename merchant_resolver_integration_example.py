#!/usr/bin/env python3
"""
Integration example: Using MerchantResolver with GoldMiner ETL Pipeline

This example demonstrates how to integrate MerchantResolver into the
GoldMiner ETL pipeline to normalize merchant names in transaction data.
"""
import pandas as pd
from pathlib import Path
from goldminer.utils import MerchantResolver, setup_logger


def create_sample_transaction_data():
    """Create sample transaction data with varied merchant names."""
    data = {
        'transaction_id': [f'TXN{i:04d}' for i in range(1, 21)],
        'date': pd.date_range('2024-01-01', periods=20, freq='D'),
        'amount': [150.50, 89.99, 250.00, 45.00, 120.00, 
                   75.50, 200.00, 35.99, 180.00, 95.00,
                   110.50, 65.00, 300.00, 50.00, 140.00,
                   85.50, 220.00, 40.00, 160.00, 90.00],
        'payee': [
            # Carrefour variations
            'Carrefour City',
            'CARREFOUR MAADI',
            'كارفور',
            'Carrefour Express',
            
            # McDonald's variations
            'McDonald\'s Egypt',
            'ماكدونالدز',
            'McDonalds',
            'MC DONALDS',
            
            # Vodafone variations
            'Vodafone Egypt',
            'فودافون',
            'VODAFONE',
            'Vodafone Cash',
            
            # Other merchants
            'UBER',
            'Pizza Hut',
            'Amazon.com',
            'Jumia Online',
            'Orange EG',
            
            # Unknown merchants (not in aliases)
            'Local Coffee Shop',
            'Corner Grocery Store',
            'Unknown Vendor'
        ]
    }
    return pd.DataFrame(data)


def resolve_merchants_in_dataframe(df: pd.DataFrame, payee_column: str = 'payee') -> pd.DataFrame:
    """
    Resolve merchant names in a DataFrame using MerchantResolver.
    
    Args:
        df: DataFrame containing transaction data
        payee_column: Name of the column containing merchant/payee names
    
    Returns:
        DataFrame with additional columns for canonical merchant and confidence
    """
    logger = setup_logger(__name__)
    resolver = MerchantResolver()
    
    logger.info(f"Resolving merchants in {len(df)} transactions...")
    
    # Create lists to store results
    canonical_merchants = []
    confidence_scores = []
    
    # Process each transaction
    for payee in df[payee_column]:
        canonical, confidence = resolver.resolve_merchant(
            payee,
            return_confidence=True
        )
        canonical_merchants.append(canonical)
        confidence_scores.append(confidence)
    
    # Add new columns to DataFrame
    df['canonical_merchant'] = canonical_merchants
    df['merchant_confidence'] = confidence_scores
    df['needs_review'] = df['merchant_confidence'].isna()
    
    # Summary statistics
    matched = df['merchant_confidence'].notna().sum()
    unmatched = df['merchant_confidence'].isna().sum()
    avg_confidence = df['merchant_confidence'].mean()
    
    logger.info(f"Resolution complete:")
    logger.info(f"  Matched: {matched} ({matched/len(df)*100:.1f}%)")
    logger.info(f"  Unmatched: {unmatched} ({unmatched/len(df)*100:.1f}%)")
    logger.info(f"  Average confidence: {avg_confidence:.1f}%")
    
    return df


def analyze_merchant_resolution(df: pd.DataFrame):
    """Analyze and display merchant resolution results."""
    print("\n" + "=" * 80)
    print("MERCHANT RESOLUTION ANALYSIS")
    print("=" * 80)
    
    # Display all transactions with resolution
    print("\nAll Transactions:")
    print("-" * 80)
    display_df = df[['transaction_id', 'payee', 'canonical_merchant', 
                     'merchant_confidence', 'needs_review', 'amount']]
    
    for _, row in display_df.iterrows():
        conf = f"{row['merchant_confidence']:.1f}%" if pd.notna(row['merchant_confidence']) else "N/A"
        review = "⚠️ " if row['needs_review'] else "✓ "
        print(f"{review}{row['transaction_id']}: {row['payee']:25} → {row['canonical_merchant']:20} "
              f"(Conf: {conf:7}) ${row['amount']:.2f}")
    
    # Summary by canonical merchant
    print("\n" + "=" * 80)
    print("SUMMARY BY CANONICAL MERCHANT")
    print("=" * 80)
    
    merchant_summary = df.groupby('canonical_merchant').agg({
        'amount': ['count', 'sum', 'mean'],
        'merchant_confidence': 'mean'
    }).round(2)
    
    merchant_summary.columns = ['Transactions', 'Total Amount', 'Avg Amount', 'Avg Confidence']
    merchant_summary = merchant_summary.sort_values('Total Amount', ascending=False)
    
    print(merchant_summary)
    
    # Unmatched merchants
    print("\n" + "=" * 80)
    print("UNMATCHED MERCHANTS (Need Review)")
    print("=" * 80)
    
    unmatched = df[df['needs_review']]
    if len(unmatched) > 0:
        print(f"\nFound {len(unmatched)} transactions with unmatched merchants:")
        for _, row in unmatched.iterrows():
            print(f"  - {row['payee']} (${row['amount']:.2f})")
        print(f"\nTotal value of unmatched transactions: ${unmatched['amount'].sum():.2f}")
    else:
        print("\nNo unmatched merchants found!")


def save_results(df: pd.DataFrame, output_path: str = 'resolved_transactions.csv'):
    """Save resolved transaction data to CSV."""
    logger = setup_logger(__name__)
    
    output_file = Path(output_path)
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    logger.info(f"Results saved to: {output_file.absolute()}")
    print(f"\n✓ Results saved to: {output_file.absolute()}")


def main():
    """Run the integration example."""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  MerchantResolver + GoldMiner ETL Integration Example".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        # Step 1: Create sample data
        print("\n[1/4] Creating sample transaction data...")
        df = create_sample_transaction_data()
        print(f"✓ Created {len(df)} sample transactions")
        
        # Step 2: Resolve merchants
        print("\n[2/4] Resolving merchant names...")
        df = resolve_merchants_in_dataframe(df)
        print("✓ Merchant resolution complete")
        
        # Step 3: Analyze results
        print("\n[3/4] Analyzing results...")
        analyze_merchant_resolution(df)
        
        # Step 4: Save results
        print("\n[4/4] Saving results...")
        save_results(df, '/tmp/resolved_transactions.csv')
        
        print("\n" + "=" * 80)
        print("INTEGRATION EXAMPLE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nKey Takeaways:")
        print("  • MerchantResolver seamlessly integrates with pandas DataFrames")
        print("  • Confidence scores help identify transactions needing manual review")
        print("  • Original payee names are preserved for audit purposes")
        print("  • Canonical names enable accurate aggregation and reporting")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
