#!/usr/bin/env python3
"""
Demonstration script for AnomalyDetector functionality.

This script showcases the three types of anomaly detection:
1. High value transactions (above 90th percentile)
2. Burst frequency (same merchant used ≥ 3 times within 24h)
3. Unknown merchants (not seen in past 100 transactions)
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from goldminer.analysis import AnomalyDetector


def demo_high_value_detection():
    """Demonstrate high value anomaly detection."""
    print("=" * 70)
    print("Demo 1: High Value Detection")
    print("=" * 70)
    
    detector = AnomalyDetector()
    
    # Create transaction history with amounts from 100 to 1000
    history = [
        {'amount': i * 100, 'payee': 'Regular Merchant', 'date': '2024-01-01'}
        for i in range(1, 11)
    ]
    
    print(f"\nTransaction history: 10 transactions with amounts 100-1000")
    print(f"90th percentile threshold: ~900")
    
    # Test normal transaction
    normal_txn = {
        'amount': 500,
        'payee': 'Regular Merchant',
        'date': '2024-01-15'
    }
    
    print(f"\nTest 1: Normal transaction (amount: {normal_txn['amount']})")
    anomalies = detector.detect_anomalies(normal_txn, history)
    print(f"Result: {anomalies if anomalies else 'No anomalies detected'}")
    
    # Test high value transaction
    high_value_txn = {
        'amount': 1500,
        'payee': 'Regular Merchant',
        'date': '2024-01-15'
    }
    
    print(f"\nTest 2: High value transaction (amount: {high_value_txn['amount']})")
    anomalies = detector.detect_anomalies(high_value_txn, history)
    print(f"Result: {anomalies}")
    print(f"✓ High value anomaly detected!")


def demo_burst_frequency_detection():
    """Demonstrate burst frequency anomaly detection."""
    print("\n" + "=" * 70)
    print("Demo 2: Burst Frequency Detection")
    print("=" * 70)
    
    detector = AnomalyDetector()
    base_time = datetime(2024, 1, 15, 10, 0, 0)
    
    # Create history with 2 recent transactions to same merchant
    history = [
        {
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': (base_time - timedelta(hours=12)).strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'amount': 50,
            'payee': 'Coffee Shop',
            'date': (base_time - timedelta(hours=6)).strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    print(f"\nTransaction history: 2 transactions to 'Coffee Shop' in last 12 hours")
    print(f"Burst threshold: 3 transactions within 24 hours")
    
    # Third transaction triggers burst
    burst_txn = {
        'amount': 50,
        'payee': 'Coffee Shop',
        'date': base_time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    print(f"\nTest: Third transaction to 'Coffee Shop' within 24h window")
    anomalies = detector.detect_anomalies(burst_txn, history)
    print(f"Result: {anomalies}")
    print(f"✓ Burst frequency anomaly detected!")


def demo_unknown_merchant_detection():
    """Demonstrate unknown merchant anomaly detection."""
    print("\n" + "=" * 70)
    print("Demo 3: Unknown Merchant Detection")
    print("=" * 70)
    
    detector = AnomalyDetector()
    
    # Create history with known merchants
    history = [
        {'amount': 50, 'payee': 'Coffee Shop', 'date': '2024-01-01'},
        {'amount': 60, 'payee': 'Restaurant ABC', 'date': '2024-01-02'},
        {'amount': 70, 'payee': 'Grocery Store', 'date': '2024-01-03'},
    ]
    
    print(f"\nKnown merchants in history:")
    for txn in history:
        print(f"  • {txn['payee']}")
    
    # Test known merchant
    known_txn = {
        'amount': 55,
        'payee': 'Coffee Shop',
        'date': '2024-01-15'
    }
    
    print(f"\nTest 1: Transaction to known merchant '{known_txn['payee']}'")
    anomalies = detector.detect_anomalies(known_txn, history)
    print(f"Result: {anomalies if anomalies else 'No anomalies detected'}")
    
    # Test unknown merchant
    unknown_txn = {
        'amount': 100,
        'payee': 'Brand New Store',
        'date': '2024-01-15'
    }
    
    print(f"\nTest 2: Transaction to unknown merchant '{unknown_txn['payee']}'")
    anomalies = detector.detect_anomalies(unknown_txn, history)
    print(f"Result: {anomalies}")
    print(f"✓ Unknown merchant anomaly detected!")


def demo_multiple_anomalies():
    """Demonstrate multiple anomalies in single transaction."""
    print("\n" + "=" * 70)
    print("Demo 4: Multiple Anomalies in Single Transaction")
    print("=" * 70)
    
    detector = AnomalyDetector()
    
    # Small history for high value detection
    history = [
        {'amount': i * 10, 'payee': 'Regular Store', 'date': '2024-01-01'}
        for i in range(1, 11)
    ]
    
    print(f"\nTransaction history: 10 transactions with amounts 10-100")
    print(f"Known merchants: Regular Store")
    
    # Transaction with multiple anomalies
    multi_anomaly_txn = {
        'amount': 500,  # High value
        'payee': 'Suspicious Store',  # Unknown merchant
        'date': '2024-01-15'
    }
    
    print(f"\nTest: Transaction with amount {multi_anomaly_txn['amount']} to '{multi_anomaly_txn['payee']}'")
    anomalies = detector.detect_anomalies(multi_anomaly_txn, history)
    print(f"Result: {anomalies}")
    print(f"✓ Multiple anomalies detected: {len(anomalies)} types")


def demo_batch_processing():
    """Demonstrate batch anomaly detection."""
    print("\n" + "=" * 70)
    print("Demo 5: Batch Anomaly Detection")
    print("=" * 70)
    
    detector = AnomalyDetector()
    
    # Create a batch of transactions
    transactions = [
        {'amount': 50, 'payee': 'Merchant A', 'date': '2024-01-01'},
        {'amount': 60, 'payee': 'Merchant B', 'date': '2024-01-02'},
        {'amount': 70, 'payee': 'Merchant A', 'date': '2024-01-03'},
        {'amount': 65, 'payee': 'Merchant C', 'date': '2024-01-04'},
        {'amount': 55, 'payee': 'Merchant B', 'date': '2024-01-05'},
        {'amount': 500, 'payee': 'Merchant D', 'date': '2024-01-06'},  # High value + unknown
    ]
    
    print(f"\nProcessing batch of {len(transactions)} transactions")
    
    # Process batch
    results = detector.detect_anomalies_batch(transactions)
    
    print(f"\nResults:")
    print(f"Total anomalies detected: {len(results)}")
    for idx, anomaly_list in results.items():
        txn = transactions[idx]
        print(f"  Transaction {idx}: {txn['payee']} (${txn['amount']}) → {anomaly_list}")
    
    # Generate comprehensive report
    report = detector.generate_report(transactions)
    print(f"\nSummary Report:")
    print(f"  Total transactions: {report['total_transactions']}")
    print(f"  Anomalies detected: {report['total_anomalies_detected']}")
    print(f"  Anomaly rate: {report['anomaly_rate']:.2%}")
    print(f"  Breakdown:")
    for anomaly_type, count in report['anomaly_counts'].items():
        print(f"    • {anomaly_type}: {count}")


def main():
    """Main execution function."""
    print("\n" + "=" * 70)
    print("GoldMiner Anomaly Detector - Demonstration")
    print("=" * 70)
    
    # Run all demos
    demo_high_value_detection()
    demo_burst_frequency_detection()
    demo_unknown_merchant_detection()
    demo_multiple_anomalies()
    demo_batch_processing()
    
    print("\n" + "=" * 70)
    print("Demonstration Complete!")
    print("=" * 70)
    print("\nKey Features:")
    print("  ✓ High value detection (90th percentile)")
    print("  ✓ Burst frequency detection (3+ times in 24h)")
    print("  ✓ Unknown merchant detection (not in last 100)")
    print("  ✓ Multiple anomaly detection per transaction")
    print("  ✓ Batch processing with comprehensive reports")
    print("  ✓ Configurable thresholds via anomaly_config.yaml")
    print("\nUsage:")
    print("  from goldminer.analysis import AnomalyDetector")
    print("  detector = AnomalyDetector()")
    print("  anomalies = detector.detect_anomalies(transaction, history)")
    print()


if __name__ == '__main__':
    main()
