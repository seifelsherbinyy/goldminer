"""
MerchantResolver module for resolving merchant names to canonical names.

This module provides intelligent merchant name resolution based on:
- Exact alias matching
- Fuzzy string matching using RapidFuzz
- Configurable similarity threshold
- Multi-language support (Arabic and English)
"""
from typing import Optional, Tuple, Dict, List, Any
from pathlib import Path
import yaml
from rapidfuzz import fuzz, process
from goldminer.utils.logger import setup_logger


class MerchantResolver:
    """
    Resolves merchant names to their canonical forms using fuzzy matching.
    
    Uses RapidFuzz to compare input payee strings against an alias dictionary
    loaded from merchant_aliases.yaml. Each entry contains a canonical name
    and a list of known aliases.
    
    Attributes:
        aliases_path: Path to the merchant aliases YAML file
        similarity_threshold: Minimum similarity score for matches (0-100)
        merchant_map: Dictionary mapping aliases to canonical names
        logger: Logger instance
    
    Examples:
        >>> resolver = MerchantResolver()
        >>> canonical = resolver.resolve_merchant("كارفور")
        >>> print(canonical)
        'Carrefour'
        
        >>> canonical, score = resolver.resolve_merchant("CARREFOUR MAADI", return_confidence=True)
        >>> print(f"{canonical} (confidence: {score}%)")
        'Carrefour (confidence: 95.0%)'
    """
    
    def __init__(
        self,
        aliases_path: Optional[str] = None,
        similarity_threshold: float = 85.0
    ):
        """
        Initialize the MerchantResolver.
        
        Args:
            aliases_path: Path to YAML file containing merchant aliases.
                         If None, uses default merchant_aliases.yaml in project root
            similarity_threshold: Minimum similarity score for fuzzy matching (0-100).
                                 Default is 85.0 (85%)
        
        Raises:
            FileNotFoundError: If aliases file doesn't exist
            ValueError: If aliases file is invalid or threshold is out of range
        """
        self.logger = setup_logger(__name__)
        
        # Validate threshold
        if not 0 <= similarity_threshold <= 100:
            raise ValueError(f"Similarity threshold must be between 0 and 100, got {similarity_threshold}")
        
        self.similarity_threshold = similarity_threshold
        
        # Load aliases
        if aliases_path is None:
            # Default to merchant_aliases.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            aliases_path = project_root / "merchant_aliases.yaml"
        
        self.aliases_path = Path(aliases_path)
        self.merchant_map = self._load_aliases()
        
        # Create a list of all aliases for efficient searching
        self.all_aliases = list(self.merchant_map.keys())
        
        self.logger.info(
            f"MerchantResolver initialized with {len(self.merchant_map)} aliases "
            f"from {len(set(self.merchant_map.values()))} canonical merchants "
            f"(threshold: {self.similarity_threshold}%)"
        )
    
    def _load_aliases(self) -> Dict[str, str]:
        """
        Load merchant aliases from YAML file.
        
        Returns:
            Dictionary mapping each alias to its canonical merchant name
            
        Raises:
            FileNotFoundError: If aliases file doesn't exist
            ValueError: If aliases file is invalid
        """
        if not self.aliases_path.exists():
            self.logger.error(f"Aliases file not found: {self.aliases_path}")
            raise FileNotFoundError(f"Aliases file not found: {self.aliases_path}")
        
        try:
            with open(self.aliases_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("Aliases file must contain a dictionary")
            
            if 'merchants' not in data:
                raise ValueError("Aliases file must contain 'merchants' key")
            
            if not isinstance(data['merchants'], list):
                raise ValueError("'merchants' must be a list")
            
            # Build the alias-to-canonical mapping
            merchant_map = {}
            
            for merchant_entry in data['merchants']:
                if not isinstance(merchant_entry, dict):
                    self.logger.warning(f"Skipping invalid merchant entry: {merchant_entry}")
                    continue
                
                canonical = merchant_entry.get('canonical')
                aliases = merchant_entry.get('aliases', [])
                
                if not canonical:
                    self.logger.warning(f"Skipping merchant entry without canonical name: {merchant_entry}")
                    continue
                
                if not isinstance(aliases, list):
                    self.logger.warning(f"Skipping merchant {canonical} with invalid aliases: {aliases}")
                    continue
                
                # Map each alias to the canonical name
                for alias in aliases:
                    if isinstance(alias, str):
                        # Case-insensitive matching - store lowercase for lookups
                        merchant_map[alias.lower()] = canonical
                    else:
                        self.logger.warning(f"Skipping non-string alias for {canonical}: {alias}")
            
            self.logger.info(f"Loaded {len(merchant_map)} aliases for {len(set(merchant_map.values()))} merchants")
            return merchant_map
            
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in {self.aliases_path}: {str(e)}")
            raise ValueError(f"Invalid YAML in aliases file: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error loading aliases from {self.aliases_path}: {str(e)}")
            raise
    
    def resolve_merchant(
        self,
        payee: str,
        return_confidence: bool = False
    ) -> Tuple[str, Optional[float]]:
        """
        Resolve a payee string to a canonical merchant name.
        
        Uses a two-stage approach:
        1. Exact match: Check if the payee (case-insensitive) exactly matches any alias
        2. Fuzzy match: Use RapidFuzz to find the best matching alias above threshold
        
        Args:
            payee: The payee/merchant string to resolve
            return_confidence: If True, return a tuple of (canonical_name, confidence_score)
                             If False, return just the canonical name
        
        Returns:
            If return_confidence is False:
                - The canonical merchant name if match found, or original payee if not
            If return_confidence is True:
                - Tuple of (canonical_name, confidence_score) where score is 0-100
                  or (original_payee, None) if no match found
        
        Examples:
            >>> resolver = MerchantResolver()
            >>> resolver.resolve_merchant("كارفور")
            'Carrefour'
            
            >>> resolver.resolve_merchant("CARREFOUR MAADI", return_confidence=True)
            ('Carrefour', 100.0)
            
            >>> resolver.resolve_merchant("Unknown Merchant", return_confidence=True)
            ('Unknown Merchant', None)
        """
        # Handle None input
        if payee is None:
            self.logger.warning("Payee input is None")
            if return_confidence:
                return (None, None)
            return None
        
        # Handle non-string input
        if not isinstance(payee, str):
            self.logger.warning(f"Invalid payee input type: {type(payee)}")
            if return_confidence:
                return (None, None)
            return None
        
        # Handle empty string
        if not payee:
            if return_confidence:
                return ("", None)
            return ""
        
        payee_lower = payee.lower().strip()
        
        # Handle empty string after stripping (whitespace-only input)
        if not payee_lower:
            if return_confidence:
                return ("", None)
            return ""
        
        # Stage 1: Exact match (case-insensitive)
        if payee_lower in self.merchant_map:
            canonical = self.merchant_map[payee_lower]
            self.logger.debug(f"Exact match: '{payee}' -> '{canonical}'")
            if return_confidence:
                return (canonical, 100.0)
            return canonical
        
        # Stage 2: Fuzzy match using RapidFuzz
        # Use extractOne to find the best match
        result = process.extractOne(
            payee_lower,
            self.all_aliases,
            scorer=fuzz.ratio,
            score_cutoff=self.similarity_threshold
        )
        
        if result:
            best_alias, score, _ = result
            canonical = self.merchant_map[best_alias]
            self.logger.debug(
                f"Fuzzy match: '{payee}' -> '{canonical}' "
                f"(matched alias: '{best_alias}', score: {score:.1f})"
            )
            if return_confidence:
                return (canonical, float(score))
            return canonical
        
        # No match found
        self.logger.debug(
            f"No match found for '{payee}' "
            f"(threshold: {self.similarity_threshold})"
        )
        if return_confidence:
            return (payee, None)
        return payee
    
    def get_merchant_info(self, canonical_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a canonical merchant name.
        
        Args:
            canonical_name: The canonical merchant name
        
        Returns:
            Dictionary containing merchant info (canonical name and aliases),
            or None if not found
        
        Examples:
            >>> resolver = MerchantResolver()
            >>> info = resolver.get_merchant_info("Carrefour")
            >>> print(info['aliases'])
            ['كارفور', 'Carrefour EG', 'Carrefour City', ...]
        """
        # Find all aliases that map to this canonical name
        aliases = [
            alias for alias, canonical in self.merchant_map.items()
            if canonical == canonical_name
        ]
        
        if not aliases:
            return None
        
        return {
            'canonical': canonical_name,
            'aliases': aliases,
            'alias_count': len(aliases)
        }
    
    def get_all_merchants(self) -> List[str]:
        """
        Get a list of all canonical merchant names.
        
        Returns:
            Sorted list of canonical merchant names
        
        Examples:
            >>> resolver = MerchantResolver()
            >>> merchants = resolver.get_all_merchants()
            >>> print(merchants[:3])
            ['Amazon', 'Careem', 'Carrefour']
        """
        return sorted(set(self.merchant_map.values()))
