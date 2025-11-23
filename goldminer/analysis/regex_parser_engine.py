"""
RegexParserEngine for extracting structured transaction fields from SMS messages.

This module provides functionality for parsing SMS text using bank-specific
regex templates to extract transaction details like amount, currency, date,
payee, transaction type, and card suffix.
"""
import re
import yaml
import json
import os
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from goldminer.utils import setup_logger
from goldminer.analysis.transaction_classifier import TransactionClassifier


class RegexParserEngine:
    """
    Extracts structured transaction fields from SMS messages using regex templates.
    
    This class loads bank-specific parsing templates from YAML or JSON files and
    applies regex patterns to extract transaction details. It handles partial matches
    and provides confidence indicators when critical fields are missing.
    
    Attributes:
        templates (Dict[str, List[Dict]]): Dictionary mapping bank IDs to their templates
        logger: Logger instance for tracking parsing operations
        use_card_classifier: Whether to use CardClassifier for enhanced card suffix extraction
    
    Note:
        For comprehensive examples, see the unit tests in tests/unit/test_regex_parser_engine.py
    """
    
    def __init__(
        self,
        templates_file: Optional[str] = None,
        use_card_classifier: bool = True,
        transaction_classifier: Optional[TransactionClassifier] = None,
        use_transaction_classifier: bool = True,
    ):
        """
        Initialize the RegexParserEngine.
        
        Args:
            templates_file: Path to YAML or JSON file containing parsing templates.
                          If None, uses default 'sms_parsing_templates.yaml' in project root.
            use_card_classifier: Whether to use CardClassifier for enhanced card suffix
                               extraction. Default is True.
            transaction_classifier: Optional TransactionClassifier instance to enrich
                                    parsed results with ML categories.
            use_transaction_classifier: Whether to enable ML classification after parsing.
        
        Raises:
            FileNotFoundError: If templates file doesn't exist
            ValueError: If templates file is invalid or malformed
        
        Examples:
            >>> parser = RegexParserEngine()
            >>> len(parser.templates) > 0
            True
        """
        self.logger = setup_logger(__name__)
        self.use_card_classifier = use_card_classifier
        self.transaction_classifier = None
        
        # Determine templates file path
        if templates_file is None:
            # Default to sms_parsing_templates.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            templates_file = project_root / 'sms_parsing_templates.yaml'
        
        self.templates_file = str(templates_file)
        
        # Load templates
        self.templates = self._load_templates()

        if use_transaction_classifier:
            try:
                self.transaction_classifier = transaction_classifier or TransactionClassifier()
                if self.transaction_classifier.pipeline:
                    self.logger.info("Transaction classifier loaded and ready for inference")
                else:
                    self.logger.info("Transaction classifier initialized without a trained model")
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning(f"Transaction classifier unavailable: {exc}")
        
        self.logger.info(
            f"RegexParserEngine initialized with {len(self.templates)} bank templates"
        )
    
    def _load_templates(self) -> Dict[str, List[Dict]]:
        """
        Load parsing templates from YAML or JSON file.
        
        Returns:
            Dictionary mapping bank IDs to lists of template dictionaries
            
        Raises:
            FileNotFoundError: If templates file doesn't exist
            ValueError: If templates file is invalid or malformed
        """
        if not os.path.exists(self.templates_file):
            self.logger.error(f"Templates file not found: {self.templates_file}")
            raise FileNotFoundError(f"Templates file not found: {self.templates_file}")
        
        try:
            # Try loading as YAML first
            if self.templates_file.endswith(('.yaml', '.yml')):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates = yaml.safe_load(f)
            elif self.templates_file.endswith('.json'):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
            else:
                # Try YAML by default
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    templates = yaml.safe_load(f)
            
            if not templates or not isinstance(templates, dict):
                raise ValueError("Templates file must contain a valid dictionary")
            
            # Validate templates structure
            for bank_id, template_list in templates.items():
                if not isinstance(template_list, list):
                    raise ValueError(f"Templates for bank '{bank_id}' must be a list")
                
                for template in template_list:
                    if not isinstance(template, dict):
                        raise ValueError(f"Each template for '{bank_id}' must be a dictionary")
                    if 'patterns' not in template:
                        raise ValueError(f"Template in '{bank_id}' missing 'patterns' key")
            
            self.logger.info(f"Loaded templates for {len(templates)} banks from {self.templates_file}")
            return templates
            
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file: {e}")
            raise ValueError(f"Invalid YAML in templates file: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON file: {e}")
            raise ValueError(f"Invalid JSON in templates file: {e}")
        except Exception as e:
            self.logger.error(f"Error loading templates: {e}")
            raise
    
    @staticmethod
    def convert_arabic_indic_numerals(text: str) -> str:
        """
        Convert Arabic-Indic numerals to Western (Latin) numerals.
        
        This method replaces Arabic-Indic digits (٠-٩) with Western equivalents (0-9)
        and converts Arabic comma separators to their Western counterparts.
        It handles mixed-language strings correctly and preserves all non-numeral
        characters, including Latin alphabet characters.
        
        Arabic-Indic numerals used in many Arabic-speaking countries:
        - ٠ (U+0660) -> 0
        - ١ (U+0661) -> 1
        - ٢ (U+0662) -> 2
        - ٣ (U+0663) -> 3
        - ٤ (U+0664) -> 4
        - ٥ (U+0665) -> 5
        - ٦ (U+0666) -> 6
        - ٧ (U+0667) -> 7
        - ٨ (U+0668) -> 8
        - ٩ (U+0669) -> 9
        - ٫ (U+066B) -> . (Arabic decimal separator)
        - ٬ (U+066C) -> , (Arabic thousands separator)
        
        Args:
            text: Input text that may contain Arabic-Indic numerals
            
        Returns:
            Text with Arabic-Indic numerals converted to Western numerals
            
        Examples:
            >>> RegexParserEngine.convert_arabic_indic_numerals("١٢٣")
            '123'
            >>> RegexParserEngine.convert_arabic_indic_numerals("مبلغ ١٥٠٫٥٠ جنيه")
            'مبلغ 150.50 جنيه'
            >>> RegexParserEngine.convert_arabic_indic_numerals("Mixed: ١٢٣ and 456")
            'Mixed: 123 and 456'
            >>> RegexParserEngine.convert_arabic_indic_numerals("Latin text ABC")
            'Latin text ABC'
            >>> RegexParserEngine.convert_arabic_indic_numerals("١٬٢٣٤٫٥٦")
            '1,234.56'
        """
        if not text or not isinstance(text, str):
            return text
        
        # Define the translation table for Arabic-Indic to Western numerals
        # Arabic-Indic digits: ٠١٢٣٤٥٦٧٨٩
        # Western digits: 0123456789
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
            '٫': '.',  # U+066B - Arabic decimal separator
            '٬': ',',  # U+066C - Arabic thousands separator
        })
        
        return text.translate(translation_table)
    
    def _extract_field(self, sms: str, pattern: str, field_name: str) -> Optional[str]:
        """
        Extract a field from SMS using a regex pattern.
        
        Args:
            sms: SMS message text
            pattern: Regex pattern with named group
            field_name: Name of the field being extracted
            
        Returns:
            Extracted value or None if not found
        """
        try:
            match = re.search(pattern, sms, re.IGNORECASE | re.UNICODE)
            if match:
                # Get the named group values
                groups = match.groupdict()
                if groups:
                    # Prefer the field name itself if it exists as a named group
                    if field_name in groups and groups[field_name] is not None:
                        value = groups[field_name].strip()
                        # Convert Arabic-Indic numerals to Western numerals
                        return self.convert_arabic_indic_numerals(value)
                    # Otherwise return the first non-None value
                    for value in groups.values():
                        if value is not None:
                            value = value.strip()
                            # Convert Arabic-Indic numerals to Western numerals
                            return self.convert_arabic_indic_numerals(value)
            return None
        except re.error as e:
            self.logger.warning(f"Regex error for pattern '{pattern}': {e}")
            return None
    
    def _extract_card_suffix_enhanced(self, sms: str) -> Optional[str]:
        """
        Extract card suffix using CardClassifier for enhanced extraction.
        
        This method uses CardClassifier's extract_card_suffix which supports
        more patterns and better handles both English and Arabic text.
        
        Args:
            sms: SMS message text
            
        Returns:
            4-digit card suffix or None if not found
        """
        try:
            # Import CardClassifier here to avoid circular imports
            from .card_classifier import CardClassifier
            return CardClassifier.extract_card_suffix(sms)
        except Exception as e:
            self.logger.warning(f"Error using CardClassifier for suffix extraction: {e}")
            return None
    
    def _apply_template(
        self,
        sms: str,
        template: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        """
        Apply a single template to extract fields from SMS.
        
        Args:
            sms: SMS message text
            template: Template dictionary with patterns
            
        Returns:
            Dictionary of extracted field values
        """
        extracted = {}
        patterns = template.get('patterns', {})
        
        for field_name, pattern in patterns.items():
            value = self._extract_field(sms, pattern, field_name)
            extracted[field_name] = value
        
        return extracted
    
    def _calculate_confidence(
        self,
        extracted: Dict[str, Optional[str]],
        required_fields: List[str]
    ) -> str:
        """
        Calculate confidence level based on extracted fields.
        
        Args:
            extracted: Dictionary of extracted field values
            required_fields: List of field names that are required
            
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        # Check if all required fields are present
        missing_required = [
            field for field in required_fields
            if field not in extracted or extracted[field] is None
        ]
        
        if missing_required:
            return 'low'
        
        # Count how many optional fields were extracted
        total_fields = len(extracted)
        extracted_fields = sum(1 for v in extracted.values() if v is not None)
        
        if extracted_fields >= total_fields - 1:  # All or all but one
            return 'high'
        elif extracted_fields >= total_fields // 2:  # At least half
            return 'medium'
        else:
            return 'low'
    
    def parse_sms(
        self,
        sms: str,
        bank_id: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Parse SMS text and extract structured transaction fields.
        
        This method attempts to extract transaction details from the SMS using
        bank-specific templates. It tries all templates for the specified bank
        (or all banks if bank_id is None) and returns the best match.
        
        Args:
            sms: SMS message text to parse
            bank_id: Bank identifier (e.g., 'HSBC', 'CIB'). If None, tries all banks.
            template_name: Specific template name to use. If None, tries all templates.
            
        Returns:
            Dictionary containing:
                - amount: Transaction amount (str or None)
                - currency: Currency code (str or None)
                - date: Transaction date (str or None)
                - payee: Payee/merchant name (str or None)
                - transaction_type: Type of transaction (str or None)
                - card_suffix: Last 4 digits of card (str or None)
                - confidence: Confidence level ('high', 'medium', 'low')
                - matched_bank: Bank ID that matched (if bank_id was None)
                - matched_template: Template name that matched
                - ml_category: ML-predicted category (if classifier is available)
                - ml_category_score: Confidence score from the classifier
                - ml_category_confidence: Discrete confidence label for ML prediction
                - sms_text: The raw SMS text that was parsed
        
        Examples:
            >>> parser = RegexParserEngine()
            >>> # Example with amount extraction
            >>> sms = "Transaction charged 100 EGP"
            >>> result = parser.parse_sms(sms, bank_id="HSBC")
            >>> result['amount'] is not None or result['confidence'] == 'low'
            True
        """
        if not sms or not isinstance(sms, str):
            self.logger.warning(f"Invalid SMS input: {type(sms)}")
            return self._empty_result(confidence='low')
        
        sms = sms.strip()
        if not sms:
            self.logger.warning("Empty SMS message provided")
            return self._empty_result(confidence='low')
        
        # Determine which banks to try
        banks_to_try = []
        if bank_id is not None:
            if bank_id in self.templates:
                banks_to_try = [(bank_id, self.templates[bank_id])]
            else:
                self.logger.warning(f"Bank ID '{bank_id}' not found in templates")
                return self._empty_result(confidence='low')
        else:
            # Try all banks
            banks_to_try = list(self.templates.items())
        
        best_result = None
        best_score = 0
        
        # Try each bank's templates
        for current_bank_id, template_list in banks_to_try:
            for template in template_list:
                # Skip if specific template name requested and doesn't match
                if template_name is not None and template.get('name') != template_name:
                    continue
                
                # Extract fields using this template
                extracted = self._apply_template(sms, template)
                
                # Enhance card suffix extraction using CardClassifier if enabled
                if self.use_card_classifier and extracted.get('card_suffix') is None:
                    enhanced_suffix = self._extract_card_suffix_enhanced(sms)
                    if enhanced_suffix:
                        extracted['card_suffix'] = enhanced_suffix
                
                # Calculate confidence
                required_fields = template.get('required_fields', ['amount'])
                confidence = self._calculate_confidence(extracted, required_fields)
                
                # Score this result
                score = sum(1 for v in extracted.values() if v is not None)
                
                # Keep track of best result
                if score > best_score or (score == best_score and confidence == 'high'):
                    best_score = score
                    best_result = {
                        **extracted,
                        'confidence': confidence,
                        'matched_bank': current_bank_id if bank_id is None else bank_id,
                        'matched_template': template.get('name', 'unnamed')
                    }
        
        # Return best result or empty result
        if best_result is None:
            self.logger.warning(f"No template matched for SMS: {sms[:50]}...")
            return self._empty_result(
                confidence='low',
                matched_bank=bank_id if bank_id else 'unknown',
                sms_text=sms,
            )

        best_result['sms_text'] = sms

        if self.transaction_classifier:
            classification = self.transaction_classifier.classify_sms(
                sms_text=sms,
                parsed_fields=best_result,
            )
            best_result.update(classification.to_dict())
        else:
            best_result.setdefault('ml_category', None)
            best_result.setdefault('ml_category_score', None)
            best_result.setdefault('ml_category_confidence', None)

        self.logger.info(
            f"Parsed SMS successfully: bank={best_result.get('matched_bank')}, "
            f"confidence={best_result.get('confidence')}"
        )
        
        return best_result
    
    def _empty_result(
        self,
        confidence: str = 'low',
        matched_bank: Optional[str] = None,
        sms_text: Optional[str] = None,
    ) -> Dict[str, Optional[str]]:
        """
        Create an empty result dictionary.
        
        Args:
            confidence: Confidence level
            matched_bank: Bank ID if known
            
        Returns:
            Dictionary with all fields set to None
        """
        return {
            'amount': None,
            'currency': None,
            'date': None,
            'payee': None,
            'transaction_type': None,
            'card_suffix': None,
            'confidence': confidence,
            'matched_bank': matched_bank,
            'matched_template': None,
            'sms_text': sms_text,
            'ml_category': None,
            'ml_category_score': None,
            'ml_category_confidence': None,
        }
    
    def parse_sms_batch(
        self,
        sms_list: List[str],
        bank_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Optional[str]]]:
        """
        Parse multiple SMS messages in batch.
        
        Args:
            sms_list: List of SMS message texts
            bank_ids: Optional list of bank IDs corresponding to each SMS.
                     If None, tries all banks for each SMS.
            
        Returns:
            List of parsed result dictionaries
            
        Examples:
            >>> parser = RegexParserEngine()
            >>> messages = [
            ...     "HSBC card 1234 charged 100 EGP",
            ...     "CIB transaction 200 جنيه"
            ... ]
            >>> results = parser.parse_sms_batch(messages, bank_ids=["HSBC", "CIB"])
            >>> len(results)
            2
        """
        results = []
        
        if bank_ids is None:
            bank_ids = [None] * len(sms_list)
        elif len(bank_ids) != len(sms_list):
            raise ValueError("bank_ids length must match sms_list length")
        
        for sms, bank_id in zip(sms_list, bank_ids):
            result = self.parse_sms(sms, bank_id=bank_id)
            results.append(result)
        
        self.logger.info(f"Parsed batch of {len(sms_list)} SMS messages")
        return results
    
    def get_supported_banks(self) -> List[str]:
        """
        Get list of supported bank IDs.
        
        Returns:
            List of bank identifiers that have templates loaded
            
        Examples:
            >>> parser = RegexParserEngine()
            >>> banks = parser.get_supported_banks()
            >>> 'HSBC' in banks
            True
        """
        return list(self.templates.keys())
    
    def get_bank_templates(self, bank_id: str) -> List[str]:
        """
        Get list of template names for a specific bank.
        
        Args:
            bank_id: Bank identifier
            
        Returns:
            List of template names for the specified bank
            
        Raises:
            ValueError: If bank_id is not found
            
        Examples:
            >>> parser = RegexParserEngine()
            >>> templates = parser.get_bank_templates("HSBC")
            >>> len(templates) > 0
            True
        """
        if bank_id not in self.templates:
            raise ValueError(f"Bank ID '{bank_id}' not found in templates")
        
        return [t.get('name', 'unnamed') for t in self.templates[bank_id]]
    
    def reload_templates(self, templates_file: Optional[str] = None) -> None:
        """
        Reload parsing templates from file.
        
        Useful for updating templates without recreating the parser instance.
        
        Args:
            templates_file: Path to templates file. If None, reloads from current file.
            
        Examples:
            >>> parser = RegexParserEngine()
            >>> parser.reload_templates()  # Reload from same file
            >>> len(parser.templates) > 0
            True
        """
        if templates_file is not None:
            self.templates_file = templates_file
        
        self.templates = self._load_templates()
        self.logger.info("Templates reloaded successfully")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
