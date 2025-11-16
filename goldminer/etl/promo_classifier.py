"""
PromoClassifier module for identifying promotional/marketing SMS messages.

This module provides functionality to detect promotional and marketing messages
that should be filtered out before they enter the transaction processing pipeline.
It supports both English and Arabic keywords and can load custom keyword sets
from YAML configuration files.
"""
import os
import re
import yaml
from typing import Dict, List, Set, Optional, Any
from pathlib import Path
from goldminer.utils import setup_logger


class PromoResult:
    """
    Structured result object for promotional message classification.
    
    Attributes:
        skip: Boolean indicating whether the message should be skipped
        reason: Explanation of why the message was classified as promotional
        matched_keywords: List of keywords that were found in the message
        confidence: Confidence level of the classification ('high', 'medium', 'low')
    """
    
    def __init__(self, skip: bool = False, reason: str = "", 
                 matched_keywords: Optional[List[str]] = None,
                 confidence: str = "low"):
        """
        Initialize PromoResult.
        
        Args:
            skip: Whether to skip this message
            reason: Reason for classification
            matched_keywords: List of matched promotional keywords
            confidence: Confidence level ('high', 'medium', 'low')
        """
        self.skip = skip
        self.reason = reason
        self.matched_keywords = matched_keywords if matched_keywords else []
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'skip': self.skip,
            'reason': self.reason,
            'matched_keywords': self.matched_keywords,
            'confidence': self.confidence
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"PromoResult(skip={self.skip}, reason='{self.reason}', matched_keywords={self.matched_keywords}, confidence='{self.confidence}')"


class PromoClassifier:
    """
    Classifier for identifying promotional/marketing SMS messages.
    
    This classifier checks SMS messages against predefined keyword lists
    in both English and Arabic to determine if a message is promotional
    rather than a financial transaction. Promotional messages are flagged
    for filtering before they enter the main transaction pipeline.
    
    Features:
    - Supports English and Arabic promotional keywords
    - Case-insensitive matching for English keywords
    - Loads keyword sets from YAML configuration files
    - Returns structured results with skip flag and reason
    - Configurable confidence levels based on keyword matches
    
    Examples:
        >>> classifier = PromoClassifier()
        >>> result = classifier.is_promotional("Get 50% discount on all items!")
        >>> result.skip
        True
        >>> result.reason
        'Promotional message detected'
    """
    
    def __init__(self, keywords_file: Optional[str] = None):
        """
        Initialize PromoClassifier.
        
        Args:
            keywords_file: Path to YAML file containing promotional keywords.
                          If None, uses default keywords.
        """
        self.logger = setup_logger(__name__)
        self.english_keywords: Set[str] = set()
        self.arabic_keywords: Set[str] = set()
        
        # Load keywords from file or use defaults
        if keywords_file and os.path.exists(keywords_file):
            self._load_keywords_from_file(keywords_file)
        else:
            # Try to load from default location
            default_path = self._get_default_keywords_path()
            if default_path and os.path.exists(default_path):
                self._load_keywords_from_file(default_path)
            else:
                # Use hardcoded defaults
                self._load_default_keywords()
        
        self.logger.info(f"Initialized PromoClassifier with {len(self.english_keywords)} English "
                        f"and {len(self.arabic_keywords)} Arabic keywords")
    
    def _get_default_keywords_path(self) -> Optional[str]:
        """
        Get the default path for the promo_keywords.yaml file.
        
        Searches in the following locations:
        1. Same directory as this module
        2. Project root directory
        3. Current working directory
        
        Returns:
            Path to promo_keywords.yaml or None if not found
        """
        # Try module directory's parent (project root)
        module_dir = Path(__file__).parent.parent.parent
        candidate_paths = [
            module_dir / 'promo_keywords.yaml',
            Path.cwd() / 'promo_keywords.yaml',
        ]
        
        for path in candidate_paths:
            if path.exists():
                return str(path)
        
        return None
    
    def _load_default_keywords(self):
        """Load hardcoded default keywords."""
        self.english_keywords = {
            'offer', 'discount', 'sale', 'enjoy', 'special offer',
            'limited time', 'promotion', 'promo', 'deal', 'deals',
            'save', 'saving', 'cashback', 'reward', 'rewards',
            'exclusive', 'free', 'gift', 'bonus', 'win', 'winner',
            'congratulations', 'congrats', 'voucher', 'coupon', 'redeem'
        }
        
        # Note: Removed ambiguous keywords like "خصم" which can mean both "discount" and "debit"
        # Only use clearly promotional Arabic keywords
        self.arabic_keywords = {
            'عرض خاص', 'لفترة محدودة', 'عروض',
            'توفير', 'مجاني', 'هدية', 'مكافأة',
            'مكافآت', 'حصري', 'خصومات', 'استمتع', 'تخفيض',
            'تخفيضات', 'كاش باك', 'قسيمة', 'كوبون',
            'مبروك', 'فائز', 'اربح', 'جائزة', 'وفر الآن',
            'احصل على', 'فرصة'
        }
        
        self.logger.info("Loaded default promotional keywords")
    
    def _load_keywords_from_file(self, filepath: str):
        """
        Load promotional keywords from a YAML file.
        
        Args:
            filepath: Path to YAML file
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                self.logger.warning(f"Empty YAML file: {filepath}, using defaults")
                self._load_default_keywords()
                return
            
            # Load English keywords
            if 'english' in data and isinstance(data['english'], list):
                self.english_keywords = set(data['english'])
            
            # Load Arabic keywords
            if 'arabic' in data and isinstance(data['arabic'], list):
                self.arabic_keywords = set(data['arabic'])
            
            self.logger.info(f"Loaded keywords from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error loading keywords from {filepath}: {str(e)}")
            self.logger.info("Falling back to default keywords")
            self._load_default_keywords()
    
    def _find_matching_keywords(self, text: str) -> List[str]:
        """
        Find all matching promotional keywords in the text.
        
        Args:
            text: Text to search for keywords
            
        Returns:
            List of matched keywords
        """
        matched = []
        text_lower = text.lower()
        
        # Check English keywords (case-insensitive)
        for keyword in self.english_keywords:
            # Use word boundary matching to avoid partial matches
            # e.g., "discount" shouldn't match "discounted"
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched.append(keyword)
        
        # Check Arabic keywords (case-sensitive for Arabic)
        for keyword in self.arabic_keywords:
            if keyword in text:
                matched.append(keyword)
        
        return matched
    
    def is_promotional(self, sms: str) -> bool:
        """
        Check if an SMS message is promotional.
        
        This is a simple boolean method for backward compatibility.
        For detailed results, use classify() instead.
        
        Args:
            sms: SMS message text to classify
            
        Returns:
            True if the message is promotional, False otherwise
            
        Examples:
            >>> classifier = PromoClassifier()
            >>> classifier.is_promotional("Get 50% discount today!")
            True
            >>> classifier.is_promotional("Your card was charged 100 EGP")
            False
        """
        result = self.classify(sms)
        return result.skip
    
    def classify(self, sms: str) -> PromoResult:
        """
        Classify an SMS message as promotional or not.
        
        Returns a structured result with detailed information including:
        - Whether to skip the message
        - Reason for classification
        - List of matched keywords
        - Confidence level
        
        Args:
            sms: SMS message text to classify
            
        Returns:
            PromoResult object with classification details
            
        Examples:
            >>> classifier = PromoClassifier()
            >>> result = classifier.classify("Special offer: 50% off!")
            >>> result.skip
            True
            >>> result.matched_keywords
            ['special offer', 'offer', 'off']
            >>> result.confidence
            'high'
        """
        if not sms or not isinstance(sms, str):
            return PromoResult(
                skip=False,
                reason="Invalid input",
                confidence="low"
            )
        
        # Handle empty strings after strip
        sms_stripped = sms.strip()
        if not sms_stripped:
            return PromoResult(
                skip=False,
                reason="Invalid input",
                confidence="low"
            )
        
        # Find matching keywords
        matched_keywords = self._find_matching_keywords(sms_stripped)
        
        if not matched_keywords:
            # No promotional keywords found
            return PromoResult(
                skip=False,
                reason="No promotional keywords detected",
                confidence="high"
            )
        
        # Determine confidence based on number of matches
        num_matches = len(matched_keywords)
        if num_matches >= 3:
            confidence = "high"
        elif num_matches == 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Message is promotional
        keyword_list = ', '.join(matched_keywords[:3])  # Show up to 3 keywords
        if len(matched_keywords) > 3:
            keyword_list += f" (and {len(matched_keywords) - 3} more)"
        
        return PromoResult(
            skip=True,
            reason=f"Promotional message detected (keywords: {keyword_list})",
            matched_keywords=matched_keywords,
            confidence=confidence
        )
    
    def classify_batch(self, messages: List[str]) -> List[PromoResult]:
        """
        Classify a batch of SMS messages.
        
        Args:
            messages: List of SMS messages to classify
            
        Returns:
            List of PromoResult objects
            
        Examples:
            >>> classifier = PromoClassifier()
            >>> messages = [
            ...     "Special offer for you!",
            ...     "Your card was charged 100 EGP"
            ... ]
            >>> results = classifier.classify_batch(messages)
            >>> len(results)
            2
            >>> results[0].skip
            True
            >>> results[1].skip
            False
        """
        results = []
        
        for i, message in enumerate(messages):
            try:
                result = self.classify(message)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error classifying message {i}: {str(e)}")
                results.append(PromoResult(
                    skip=False,
                    reason=f"Classification error: {str(e)}",
                    confidence="low"
                ))
        
        # Log summary
        skipped = sum(1 for r in results if r.skip)
        self.logger.info(f"Classified batch of {len(messages)} messages: "
                        f"{skipped} promotional, {len(messages) - skipped} non-promotional")
        
        return results
    
    def add_keywords(self, english: Optional[List[str]] = None, 
                     arabic: Optional[List[str]] = None):
        """
        Add custom keywords to the classifier.
        
        Args:
            english: List of English keywords to add
            arabic: List of Arabic keywords to add
        """
        if english:
            self.english_keywords.update(english)
            self.logger.info(f"Added {len(english)} English keywords")
        
        if arabic:
            self.arabic_keywords.update(arabic)
            self.logger.info(f"Added {len(arabic)} Arabic keywords")
    
    def remove_keywords(self, english: Optional[List[str]] = None,
                       arabic: Optional[List[str]] = None):
        """
        Remove keywords from the classifier.
        
        Args:
            english: List of English keywords to remove
            arabic: List of Arabic keywords to remove
        """
        if english:
            self.english_keywords.difference_update(english)
            self.logger.info(f"Removed {len(english)} English keywords")
        
        if arabic:
            self.arabic_keywords.difference_update(arabic)
            self.logger.info(f"Removed {len(arabic)} Arabic keywords")
    
    def get_keywords(self) -> Dict[str, List[str]]:
        """
        Get current keyword sets.
        
        Returns:
            Dictionary with 'english' and 'arabic' keyword lists
        """
        return {
            'english': sorted(list(self.english_keywords)),
            'arabic': sorted(list(self.arabic_keywords))
        }


if __name__ == "__main__":
    import doctest
    doctest.testmod()
