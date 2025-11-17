"""
Anomaly Detection module for identifying unusual transaction patterns.

This module provides the AnomalyDetector class for detecting anomalies including:
- High value transactions (above historical percentile)
- Burst frequency (same merchant used frequently in short time)
- Unknown merchants (payee not seen in recent history)
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import yaml
from functools import lru_cache
from goldminer.utils import setup_logger


class AnomalyDetector:
    """
    Detects anomalies in transaction data using configurable rules.
    
    Supports three types of anomaly detection:
    1. high_value: Amount exceeds user's historical 90th percentile
    2. burst_frequency: Same merchant used ≥ 3 times within 24h
    3. unknown_merchant: Payee not seen in past 100 transactions
    
    Uses pandas rolling statistics and optional caching for performance.
    
    Attributes:
        config: Configuration dictionary from anomaly_config.yaml
        logger: Logger instance for tracking operations
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the AnomalyDetector.
        
        Args:
            config_path: Path to anomaly_config.yaml. If None, uses default.
        """
        self.logger = setup_logger(__name__)
        
        # Load configuration
        if config_path is None:
            # Default to anomaly_config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "anomaly_config.yaml"
        
        self.config = self._load_config(config_path)
        self.logger.info(f"AnomalyDetector initialized with config from {config_path}")
        
        # Extract configuration values
        self.high_value_percentile = self.config['anomaly_detection']['high_value']['percentile']
        self.min_history_transactions = self.config['anomaly_detection']['high_value']['min_history_transactions']
        self.burst_count_threshold = self.config['anomaly_detection']['burst_frequency']['count_threshold']
        self.burst_time_window_hours = self.config['anomaly_detection']['burst_frequency']['time_window_hours']
        self.unknown_merchant_window = self.config['anomaly_detection']['unknown_merchant']['history_window']
        self.enabled_rules = self.config['anomaly_detection']['enabled_rules']
        self.caching_enabled = self.config['anomaly_detection']['caching']['enabled']
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            FileNotFoundError: If config file doesn't exist
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            self.logger.warning(f"Config file not found: {config_path}, using defaults")
            # Return default configuration
            return {
                'anomaly_detection': {
                    'high_value': {'percentile': 90, 'min_history_transactions': 10},
                    'burst_frequency': {'count_threshold': 3, 'time_window_hours': 24},
                    'unknown_merchant': {'history_window': 100},
                    'enabled_rules': ['high_value', 'burst_frequency', 'unknown_merchant'],
                    'caching': {'enabled': True, 'max_cache_size': 1000}
                }
            }
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def detect_anomalies(self, transaction: dict, history: List[dict]) -> List[str]:
        """
        Detect anomalies for a single transaction against its history.
        
        Args:
            transaction: Dictionary containing current transaction data with keys:
                - amount: Transaction amount (float)
                - payee or merchant: Merchant/payee name (str)
                - date or timestamp: Transaction date (str or datetime)
            history: List of historical transaction dictionaries with same structure
            
        Returns:
            List of anomaly flags detected (e.g., ['high_value', 'unknown_merchant'])
        """
        anomalies = []
        
        # Validate transaction structure
        if not transaction or not isinstance(transaction, dict):
            self.logger.warning("Invalid transaction format")
            return anomalies
        
        # Check each enabled rule
        if 'high_value' in self.enabled_rules:
            if self._detect_high_value(transaction, history):
                anomalies.append('high_value')
        
        if 'burst_frequency' in self.enabled_rules:
            if self._detect_burst_frequency(transaction, history):
                anomalies.append('burst_frequency')
        
        if 'unknown_merchant' in self.enabled_rules:
            if self._detect_unknown_merchant(transaction, history):
                anomalies.append('unknown_merchant')
        
        if anomalies:
            self.logger.info(f"Detected anomalies: {anomalies} for transaction")
        
        return anomalies
    
    def _detect_high_value(self, transaction: dict, history: List[dict]) -> bool:
        """
        Detect if transaction amount is above user's historical percentile.
        
        Args:
            transaction: Current transaction
            history: Historical transactions
            
        Returns:
            True if high_value anomaly detected, False otherwise
        """
        # Extract amount from transaction
        amount = transaction.get('amount')
        if amount is None:
            return False
        
        # Need minimum history for reliable percentile
        if len(history) < self.min_history_transactions:
            return False
        
        # Convert history to DataFrame for efficient percentile calculation
        try:
            amounts = []
            for txn in history:
                txn_amount = txn.get('amount')
                if txn_amount is not None:
                    amounts.append(float(txn_amount))
            
            if not amounts:
                return False
            
            # Calculate percentile using pandas
            df = pd.DataFrame({'amount': amounts})
            percentile_value = df['amount'].quantile(self.high_value_percentile / 100.0)
            
            # Check if current amount exceeds percentile
            return float(amount) > percentile_value
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Error calculating percentile: {e}")
            return False
    
    def _detect_burst_frequency(self, transaction: dict, history: List[dict]) -> bool:
        """
        Detect if same merchant is used too frequently in short time window.
        
        Args:
            transaction: Current transaction
            history: Historical transactions
            
        Returns:
            True if burst_frequency anomaly detected, False otherwise
        """
        # Extract merchant/payee from transaction
        merchant = transaction.get('payee') or transaction.get('merchant')
        if not merchant:
            return False
        
        # Extract transaction date
        txn_date = self._parse_date(transaction.get('date') or transaction.get('timestamp'))
        if not txn_date:
            return False
        
        # Calculate time window
        time_window_start = txn_date - timedelta(hours=self.burst_time_window_hours)
        
        # Count transactions to same merchant within time window
        try:
            count = 0
            for hist_txn in history:
                hist_merchant = hist_txn.get('payee') or hist_txn.get('merchant')
                hist_date = self._parse_date(hist_txn.get('date') or hist_txn.get('timestamp'))
                
                if (hist_merchant and hist_date and 
                    hist_merchant.lower().strip() == merchant.lower().strip() and
                    time_window_start <= hist_date <= txn_date):
                    count += 1
            
            # Include current transaction in count
            count += 1
            
            return count >= self.burst_count_threshold
            
        except Exception as e:
            self.logger.warning(f"Error detecting burst frequency: {e}")
            return False
    
    def _detect_unknown_merchant(self, transaction: dict, history: List[dict]) -> bool:
        """
        Detect if payee/merchant has not been seen in recent transaction history.
        
        Args:
            transaction: Current transaction
            history: Historical transactions
            
        Returns:
            True if unknown_merchant anomaly detected, False otherwise
        """
        # Extract merchant/payee from transaction
        merchant = transaction.get('payee') or transaction.get('merchant')
        if not merchant:
            return False
        
        merchant_normalized = merchant.lower().strip()
        
        # Look at last N transactions
        recent_history = history[-self.unknown_merchant_window:] if len(history) > self.unknown_merchant_window else history
        
        # Check if merchant appears in recent history
        try:
            for hist_txn in recent_history:
                hist_merchant = hist_txn.get('payee') or hist_txn.get('merchant')
                if hist_merchant and hist_merchant.lower().strip() == merchant_normalized:
                    return False  # Merchant found in history, not unknown
            
            # Merchant not found in recent history
            return True
            
        except Exception as e:
            self.logger.warning(f"Error detecting unknown merchant: {e}")
            return False
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """
        Parse date from various formats.
        
        Args:
            date_value: Date value (str, datetime, or None)
            
        Returns:
            datetime object or None if parsing fails
        """
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            # Try common date formats
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue
        
        return None
    
    def detect_anomalies_batch(self, transactions: List[dict]) -> Dict[int, List[str]]:
        """
        Detect anomalies for a batch of transactions.
        
        Each transaction is checked against all previous transactions in the batch
        as its history.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Dictionary mapping transaction index to list of anomaly flags
        """
        results = {}
        
        for idx, transaction in enumerate(transactions):
            # Use all previous transactions as history
            history = transactions[:idx]
            anomalies = self.detect_anomalies(transaction, history)
            if anomalies:
                results[idx] = anomalies
        
        return results
    
    def generate_report(self, transactions: List[dict]) -> Dict[str, Any]:
        """
        Generate a comprehensive anomaly detection report for a batch of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Report dictionary with statistics and detected anomalies
        """
        anomaly_results = self.detect_anomalies_batch(transactions)
        
        # Count anomalies by type
        anomaly_counts = {
            'high_value': 0,
            'burst_frequency': 0,
            'unknown_merchant': 0
        }
        
        for anomalies in anomaly_results.values():
            for anomaly_type in anomalies:
                if anomaly_type in anomaly_counts:
                    anomaly_counts[anomaly_type] += 1
        
        report = {
            'total_transactions': len(transactions),
            'total_anomalies_detected': len(anomaly_results),
            'anomaly_rate': len(anomaly_results) / len(transactions) if transactions else 0,
            'anomaly_counts': anomaly_counts,
            'anomalies_by_transaction': anomaly_results
        }
        
        self.logger.info(f"Generated anomaly report: {len(anomaly_results)} anomalies in {len(transactions)} transactions")
        
        return report
