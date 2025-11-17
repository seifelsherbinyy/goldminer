"""
Demonstration script for ParquetExporter usage.

This script shows various ways to use the ParquetExporter class to export
transaction data to optimized Parquet files.
"""
from goldminer.etl import ParquetExporter
from datetime import datetime, timedelta


def create_sample_transactions():
    """Create sample transaction data for demonstration."""
    base_date = datetime.now() - timedelta(days=90)
    transactions = []
    
    categories = ['Food', 'Transport', 'Entertainment', 'Bills', 'Shopping']
    for i in range(50):
        date = base_date + timedelta(days=i % 30)
        transaction = {
            'id': f'TXN{i:05d}',
            'date': date.strftime('%Y-%m-%d'),
            'payee': f'Merchant {i % 5}',
            'normalized_merchant': f'MERCHANT_{i % 5}',
            'category': categories[i % len(categories)],
            'subcategory': 'General',
            'amount': round(50 + (i * 13.7) % 500, 2),
            'currency': 'USD',
            'account_id': 'ACC001',
            'account_type': 'Credit' if i % 2 == 0 else 'Debit',
            'interest_rate': 0.15 if i % 2 == 0 else None,
            'tags': ['online', 'recurring'] if i % 3 == 0 else ['in-store'],
            'urgency': 'normal',
            'confidence': 'high'
        }
        transactions.append(transaction)
    
    return transactions


def demo_basic_export():
    """Demonstrate basic Parquet export."""
    print("\n=== Demo 1: Basic Parquet Export ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export with default settings (snappy compression)
    exporter.export_to_parquet(
        transactions, 
        filepath='output_basic.parquet'
    )
    
    print(f"✓ Exported {len(transactions)} transactions to 'output_basic.parquet'")
    
    # Get schema info
    schema_info = exporter.get_schema_info('output_basic.parquet')
    print(f"  - Columns: {schema_info['num_columns']}")
    print(f"  - Row groups: {schema_info['num_row_groups']}")
    print(f"  - Metadata: {schema_info['metadata']}")


def demo_compressed_export():
    """Demonstrate export with different compression."""
    print("\n=== Demo 2: Export with Brotli Compression ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export with brotli compression (better compression ratio)
    exporter.export_to_parquet(
        transactions, 
        filepath='output_compressed.parquet',
        compression='brotli'
    )
    
    print(f"✓ Exported {len(transactions)} transactions with Brotli compression")


def demo_partitioned_export():
    """Demonstrate export with partitioning."""
    print("\n=== Demo 3: Export with Year/Month Partitioning ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export with partitioning by year and month
    exporter.export_to_parquet(
        transactions, 
        filepath='output_partitioned.parquet',
        partition_cols=['year', 'month']
    )
    
    print(f"✓ Exported {len(transactions)} transactions with year/month partitioning")
    print("  - Data is organized in directories by year and month")


def demo_metadata_export():
    """Demonstrate export with custom metadata."""
    print("\n=== Demo 4: Export with Custom Metadata ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export with user ID in metadata
    exporter.export_to_parquet(
        transactions, 
        filepath='output_metadata.parquet',
        user_id='user_12345'
    )
    
    print(f"✓ Exported {len(transactions)} transactions with custom metadata")
    
    # Read metadata
    schema_info = exporter.get_schema_info('output_metadata.parquet')
    print(f"  - Export timestamp: {schema_info['metadata'].get('export_timestamp', 'N/A')}")
    print(f"  - User ID: {schema_info['metadata'].get('user_id', 'N/A')}")
    print(f"  - Number of rows: {schema_info['metadata'].get('num_rows', 'N/A')}")


def demo_compatibility_check():
    """Demonstrate compatibility validation."""
    print("\n=== Demo 5: Compatibility Validation ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export file
    exporter.export_to_parquet(
        transactions, 
        filepath='output_compat.parquet'
    )
    
    # Validate compatibility
    results = exporter.validate_compatibility('output_compat.parquet')
    
    print(f"✓ Compatibility check results:")
    print(f"  - PyArrow: {'✓ OK' if results['pyarrow'] else '✗ Failed'}")
    print(f"  - Pandas: {'✓ OK' if results['pandas'] else '✗ Failed'}")
    print(f"  - Polars: {'✓ OK' if results['polars'] else '✗ Failed' if results['polars'] is False else '- Not installed'}")


def demo_schema_consistency():
    """Demonstrate schema consistency across exports."""
    print("\n=== Demo 6: Schema Consistency Verification ===")
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export twice
    exporter.export_to_parquet(transactions, 'output_schema1.parquet')
    exporter.export_to_parquet(transactions, 'output_schema2.parquet')
    
    # Get schema info from both
    schema1 = exporter.get_schema_info('output_schema1.parquet')
    schema2 = exporter.get_schema_info('output_schema2.parquet')
    
    # Compare
    columns_match = schema1['column_names'] == schema2['column_names']
    types_match = schema1['column_types'] == schema2['column_types']
    
    print(f"✓ Schema consistency check:")
    print(f"  - Column names match: {'✓ Yes' if columns_match else '✗ No'}")
    print(f"  - Column types match: {'✓ Yes' if types_match else '✗ No'}")


def demo_read_with_pandas():
    """Demonstrate reading Parquet file with Pandas."""
    print("\n=== Demo 7: Reading Parquet with Pandas ===")
    
    import pandas as pd
    
    exporter = ParquetExporter()
    transactions = create_sample_transactions()
    
    # Export
    exporter.export_to_parquet(transactions, 'output_pandas.parquet')
    
    # Read with Pandas
    df = pd.read_parquet('output_pandas.parquet')
    
    print(f"✓ Read {len(df)} rows with Pandas")
    print(f"  - Columns: {', '.join(df.columns[:5])}...")
    print(f"  - Memory usage: {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    print(f"\nFirst 3 rows:")
    print(df[['id', 'date', 'payee', 'amount', 'category']].head(3).to_string(index=False))


if __name__ == '__main__':
    print("=" * 60)
    print("ParquetExporter Demonstration")
    print("=" * 60)
    
    try:
        demo_basic_export()
        demo_compressed_export()
        demo_partitioned_export()
        demo_metadata_export()
        demo_compatibility_check()
        demo_schema_consistency()
        demo_read_with_pandas()
        
        print("\n" + "=" * 60)
        print("✓ All demonstrations completed successfully!")
        print("=" * 60)
        
        # Cleanup
        import os
        import shutil
        
        print("\nCleaning up demo files...")
        for filename in ['output_basic.parquet', 'output_compressed.parquet', 
                        'output_metadata.parquet', 'output_compat.parquet',
                        'output_schema1.parquet', 'output_schema2.parquet',
                        'output_pandas.parquet']:
            if os.path.exists(filename):
                os.remove(filename)
        
        if os.path.exists('output_partitioned'):
            shutil.rmtree('output_partitioned')
        
        print("✓ Cleanup complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
