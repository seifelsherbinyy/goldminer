#!/usr/bin/env python3
"""
XLSXExporter Integration Example

This script demonstrates how to integrate XLSXExporter with the GoldMiner ETL pipeline
to export transaction data from the database to Excel format.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.config import ConfigManager
from goldminer.etl import TransactionDB, XLSXExporter
from datetime import datetime, timedelta


def create_sample_transactions_in_db():
    """
    Create sample transactions in the database.
    
    Returns:
        TransactionDB instance with sample data
    """
    import random
    
    # Create temporary database
    db = TransactionDB("data/processed/demo_export.db")
    
    # Clear existing data for demo
    conn = db.connection
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    
    print("Generating and inserting sample transactions...")
    
    # Generate sample transactions
    categories = ['Food & Dining', 'Transportation', 'Entertainment', 'Bills & Utilities', 
                  'Shopping', 'Healthcare', 'Travel', 'Education']
    payees = [
        'Coffee Shop', 'Subway Station', 'Netflix', 'Electric Company',
        'Amazon', 'Pharmacy', 'Airline', 'University',
        'Restaurant', 'Gas Station', 'Cinema', 'Internet Provider',
        'Target', 'Doctor', 'Hotel', 'Bookstore'
    ]
    accounts = ['ACC-CREDIT-001', 'ACC-DEBIT-002', 'ACC-DEBIT-003']
    account_types = ['Credit', 'Debit', 'Debit']
    
    base_date = datetime.now() - timedelta(days=180)
    
    for i in range(200):
        # Generate date within the last 6 months
        days_offset = random.randint(0, 180)
        transaction_date = base_date + timedelta(days=days_offset)
        
        # Generate amount with some pattern
        category = random.choice(categories)
        if category == 'Bills & Utilities':
            amount = round(random.uniform(50, 300), 2)
        elif category == 'Travel':
            amount = round(random.uniform(200, 2000), 2)
        elif category == 'Food & Dining':
            amount = round(random.uniform(5, 100), 2)
        else:
            amount = round(random.uniform(10, 500), 2)
        
        # Add some anomalies (high value transactions)
        anomaly_flag = ''
        if amount > 1500:
            anomaly_flag = 'high_value'
        elif i % 30 == 0:  # Periodic anomalies
            anomaly_flag = 'burst_frequency'
        elif i % 40 == 0:
            anomaly_flag = 'unknown_merchant'
        
        account_idx = i % len(accounts)
        
        transaction = {
            'date': transaction_date.strftime('%Y-%m-%d'),
            'payee': random.choice(payees),
            'category': category,
            'subcategory': f'Sub-{category.split()[0]}',
            'amount': amount,
            'account_id': accounts[account_idx],
            'account_type': account_types[account_idx],
            'tags': f'tag-{i % 5}' if i % 3 == 0 else None,
            'anomalies': anomaly_flag if anomaly_flag else None,
            'confidence': 0.9 if anomaly_flag == '' else 0.7,
            'currency': 'USD'
        }
        
        db.insert(transaction)
    
    print(f"Inserted {db.count()} transactions into database")
    
    return db


def export_from_database():
    """
    Export transactions from database to Excel.
    """
    print("\n" + "=" * 80)
    print("XLSXExporter Integration Example - Database to Excel")
    print("=" * 80)
    print()
    
    # Create and populate database
    print("Step 1: Creating sample database...")
    db = create_sample_transactions_in_db()
    print(f"        Database ready with {db.count()} transactions")
    print()
    
    # Query transactions from database
    print("Step 2: Querying transactions from database...")
    all_transactions = db.query()
    print(f"        Retrieved {len(all_transactions)} transactions")
    print()
    
    # Convert to list of dictionaries for export
    transaction_dicts = []
    for txn in all_transactions:
        # Convert sqlite3.Row to dict
        transaction_dicts.append({
            'id': txn['id'],
            'date': txn['date'],
            'payee': txn['payee'],
            'category': txn['category'],
            'subcategory': txn['subcategory'],
            'amount': txn['amount'],
            'currency': txn['currency'],
            'account_id': txn['account_id'],
            'account_type': txn['account_type'],
            'tags': txn['tags'],
            'anomalies': txn['anomalies'],
            'confidence': txn['confidence']
        })
    
    # Create exporter and export
    print("Step 3: Exporting to Excel...")
    exporter = XLSXExporter()
    output_file = 'database_export.xlsx'
    exporter.export_to_excel(transaction_dicts, output_file)
    print(f"        ✓ Successfully exported to '{output_file}'")
    print()
    
    # Show summary
    print("Step 4: Export Summary")
    anomaly_count = sum(1 for t in transaction_dicts if t['anomalies'])
    total_amount = sum(t['amount'] for t in transaction_dicts)
    
    print(f"        Total transactions: {len(transaction_dicts)}")
    print(f"        Total amount: ${total_amount:,.2f}")
    print(f"        Anomalies detected: {anomaly_count}")
    print()
    
    # Show workbook structure
    print("Step 5: Workbook Structure")
    print("        • Sheet 1: Transactions - Full transaction details")
    print("        • Sheet 2: Monthly Summary - Aggregated data with charts")
    print("        • Sheet 3: Anomalies - Flagged transactions only")
    print()
    
    print("=" * 80)
    print(f"✓ Integration complete! Open '{output_file}' in Excel to view results.")
    print("=" * 80)
    
    # Close database
    db.close()


def export_filtered_transactions():
    """
    Export filtered transactions (e.g., by category or date range).
    """
    print("\n" + "=" * 80)
    print("Filtered Export Example")
    print("=" * 80)
    print()
    
    # Open database
    db = TransactionDB("data/processed/demo_export.db")
    
    # Query transactions for a specific category
    print("Exporting only 'Food & Dining' transactions...")
    food_transactions = db.query(filters={'category': 'Food & Dining'})
    
    if food_transactions:
        # Convert to dicts
        transaction_dicts = []
        for txn in food_transactions:
            transaction_dicts.append(dict(txn))
        
        # Export
        exporter = XLSXExporter()
        output_file = 'food_dining_export.xlsx'
        exporter.export_to_excel(transaction_dicts, output_file)
        print(f"✓ Exported {len(transaction_dicts)} Food & Dining transactions to '{output_file}'")
    else:
        print("No Food & Dining transactions found")
    
    db.close()
    print()


def main():
    """Main function."""
    # Full export from database
    export_from_database()
    
    # Filtered export example
    export_filtered_transactions()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
