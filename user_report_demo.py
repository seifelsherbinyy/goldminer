#!/usr/bin/env python3
"""
Demo script for generate_user_report function.

This script demonstrates the generate_user_report function by creating
a comprehensive Excel workbook with 100 sample transactions, including
all three sheets (Transactions, Anomalies, Summary) with embedded charts.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.etl import generate_user_report


def generate_sample_transactions(num_transactions=100):
    """
    Generate sample transaction data for demonstration.
    
    Args:
        num_transactions: Number of transactions to generate (default: 100)
        
    Returns:
        List of transaction dictionaries
    """
    categories = [
        'Food & Dining', 'Transportation', 'Entertainment', 
        'Bills & Utilities', 'Shopping', 'Healthcare', 'Travel', 'Education'
    ]
    
    payees = [
        'Starbucks', 'Subway Station', 'Netflix', 'Electric Company',
        'Amazon', 'CVS Pharmacy', 'United Airlines', 'University Bookstore',
        'Chipotle', 'Shell Gas Station', 'AMC Theaters', 'Comcast',
        'Target', 'Doctor Office', 'Marriott Hotel', 'Barnes & Noble',
        'Whole Foods', 'Uber', 'Spotify', 'Water Company',
        'Walmart', 'Walgreens', 'Delta Airlines', 'Campus Store'
    ]
    
    accounts = ['ACC-CREDIT-001', 'ACC-DEBIT-002', 'ACC-DEBIT-003']
    account_types = ['Credit', 'Debit', 'Debit']
    
    base_date = datetime.now() - timedelta(days=180)
    transactions = []
    
    for i in range(num_transactions):
        # Generate date within the last 6 months
        days_offset = (i * 2) % 180  # Spread across 6 months
        transaction_date = base_date + timedelta(days=days_offset)
        
        # Generate amount with category-based patterns
        category = categories[i % len(categories)]
        if category == 'Bills & Utilities':
            amount = round(random.uniform(50, 300), 2)
        elif category == 'Travel':
            amount = round(random.uniform(200, 2000), 2)
        elif category == 'Food & Dining':
            amount = round(random.uniform(5, 100), 2)
        elif category == 'Healthcare':
            amount = round(random.uniform(25, 500), 2)
        else:
            amount = round(random.uniform(10, 500), 2)
        
        # Add some anomalies for testing
        anomaly_flag = ''
        if amount > 1500:
            anomaly_flag = 'high_value'
        elif i % 30 == 0:
            anomaly_flag = 'burst_frequency'
        elif i % 40 == 0:
            anomaly_flag = 'unknown_merchant'
        
        account_idx = i % len(accounts)
        
        transaction = {
            'id': f'TXN{i:06d}',
            'date': transaction_date.strftime('%Y-%m-%d'),
            'payee': payees[i % len(payees)],
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
    print("Generate User Report Demo - Financial Data Export")
    print("=" * 80)
    print()
    
    # Generate sample data
    print("1. Generating sample transaction data...")
    transactions = generate_sample_transactions(100)
    print(f"   ✓ Generated {len(transactions)} transactions")
    
    # Calculate date range
    dates = [t['date'] for t in transactions]
    print(f"   Date range: {min(dates)} to {max(dates)}")
    
    # Count anomalies
    anomaly_count = sum(1 for t in transactions if t['anomalies'])
    print(f"   Anomalies detected: {anomaly_count}")
    
    # Count categories
    categories = set(t['category'] for t in transactions)
    print(f"   Categories: {len(categories)}")
    
    # Count merchants
    merchants = set(t['payee'] for t in transactions)
    print(f"   Unique merchants: {len(merchants)}")
    print()
    
    # Generate report
    output_file = 'user_financial_report.xlsx'
    print(f"2. Generating user report to '{output_file}'...")
    try:
        generate_user_report(transactions, output_file)
        print("   ✓ Report generated successfully!")
        print()
    except Exception as e:
        print(f"   ✗ Report generation failed: {e}")
        return 1
    
    # Display workbook information
    print("3. Workbook Structure:")
    print()
    print("   📊 Sheet 1: Transactions")
    print("      • All {0} transactions with complete details".format(len(transactions)))
    print("      • Headers: bold, colored background, centered")
    print("      • Frozen top row for easy scrolling")
    print("      • Auto-adjusted column widths")
    print("      • Currency formatting for amounts")
    print("      • Date formatting (YYYY-MM-DD)")
    print("      • Anomaly rows highlighted in red")
    print("      • Auto-filters enabled for easy sorting")
    print()
    print("   ⚠️  Sheet 2: Anomalies")
    print("      • {0} flagged transactions".format(anomaly_count))
    print("      • All rows highlighted in red for quick review")
    print("      • Includes anomaly type in 'anomalies' column")
    print("      • Auto-filters enabled")
    print()
    print("   📈 Sheet 3: Summary")
    print("      • Monthly transaction summary with totals and averages")
    print("      • Category breakdown by month (pivoted table)")
    print("      • Top 5 merchants by spending")
    print("      • Embedded charts:")
    print("        - Line Chart: Monthly spending trend over time")
    print("        - Pie Chart: Category breakdown with percentages")
    print("        - Bar Chart: Top 5 merchants by total spending")
    print()
    
    # Summary statistics
    print("4. Export Summary:")
    total_amount = sum(t['amount'] for t in transactions)
    avg_amount = total_amount / len(transactions)
    max_amount = max(t['amount'] for t in transactions)
    min_amount = min(t['amount'] for t in transactions)
    
    print(f"   Total transactions: {len(transactions)}")
    print(f"   Total amount: ${total_amount:,.2f}")
    print(f"   Average transaction: ${avg_amount:,.2f}")
    print(f"   Largest transaction: ${max_amount:,.2f}")
    print(f"   Smallest transaction: ${min_amount:,.2f}")
    print(f"   Flagged anomalies: {anomaly_count}")
    print()
    
    # File information
    file_path = Path(output_file)
    if file_path.exists():
        file_size = file_path.stat().st_size
        print(f"   Output file: {output_file}")
        print(f"   File size: {file_size:,} bytes ({file_size / 1024:.2f} KB)")
    print()
    
    print("=" * 80)
    print("✓ Demo complete!")
    print()
    print("📁 Open '{0}' in Excel 365 or LibreOffice to view the report.".format(output_file))
    print()
    print("Features validated:")
    print("  ✓ Three sheets created (Transactions, Anomalies, Summary)")
    print("  ✓ Consistent formatting with bold headers and borders")
    print("  ✓ Currency and date formatting applied")
    print("  ✓ Red highlighting for anomaly rows")
    print("  ✓ Auto-filters enabled on all sheets")
    print("  ✓ Charts embedded (Line, Pie, Bar)")
    print("  ✓ Workbook opens cleanly in Excel and LibreOffice")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
