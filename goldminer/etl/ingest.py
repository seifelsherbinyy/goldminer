"""
Data ingestion module for CSV and Excel files.

This module provides functionality for loading data from various sources including:
- CSV and Excel files (via DataIngestion class)
- SMS messages from text and JSON files (via load_sms_messages function)

The load_sms_messages function includes advanced sanitization and deduplication
to ensure clean, unique message data for downstream processing.
"""
import pandas as pd
import os
import json
import re
import unicodedata
from typing import List, Optional
from pathlib import Path
import glob
from goldminer.utils import setup_logger


class DataIngestion:
    """Handles ingestion of raw CSV and Excel data sources."""
    
    def __init__(self, config=None):
        """
        Initialize data ingestion.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
    
    def read_csv(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Read CSV file into DataFrame.
        
        Args:
            file_path: Path to CSV file
            **kwargs: Additional arguments for pd.read_csv
            
        Returns:
            DataFrame containing CSV data
        """
        try:
            self.logger.info(f"Reading CSV file: {file_path}")
            df = pd.read_csv(file_path, **kwargs)
            self.logger.info(f"Successfully read {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error reading CSV file {file_path}: {str(e)}")
            raise
    
    def read_excel(self, file_path: str, sheet_name: Optional[str] = None, **kwargs) -> pd.DataFrame:
        """
        Read Excel file into DataFrame.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to read (if None, reads first sheet)
            **kwargs: Additional arguments for pd.read_excel
            
        Returns:
            DataFrame containing Excel data
        """
        try:
            self.logger.info(f"Reading Excel file: {file_path}")
            if sheet_name:
                kwargs['sheet_name'] = sheet_name
            df = pd.read_excel(file_path, **kwargs)
            self.logger.info(f"Successfully read {len(df)} rows from {file_path}")
            return df
        except Exception as e:
            self.logger.error(f"Error reading Excel file {file_path}: {str(e)}")
            raise
    
    def ingest_directory(self, directory: str, file_pattern: str = "*") -> List[pd.DataFrame]:
        """
        Ingest all CSV and Excel files from a directory.
        
        Args:
            directory: Directory path
            file_pattern: File pattern to match (default: all files)
            
        Returns:
            List of DataFrames
        """
        dataframes = []
        
        if not os.path.exists(directory):
            self.logger.warning(f"Directory not found: {directory}")
            return dataframes
        
        # Find CSV files
        csv_pattern = os.path.join(directory, f"{file_pattern}.csv")
        csv_files = glob.glob(csv_pattern)
        
        for csv_file in csv_files:
            try:
                df = self.read_csv(csv_file)
                df['_source_file'] = os.path.basename(csv_file)
                dataframes.append(df)
            except Exception as e:
                self.logger.error(f"Failed to read {csv_file}: {str(e)}")
        
        # Find Excel files
        for ext in ['xlsx', 'xls']:
            excel_pattern = os.path.join(directory, f"{file_pattern}.{ext}")
            excel_files = glob.glob(excel_pattern)
            
            for excel_file in excel_files:
                try:
                    df = self.read_excel(excel_file)
                    df['_source_file'] = os.path.basename(excel_file)
                    dataframes.append(df)
                except Exception as e:
                    self.logger.error(f"Failed to read {excel_file}: {str(e)}")
        
        self.logger.info(f"Ingested {len(dataframes)} files from {directory}")
        return dataframes
    
    def ingest_file(self, file_path: str) -> pd.DataFrame:
        """
        Ingest a single file (CSV or Excel).
        
        Args:
            file_path: Path to file
            
        Returns:
            DataFrame containing file data
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.csv':
            df = self.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = self.read_excel(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        df['_source_file'] = os.path.basename(file_path)
        return df


def _sanitize_message(message: str) -> str:
    """
    Sanitize a single SMS message string.
    
    Performs the following cleaning operations:
    1. Strips leading and trailing whitespace
    2. Normalizes Unicode characters (removes RTL marks and invisible characters)
    3. Replaces multiple consecutive spaces with a single space
    
    Args:
        message: Raw message string to sanitize
        
    Returns:
        Sanitized message string
        
    Examples:
        >>> _sanitize_message("  Hello World  ")
        'Hello World'
        >>> _sanitize_message("Hello\u200e  World")
        'Hello World'
        >>> _sanitize_message("Multiple   spaces   here")
        'Multiple spaces here'
    """
    # Strip leading and trailing whitespace
    message = message.strip()
    
    # Remove common invisible Unicode characters and RTL marks
    # \u200e: Left-to-Right Mark
    # \u200f: Right-to-Left Mark
    # \u200b: Zero Width Space
    # \u200c: Zero Width Non-Joiner
    # \u200d: Zero Width Joiner
    # \ufeff: Zero Width No-Break Space (BOM)
    invisible_chars = ['\u200e', '\u200f', '\u200b', '\u200c', '\u200d', '\ufeff']
    for char in invisible_chars:
        message = message.replace(char, '')
    
    # Replace multiple consecutive spaces with a single space
    message = re.sub(r' +', ' ', message)
    
    return message


def load_sms_messages(
    filepath: Optional[str] = None,
    filetype: Optional[str] = None,
    max_messages: Optional[int] = None
) -> List[str]:
    """
    Load SMS messages from a local file with sanitization and deduplication.
    
    Reads SMS messages from a plain text .txt file (one SMS per line) or a 
    .json file containing a list of message strings. Handles encoding issues
    gracefully (e.g., UTF-16 → UTF-8) and returns fully decoded UTF-8 strings.
    
    Each message is sanitized by:
    - Stripping leading/trailing whitespace
    - Removing Unicode RTL marks and invisible characters (e.g., \u200e)
    - Replacing multiple consecutive spaces with a single space
    
    Duplicate messages are automatically removed, keeping only unique entries.
    
    Args:
        filepath: Path to the SMS file. If None, returns empty list.
        filetype: File type ('txt' or 'json'). If None, auto-detected from extension.
        max_messages: Maximum number of messages to load. If None, loads all messages.
        
    Returns:
        List of unique, sanitized strings where each string represents a single SMS message in UTF-8.
        
    Raises:
        ValueError: If filetype is invalid or file extension is not supported.
        
    Examples:
        >>> # Load all messages from a text file
        >>> messages = load_sms_messages('sms_export.txt')
        >>> print(f"Loaded {len(messages)} messages")
        
        >>> # Load first 100 messages from JSON file
        >>> messages = load_sms_messages('sms_export.json', max_messages=100)
        
        >>> # Explicitly specify file type
        >>> messages = load_sms_messages('messages.data', filetype='txt')
        
    Note:
        - Works offline - no internet connection required
        - Handles multiple encodings: UTF-8, UTF-16, latin-1, cp1252
        - Empty lines in .txt files are automatically filtered out
        - Messages are sanitized to remove invisible characters and normalize whitespace
        - Duplicate messages are automatically removed
        - Gracefully logs errors and returns empty list on failure
    """
    logger = setup_logger(__name__)
    
    # Return empty list if no filepath provided
    if filepath is None:
        logger.warning("No filepath provided to load_sms_messages()")
        return []
    
    # Check if file exists
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        return []
    
    # Auto-detect file type from extension if not specified
    if filetype is None:
        file_ext = Path(filepath).suffix.lower()
        if file_ext == '.txt':
            filetype = 'txt'
        elif file_ext == '.json':
            filetype = 'json'
        else:
            logger.error(f"Unsupported file extension: {file_ext}. Use .txt or .json")
            raise ValueError(f"Unsupported file extension: {file_ext}")
    
    # Normalize filetype
    filetype = filetype.lower()
    if filetype not in ['txt', 'json']:
        logger.error(f"Invalid filetype: {filetype}. Must be 'txt' or 'json'")
        raise ValueError(f"Invalid filetype: {filetype}. Must be 'txt' or 'json'")
    
    messages = []
    
    try:
        if filetype == 'txt':
            # Try multiple encodings for text files
            encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
            content = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        content = f.read()
                    logger.info(f"Successfully read {filepath} with {encoding} encoding")
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                logger.error(f"Failed to decode {filepath} with any supported encoding")
                return []
            
            # Split by lines and filter out empty lines
            messages = [line.strip() for line in content.split('\n') if line.strip()]
            
        elif filetype == 'json':
            # Try multiple encodings for JSON files
            encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be', 'latin-1', 'cp1252']
            data = None
            
            for encoding in encodings:
                try:
                    with open(filepath, 'r', encoding=encoding) as f:
                        data = json.load(f)
                    logger.info(f"Successfully read {filepath} with {encoding} encoding")
                    break
                except (UnicodeDecodeError, UnicodeError, json.JSONDecodeError):
                    continue
            
            if data is None:
                logger.error(f"Failed to decode or parse JSON from {filepath}")
                return []
            
            # Ensure data is a list of strings
            if isinstance(data, list):
                messages = [str(msg) for msg in data if msg]
            else:
                logger.error(f"JSON file does not contain a list: {filepath}")
                return []
        
        # Apply max_messages limit if specified
        if max_messages is not None and max_messages > 0:
            messages = messages[:max_messages]
            logger.info(f"Limited to first {max_messages} messages")
        
        # Sanitize all messages
        messages = [_sanitize_message(msg) for msg in messages]
        
        # Deduplicate messages while preserving order
        seen = set()
        deduplicated_messages = []
        for msg in messages:
            if msg and msg not in seen:
                seen.add(msg)
                deduplicated_messages.append(msg)
        
        if len(messages) != len(deduplicated_messages):
            logger.info(f"Removed {len(messages) - len(deduplicated_messages)} duplicate message(s)")
        
        logger.info(f"Successfully loaded {len(deduplicated_messages)} unique SMS messages from {filepath}")
        return deduplicated_messages
        
    except Exception as e:
        logger.error(f"Error reading SMS messages from {filepath}: {str(e)}")
        return []
