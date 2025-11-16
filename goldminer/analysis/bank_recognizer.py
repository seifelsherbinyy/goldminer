"""
Bank Pattern Recognition module for identifying banks from SMS messages.

This module provides functionality for determining the issuing bank by matching
SMS content against known pattern fragments. It supports both exact regex matching
and fuzzy matching for partial overlaps.
"""
import re
import yaml
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from fuzzywuzzy import fuzz
from goldminer.utils import setup_logger


class BankPatternRecognizer:
    """
    Recognizes banks from SMS messages using pattern matching.
    
    This class loads bank patterns from a YAML configuration file and provides
    methods to identify banks from SMS text. It supports both exact regex matching
    and fuzzy matching for improved accuracy.
    
    Attributes:
        bank_patterns (Dict[str, List[str]]): Dictionary mapping bank IDs to their patterns
        fuzzy_threshold (int): Minimum fuzzy matching score (0-100) to consider a match
        logger: Logger instance for tracking matches and unmatched messages
    
    Examples:
        >>> recognizer = BankPatternRecognizer()
        >>> bank = recognizer.identify_bank("Your HSBC card ending 1234 was used")
        >>> print(bank)
        'HSBC'
        
        >>> bank = recognizer.identify_bank("تم الخصم من بطاقتك من CIB")
        >>> print(bank)
        'CIB'
        
        >>> bank = recognizer.identify_bank("Unknown message")
        >>> print(bank)
        'unknown_bank'
    """
    
    def __init__(
        self,
        patterns_file: Optional[str] = None,
        fuzzy_threshold: int = 80,
        enable_fuzzy: bool = True
    ):
        """
        Initialize the BankPatternRecognizer.
        
        Args:
            patterns_file: Path to YAML file containing bank patterns.
                          If None, uses default 'bank_patterns.yaml' in project root.
            fuzzy_threshold: Minimum fuzzy matching score (0-100) to consider a match.
                           Default is 80. Higher values require closer matches.
            enable_fuzzy: Whether to enable fuzzy matching. Default is True.
        
        Raises:
            FileNotFoundError: If patterns file doesn't exist
            ValueError: If patterns file is invalid or empty
        """
        self.logger = setup_logger(__name__)
        self.fuzzy_threshold = fuzzy_threshold
        self.enable_fuzzy = enable_fuzzy
        
        # Determine patterns file path
        if patterns_file is None:
            # Default to bank_patterns.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            patterns_file = project_root / 'bank_patterns.yaml'
        
        self.patterns_file = str(patterns_file)
        
        # Load patterns
        self.bank_patterns = self._load_patterns()
        
        self.logger.info(
            f"BankPatternRecognizer initialized with {len(self.bank_patterns)} banks, "
            f"fuzzy_threshold={fuzzy_threshold}, fuzzy_enabled={enable_fuzzy}"
        )
    
    def _load_patterns(self) -> Dict[str, List[str]]:
        """
        Load bank patterns from YAML file.
        
        Returns:
            Dictionary mapping bank IDs to lists of pattern strings
            
        Raises:
            FileNotFoundError: If patterns file doesn't exist
            ValueError: If patterns file is invalid or empty
        """
        if not os.path.exists(self.patterns_file):
            self.logger.error(f"Patterns file not found: {self.patterns_file}")
            raise FileNotFoundError(f"Bank patterns file not found: {self.patterns_file}")
        
        try:
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                patterns = yaml.safe_load(f)
            
            if not patterns or not isinstance(patterns, dict):
                raise ValueError("Patterns file must contain a valid dictionary")
            
            # Validate that all values are lists
            for bank_id, pattern_list in patterns.items():
                if not isinstance(pattern_list, list):
                    raise ValueError(f"Patterns for bank '{bank_id}' must be a list")
                if not pattern_list:
                    self.logger.warning(f"Bank '{bank_id}' has no patterns defined")
            
            self.logger.info(f"Loaded patterns for {len(patterns)} banks from {self.patterns_file}")
            return patterns
            
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file: {e}")
            raise ValueError(f"Invalid YAML in patterns file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading patterns: {e}")
            raise
    
    def _match_patterns(self, sms: str, patterns: List[str]) -> bool:
        """
        Check if SMS matches any of the given patterns using regex.
        
        Args:
            sms: SMS message text
            patterns: List of regex patterns to match against
            
        Returns:
            True if any pattern matches, False otherwise
        """
        sms_lower = sms.lower()
        
        for pattern in patterns:
            try:
                # Try case-insensitive regex match
                if re.search(pattern, sms, re.IGNORECASE):
                    return True
            except re.error:
                # If pattern is not valid regex, try exact substring match
                if pattern.lower() in sms_lower:
                    return True
        
        return False
    
    def _fuzzy_match_patterns(self, sms: str, patterns: List[str]) -> Tuple[bool, int]:
        """
        Check if SMS fuzzy matches any of the given patterns.
        
        Uses fuzzy string matching to find partial overlaps. This is useful
        for handling typos, abbreviations, or slight variations in SMS text.
        
        Args:
            sms: SMS message text
            patterns: List of patterns to fuzzy match against
            
        Returns:
            Tuple of (match_found, best_score) where match_found is True if
            any pattern scores above the threshold, and best_score is the
            highest fuzzy matching score found.
        """
        best_score = 0
        
        for pattern in patterns:
            # Use partial ratio for substring matching
            score = fuzz.partial_ratio(pattern.lower(), sms.lower())
            best_score = max(best_score, score)
            
            if score >= self.fuzzy_threshold:
                return True, score
        
        return False, best_score
    
    def identify_bank(self, sms: str, return_confidence: bool = False) -> str:
        """
        Identify the bank from an SMS message.
        
        This method attempts to match the SMS against known bank patterns using:
        1. Exact regex pattern matching
        2. Fuzzy matching (if enabled) for partial overlaps
        
        The first bank with a matching pattern is returned. If no match is found,
        'unknown_bank' is returned and the SMS is logged for review.
        
        Args:
            sms: SMS message text to analyze
            return_confidence: If True, returns tuple of (bank_id, confidence_score).
                             Confidence is 100 for exact matches, fuzzy score for fuzzy matches.
                             Default is False.
            
        Returns:
            Bank ID string (e.g., 'HSBC', 'CIB') or 'unknown_bank' if no match found.
            If return_confidence is True, returns tuple of (bank_id, confidence_score).
            
        Examples:
            >>> recognizer = BankPatternRecognizer()
            >>> recognizer.identify_bank("Your HSBC card was charged")
            'HSBC'
            
            >>> recognizer.identify_bank("CIB: Your balance is 1000")
            'CIB'
            
            >>> recognizer.identify_bank("تم الخصم من بطاقتك من CIB")
            'CIB'
            
            >>> recognizer.identify_bank("Unknown bank message")
            'unknown_bank'
            
            >>> recognizer.identify_bank("HSBC transaction", return_confidence=True)
            ('HSBC', 100)
        """
        if not sms or not isinstance(sms, str):
            self.logger.warning(f"Invalid SMS input: {type(sms)}")
            return ('unknown_bank', 0) if return_confidence else 'unknown_bank'
        
        sms = sms.strip()
        if not sms:
            self.logger.warning("Empty SMS message provided")
            return ('unknown_bank', 0) if return_confidence else 'unknown_bank'
        
        # Try exact pattern matching first
        for bank_id, patterns in self.bank_patterns.items():
            if self._match_patterns(sms, patterns):
                self.logger.info(f"Exact match found: {bank_id} for SMS: {sms[:50]}...")
                return (bank_id, 100) if return_confidence else bank_id
        
        # Try fuzzy matching if enabled
        if self.enable_fuzzy:
            best_bank = None
            best_score = 0
            
            for bank_id, patterns in self.bank_patterns.items():
                matched, score = self._fuzzy_match_patterns(sms, patterns)
                if matched and score > best_score:
                    best_bank = bank_id
                    best_score = score
            
            if best_bank:
                self.logger.info(
                    f"Fuzzy match found: {best_bank} (score={best_score}) for SMS: {sms[:50]}..."
                )
                return (best_bank, best_score) if return_confidence else best_bank
        
        # No match found - log for review
        self.logger.warning(f"No bank match found for SMS: {sms[:100]}...")
        return ('unknown_bank', 0) if return_confidence else 'unknown_bank'
    
    def identify_banks_batch(
        self,
        sms_list: List[str],
        return_confidence: bool = False
    ) -> List[str]:
        """
        Identify banks from a batch of SMS messages.
        
        Args:
            sms_list: List of SMS message texts
            return_confidence: If True, returns list of tuples (bank_id, confidence_score)
            
        Returns:
            List of bank IDs (or tuples if return_confidence=True) corresponding
            to each SMS in the input list
            
        Examples:
            >>> recognizer = BankPatternRecognizer()
            >>> messages = ["HSBC transaction", "CIB alert", "Unknown"]
            >>> recognizer.identify_banks_batch(messages)
            ['HSBC', 'CIB', 'unknown_bank']
        """
        results = []
        for sms in sms_list:
            result = self.identify_bank(sms, return_confidence=return_confidence)
            results.append(result)
        
        self.logger.info(f"Processed batch of {len(sms_list)} SMS messages")
        return results
    
    def get_bank_statistics(self, sms_list: List[str]) -> Dict[str, int]:
        """
        Get statistics on bank distribution in a list of SMS messages.
        
        Args:
            sms_list: List of SMS message texts
            
        Returns:
            Dictionary mapping bank IDs to their occurrence counts
            
        Examples:
            >>> recognizer = BankPatternRecognizer()
            >>> messages = ["HSBC alert", "HSBC transaction", "CIB alert"]
            >>> recognizer.get_bank_statistics(messages)
            {'HSBC': 2, 'CIB': 1}
        """
        bank_ids = self.identify_banks_batch(sms_list)
        
        stats = {}
        for bank_id in bank_ids:
            stats[bank_id] = stats.get(bank_id, 0) + 1
        
        self.logger.info(f"Generated statistics for {len(sms_list)} messages across {len(stats)} banks")
        return stats
    
    def reload_patterns(self, patterns_file: Optional[str] = None) -> None:
        """
        Reload bank patterns from file.
        
        Useful for updating patterns without recreating the recognizer instance.
        
        Args:
            patterns_file: Path to patterns file. If None, reloads from current file.
        """
        if patterns_file is not None:
            self.patterns_file = patterns_file
        
        self.bank_patterns = self._load_patterns()
        self.logger.info("Bank patterns reloaded successfully")
