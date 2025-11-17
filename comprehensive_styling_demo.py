#!/usr/bin/env python3
"""
Comprehensive XLSX Styling Demo Script

This script demonstrates all the professional styling features of the XLSXExporter,
showcasing at least three distinct styles per sheet:
1. Header style (dark gray background, white bold text, Calibri)
2. Numeric/currency style (currency formatting, Calibri)
3. Tagged text style (anomaly tags, styled text)
4. Alternating row shading (light gray for better readability)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.etl import XLSXExporter


def generate_comprehensive_demo_transactions(num_transactions=200):
    """
    Generate comprehensive sample transaction data with various features
    to showcase all styling capabilities.
    
    Args:
        num_transactions: Number of transactions to generate
        
    Returns:
        List of transaction dictionaries
    """
    categories = [
        'Food & Dining', 'Transportation', 'Entertainment', 'Bills & Utilities', 
        'Shopping', 'Healthcare', 'Travel', 'Education', 'Personal Care', 'Gifts'
    ]
    
    payees = [
        'Whole Foods Market', 'Uber', 'Netflix', 'Electric Company',
        'Amazon', 'CVS Pharmacy', 'Delta Airlines', 'University',
        'Starbucks', 'Shell Gas Station', 'AMC Theatres', 'AT&T',
        'Target', 'Kaiser Permanente', 'Marriott Hotel', 'Barnes & Noble',
        'Chipotle', 'Lyft', 'Spotify', 'Water Utility',
        'Best Buy', 'Walgreens', 'United Airlines', 'Coursera'
    ]
    
    accounts = ['Credit-Card-VISA-1234', 'Debit-Card-5678', 'Checking-Account-9012']
    account_types = ['Credit', 'Debit', 'Checking']
    
    anomaly_types = ['high_value', 'burst_frequency', 'unknown_merchant', 'duplicate', 'unusual_time']
    urgency_levels = ['normal', 'low', 'medium', 'high']
    
    base_date = datetime.now() - timedelta(days=180)
    transactions = []
    
    for i in range(num_transactions):
        # Generate date within the last 6 months
        days_offset = random.randint(0, 180)
        transaction_date = base_date + timedelta(days=days_offset)
        
        # Generate amount with category-specific patterns
        category = random.choice(categories)
        if category == 'Bills & Utilities':
            amount = round(random.uniform(50, 300), 2)
        elif category == 'Travel':
            amount = round(random.uniform(200, 2500), 2)
        elif category == 'Food & Dining':
            amount = round(random.uniform(5, 150), 2)
        elif category == 'Shopping':
            amount = round(random.uniform(20, 800), 2)
        elif category == 'Healthcare':
            amount = round(random.uniform(30, 500), 2)
        else:
            amount = round(random.uniform(10, 600), 2)
        
        # Determine urgency based on amount
        if amount > 1000:
            urgency = 'high'
        elif amount > 500:
            urgency = 'medium'
        elif amount < 10:
            urgency = 'low'
        else:
            urgency = 'normal'
        
        # Add anomalies strategically
        anomaly_flag = ''
        if amount > 1500:
            anomaly_flag = 'high_value'
        elif i % 25 == 0:  # Periodic anomalies
            anomaly_flag = random.choice(anomaly_types)
        
        account_idx = i % len(accounts)
        
        # Add some tags for interesting transactions
        tags = []
        if category == 'Travel':
            tags.append('vacation')
        if amount > 1000:
            tags.append('large-purchase')
        if anomaly_flag:
            tags.append('flagged')
        
        transaction = {
            'id': f'TXN{i:06d}',
            'date': transaction_date.strftime('%Y-%m-%d'),
            'payee': random.choice(payees),
            'category': category,
            'subcategory': f'{category.split()[0]}-Sub',
            'amount': amount,
            'currency': 'USD',
            'account_id': accounts[account_idx],
            'account_type': account_types[account_idx],
            'urgency': urgency,
            'tags': ','.join(tags) if tags else '',
            'anomalies': anomaly_flag,
            'confidence': 'high' if anomaly_flag == '' else 'medium' if amount < 2000 else 'low'
        }
        
        transactions.append(transaction)
    
    return transactions


def print_style_summary(transactions):
    """Print a summary of the styles that will be applied."""
    print()
    print("=" * 80)
    print("STYLING FEATURES DEMONSTRATED")
    print("=" * 80)
    print()
    
    print("📋 STYLE 1: Header Style")
    print("   • Dark gray background (#404040)")
    print("   • White bold text (Calibri 11pt)")
    print("   • Centered alignment with text wrapping")
    print("   • Applied to: All header rows in all sheets")
    print()
    
    print("💰 STYLE 2: Numeric/Currency Style")
    print("   • Currency formatting ($X,XXX.XX)")
    print("   • Calibri 11pt font")
    print("   • Applied to: Amount columns in all sheets")
    
    # Count currency values
    total_amount = sum(t['amount'] for t in transactions)
    max_amount = max(t['amount'] for t in transactions)
    min_amount = min(t['amount'] for t in transactions)
    print(f"   • Total amount: ${total_amount:,.2f}")
    print(f"   • Range: ${min_amount:,.2f} - ${max_amount:,.2f}")
    print()
    
    print("🏷️  STYLE 3: Tagged Text Style")
    print("   • Italic font with custom color for anomaly tags")
    print("   • Red borders for anomaly rows")
    print("   • Applied to: Anomaly-flagged transactions")
    
    # Count anomalies
    anomaly_count = sum(1 for t in transactions if t['anomalies'])
    anomaly_types = set(t['anomalies'] for t in transactions if t['anomalies'])
    print(f"   • Anomalies detected: {anomaly_count}")
    print(f"   • Anomaly types: {', '.join(sorted(anomaly_types))}")
    print()
    
    print("🎨 STYLE 4: Alternating Row Shading")
    print("   • Light gray background (#F2F2F2)")
    print("   • Applied to every other row for better scannability")
    print("   • Applied to: All data tables in all sheets")
    print()
    
    print("📊 STYLE 5: Urgency-Based Conditional Formatting")
    print("   • High urgency: Red background with bold white text")
    print("   • Medium urgency: Yellow background")
    print("   • Normal/Low urgency: Light green tint")
    
    # Count by urgency
    urgency_counts = {}
    for t in transactions:
        urgency = t.get('urgency', 'normal')
        urgency_counts[urgency] = urgency_counts.get(urgency, 0) + 1
    
    print(f"   • High urgency: {urgency_counts.get('high', 0)} transactions")
    print(f"   • Medium urgency: {urgency_counts.get('medium', 0)} transactions")
    print(f"   • Normal urgency: {urgency_counts.get('normal', 0)} transactions")
    print(f"   • Low urgency: {urgency_counts.get('low', 0)} transactions")
    print()
    
    print("✨ Additional Features:")
    print("   • Freeze panes on all sheets (first row frozen)")
    print("   • Auto-adjusted column widths for optimal readability")
    print("   • Consistent Calibri font across all sheets")
    print("   • Professional borders on all cells")
    print("   • Charts with matching color scheme (Monthly Summary)")
    print()


def main():
    """Main demonstration function."""
    print("=" * 80)
    print("COMPREHENSIVE XLSX STYLING DEMO")
    print("Demonstrating Professional Excel Export with Multiple Styles")
    print("=" * 80)
    print()
    
    # Generate sample data
    print("1. Generating comprehensive sample transaction data...")
    transactions = generate_comprehensive_demo_transactions(200)
    print(f"   Generated {len(transactions)} transactions")
    print(f"   Date range: {transactions[0]['date']} to {transactions[-1]['date']}")
    
    # Print style summary
    print_style_summary(transactions)
    
    # Create exporter
    print("2. Initializing XLSXExporter with professional styling...")
    exporter = XLSXExporter()
    print("   ✓ Style templates loaded")
    print("   ✓ Font: Calibri 11pt")
    print("   ✓ Header color: Dark gray (#404040)")
    print("   ✓ Alternating row shading: Light gray (#F2F2F2)")
    print()
    
    # Export to Excel
    output_file = 'comprehensive_styling_demo.xlsx'
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
    print()
    print("   📄 Sheet 1: Transactions")
    print("      • All transaction details with full styling")
    print("      • Styles applied: Headers, Currency, Alternating Rows, Urgency, Anomaly Borders")
    print()
    print("   📄 Sheet 2: Monthly Summary")
    print("      • Aggregated data with monthly totals and category breakdowns")
    print("      • Styles applied: Headers, Currency, Alternating Rows, Charts")
    print()
    print("   📄 Sheet 3: Anomalies")
    print("      • Flagged transactions with enhanced visibility")
    print("      • Styles applied: Headers, Currency, Alternating Rows, Urgency, Anomaly Borders")
    print()
    
    # Summary statistics
    print("5. Export Summary:")
    total_amount = sum(t['amount'] for t in transactions)
    avg_amount = total_amount / len(transactions)
    max_amount = max(t['amount'] for t in transactions)
    min_amount = min(t['amount'] for t in transactions)
    anomaly_count = sum(1 for t in transactions if t['anomalies'])
    
    print(f"   Total transactions: {len(transactions)}")
    print(f"   Total amount: ${total_amount:,.2f}")
    print(f"   Average amount: ${avg_amount:,.2f}")
    print(f"   Max amount: ${max_amount:,.2f}")
    print(f"   Min amount: ${min_amount:,.2f}")
    print(f"   Anomalies flagged: {anomaly_count}")
    print()
    
    print("=" * 80)
    print(f"✅ Export complete! Open '{output_file}' in Excel to view:")
    print()
    print("   • 5+ distinct styles applied consistently across all sheets")
    print("   • Professional dark gray headers with white bold text")
    print("   • Alternating row shading for easy data scanning")
    print("   • Currency formatting for all monetary values")
    print("   • Conditional formatting for urgency levels")
    print("   • Special styling for anomaly-flagged transactions")
    print("=" * 80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
