"""
CardClassifier for extracting card suffixes and mapping to account metadata.

This module provides functionality for extracting card suffixes from SMS messages
in both English and Arabic, and looking up associated account metadata.
"""
import re
import yaml
import os
from typing import Dict, Optional, Any
from pathlib import Path
from goldminer.utils import setup_logger


class CardClassifier:
    """
    Extracts card suffixes from SMS messages and maps them to account metadata.
    
    This class handles card suffix extraction in both English and Arabic,
    normalizes Arabic-Indic numerals, and provides account metadata lookup
    from a YAML data source.
    
    Attributes:
        accounts_file (str): Path to accounts metadata YAML file
        accounts (Dict): Dictionary mapping card suffixes to account metadata
        logger: Logger instance for tracking operations
    """
    
    def __init__(self, accounts_file: Optional[str] = None):
        """
        Initialize the CardClassifier.
        
        Args:
            accounts_file: Path to YAML file containing account metadata.
                          If None, uses default 'accounts.yaml' in project root.
        
        Raises:
            FileNotFoundError: If accounts file doesn't exist
            ValueError: If accounts file is invalid or malformed
        
        Examples:
            >>> classifier = CardClassifier()
            >>> isinstance(classifier.accounts, dict)
            True
        """
        self.logger = setup_logger(__name__)
        
        # Determine accounts file path
        if accounts_file is None:
            # Default to accounts.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            accounts_file = project_root / 'accounts.yaml'
        
        self.accounts_file = str(accounts_file)
        
        # Load account metadata
        self.accounts = self._load_accounts()
        
        self.logger.info(
            f"CardClassifier initialized with {len(self.accounts)} account records"
        )
    
    def _load_accounts(self) -> Dict[str, Dict[str, Any]]:
        """
        Load account metadata from YAML file.
        
        Returns:
            Dictionary mapping card suffixes to account metadata
            
        Raises:
            FileNotFoundError: If accounts file doesn't exist
            ValueError: If accounts file is invalid or malformed
        """
        if not os.path.exists(self.accounts_file):
            self.logger.warning(f"Accounts file not found: {self.accounts_file}")
            # Return empty dict if file doesn't exist (graceful fallback)
            return {}
        
        try:
            with open(self.accounts_file, 'r', encoding='utf-8') as f:
                accounts_data = yaml.safe_load(f)
            
            if not accounts_data:
                self.logger.warning("Accounts file is empty")
                return {}
            
            if not isinstance(accounts_data, dict):
                raise ValueError("Accounts file must contain a dictionary")
            
            # Validate account structure
            for suffix, metadata in accounts_data.items():
                if not isinstance(metadata, dict):
                    raise ValueError(f"Account metadata for suffix '{suffix}' must be a dictionary")
                
                # Ensure required fields exist
                required_fields = ['account_id', 'account_type']
                for field in required_fields:
                    if field not in metadata:
                        raise ValueError(f"Account '{suffix}' missing required field: {field}")
            
            self.logger.info(f"Loaded {len(accounts_data)} account records from {self.accounts_file}")
            return accounts_data
            
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file: {e}")
            raise ValueError(f"Invalid YAML in accounts file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading accounts: {e}")
            raise
    
    @staticmethod
    def convert_arabic_indic_numerals(text: str) -> str:
        """
        Convert Arabic-Indic numerals to Western (Latin) numerals.
        
        This method replaces Arabic-Indic digits (٠-٩) with Western equivalents (0-9).
        
        Args:
            text: Input text that may contain Arabic-Indic numerals
            
        Returns:
            Text with Arabic-Indic numerals converted to Western numerals
            
        Examples:
            >>> CardClassifier.convert_arabic_indic_numerals("١٢٣٤")
            '1234'
            >>> CardClassifier.convert_arabic_indic_numerals("رقم ١٢٣٤")
            'رقم 1234'
        """
        if not text or not isinstance(text, str):
            return text
        
        # Define the translation table for Arabic-Indic to Western numerals
        translation_table = str.maketrans({
            '٠': '0',  # U+0660
            '١': '1',  # U+0661
            '٢': '2',  # U+0662
            '٣': '3',  # U+0663
            '٤': '4',  # U+0664
            '٥': '5',  # U+0665
            '٦': '6',  # U+0666
            '٧': '7',  # U+0667
            '٨': '8',  # U+0668
            '٩': '9',  # U+0669
        })
        
        return text.translate(translation_table)
    
    @staticmethod
    def extract_card_suffix(sms: str) -> Optional[str]:
        """
        Extract card suffix from SMS text.
        
        Supports both English patterns (e.g., "ending 4321") and Arabic patterns
        (e.g., "رقم ١٢٣٤"). Returns normalized 4-digit suffix or None if not found.
        
        Args:
            sms: SMS message text to extract card suffix from
            
        Returns:
            4-digit card suffix as string, or None if not found
            
        Examples:
            >>> CardClassifier.extract_card_suffix("Transaction on card ending 1234")
            '1234'
            >>> CardClassifier.extract_card_suffix("بطاقة رقم ١٢٣٤")
            '1234'
            >>> CardClassifier.extract_card_suffix("HSBC card **5678 charged")
            '5678'
            >>> CardClassifier.extract_card_suffix("No card info here")
            
        """
        if not sms or not isinstance(sms, str):
            return None
        
        # Convert Arabic-Indic numerals first
        normalized_sms = CardClassifier.convert_arabic_indic_numerals(sms)
        
        # English patterns - various ways to indicate card suffix
        # Using word boundaries or lookahead to ensure exactly 4 digits
        english_patterns = [
            r'(?:ending|card ending|ends with)\s+(\d{4})(?!\d)',  # "ending 1234", "card ending 1234"
            r'(?:card|Card)\s+(?:number\s+)?(?:\*+\s*)?(\d{4})(?!\d)',  # "card 1234", "Card **1234"
            r'\*+(\d{4})(?!\d)',  # "**1234", "****1234"
        ]
        
        # Arabic patterns - various ways to indicate card suffix
        arabic_patterns = [
            r'(?:رقم|بطاقة رقم|ينتهي)\s+(\d{4})(?!\d)',  # "رقم 1234", "بطاقة رقم 1234"
            r'(?:بطاقة)\s+(?:\*+\s*)?(\d{4})(?!\d)',  # "بطاقة 1234", "بطاقة **1234"
        ]
        
        # Try all patterns
        all_patterns = english_patterns + arabic_patterns
        
        for pattern in all_patterns:
            match = re.search(pattern, normalized_sms, re.IGNORECASE | re.UNICODE)
            if match:
                suffix = match.group(1)
                # Ensure it's exactly 4 digits
                if len(suffix) == 4 and suffix.isdigit():
                    return suffix
        
        return None
    
    def lookup_account(self, card_suffix: str) -> Dict[str, Any]:
        """
        Look up account metadata by card suffix.
        
        Returns account information if the suffix is known, otherwise returns
        a fallback response with default/unknown values.
        
        Args:
            card_suffix: 4-digit card suffix to look up
            
        Returns:
            Dictionary containing account metadata:
                - account_id: Account identifier
                - account_type: Type (Credit, Debit, Prepaid)
                - interest_rate: Interest rate (for credit cards)
                - credit_limit: Credit limit (for credit cards)
                - billing_cycle: Billing cycle day
                - label: Human-readable label
                - card_suffix: The card suffix used for lookup
                - is_known: Boolean indicating if account was found
            
        Examples:
            >>> classifier = CardClassifier()
            >>> result = classifier.lookup_account("1234")
            >>> 'account_id' in result
            True
            >>> 'is_known' in result
            True
        """
        if not card_suffix:
            return self._create_fallback_account(card_suffix, "Invalid suffix")
        
        # Look up in loaded accounts
        if card_suffix in self.accounts:
            account_data = self.accounts[card_suffix].copy()
            account_data['card_suffix'] = card_suffix
            account_data['is_known'] = True
            
            self.logger.info(f"Found account for card suffix {card_suffix}")
            return account_data
        
        # Fallback for unknown suffix
        self.logger.warning(f"Unknown card suffix: {card_suffix}")
        return self._create_fallback_account(card_suffix, "Unknown card")
    
    def _create_fallback_account(self, card_suffix: Optional[str], label: str) -> Dict[str, Any]:
        """
        Create a fallback account record for unknown suffixes.
        
        Args:
            card_suffix: Card suffix (may be None)
            label: Label to use for the account
            
        Returns:
            Dictionary with default/unknown account values
        """
        return {
            'account_id': f'unknown_{card_suffix}' if card_suffix else 'unknown',
            'account_type': 'Unknown',
            'interest_rate': None,
            'credit_limit': None,
            'billing_cycle': None,
            'label': label,
            'card_suffix': card_suffix,
            'is_known': False
        }
    
    def classify_sms(self, sms: str) -> Dict[str, Any]:
        """
        Extract card suffix from SMS and return associated account metadata.
        
        Convenience method that combines extract_card_suffix and lookup_account.
        
        Args:
            sms: SMS message text
            
        Returns:
            Dictionary containing account metadata (or fallback if not found)
            
        Examples:
            >>> classifier = CardClassifier()
            >>> result = classifier.classify_sms("Transaction on card ending 1234")
            >>> 'account_id' in result
            True
        """
        suffix = self.extract_card_suffix(sms)
        if suffix is None:
            self.logger.debug("No card suffix found in SMS")
            return self._create_fallback_account(None, "No card suffix in SMS")
        
        return self.lookup_account(suffix)
    
    def reload_accounts(self, accounts_file: Optional[str] = None) -> None:
        """
        Reload account metadata from file.
        
        Useful for updating accounts without recreating the classifier instance.
        
        Args:
            accounts_file: Path to accounts file. If None, reloads from current file.
            
        Examples:
            >>> classifier = CardClassifier()
            >>> classifier.reload_accounts()  # Reload from same file
        """
        if accounts_file is not None:
            self.accounts_file = accounts_file
        
        self.accounts = self._load_accounts()
        self.logger.info("Accounts reloaded successfully")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
