"""
FieldValidator module for enforcing typing, required fields, and validation logic on parsed SMS data.

This module provides Pydantic models for structured transaction data validation,
ensuring data quality and consistency throughout the ETL pipeline.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, field_validator, model_validator
from goldminer.utils import setup_logger


class ParsedTransaction(BaseModel):
    """
    Pydantic model for parsed transaction data with comprehensive validation.
    
    This model enforces typing and validation rules on SMS transaction data,
    including validation of amounts, currencies, dates, and other transaction fields.
    
    Attributes:
        amount: Transaction amount as string (to preserve precision)
        currency: Currency code (e.g., 'EGP', 'USD', 'EUR')
        date: Transaction date as string
        payee: Payee or merchant name
        txn_type: Transaction type (e.g., 'POS', 'ATM', 'Online')
        card_suffix: Last 4 digits of card number
        bank_id: Bank identifier
        confidence: Confidence level ('high', 'medium', 'low')
        warnings: List of validation warnings
    """
    
    amount: Optional[str] = Field(default=None, description="Transaction amount")
    currency: Optional[str] = Field(default=None, description="Currency code")
    date: Optional[str] = Field(default=None, description="Transaction date")
    payee: Optional[str] = Field(default=None, description="Payee/merchant name")
    txn_type: Optional[str] = Field(default=None, description="Transaction type")
    card_suffix: Optional[str] = Field(default=None, description="Last 4 digits of card")
    bank_id: Optional[str] = Field(default=None, description="Bank identifier")
    confidence: str = Field(default="low", description="Confidence level")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    transaction_state: Optional[str] = Field(default=None, description="State classification")
    resolved_date: Optional[str] = Field(default=None, description="Resolved transaction date")
    extracted_date_raw: Optional[str] = Field(default=None, description="Raw extracted date string")
    text_repaired: bool = Field(default=False, description="Whether text repair was applied")
    
    model_config = {
        "validate_assignment": True,
        "str_strip_whitespace": True,
    }
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate amount field - ensure it's a valid numeric string.
        
        Args:
            v: Amount value to validate
            
        Returns:
            Validated amount or None
        """
        if v is None or v == '':
            return None
        
        # Remove common formatting (commas, spaces)
        cleaned = v.replace(',', '').replace(' ', '').strip()
        
        if not cleaned:
            return None
        
        try:
            # Validate that it can be converted to decimal
            Decimal(cleaned)
            return cleaned
        except (InvalidOperation, ValueError):
            # Return original value and let warnings be added in model validator
            return v
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate currency code.
        
        Args:
            v: Currency code to validate
            
        Returns:
            Validated currency code or None
        """
        if v is None or v == '':
            return None
        
        v = v.strip().upper()
        
        # List of valid currency codes (ISO 4217 common ones + Arabic)
        valid_currencies = {
            'EGP', 'USD', 'EUR', 'GBP', 'SAR', 'AED', 'KWD', 'QAR', 'BHD', 'OMR',
            'JOD', 'LBP', 'IQD', 'SYP', 'YER', 'TND', 'MAD', 'DZD', 'SDG', 'LYD',
            # Arabic currency names
            'جنيه', 'دولار', 'يورو', 'ريال', 'درهم', 'دينار'
        }
        
        if v not in valid_currencies:
            # Return original and let warnings be added in model validator
            return v
        
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate date field - attempt to parse various date formats.
        
        Args:
            v: Date string to validate
            
        Returns:
            Validated date string or None
        """
        if v is None or v == '':
            return None
        
        v = v.strip()
        
        # Common date formats to try
        date_formats = [
            '%d/%m/%Y',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%d.%m.%Y',
            '%Y.%m.%d',
            '%d %b %Y',
            '%d %B %Y',
            '%b %d, %Y',
            '%B %d, %Y',
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(v, fmt)
                return v  # Valid date
            except ValueError:
                continue
        
        # Return original and let warnings be added in model validator
        return v
    
    @field_validator('card_suffix')
    @classmethod
    def validate_card_suffix(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate card suffix - ensure it's 4 digits.
        
        Args:
            v: Card suffix to validate
            
        Returns:
            Validated card suffix or None
        """
        if v is None or v == '':
            return None
        
        v = v.strip()
        
        # Should be exactly 4 digits
        if not (v.isdigit() and len(v) == 4):
            # Return original and let warnings be added in model validator
            return v
        
        return v
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        """
        Validate confidence level.
        
        Args:
            v: Confidence level
            
        Returns:
            Validated confidence level
        """
        v = v.lower().strip()
        valid_levels = {'high', 'medium', 'low'}
        
        if v not in valid_levels:
            return 'low'
        
        return v

    @field_validator('transaction_state')
    @classmethod
    def validate_transaction_state(cls, v: Optional[str]) -> Optional[str]:
        """Ensure transaction_state is one of the known enumerations."""

        if v is None:
            return None

        allowed = {'MONETARY', 'PROMO', 'OTP', 'DECLINED', 'UNKNOWN'}
        value = v.strip().upper()
        return value if value in allowed else 'UNKNOWN'
    
    @model_validator(mode='after')
    def validate_model_and_add_warnings(self) -> 'ParsedTransaction':
        """
        Perform cross-field validation and populate warnings list.
        
        This validator runs after all field validators and checks for:
        - Invalid numeric formats in amount
        - Invalid currency codes
        - Malformed dates
        - Invalid card suffixes
        - Missing critical fields
        
        Returns:
            Self with updated warnings and confidence
        """
        # Only run validation if warnings list is empty (to avoid recursion)
        if len(self.warnings) > 0:
            return self
        
        warnings = []
        
        # Check amount validity
        if self.amount is not None:
            try:
                amount_val = Decimal(self.amount.replace(',', '').replace(' ', ''))
                if amount_val <= 0:
                    warnings.append("Amount must be positive")
            except (InvalidOperation, ValueError, AttributeError):
                warnings.append(f"Invalid numeric format for amount: {self.amount}")
        else:
            warnings.append("Missing required field: amount")
        
        # Check currency validity
        if self.currency is not None:
            valid_currencies = {
                'EGP', 'USD', 'EUR', 'GBP', 'SAR', 'AED', 'KWD', 'QAR', 'BHD', 'OMR',
                'JOD', 'LBP', 'IQD', 'SYP', 'YER', 'TND', 'MAD', 'DZD', 'SDG', 'LYD',
                'جنيه', 'دولار', 'يورو', 'ريال', 'درهم', 'دينار'
            }
            if self.currency.upper() not in valid_currencies and self.currency not in valid_currencies:
                warnings.append(f"Invalid currency code: {self.currency}")
        else:
            warnings.append("Missing currency field")
        
        # Check date validity
        if self.date is not None:
            date_formats = [
                '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d',
                '%d.%m.%Y', '%Y.%m.%d', '%d %b %Y', '%d %B %Y', '%b %d, %Y', '%B %d, %Y',
            ]
            valid_date = False
            for fmt in date_formats:
                try:
                    datetime.strptime(self.date, fmt)
                    valid_date = True
                    break
                except ValueError:
                    continue
            
            if not valid_date:
                warnings.append(f"Malformed date: {self.date}")
        
        # Check card suffix validity
        if self.card_suffix is not None:
            if not (self.card_suffix.isdigit() and len(self.card_suffix) == 4):
                warnings.append(f"Invalid card suffix (must be 4 digits): {self.card_suffix}")
        
        # Directly update warnings using object.__setattr__ to avoid validation recursion
        object.__setattr__(self, 'warnings', warnings)
        
        # Update confidence based on critical field failures
        critical_fields_missing = any(
            'Missing required field' in w or 'Invalid numeric format' in w 
            for w in warnings
        )
        
        new_confidence = self.confidence
        if critical_fields_missing or len(warnings) >= 2:
            # Low confidence if missing critical fields or 2+ warnings
            new_confidence = 'low'
        elif len(warnings) > 0:
            # Medium confidence if any warnings
            new_confidence = 'medium'
        elif self.amount and self.currency and self.date:
            # High confidence only if all key fields present and valid
            new_confidence = 'high'
        
        # Directly update confidence using object.__setattr__ to avoid validation recursion
        object.__setattr__(self, 'confidence', new_confidence)
        
        return self


class FieldValidator:
    """
    Field validation manager that validates parsed SMS transaction data.
    
    This class provides a safe interface for validating transaction data,
    catching all exceptions and returning structured results with warnings
    instead of raising errors.
    """
    
    def __init__(self):
        """Initialize the FieldValidator."""
        self.logger = setup_logger(__name__)
    
    def validate(self, data: Dict[str, Any]) -> ParsedTransaction:
        """
        Validate parsed transaction data.
        
        This method never raises exceptions during normal operation. Instead,
        it catches all errors, logs them, and returns a structured object
        with appropriate warnings.
        
        Args:
            data: Dictionary containing parsed transaction fields
            
        Returns:
            ParsedTransaction object with validation results and warnings
            
        Examples:
            >>> validator = FieldValidator()
            >>> data = {'amount': '100.50', 'currency': 'EGP', 'date': '15/11/2024'}
            >>> result = validator.validate(data)
            >>> result.confidence in ['high', 'medium', 'low']
            True
            >>> result.amount
            '100.50'
        """
        try:
            # Handle field name aliases
            normalized_data = data.copy()
            
            # transaction_type -> txn_type
            if 'transaction_type' in normalized_data and 'txn_type' not in normalized_data:
                normalized_data['txn_type'] = normalized_data.pop('transaction_type')
            
            # matched_bank -> bank_id
            if 'matched_bank' in normalized_data and 'bank_id' not in normalized_data:
                normalized_data['bank_id'] = normalized_data.pop('matched_bank')
            
            # Remove extra fields that aren't part of the model
            allowed_fields = {
                'amount', 'currency', 'date', 'payee', 'txn_type',
                'card_suffix', 'bank_id', 'confidence', 'warnings',
                'transaction_state', 'resolved_date', 'extracted_date_raw', 'text_repaired'
            }
            normalized_data = {k: v for k, v in normalized_data.items() if k in allowed_fields}
            
            # Create ParsedTransaction with validation
            transaction = ParsedTransaction(**normalized_data)
            
            # Log validation result
            if transaction.warnings:
                self.logger.warning(
                    f"Transaction validation completed with warnings: {transaction.warnings}"
                )
            else:
                self.logger.info("Transaction validation successful")
            
            return transaction
            
        except Exception as e:
            # Catch any validation errors and return low-confidence result
            self.logger.error(f"Validation error: {str(e)}")
            
            # Create a safe data dict with only valid types
            safe_data = {}
            for key in [
                'amount', 'currency', 'date', 'payee', 'txn_type', 'card_suffix',
                'bank_id', 'transaction_state', 'resolved_date', 'extracted_date_raw',
                'text_repaired'
            ]:
                value = data.get(key)
                # Only include if it's a string or None
                if value is None or isinstance(value, str):
                    safe_data[key] = value
                elif isinstance(value, (int, float)):
                    safe_data[key] = str(value)
                elif isinstance(value, bool):
                    safe_data[key] = value
            
            # Handle aliases in safe data
            if 'transaction_type' in data and 'txn_type' not in safe_data:
                value = data['transaction_type']
                if isinstance(value, str):
                    safe_data['txn_type'] = value
            
            if 'matched_bank' in data and 'bank_id' not in safe_data:
                value = data['matched_bank']
                if isinstance(value, str):
                    safe_data['bank_id'] = value
            
            # Create a low-confidence transaction with error message
            try:
                return ParsedTransaction(
                    **safe_data,
                    confidence='low',
                    warnings=[f"Validation exception: {str(e)}"]
                )
            except Exception:
                # Ultimate fallback
                return ParsedTransaction(
                    confidence='low',
                    warnings=[f"Critical validation exception: {str(e)}"]
                )
    
    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[ParsedTransaction]:
        """
        Validate a batch of parsed transaction data.
        
        Args:
            data_list: List of dictionaries containing parsed transaction fields
            
        Returns:
            List of ParsedTransaction objects with validation results
            
        Examples:
            >>> validator = FieldValidator()
            >>> data_list = [
            ...     {'amount': '100', 'currency': 'EGP'},
            ...     {'amount': '200', 'currency': 'USD'}
            ... ]
            >>> results = validator.validate_batch(data_list)
            >>> len(results)
            2
        """
        results = []
        
        for i, data in enumerate(data_list):
            try:
                result = self.validate(data)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error validating item {i}: {str(e)}")
                # Add a low-confidence result even on exception
                results.append(ParsedTransaction(
                    confidence='low',
                    warnings=[f"Batch validation error at index {i}: {str(e)}"]
                ))
        
        self.logger.info(f"Validated batch of {len(data_list)} transactions")
        return results


if __name__ == "__main__":
    import doctest
    doctest.testmod()
