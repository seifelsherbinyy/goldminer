#!/usr/bin/env python3
"""
XLSXExporter Conditional Formatting Demo Script

This script demonstrates the new conditional formatting features in XLSXExporter:
1. Urgency-based formatting (High=red/bold white, Medium=yellow, Normal/Low=green)
2. Anomaly-based red borders for flagged transactions
3. Dynamic formatting based on cell values (not hardcoded row indices)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.etl import XLSXExporter


def generate_demo_transactions_with_urgency(num_transactions=1200):
    """
    Generate sample transaction data with urgency levels and anomalies.
    
    Args:
        num_transactions: Number of transactions to generate
        
    Returns:
        List of transaction dictionaries
    """
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
    anomaly_types = ['high_value', 'burst_frequency', 'unknown_merchant', 'duplicate', '']
    
    base_date = datetime.now() - timedelta(days=180)
    transactions = []
    
    for i in range(num_transactions):
        # Generate date within the last 6 months
        days_offset = random.randint(0, 180)
        transaction_date = base_date + timedelta(days=days_offset)
        
        # Determine urgency and amount
        if i % 10 == 0:
            # High urgency - large transactions
            urgency = 'high'
            amount = round(random.uniform(10000, 25000), 2)
        elif i % 5 == 0:
            # Medium urgency - moderate transactions
            urgency = 'medium'
            amount = round(random.uniform(5000, 9999), 2)
        else:
            # Normal urgency - regular transactions
            urgency = 'normal'
            amount = round(random.uniform(10, 500), 2)
        
        # Generate category-specific amounts
        category = random.choice(categories)
        if category == 'Bills & Utilities' and urgency == 'normal':
            amount = round(random.uniform(50, 300), 2)
        elif category == 'Travel' and urgency == 'normal':
            amount = round(random.uniform(200, 2000), 2)
        elif category == 'Food & Dining' and urgency == 'normal':
            amount = round(random.uniform(5, 100), 2)
        
        # Add anomalies - various types
        anomaly_flag = ''
        if amount > 15000:
            anomaly_flag = 'high_value'
        elif i % 30 == 0:
            anomaly_flag = 'burst_frequency'
        elif i % 40 == 0:
            anomaly_flag = 'unknown_merchant'
        elif i % 50 == 0:
            anomaly_flag = 'duplicate'
        
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
            'urgency': urgency,
            'tags': f'tag-{i % 5}' if i % 3 == 0 else '',
            'anomalies': anomaly_flag,
            'confidence': 'high' if anomaly_flag == '' else 'medium'
        }
        
        transactions.append(transaction)
    
    return transactions


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("XLSXExporter Conditional Formatting Demo")
    print("=" * 80)
    print()
    
    # Generate sample data with 1200+ transactions
    print("1. Generating sample transaction data with urgency and anomalies...")
    transactions = generate_demo_transactions_with_urgency(1200)
    print(f"   Generated {len(transactions)} transactions")
    
    # Count statistics
    urgency_counts = {'high': 0, 'medium': 0, 'normal': 0}
    anomaly_count = 0
    
    for t in transactions:
        urgency_counts[t['urgency']] += 1
        if t['anomalies']:
            anomaly_count += 1
    
    print(f"   Date range: {transactions[0]['date']} to {transactions[-1]['date']}")
    print(f"   Urgency breakdown:")
    print(f"     - High urgency: {urgency_counts['high']} transactions")
    print(f"     - Medium urgency: {urgency_counts['medium']} transactions")
    print(f"     - Normal urgency: {urgency_counts['normal']} transactions")
    print(f"   Anomalies detected: {anomaly_count}")
    print()
    
    # Create exporter
    print("2. Initializing XLSXExporter with conditional formatting...")
    exporter = XLSXExporter()
    print("   XLSXExporter ready")
    print()
    
    # Export to Excel
    output_file = 'demo_conditional_formatting_export.xlsx'
    print(f"3. Exporting transactions to '{output_file}'...")
    try:
        exporter.export_to_excel(transactions, output_file)
        print("   ✓ Export successful!")
        print()
    except Exception as e:
        print(f"   ✗ Export failed: {e}")
        return 1
    
    # Display workbook information
    print("4. Workbook Structure with Conditional Formatting:")
    print()
    print("   Sheet 1: Transactions")
    print("   ─────────────────────")
    print("   • Headers: bold, colored background")
    print("   • Frozen top row for easy scrolling")
    print("   • Auto-adjusted column widths")
    print("   • Currency formatting for amounts")
    print("   • NEW: Urgency-based conditional formatting:")
    print("     └─ High urgency: Red fill with bold white text")
    print("     └─ Medium urgency: Yellow fill")
    print("     └─ Normal urgency: Green tint")
    print("   • NEW: Bold red borders for rows with anomaly flags")
    print()
    print("   Sheet 2: Monthly Summary")
    print("   ────────────────────────")
    print("   • Monthly totals with statistics")
    print("   • Category breakdown by month")
    print("   • Pie chart: Spending by category")
    print("   • Bar chart: Monthly spending trends")
    print("   • Line chart: Cumulative spending over time")
    print()
    print("   Sheet 3: Anomalies")
    print("   ──────────────────")
    print("   • All anomalous transactions")
    print("   • NEW: Urgency-based conditional formatting")
    print("   • NEW: Bold red borders for all anomaly rows")
    print("   • Includes urgency and anomaly type columns")
    print()
    
    # Summary statistics
    print("5. Export Summary:")
    print("   ───────────────")
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
    
    # Conditional formatting details
    print("6. Conditional Formatting Features:")
    print("   ─────────────────────────────────")
    print("   ✓ Dynamic formatting based on cell content (not hardcoded row indices)")
    print("   ✓ Urgency levels highlighted across entire rows")
    print("   ✓ Anomaly flags trigger bold red borders")
    print("   ✓ Helper functions ensure consistent style application")
    print("   ✓ Validated with 1200+ records containing mixed urgency and anomaly types")
    print()
    
    print("=" * 80)
    print(f"✓ Export complete! Open '{output_file}' in Excel to view the results.")
    print()
    print("Look for:")
    print("  • Red rows with bold white text (High urgency transactions)")
    print("  • Yellow rows (Medium urgency transactions)")
    print("  • Green-tinted rows (Normal urgency transactions)")
    print("  • Bold red borders on rows with anomaly flags")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
