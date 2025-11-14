"""
Simple Visualization Examples for Transaction Analysis

This script demonstrates how to create simple visualizations using matplotlib
for the transaction analysis data. These are optional and require matplotlib to be installed.

Install matplotlib:
    pip install matplotlib

"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Check if matplotlib is available
try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not installed. Install with: pip install matplotlib")
    print("These visualizations are optional and not required for core functionality.")

from goldminer.analysis import TransactionAnalyzer


def generate_sample_data(days=30):
    """Generate sample transaction data for visualization."""
    dates = []
    amounts = []
    base_date = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        for hour in range(24):
            num_transactions = np.random.randint(3, 10)
            for _ in range(num_transactions):
                timestamp = base_date + timedelta(
                    days=day, 
                    hours=hour, 
                    minutes=np.random.randint(0, 60)
                )
                base_amount = 100 if 9 <= hour <= 17 else 50
                amount = base_amount * np.random.uniform(0.5, 2.0)
                dates.append(timestamp)
                amounts.append(amount)
    
    return pd.DataFrame({'timestamp': dates, 'amount': amounts})


def plot_time_series(analyzer, df):
    """Plot daily time series with moving average."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
    daily_with_ma = analyzer.calculate_moving_averages(daily, 'amount_sum', windows=[7])
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot daily values
    ax.plot(pd.to_datetime(daily_with_ma['date']), 
            daily_with_ma['amount_sum'], 
            'o-', label='Daily Total', alpha=0.6)
    
    # Plot 7-day moving average
    ax.plot(pd.to_datetime(daily_with_ma['date']), 
            daily_with_ma['amount_sum_ma7'], 
            '-', linewidth=2, label='7-Day Moving Average')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Transaction Amount ($)')
    ax.set_title('Daily Transaction Amounts with Moving Average')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('/tmp/time_series_plot.png', dpi=300, bbox_inches='tight')
    print("✓ Time series plot saved to /tmp/time_series_plot.png")
    plt.close()


def plot_hourly_distribution(analyzer, df):
    """Plot hourly distribution as bar chart."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    hourly = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='sum')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    bars = ax.bar(hourly['hour'], hourly['amount_sum'], color='steelblue', alpha=0.7)
    
    # Highlight peak hours
    peak_hour_idx = hourly['amount_sum'].idxmax()
    bars[peak_hour_idx].set_color('darkred')
    
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Total Transaction Amount ($)')
    ax.set_title('Transaction Distribution by Hour of Day')
    ax.set_xticks(range(0, 24, 2))
    ax.grid(True, axis='y', alpha=0.3)
    
    # Add value labels on bars
    for i, bar in enumerate(bars):
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:.0f}',
                   ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('/tmp/hourly_distribution.png', dpi=300, bbox_inches='tight')
    print("✓ Hourly distribution plot saved to /tmp/hourly_distribution.png")
    plt.close()


def plot_anomalies(analyzer, df):
    """Plot daily data with anomalies highlighted."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
    anomalies = analyzer.detect_spikes_and_drops(daily, 'amount_sum', method='iqr')
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot all data
    dates = pd.to_datetime(daily['date'])
    values = daily['amount_sum']
    ax.plot(dates, values, 'o-', label='Daily Total', alpha=0.6)
    
    # Highlight spikes in red
    if anomalies['spikes']:
        spike_dates = [pd.to_datetime(s['date']) for s in anomalies['spikes']]
        spike_values = [s['value'] for s in anomalies['spikes']]
        ax.scatter(spike_dates, spike_values, color='red', s=100, 
                  label='Spikes', zorder=5, marker='^')
    
    # Highlight drops in orange
    if anomalies['drops']:
        drop_dates = [pd.to_datetime(d['date']) for d in anomalies['drops']]
        drop_values = [d['value'] for d in anomalies['drops']]
        ax.scatter(drop_dates, drop_values, color='orange', s=100, 
                  label='Drops', zorder=5, marker='v')
    
    ax.set_xlabel('Date')
    ax.set_ylabel('Transaction Amount ($)')
    ax.set_title('Daily Transactions with Anomaly Detection (IQR Method)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig('/tmp/anomalies_plot.png', dpi=300, bbox_inches='tight')
    print("✓ Anomalies plot saved to /tmp/anomalies_plot.png")
    plt.close()


def plot_performance_dashboard(analyzer, df):
    """Create a multi-panel dashboard."""
    if not MATPLOTLIB_AVAILABLE:
        return
    
    # Get data
    indicators = analyzer.calculate_performance_indicators(df, 'amount', 'timestamp')
    hourly = analyzer.summarize_by_hour(df, 'amount', 'timestamp', aggregation='mean')
    daily = analyzer.summarize_by_day(df, 'amount', 'timestamp')
    daily_with_ma = analyzer.calculate_moving_averages(daily, 'amount_sum', windows=[7])
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 10))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. Time series with moving average
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(pd.to_datetime(daily_with_ma['date']), daily_with_ma['amount_sum'], 
            'o-', alpha=0.5, label='Daily')
    ax1.plot(pd.to_datetime(daily_with_ma['date']), daily_with_ma['amount_sum_ma7'], 
            '-', linewidth=2, label='7-Day MA')
    ax1.set_title('Daily Transaction Trends', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Amount ($)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. Hourly distribution
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.bar(hourly['hour'], hourly['amount_mean'], color='steelblue', alpha=0.7)
    ax2.set_title('Average Transaction by Hour', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Hour of Day')
    ax2.set_ylabel('Avg Amount ($)')
    ax2.grid(True, axis='y', alpha=0.3)
    
    # 3. Transaction count by day of week
    ax3 = fig.add_subplot(gs[1, 1])
    day_counts = daily.groupby('day_of_week')['transaction_count'].mean()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_counts = day_counts.reindex([d for d in day_order if d in day_counts.index])
    ax3.bar(range(len(day_counts)), day_counts.values, color='coral', alpha=0.7)
    ax3.set_title('Avg Transactions by Day of Week', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Day of Week')
    ax3.set_ylabel('Avg Transaction Count')
    ax3.set_xticks(range(len(day_counts)))
    ax3.set_xticklabels([d[:3] for d in day_counts.index], rotation=45)
    ax3.grid(True, axis='y', alpha=0.3)
    
    # 4. Summary metrics
    ax4 = fig.add_subplot(gs[2, :])
    ax4.axis('off')
    
    summary_text = f"""
    PERFORMANCE SUMMARY
    
    Total Transactions: {indicators['total_transactions']:,}
    Total Value: ${indicators['total_value']:,.2f}
    Average Transaction: ${indicators['average_value']:.2f}
    Median Transaction: ${indicators['median_value']:.2f}
    
    Date Range: {indicators['date_range']['start'][:10]} to {indicators['date_range']['end'][:10]}
    Total Days: {indicators['date_range']['days']}
    
    Min Transaction: ${indicators['min_value']:.2f}
    Max Transaction: ${indicators['max_value']:,.2f}
    Standard Deviation: ${indicators['std_deviation']:.2f}
    """
    
    ax4.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
            verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.suptitle('Transaction Analysis Dashboard', fontsize=16, fontweight='bold', y=0.995)
    plt.savefig('/tmp/dashboard.png', dpi=300, bbox_inches='tight')
    print("✓ Dashboard saved to /tmp/dashboard.png")
    plt.close()


def main():
    """Main execution."""
    if not MATPLOTLIB_AVAILABLE:
        print("\n⚠️  Matplotlib is not installed.")
        print("To use these visualizations, install matplotlib:")
        print("    pip install matplotlib")
        print("\nNote: Visualizations are optional. The core TransactionAnalyzer works without matplotlib.")
        return
    
    print("=" * 80)
    print("TRANSACTION ANALYSIS VISUALIZATIONS")
    print("=" * 80)
    print()
    
    # Generate sample data
    print("Generating sample transaction data...")
    df = generate_sample_data(days=30)
    print(f"Generated {len(df)} transactions")
    print()
    
    # Initialize analyzer
    analyzer = TransactionAnalyzer()
    
    # Create visualizations
    print("Creating visualizations...")
    print()
    
    plot_time_series(analyzer, df)
    plot_hourly_distribution(analyzer, df)
    plot_anomalies(analyzer, df)
    plot_performance_dashboard(analyzer, df)
    
    print()
    print("=" * 80)
    print("All visualizations created successfully!")
    print("=" * 80)
    print()
    print("Files saved to /tmp/:")
    print("  - time_series_plot.png")
    print("  - hourly_distribution.png")
    print("  - anomalies_plot.png")
    print("  - dashboard.png")
    print()
    print("These visualizations demonstrate how the TransactionAnalyzer data")
    print("can be used to create insightful charts and dashboards.")
    print()


if __name__ == "__main__":
    main()
