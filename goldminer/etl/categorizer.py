"""
Categorizer module for assigning categories, subcategories, and tags to transactions.

This module provides intelligent categorization of transactions based on:
- Exact merchant name matching
- Fuzzy merchant name matching
- Keyword matching (English and Arabic)
- Priority-based fallback system
"""
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import yaml
import json
import re
from fuzzywuzzy import fuzz
from goldminer.utils import setup_logger
from goldminer.etl.schema_normalizer import TransactionRecord


class Categorizer:
    """
    Categorizes transactions based on merchant names, keywords, and patterns.
    
    Priority system:
    1. Exact match (match key in new format or merchant_exact in old format)
    2. Regex match (match_regex key in new format)
    3. Tag match (match_tag key in new format)
    4. Fuzzy merchant match (merchant_fuzzy in old format)
    5. Keyword match (keywords in old format)
    6. Fallback to "Uncategorized"
    
    Supports both new and legacy rule formats:
    - New format: rules with match, match_regex, match_tag keys
    - Legacy format: rules with merchant_exact, merchant_fuzzy, keywords keys
    
    Attributes:
        rules: Dictionary containing categorization rules
        fuzzy_threshold: Minimum similarity score for fuzzy matching (0-100)
        logger: Logger instance
    """
    
    def __init__(
        self,
        rules_path: Optional[str] = None,
        fuzzy_threshold: int = 80
    ):
        """
        Initialize the Categorizer.
        
        Args:
            rules_path: Path to YAML or JSON file containing categorization rules.
                       If None, uses default category_rules.yaml
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0-100)
        """
        self.logger = setup_logger(__name__)
        self.fuzzy_threshold = fuzzy_threshold
        
        # Load rules
        if rules_path is None:
            # Default to category_rules.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            rules_path = project_root / "category_rules.yaml"
        
        self.rules = self._load_rules(rules_path)
        self.logger.info(f"Categorizer initialized with {len(self.rules.get('categories', []))} category rules")
    
    def _load_rules(self, rules_path: str) -> Dict[str, Any]:
        """
        Load categorization rules from YAML or JSON file.
        
        Args:
            rules_path: Path to rules file
            
        Returns:
            Dictionary containing rules
            
        Raises:
            FileNotFoundError: If rules file doesn't exist
            ValueError: If rules file is invalid
        """
        rules_path = Path(rules_path)
        
        if not rules_path.exists():
            self.logger.error(f"Rules file not found: {rules_path}")
            raise FileNotFoundError(f"Rules file not found: {rules_path}")
        
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                if rules_path.suffix in ['.yaml', '.yml']:
                    rules = yaml.safe_load(f)
                elif rules_path.suffix == '.json':
                    rules = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {rules_path.suffix}")
            
            # Validate rules structure
            if not isinstance(rules, dict):
                raise ValueError("Rules must be a dictionary")
            
            if 'categories' not in rules:
                raise ValueError("Rules must contain 'categories' key")
            
            self.logger.info(f"Loaded {len(rules.get('categories', []))} category rules from {rules_path}")
            return rules
            
        except Exception as e:
            self.logger.error(f"Error loading rules from {rules_path}: {str(e)}")
            raise
    
    def load_rules(self, filepath: str) -> None:
        """
        Load or reload categorization rules from a YAML configuration file.
        
        This method supports both new and legacy rule formats:
        
        New format (with match, match_regex, match_tag):
            rules:
              - match: "Uber"
                category: "Transport"
                subcategory: "Ride Hailing"
                tags: ["Mobility"]
              - match_regex: ".*Vodafone.*"
                category: "Utilities"
                subcategory: "Telecom"
                tags: ["Recharge"]
              - match_tag: "subscription"
                category: "Entertainment"
                subcategory: "Streaming"
                tags: ["Recurring"]
        
        Legacy format (with merchant_exact, merchant_fuzzy, keywords):
            categories:
              - category: "Food & Dining"
                subcategory: "Restaurants"
                tags: ["Dining"]
                merchant_exact: ["McDonald's"]
                keywords:
                  english: ["restaurant"]
        
        Implements safe fallback:
        - If file is missing, logs warning and keeps existing rules
        - If file is malformed, logs error and keeps existing rules
        
        Args:
            filepath: Path to YAML configuration file
            
        Examples:
            >>> categorizer = Categorizer()
            >>> categorizer.load_rules('custom_rules.yaml')  # Load new rules
            >>> categorizer.load_rules('updated_rules.yaml')  # Reload at runtime
        """
        filepath_obj = Path(filepath)
        
        # Safe fallback: if file doesn't exist, log warning and keep existing rules
        if not filepath_obj.exists():
            self.logger.warning(f"Rules file not found: {filepath}. Keeping existing rules.")
            return
        
        try:
            with open(filepath_obj, 'r', encoding='utf-8') as f:
                new_rules = yaml.safe_load(f)
            
            # Validate rules structure
            if not isinstance(new_rules, dict):
                self.logger.error(f"Invalid rules format in {filepath}: must be a dictionary. Keeping existing rules.")
                return
            
            # Support both 'rules' (new format) and 'categories' (legacy format) keys
            if 'rules' not in new_rules and 'categories' not in new_rules:
                self.logger.error(f"Invalid rules format in {filepath}: must contain 'rules' or 'categories' key. Keeping existing rules.")
                return
            
            # Update the rules
            self.rules = new_rules
            
            # Count rules for logging
            rule_count = len(new_rules.get('rules', [])) + len(new_rules.get('categories', []))
            self.logger.info(f"Successfully loaded/reloaded {rule_count} rules from {filepath}")
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in {filepath}: {str(e)}. Keeping existing rules.")
        except Exception as e:
            self.logger.error(f"Error loading rules from {filepath}: {str(e)}. Keeping existing rules.")

        except Exception as e:
            self.logger.error(f"Error loading rules from {rules_path}: {str(e)}")
            raise
    
    def categorize(self, record: TransactionRecord) -> TransactionRecord:
        """
        Categorize a transaction record.
        
        Applies priority-based categorization:
        1. Exact match (new format: match key)
        2. Regex match (new format: match_regex key)
        3. Tag match (new format: match_tag key)
        4. Exact merchant match (legacy format: merchant_exact)
        5. Fuzzy merchant match (legacy format: merchant_fuzzy)
        6. Keyword match (legacy format: keywords)
        7. Fallback to "Uncategorized"
        
        Args:
            record: TransactionRecord to categorize
            
        Returns:
            TransactionRecord with category, subcategory, and tags populated
            
        Examples:
            >>> categorizer = Categorizer()
            >>> record = TransactionRecord(id='123', payee='McDonald\\'s', normalized_merchant='McDonald\\'s')
            >>> categorized = categorizer.categorize(record)
            >>> categorized.category
            'Food & Dining'
            >>> categorized.subcategory
            'Restaurants'
        """
        # Try new format rules first (match, match_regex, match_tag)
        result = self._match_new_format(record)
        if result:
            category, subcategory, tags = result
            record.category = category
            record.subcategory = subcategory
            # Merge with existing tags
            existing_tags = set(record.tags) if record.tags else set()
            record.tags = list(existing_tags | set(tags))
            self.logger.debug(f"New format match: {record.payee} -> {category}/{subcategory}")
            return record
        
        # Try exact merchant match (legacy format)
        result = self._match_exact_merchant(record)
        if result:
            category, subcategory, tags = result
            record.category = category
            record.subcategory = subcategory
            # Merge with existing tags
            existing_tags = set(record.tags) if record.tags else set()
            record.tags = list(existing_tags | set(tags))
            self.logger.debug(f"Exact merchant match: {record.payee} -> {category}/{subcategory}")
            return record
        
        # Try fuzzy merchant match (legacy format)
        result = self._match_fuzzy_merchant(record)
        if result:
            category, subcategory, tags = result
            record.category = category
            record.subcategory = subcategory
            existing_tags = set(record.tags) if record.tags else set()
            record.tags = list(existing_tags | set(tags))
            self.logger.debug(f"Fuzzy merchant match: {record.payee} -> {category}/{subcategory}")
            return record
        
        # Try keyword match (legacy format)
        result = self._match_keywords(record)
        if result:
            category, subcategory, tags = result
            record.category = category
            record.subcategory = subcategory
            existing_tags = set(record.tags) if record.tags else set()
            record.tags = list(existing_tags | set(tags))
            self.logger.debug(f"Keyword match: {record.payee} -> {category}/{subcategory}")
            return record
        
        # Fallback to uncategorized
        fallback = self.rules.get('fallback', {})
        record.category = fallback.get('category', 'Uncategorized')
        record.subcategory = fallback.get('subcategory', 'General')
        existing_tags = set(record.tags) if record.tags else set()
        fallback_tags = set(fallback.get('tags', []))
        record.tags = list(existing_tags | fallback_tags)
        self.logger.debug(f"Fallback categorization: {record.payee} -> Uncategorized")
        return record
        fallback_tags = set(fallback.get('tags', []))
        record.tags = list(existing_tags | fallback_tags)
        self.logger.debug(f"Fallback categorization: {record.payee} -> Uncategorized")
        return record
    
    def categorize_batch(self, records: List[TransactionRecord]) -> List[TransactionRecord]:
        """
        Categorize a batch of transaction records.
        
        Args:
            records: List of TransactionRecord objects
            
        Returns:
            List of categorized TransactionRecord objects
        """
        categorized = []
        for record in records:
            try:
                categorized_record = self.categorize(record)
                categorized.append(categorized_record)
            except Exception as e:
                self.logger.error(f"Error categorizing record {record.id}: {str(e)}")
                # Add uncategorized record on error
                record.category = 'Uncategorized'
                record.subcategory = 'General'
                categorized.append(record)
        
        self.logger.info(f"Categorized batch of {len(categorized)} records")
        return categorized
    
    def _match_new_format(self, record: TransactionRecord) -> Optional[Tuple[str, str, List[str]]]:
        """
        Try to match using new rule format (match, match_regex, match_tag).
        
        Priority order within new format:
        1. match (exact string match)
        2. match_regex (regex pattern match)
        3. match_tag (tag-based match)
        
        Args:
            record: TransactionRecord to match
            
        Returns:
            Tuple of (category, subcategory, tags) if match found, None otherwise
        """
        # Get rules in new format
        new_rules = self.rules.get('rules', [])
        if not new_rules:
            return None
        
        if not record.normalized_merchant and not record.payee:
            return None
        
        merchant = record.normalized_merchant or record.payee
        if not merchant:
            return None
        
        merchant_lower = merchant.lower().strip()
        
        # Priority 1: Try exact match
        for rule in new_rules:
            if 'match' in rule:
                match_value = rule['match']
                if match_value.lower().strip() == merchant_lower:
                    return (
                        rule.get('category', 'Uncategorized'),
                        rule.get('subcategory', 'General'),
                        rule.get('tags', [])
                    )
        
        # Priority 2: Try regex match
        for rule in new_rules:
            if 'match_regex' in rule:
                try:
                    pattern = rule['match_regex']
                    if re.search(pattern, merchant, re.IGNORECASE):
                        return (
                            rule.get('category', 'Uncategorized'),
                            rule.get('subcategory', 'General'),
                            rule.get('tags', [])
                        )
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern '{pattern}': {str(e)}")
                    continue
        
        # Priority 3: Try tag match
        if record.tags:
            record_tags = set(tag.lower() for tag in record.tags)
            for rule in new_rules:
                if 'match_tag' in rule:
                    match_tag = rule['match_tag'].lower()
                    if match_tag in record_tags:
                        return (
                            rule.get('category', 'Uncategorized'),
                            rule.get('subcategory', 'General'),
                            rule.get('tags', [])
                        )
        
        return None
    
    def _match_exact_merchant(self, record: TransactionRecord) -> Optional[Tuple[str, str, List[str]]]:
        """
        Try to match merchant name exactly.
        
        Args:
            record: TransactionRecord to match
            
        Returns:
            Tuple of (category, subcategory, tags) if match found, None otherwise
        """
        if not record.normalized_merchant and not record.payee:
            return None
        
        merchant = record.normalized_merchant or record.payee
        if not merchant:
            return None
        
        # Normalize for comparison (case-insensitive)
        merchant_lower = merchant.lower().strip()
        
        for rule in self.rules.get('categories', []):
            # Check exact matches
            exact_merchants = rule.get('merchant_exact', [])
            for exact_merchant in exact_merchants:
                if merchant_lower == exact_merchant.lower().strip():
                    return (
                        rule.get('category'),
                        rule.get('subcategory'),
                        rule.get('tags', [])
                    )
        
        return None
    
    def _match_fuzzy_merchant(self, record: TransactionRecord) -> Optional[Tuple[str, str, List[str]]]:
        """
        Try to match merchant name using fuzzy matching.
        
        Args:
            record: TransactionRecord to match
            
        Returns:
            Tuple of (category, subcategory, tags) if match found, None otherwise
        """
        if not record.normalized_merchant and not record.payee:
            return None
        
        merchant = record.normalized_merchant or record.payee
        if not merchant:
            return None
        
        merchant_lower = merchant.lower().strip()
        
        best_match = None
        best_score = 0
        
        for rule in self.rules.get('categories', []):
            # Check fuzzy matches
            fuzzy_merchants = rule.get('merchant_fuzzy', [])
            for fuzzy_merchant in fuzzy_merchants:
                fuzzy_merchant_lower = fuzzy_merchant.lower().strip()
                
                # Use multiple fuzzy matching algorithms and take the best score
                token_sort = fuzz.token_sort_ratio(merchant_lower, fuzzy_merchant_lower)
                token_set = fuzz.token_set_ratio(merchant_lower, fuzzy_merchant_lower)
                partial = fuzz.partial_ratio(merchant_lower, fuzzy_merchant_lower)
                
                # Take the maximum score from different algorithms
                score = max(token_sort, token_set, partial)
                
                # Also check if fuzzy merchant is contained in the actual merchant
                if fuzzy_merchant_lower in merchant_lower:
                    score = max(score, 90)  # Boost score for substring match
                
                if score >= self.fuzzy_threshold and score > best_score:
                    best_score = score
                    best_match = (
                        rule.get('category'),
                        rule.get('subcategory'),
                        rule.get('tags', [])
                    )
        
        if best_match:
            self.logger.debug(f"Fuzzy match score: {best_score}")
        
        return best_match
    
    def _match_keywords(self, record: TransactionRecord) -> Optional[Tuple[str, str, List[str]]]:
        """
        Try to match based on keywords in merchant/payee name.
        
        Checks both English and Arabic keywords.
        
        Args:
            record: TransactionRecord to match
            
        Returns:
            Tuple of (category, subcategory, tags) if match found, None otherwise
        """
        if not record.normalized_merchant and not record.payee:
            return None
        
        merchant = record.normalized_merchant or record.payee
        if not merchant:
            return None
        
        merchant_lower = merchant.lower().strip()
        
        for rule in self.rules.get('categories', []):
            keywords = rule.get('keywords', {})
            
            # Check English keywords
            english_keywords = keywords.get('english', [])
            for keyword in english_keywords:
                if keyword.lower() in merchant_lower:
                    return (
                        rule.get('category'),
                        rule.get('subcategory'),
                        rule.get('tags', [])
                    )
            
            # Check Arabic keywords
            arabic_keywords = keywords.get('arabic', [])
            for keyword in arabic_keywords:
                if keyword in merchant:  # Arabic is case-sensitive
                    return (
                        rule.get('category'),
                        rule.get('subcategory'),
                        rule.get('tags', [])
                    )
        
        return None
    
    def get_category_statistics(self, records: List[TransactionRecord]) -> Dict[str, Any]:
        """
        Generate statistics about categorization results.
        
        Args:
            records: List of categorized TransactionRecord objects
            
        Returns:
            Dictionary with categorization statistics
        """
        if not records:
            return {
                'total_records': 0,
                'categories': {},
                'uncategorized_count': 0,
                'uncategorized_percentage': 0.0
            }
        
        category_counts = {}
        uncategorized_count = 0
        
        for record in records:
            category = record.category or 'Uncategorized'
            if category == 'Uncategorized':
                uncategorized_count += 1
            
            if category not in category_counts:
                category_counts[category] = {
                    'count': 0,
                    'subcategories': {}
                }
            
            category_counts[category]['count'] += 1
            
            # Count subcategories
            subcategory = record.subcategory or 'General'
            if subcategory not in category_counts[category]['subcategories']:
                category_counts[category]['subcategories'][subcategory] = 0
            category_counts[category]['subcategories'][subcategory] += 1
        
        total_records = len(records)
        
        return {
            'total_records': total_records,
            'categories': category_counts,
            'uncategorized_count': uncategorized_count,
            'uncategorized_percentage': (uncategorized_count / total_records * 100) if total_records > 0 else 0.0
        }


if __name__ == "__main__":
    import doctest
    doctest.testmod()
