"""Configuration manager for ETL pipeline."""
import os
import yaml
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """Manages configuration for the ETL pipeline."""
    
    def __init__(self, config_path: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file. If None, uses default.
        """
        if config_path is None:
            config_path = os.path.join(
                Path(__file__).parent.parent.parent, "config.yaml"
            )
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not os.path.exists(self.config_path):
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config or self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "database": {
                "path": "data/processed/goldminer.db",
                "table_name": "unified_data"
            },
            "data_sources": {
                "raw_data_dir": "data/raw",
                "processed_data_dir": "data/processed"
            },
            "etl": {
                "date_formats": [
                    "%Y-%m-%d",
                    "%m/%d/%Y",
                    "%d-%m-%Y",
                    "%Y/%m/%d",
                    "%d/%m/%Y",
                    "%B %d, %Y",
                    "%b %d, %Y",
                    "%Y-%m-%d %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S"
                ],
                "duplicate_columns": [],  # Empty means use all columns
                "normalization": {
                    "strip_whitespace": True,
                    "lowercase_columns": True,
                    "remove_special_chars": False
                }
            },
            "analysis": {
                "anomaly_detection": {
                    "zscore_threshold": 3.0,
                    "iqr_multiplier": 1.5
                },
                "trend_window": 7,  # days for moving average
                "forecasting": {
                    "horizon_months": 36,
                    "simulations": 500,
                    "risk_level": "balanced",
                    "risk_profiles": {
                        "conservative": {
                            "expected_return": 0.03,
                            "volatility": 0.06,
                            "reserve_months": 6,
                            "equity_allocation": 0.45
                        },
                        "balanced": {
                            "expected_return": 0.05,
                            "volatility": 0.12,
                            "reserve_months": 4,
                            "equity_allocation": 0.6
                        },
                        "aggressive": {
                            "expected_return": 0.07,
                            "volatility": 0.18,
                            "reserve_months": 3,
                            "equity_allocation": 0.75
                        }
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": "logs/goldminer.log"
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports nested keys with dots).
        
        Args:
            key: Configuration key (e.g., 'database.path')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save_config(self, config_path: str = None):
        """Save current configuration to file."""
        if config_path is None:
            config_path = self.config_path
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
