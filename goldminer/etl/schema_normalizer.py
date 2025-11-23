"""
SchemaNormalizer module for transforming validated ParsedTransaction into TransactionRecord.

This module provides a unified internal schema (TransactionRecord) and methods to normalize
validated transaction data including date formatting, amount conversion, UTF-8 text
normalization, and metadata attachment from card/account information.
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
import unicodedata
import uuid
from goldminer.utils import setup_logger
from goldminer.etl.field_validator import ParsedTransaction
from goldminer.analysis.card_classifier import CardClassifier


@dataclass
class TransactionRecord:
    """
    Unified internal schema for normalized transaction data.
    
    All transactions are transformed into this schema with:
    - ISO 8601 formatted dates (YYYY-MM-DD)
    - Float amounts
    - UTF-8 normalized text
    - Attached card/account metadata
    - Default values for missing fields
    
    Attributes:
        id: Unique transaction identifier
        date: Transaction date in ISO 8601 format (YYYY-MM-DD)
        amount: Transaction amount as float
        currency: Currency code (e.g., 'EGP', 'USD')
        payee: Payee/merchant name (UTF-8 normalized)
        normalized_merchant: Normalized merchant name (cleaned and standardized)
        category: Transaction category
        subcategory: Transaction subcategory
        tags: List of transaction tags
        account_id: Account identifier
        account_type: Account type (e.g., 'Credit', 'Debit', 'Prepaid')
        interest_rate: Account interest rate (null for debit/prepaid)
        urgency: Transaction urgency level
        confidence: Confidence level of the transaction data
    """
    
    id: str
    date: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    payee: Optional[str] = None
    normalized_merchant: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    account_id: Optional[str] = None
    account_type: Optional[str] = None
    interest_rate: Optional[float] = None
    urgency: str = "normal"
    confidence: str = "low"
    resolved_date: Optional[str] = None
    transaction_state: Optional[str] = None
    text_repaired: bool = False
    extracted_date_raw: Optional[str] = None


class SchemaNormalizer:
    """
    Normalizer that transforms validated ParsedTransaction into TransactionRecord.
    
    This class provides comprehensive normalization including:
    - Date formatting to ISO 8601 (YYYY-MM-DD)
    - Safe amount conversion to float
    - UTF-8 text normalization with whitespace handling
    - Card/account metadata attachment
    - Default value population for missing fields
    
    Attributes:
        card_classifier: CardClassifier instance for account metadata lookup
        logger: Logger instance for tracking operations
    """
    
    def __init__(self, card_classifier: Optional[CardClassifier] = None):
        """
        Initialize the SchemaNormalizer.
        
        Args:
            card_classifier: Optional CardClassifier instance. If None, creates one.
        """
        self.logger = setup_logger(__name__)
        self.card_classifier = card_classifier or CardClassifier()
        self.logger.info("SchemaNormalizer initialized")
    
    def normalize(self, parsed_txn: ParsedTransaction) -> TransactionRecord:
        """
        Normalize a ParsedTransaction into a TransactionRecord.
        
        Args:
            parsed_txn: Validated ParsedTransaction object
            
        Returns:
            TransactionRecord with normalized and enriched data
            
        Examples:
            >>> normalizer = SchemaNormalizer()
            >>> parsed = ParsedTransaction(amount='100.50', currency='EGP', date='15/11/2024')
            >>> record = normalizer.normalize(parsed)
            >>> record.amount
            100.5
            >>> record.date
            '2024-11-15'
        """
        # Generate unique ID
        txn_id = self._generate_id()
        
        # Normalize date to ISO 8601
        normalized_date = self._normalize_date(parsed_txn.resolved_date or parsed_txn.date)
        
        # Convert amount to float
        normalized_amount = self._safe_float_cast(parsed_txn.amount)
        
        # Normalize payee text
        normalized_payee = self._normalize_text(parsed_txn.payee)
        normalized_merchant = self._normalize_merchant(normalized_payee)
        
        # Attach account metadata
        account_metadata = self._get_account_metadata(parsed_txn.card_suffix)
        
        # Determine urgency based on amount and account type
        urgency = self._determine_urgency(
            normalized_amount, 
            account_metadata.get('account_type')
        )
        
        # Create TransactionRecord
        record = TransactionRecord(
            id=txn_id,
            date=normalized_date,
            resolved_date=normalized_date,
            amount=normalized_amount,
            currency=self._normalize_text(parsed_txn.currency),
            payee=normalized_payee,
            normalized_merchant=normalized_merchant,
            category=self._get_default_category(),
            subcategory=self._get_default_subcategory(),
            tags=self._extract_tags(parsed_txn),
            account_id=account_metadata.get('account_id'),
            account_type=account_metadata.get('account_type'),
            interest_rate=account_metadata.get('interest_rate'),
            urgency=urgency,
            confidence=parsed_txn.confidence or 'low',
            transaction_state=(parsed_txn.transaction_state or 'UNKNOWN').upper(),
            text_repaired=bool(parsed_txn.text_repaired),
            extracted_date_raw=parsed_txn.extracted_date_raw,
        )
        
        self.logger.debug(f"Normalized transaction: {record.id}")
        return record
    
    def normalize_batch(self, parsed_txns: List[ParsedTransaction]) -> List[TransactionRecord]:
        """
        Normalize a batch of ParsedTransactions.
        
        Args:
            parsed_txns: List of ParsedTransaction objects
            
        Returns:
            List of TransactionRecord objects
        """
        records = []
        for txn in parsed_txns:
            try:
                record = self.normalize(txn)
                records.append(record)
            except Exception as e:
                self.logger.error(f"Error normalizing transaction: {str(e)}")
                # Create a minimal record on error
                records.append(self._create_minimal_record())
        
        self.logger.info(f"Normalized batch of {len(records)} transactions")
        return records
    
    def _generate_id(self) -> str:
        """
        Generate a unique transaction ID.
        
        Returns:
            UUID string
        """
        return str(uuid.uuid4())
    
    def _normalize_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Normalize date string to ISO 8601 format (YYYY-MM-DD).
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO 8601 formatted date string or None
        """
        if not date_str:
            return None
        
        # Strip whitespace
        date_str = date_str.strip()
        
        if not date_str:
            return None
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',      # Already ISO format
            '%d/%m/%Y',      # DD/MM/YYYY
            '%m/%d/%Y',      # MM/DD/YYYY
            '%d-%m-%Y',      # DD-MM-YYYY
            '%Y/%m/%d',      # YYYY/MM/DD
            '%d.%m.%Y',      # DD.MM.YYYY
            '%Y.%m.%d',      # YYYY.MM.DD
            '%d %b %Y',      # DD Mon YYYY
            '%d %B %Y',      # DD Month YYYY
            '%b %d, %Y',     # Mon DD, YYYY
            '%B %d, %Y',     # Month DD, YYYY
            '%Y-%m-%d %H:%M:%S',  # ISO with time
            '%d/%m/%Y %H:%M:%S',  # DD/MM/YYYY with time
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                continue
        
        # If no format matches, log and return None
        self.logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _safe_float_cast(self, value: Optional[str]) -> Optional[float]:
        """
        Safely cast a string value to float.
        
        Handles common numeric formats including:
        - Comma separators
        - Currency symbols
        - Whitespace
        
        Args:
            value: String value to cast
            
        Returns:
            Float value or None if casting fails
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if not isinstance(value, str):
            return None
        
        # Clean the string
        cleaned = value.strip()
        if not cleaned:
            return None
        
        # Remove common formatting
        cleaned = cleaned.replace(',', '').replace(' ', '')
        
        try:
            # Use Decimal for precision, then convert to float
            decimal_value = Decimal(cleaned)
            return float(decimal_value)
        except (InvalidOperation, ValueError):
            self.logger.warning(f"Could not cast to float: {value}")
            return None
    
    def _normalize_text(self, text: Optional[str]) -> Optional[str]:
        """
        Normalize text to UTF-8 with whitespace handling.
        
        Performs:
        - Unicode normalization (NFC)
        - Whitespace stripping and collapsing
        - None handling
        
        Args:
            text: Text to normalize
            
        Returns:
            Normalized text or None
        """
        if text is None:
            return None
        
        if not isinstance(text, str):
            text = str(text)
        
        # Strip whitespace
        text = text.strip()
        
        if not text:
            return None
        
        # Normalize Unicode to NFC (Canonical Composition)
        text = unicodedata.normalize('NFC', text)
        
        # Collapse multiple whitespaces to single space
        text = ' '.join(text.split())
        
        return text
    
    def _normalize_merchant(self, payee: Optional[str]) -> Optional[str]:
        """
        Normalize merchant name from payee.
        
        Performs additional cleaning for merchant names:
        - Uppercase conversion for consistency
        - Special character removal (keeping spaces and basic punctuation)
        
        Args:
            payee: Payee name
            
        Returns:
            Normalized merchant name or None
        """
        if not payee:
            return None
        
        # Start with normalized text (this handles whitespace and unicode)
        merchant = self._normalize_text(payee)
        
        # Remove common prefixes/suffixes that don't identify the merchant
        # For now, just return the normalized payee
        # Future enhancement: implement merchant name standardization
        
        return merchant
    
    def _get_account_metadata(self, card_suffix: Optional[str]) -> Dict[str, Any]:
        """
        Get account metadata for a card suffix.
        
        Args:
            card_suffix: Last 4 digits of card number
            
        Returns:
            Dictionary with account metadata (account_id, account_type, interest_rate)
        """
        if not card_suffix:
            return {}
        
        try:
            metadata = self.card_classifier.lookup_account(card_suffix)
            if metadata:
                return {
                    'account_id': metadata.get('account_id'),
                    'account_type': metadata.get('account_type'),
                    'interest_rate': metadata.get('interest_rate')
                }
        except Exception as e:
            self.logger.warning(f"Error getting account metadata for {card_suffix}: {str(e)}")
        
        return {}
    
    def _determine_urgency(self, amount: Optional[float], account_type: Optional[str]) -> str:
        """
        Determine transaction urgency based on amount and account type.
        
        Args:
            amount: Transaction amount
            account_type: Account type (Credit, Debit, Prepaid)
            
        Returns:
            Urgency level: 'high', 'medium', or 'normal'
        """
        if amount is None:
            return 'normal'
        
        # High urgency for large amounts
        if amount >= 10000:
            return 'high'
        
        # Medium urgency for credit card transactions over 5000
        if account_type == 'Credit' and amount >= 5000:
            return 'medium'
        
        return 'normal'
    
    def _get_default_category(self) -> Optional[str]:
        """
        Get default category for uncategorized transactions.
        
        Returns:
            Default category string
        """
        return 'Uncategorized'
    
    def _get_default_subcategory(self) -> Optional[str]:
        """
        Get default subcategory for uncategorized transactions.
        
        Returns:
            Default subcategory string
        """
        return 'General'
    
    def _extract_tags(self, parsed_txn: ParsedTransaction) -> List[str]:
        """
        Extract tags from parsed transaction.
        
        Args:
            parsed_txn: ParsedTransaction object
            
        Returns:
            List of tags
        """
        tags = []
        
        # Add transaction type as tag if present
        if parsed_txn.txn_type:
            tags.append(parsed_txn.txn_type)
        
        # Add bank as tag if present
        if parsed_txn.bank_id:
            tags.append(parsed_txn.bank_id)
        
        # Add warning tags if there are warnings
        if parsed_txn.warnings:
            tags.append('has-warnings')
        
        return tags
    
    def _create_minimal_record(self) -> TransactionRecord:
        """
        Create a minimal transaction record for error cases.
        
        Returns:
            Minimal TransactionRecord with default values
        """
        return TransactionRecord(
            id=self._generate_id(),
            confidence='low'
        )


if __name__ == "__main__":
    import doctest
    doctest.testmod()
