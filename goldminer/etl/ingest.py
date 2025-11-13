"""Data ingestion module for CSV and Excel files."""
import pandas as pd
import os
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
