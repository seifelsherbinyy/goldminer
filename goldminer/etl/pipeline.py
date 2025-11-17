"""ETL Pipeline orchestrator."""
import pandas as pd
from typing import List, Optional, Dict, Any
from goldminer.etl.ingest import DataIngestion
from goldminer.etl.schema import SchemaInference
from goldminer.etl.normalize import DataNormalizer
from goldminer.etl.clean import DataCleaner
from goldminer.etl.database import DatabaseManager
from goldminer.analysis.anomaly_detector import AnomalyDetector
from goldminer.utils import setup_logger


class ETLPipeline:
    """Orchestrates the complete ETL pipeline."""
    
    def __init__(self, config=None):
        """
        Initialize ETL pipeline.
        
        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Initialize components
        self.ingestion = DataIngestion(config)
        self.schema_inference = SchemaInference(config)
        self.normalizer = DataNormalizer(config)
        self.cleaner = DataCleaner(config)
        
        # Initialize anomaly detector (optional)
        try:
            self.anomaly_detector = AnomalyDetector()
            self.logger.info("AnomalyDetector initialized")
        except Exception as e:
            self.logger.warning(f"Could not initialize AnomalyDetector: {e}")
            self.anomaly_detector = None
        
        # Get database path from config
        if config:
            db_path = config.get('database.path', 'data/processed/goldminer.db')
        else:
            db_path = 'data/processed/goldminer.db'
        
        self.db_manager = DatabaseManager(db_path, config)
    
    def run_pipeline(self, 
                    source_path: str,
                    table_name: str = 'unified_data',
                    is_directory: bool = False,
                    skip_duplicates: bool = True,
                    skip_outliers: bool = False,
                    detect_anomalies: bool = False) -> pd.DataFrame:
        """
        Run the complete ETL pipeline.
        
        Args:
            source_path: Path to data source (file or directory)
            table_name: Name of target database table
            is_directory: Whether source_path is a directory
            skip_duplicates: Whether to remove duplicates
            skip_outliers: Whether to remove outliers
            detect_anomalies: Whether to detect anomalies in transactions
            
        Returns:
            Processed DataFrame
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting ETL Pipeline")
        self.logger.info("=" * 60)
        
        # Step 1: Ingest data
        self.logger.info("Step 1: Data Ingestion")
        if is_directory:
            dataframes = self.ingestion.ingest_directory(source_path)
            if not dataframes:
                raise ValueError(f"No data files found in {source_path}")
            df = pd.concat(dataframes, ignore_index=True)
        else:
            df = self.ingestion.ingest_file(source_path)
        
        self.logger.info(f"Ingested {len(df)} rows, {len(df.columns)} columns")
        
        # Step 2: Infer schema
        self.logger.info("Step 2: Schema Inference")
        schema = self.schema_inference.infer_schema(df)
        self.logger.info(f"Schema inferred for {len(schema['columns'])} columns")
        
        # Step 3: Normalize data
        self.logger.info("Step 3: Data Normalization")
        df = self.normalizer.normalize_dataframe(df)
        
        # Step 4: Standardize dates
        self.logger.info("Step 4: Date Standardization")
        df = self.normalizer.standardize_dates(df)
        
        # Step 5: Clean data
        self.logger.info("Step 5: Data Cleaning")
        
        # Remove duplicates
        if skip_duplicates:
            df = self.cleaner.remove_duplicates(df)
        
        # Clean text columns
        df = self.cleaner.clean_text_columns(df)
        
        # Remove outliers if requested
        if skip_outliers:
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            if numeric_cols:
                df = self.cleaner.remove_outliers(df, numeric_cols)
        
        # Step 6: Generate quality report
        self.logger.info("Step 6: Data Quality Validation")
        quality_report = self.cleaner.validate_data_quality(df)
        self.logger.info(f"Quality Report: {quality_report['duplicate_rows']} duplicates remaining")
        
        # Step 7: Anomaly Detection (optional)
        if detect_anomalies and self.anomaly_detector:
            self.logger.info("Step 7: Anomaly Detection")
            df = self._enrich_with_anomalies(df)
        
        # Step 8: Save to database
        step_num = 8 if detect_anomalies and self.anomaly_detector else 7
        self.logger.info(f"Step {step_num}: Database Storage")
        self.db_manager.save_dataframe(df, table_name, if_exists='replace')
        
        self.logger.info("=" * 60)
        self.logger.info("ETL Pipeline Completed Successfully")
        self.logger.info(f"Final dataset: {len(df)} rows, {len(df.columns)} columns")
        self.logger.info("=" * 60)
        
        return df
    
    def run_incremental_pipeline(self,
                                source_path: str,
                                table_name: str = 'unified_data',
                                is_directory: bool = False) -> pd.DataFrame:
        """
        Run incremental ETL pipeline (appends to existing data).
        
        Args:
            source_path: Path to data source (file or directory)
            table_name: Name of target database table
            is_directory: Whether source_path is a directory
            
        Returns:
            Processed DataFrame
        """
        self.logger.info("Starting Incremental ETL Pipeline")
        
        # Ingest new data
        if is_directory:
            dataframes = self.ingestion.ingest_directory(source_path)
            if not dataframes:
                raise ValueError(f"No data files found in {source_path}")
            df = pd.concat(dataframes, ignore_index=True)
        else:
            df = self.ingestion.ingest_file(source_path)
        
        # Normalize and clean
        df = self.normalizer.normalize_dataframe(df)
        df = self.normalizer.standardize_dates(df)
        df = self.cleaner.clean_text_columns(df)
        
        # Load existing data
        try:
            existing_df = self.db_manager.load_dataframe(table_name)
            self.logger.info(f"Loaded {len(existing_df)} existing rows")
            
            # Combine and remove duplicates
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = self.cleaner.remove_duplicates(combined_df)
            
            # Save back to database
            self.db_manager.save_dataframe(combined_df, table_name, if_exists='replace')
            
            self.logger.info(f"Added {len(combined_df) - len(existing_df)} new rows")
            return combined_df
            
        except Exception as e:
            self.logger.warning(f"Could not load existing data: {str(e)}")
            self.logger.info("Creating new table")
            self.db_manager.save_dataframe(df, table_name, if_exists='replace')
            return df
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status and statistics.
        
        Returns:
            Dictionary containing pipeline status
        """
        status = {
            "database_path": self.db_manager.db_path,
            "tables": []
        }
        
        try:
            tables = self.db_manager.list_tables()
            for table in tables:
                table_info = self.db_manager.get_table_info(table)
                status["tables"].append(table_info)
        except Exception as e:
            self.logger.error(f"Error getting pipeline status: {str(e)}")
        
        return status
    
    def _enrich_with_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich DataFrame with anomaly detection flags.
        
        Args:
            df: Input DataFrame with transaction data
            
        Returns:
            DataFrame with added 'anomalies' column containing lists of anomaly flags
        """
        if not self.anomaly_detector:
            self.logger.warning("AnomalyDetector not available, skipping anomaly detection")
            return df
        
        try:
            # Identify relevant columns for anomaly detection
            # Common column names for transaction data
            amount_col = None
            merchant_col = None
            date_col = None
            
            # Try to find amount column
            for col in ['amount', 'Amount', 'transaction_amount', 'value']:
                if col in df.columns:
                    amount_col = col
                    break
            
            # Try to find merchant/payee column
            for col in ['payee', 'Payee', 'merchant', 'Merchant', 'description', 'Description']:
                if col in df.columns:
                    merchant_col = col
                    break
            
            # Try to find date column
            for col in ['date', 'Date', 'transaction_date', 'timestamp', 'Timestamp']:
                if col in df.columns:
                    date_col = col
                    break
            
            if not amount_col and not merchant_col:
                self.logger.warning("Could not find required columns for anomaly detection")
                return df
            
            # Convert DataFrame to list of transaction dictionaries
            transactions = []
            for _, row in df.iterrows():
                txn = {}
                if amount_col:
                    txn['amount'] = row[amount_col]
                if merchant_col:
                    txn['payee'] = row[merchant_col]
                if date_col:
                    txn['date'] = str(row[date_col])
                transactions.append(txn)
            
            # Detect anomalies
            anomaly_results = self.anomaly_detector.detect_anomalies_batch(transactions)
            
            # Add anomaly flags to DataFrame
            df['anomalies'] = None
            df['anomalies'] = df['anomalies'].astype('object')
            
            for idx, anomaly_list in anomaly_results.items():
                df.at[idx, 'anomalies'] = ','.join(anomaly_list) if anomaly_list else None
            
            anomaly_count = len([v for v in df['anomalies'] if v is not None])
            self.logger.info(f"Detected anomalies in {anomaly_count} out of {len(df)} transactions")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error during anomaly detection: {e}")
            return df

