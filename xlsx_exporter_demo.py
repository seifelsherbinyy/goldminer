#!/usr/bin/env python3
"""
XLSXExporter Demo Script

This script demonstrates the XLSXExporter functionality, showing how to export
transaction data to well-formatted Excel workbooks with multiple sheets and charts.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.etl import XLSXExporter


def generate_demo_transactions(num_transactions=150):
    """
    Generate sample transaction data for demonstration.
    
    Args:
        num_transactions: Number of transactions to generate
        
    Returns:
        List of transaction dictionaries
    """
    import random
    
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
    transactions = []
    
    for i in range(num_transactions):
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
            'id': f'TXN{i:06d}',
            'date': transaction_date.strftime('%Y-%m-%d'),
            'payee': random.choice(payees),
            'category': category,
            'subcategory': f'Sub-{category.split()[0]}',
            'amount': amount,
            'currency': 'USD',
            'account_id': accounts[account_idx],
            'account_type': account_types[account_idx],
            'tags': f'tag-{i % 5}' if i % 3 == 0 else '',
            'anomalies': anomaly_flag,
            'confidence': 'high' if anomaly_flag == '' else 'medium'
        }
        
        transactions.append(transaction)
    
    return transactions


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("XLSXExporter Demo - Transaction Data Export")
    print("=" * 80)
    print()
    
    # Generate sample data
    print("1. Generating sample transaction data...")
    transactions = generate_demo_transactions(150)
    print(f"   Generated {len(transactions)} transactions")
    print(f"   Date range: {transactions[0]['date']} to {transactions[-1]['date']}")
    
    # Count anomalies
    anomaly_count = sum(1 for t in transactions if t['anomalies'])
    print(f"   Anomalies detected: {anomaly_count}")
    print()
    
    # Create exporter
    print("2. Initializing XLSXExporter...")
    exporter = XLSXExporter()
    print("   XLSXExporter ready")
    print()
    
    # Export to Excel
    output_file = 'demo_transactions_export.xlsx'
    print(f"3. Exporting transactions to '{output_file}'...")
    try:
        exporter.export_to_excel(transactions, output_file)
        print("   ✓ Export successful!")
        print()
    except Exception as e:
        print(f"   ✗ Export failed: {e}")
        return 1
    
    # Display workbook information
    print("4. Workbook Structure:")
    print("   Sheet 1: Transactions - Full transaction details with formatting")
    print("            • Headers: bold, colored background")
    print("            • Frozen top row for easy scrolling")
    print("            • Auto-adjusted column widths")
    print("            • Currency formatting for amounts")
    print("            • Anomaly rows highlighted in red")
    print()
    print("   Sheet 2: Monthly Summary - Aggregated data and charts")
    print("            • Monthly totals with statistics")
    print("            • Category breakdown by month")
    print("            • Pie chart: Spending by category")
    print("            • Bar chart: Monthly spending trends")
    print("            • Line chart: Cumulative spending over time")
    print()
    print("   Sheet 3: Anomalies - Flagged transactions only")
    print("            • All anomalous transactions")
    print("            • Highlighted for easy identification")
    print("            • Includes anomaly type in 'anomalies' column")
    print()
    
    # Summary statistics
    print("5. Export Summary:")
    total_amount = sum(t['amount'] for t in transactions)
    avg_amount = total_amount / len(transactions)
    max_amount = max(t['amount'] for t in transactions)
    min_amount = min(t['amount'] for t in transactions)
    
    print(f"   Total transactions: {len(transactions)}")
    print(f"   Total amount: ${total_amount:,.2f}")
    print(f"   Average amount: ${avg_amount:,.2f}")
    print(f"   Max amount: ${max_amount:,.2f}")
    print(f"   Min amount: ${min_amount:,.2f}")
    print(f"   Anomalies: {anomaly_count}")
    print()
    
    print("=" * 80)
    print(f"✓ Export complete! Open '{output_file}' in Excel to view the results.")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
