"""Transaction database management module for persistent storage using SQLite."""
import sqlite3
import uuid
import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Union, Literal
from datetime import datetime
from collections import defaultdict
from goldminer.utils import setup_logger


class TransactionDB:
    """Manages persistent storage of transactions using SQLite with full-text search."""
    
    def __init__(self, db_path: str = "data/processed/transactions.db"):
        """
        Initialize transaction database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = setup_logger(__name__)
        self.connection = None
        
        # Create database and tables on initialization
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema with indexes and FTS5 virtual table."""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        cursor = self.connection.cursor()
        
        # Create main transactions table with proper schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                payee TEXT,
                category TEXT,
                subcategory TEXT,
                amount REAL,
                account_id TEXT,
                account_type TEXT,
                interest_rate REAL,
                tags TEXT,
                urgency TEXT,
                currency TEXT,
                anomalies TEXT,
                confidence REAL,
                UNIQUE(date, payee, amount, account_id)
            )
        """)
        
        # Create indexes for fast retrieval
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date 
            ON transactions(date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_payee 
            ON transactions(payee)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category 
            ON transactions(category)
        """)
        
        # Create FTS5 virtual table for full-text search
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS transactions_fts USING fts5(
                id UNINDEXED,
                date,
                payee,
                category,
                subcategory,
                tags,
                content=transactions,
                content_rowid=rowid
            )
        """)
        
        # Create triggers to keep FTS5 table in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS transactions_ai AFTER INSERT ON transactions BEGIN
                INSERT INTO transactions_fts(rowid, id, date, payee, category, subcategory, tags)
                VALUES (new.rowid, new.id, new.date, new.payee, new.category, new.subcategory, new.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS transactions_ad AFTER DELETE ON transactions BEGIN
                INSERT INTO transactions_fts(transactions_fts, rowid, id, date, payee, category, subcategory, tags)
                VALUES('delete', old.rowid, old.id, old.date, old.payee, old.category, old.subcategory, old.tags);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS transactions_au AFTER UPDATE ON transactions BEGIN
                INSERT INTO transactions_fts(transactions_fts, rowid, id, date, payee, category, subcategory, tags)
                VALUES('delete', old.rowid, old.id, old.date, old.payee, old.category, old.subcategory, old.tags);
                INSERT INTO transactions_fts(rowid, id, date, payee, category, subcategory, tags)
                VALUES (new.rowid, new.id, new.date, new.payee, new.category, new.subcategory, new.tags);
            END
        """)
        
        self.connection.commit()
        self.logger.info(f"Database initialized at {self.db_path}")
    
    def insert(self, transaction: Dict[str, Any]) -> str:
        """
        Insert a new transaction into the database.
        
        Args:
            transaction: Dictionary containing transaction data
            
        Returns:
            Transaction ID (UUID)
            
        Raises:
            sqlite3.IntegrityError: If duplicate transaction detected
        """
        # Generate UUID if not provided
        if 'id' not in transaction or not transaction['id']:
            transaction['id'] = str(uuid.uuid4())
        
        # Ensure date is in proper format
        if 'date' in transaction and isinstance(transaction['date'], datetime):
            transaction['date'] = transaction['date'].isoformat()
        
        cursor = self.connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO transactions (
                    id, date, payee, category, subcategory, amount,
                    account_id, account_type, interest_rate, tags,
                    urgency, currency, anomalies, confidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction.get('id'),
                transaction.get('date'),
                transaction.get('payee'),
                transaction.get('category'),
                transaction.get('subcategory'),
                transaction.get('amount'),
                transaction.get('account_id'),
                transaction.get('account_type'),
                transaction.get('interest_rate'),
                transaction.get('tags'),
                transaction.get('urgency'),
                transaction.get('currency'),
                transaction.get('anomalies'),
                transaction.get('confidence')
            ))
            
            self.connection.commit()
            self.logger.debug(f"Inserted transaction {transaction['id']}")
            return transaction['id']
            
        except sqlite3.IntegrityError as e:
            self.logger.warning(f"Duplicate transaction detected: {str(e)}")
            raise
    
    def update(self, id: str, fields: Dict[str, Any]) -> bool:
        """
        Update an existing transaction by ID.
        
        Args:
            id: Transaction ID (UUID)
            fields: Dictionary of fields to update
            
        Returns:
            True if update successful, False if transaction not found
        """
        if not fields:
            return False
        
        # Build dynamic UPDATE query
        set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
        values = list(fields.values())
        values.append(id)
        
        cursor = self.connection.cursor()
        cursor.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ?",
            values
        )
        
        self.connection.commit()
        rows_affected = cursor.rowcount
        
        if rows_affected > 0:
            self.logger.debug(f"Updated transaction {id}")
            return True
        else:
            self.logger.warning(f"Transaction {id} not found")
            return False
    
    def query(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query transactions with flexible filtering.
        
        Args:
            filters: Dictionary of filter conditions. Supports:
                - Direct field matching: {'category': 'Food'}
                - Range queries: {'amount_min': 10, 'amount_max': 100}
                - Date range: {'date_from': '2024-01-01', 'date_to': '2024-12-31'}
                - Full-text search: {'search': 'restaurant'}
                - List matching: {'payee_in': ['Store1', 'Store2']}
                
        Returns:
            List of transaction dictionaries
        """
        cursor = self.connection.cursor()
        
        # Use FTS5 for full-text search
        if filters and 'search' in filters:
            search_term = filters['search']
            cursor.execute("""
                SELECT t.* FROM transactions t
                INNER JOIN transactions_fts fts ON t.rowid = fts.rowid
                WHERE transactions_fts MATCH ?
            """, (search_term,))
        else:
            # Build WHERE clause from filters
            where_clauses = []
            values = []
            
            if filters:
                for key, value in filters.items():
                    if key.endswith('_min'):
                        field = key[:-4]
                        where_clauses.append(f"{field} >= ?")
                        values.append(value)
                    elif key.endswith('_max'):
                        field = key[:-4]
                        where_clauses.append(f"{field} <= ?")
                        values.append(value)
                    elif key.endswith('_from'):
                        field = key[:-5]
                        where_clauses.append(f"{field} >= ?")
                        values.append(value)
                    elif key.endswith('_to'):
                        field = key[:-3]
                        where_clauses.append(f"{field} <= ?")
                        values.append(value)
                    elif key.endswith('_in'):
                        field = key[:-3]
                        placeholders = ','.join(['?'] * len(value))
                        where_clauses.append(f"{field} IN ({placeholders})")
                        values.extend(value)
                    elif key != 'search':
                        where_clauses.append(f"{key} = ?")
                        values.append(value)
            
            query = "SELECT * FROM transactions"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, values)
        
        # Convert rows to dictionaries
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'id': row['id'],
                'date': row['date'],
                'payee': row['payee'],
                'category': row['category'],
                'subcategory': row['subcategory'],
                'amount': row['amount'],
                'account_id': row['account_id'],
                'account_type': row['account_type'],
                'interest_rate': row['interest_rate'],
                'tags': row['tags'],
                'urgency': row['urgency'],
                'currency': row['currency'],
                'anomalies': row['anomalies'],
                'confidence': row['confidence']
            })
        
        self.logger.debug(f"Query returned {len(results)} results")
        return results
    
    def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get a transaction by ID.
        
        Args:
            id: Transaction ID (UUID)
            
        Returns:
            Transaction dictionary or None if not found
        """
        results = self.query({'id': id})
        return results[0] if results else None
    
    def delete(self, id: str) -> bool:
        """
        Delete a transaction by ID.
        
        Args:
            id: Transaction ID (UUID)
            
        Returns:
            True if deletion successful, False if transaction not found
        """
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM transactions WHERE id = ?", (id,))
        self.connection.commit()
        
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            self.logger.debug(f"Deleted transaction {id}")
            return True
        else:
            self.logger.warning(f"Transaction {id} not found")
            return False
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count transactions matching filters.
        
        Args:
            filters: Dictionary of filter conditions (same as query method)
            
        Returns:
            Number of matching transactions
        """
        cursor = self.connection.cursor()
        
        if filters and 'search' in filters:
            search_term = filters['search']
            cursor.execute("""
                SELECT COUNT(*) FROM transactions t
                INNER JOIN transactions_fts fts ON t.rowid = fts.rowid
                WHERE transactions_fts MATCH ?
            """, (search_term,))
        else:
            where_clauses = []
            values = []
            
            if filters:
                for key, value in filters.items():
                    if key.endswith('_min'):
                        field = key[:-4]
                        where_clauses.append(f"{field} >= ?")
                        values.append(value)
                    elif key.endswith('_max'):
                        field = key[:-4]
                        where_clauses.append(f"{field} <= ?")
                        values.append(value)
                    elif key.endswith('_from'):
                        field = key[:-5]
                        where_clauses.append(f"{field} >= ?")
                        values.append(value)
                    elif key.endswith('_to'):
                        field = key[:-3]
                        where_clauses.append(f"{field} <= ?")
                        values.append(value)
                    elif key.endswith('_in'):
                        field = key[:-3]
                        placeholders = ','.join(['?'] * len(value))
                        where_clauses.append(f"{field} IN ({placeholders})")
                        values.extend(value)
                    else:
                        where_clauses.append(f"{key} = ?")
                        values.append(value)
            
            query = "SELECT COUNT(*) FROM transactions"
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, values)
        
        return cursor.fetchone()[0]
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _compute_transaction_hash(self, transaction: Dict[str, Any]) -> str:
        """
        Compute a hash for a transaction based on its composite key.
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            SHA256 hash of composite key (date, amount, payee, account_id)
        """
        # Extract key fields for hashing
        date = str(transaction.get('date', ''))
        resolved_date = str(transaction.get('resolved_date', ''))
        amount = str(transaction.get('amount', ''))
        payee = str(transaction.get('payee', ''))
        account_id = str(transaction.get('account_id', ''))
        transaction_state = str(transaction.get('transaction_state', ''))

        # Create composite key string
        composite_key = f"{date}|{resolved_date}|{amount}|{payee}|{account_id}|{transaction_state}"
        
        # Compute hash
        return hashlib.sha256(composite_key.encode('utf-8')).hexdigest()
    
    def _transaction_exists(self, transaction: Dict[str, Any]) -> Optional[str]:
        """
        Check if a transaction exists based on composite key.
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            Transaction ID if exists, None otherwise
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT id FROM transactions 
            WHERE date = ? AND amount = ? AND payee = ? AND account_id = ?
        """, (
            transaction.get('date'),
            transaction.get('amount'),
            transaction.get('payee'),
            transaction.get('account_id')
        ))
        
        result = cursor.fetchone()
        return result[0] if result else None
    
    def insert_transaction(
        self, 
        transaction: Dict[str, Any], 
        mode: Literal['skip', 'upsert'] = 'skip'
    ) -> Dict[str, Any]:
        """
        Insert a transaction with duplicate checking and configurable conflict resolution.
        
        Args:
            transaction: Dictionary containing transaction data
            mode: Conflict resolution mode:
                - 'skip': Skip duplicate transactions (default)
                - 'upsert': Update existing transaction if duplicate found
                
        Returns:
            Dictionary with:
                - 'id': Transaction ID (UUID)
                - 'status': 'inserted', 'skipped', or 'updated'
                - 'message': Description of the action taken
                
        Raises:
            Exception: If database operation fails (transaction will be rolled back)
        """
        try:
            # Check if transaction exists
            existing_id = self._transaction_exists(transaction)
            
            if existing_id:
                if mode == 'skip':
                    self.logger.info(
                        f"Skipping duplicate transaction: {transaction.get('payee')} "
                        f"on {transaction.get('date')} for {transaction.get('amount')}"
                    )
                    return {
                        'id': existing_id,
                        'status': 'skipped',
                        'message': 'Duplicate transaction skipped'
                    }
                elif mode == 'upsert':
                    # Update existing transaction with new data
                    update_fields = {k: v for k, v in transaction.items() if k != 'id'}
                    self.update(existing_id, update_fields)
                    self.logger.info(
                        f"Updated duplicate transaction: {existing_id}"
                    )
                    return {
                        'id': existing_id,
                        'status': 'updated',
                        'message': 'Duplicate transaction updated'
                    }
            
            # No duplicate found, insert new transaction
            transaction_id = self.insert(transaction)
            return {
                'id': transaction_id,
                'status': 'inserted',
                'message': 'Transaction inserted successfully'
            }
            
        except Exception as e:
            self.connection.rollback()
            self.logger.error(f"Failed to insert transaction: {str(e)}")
            raise
    
    def bulk_insert(
        self,
        transactions: List[Dict[str, Any]],
        mode: Literal['skip', 'upsert'] = 'skip'
    ) -> Dict[str, Any]:
        """
        Bulk insert transactions with duplicate checking and performance tracking.
        
        Args:
            transactions: List of transaction dictionaries
            mode: Conflict resolution mode ('skip' or 'upsert')
            
        Returns:
            Dictionary with:
                - 'inserted': Number of transactions inserted
                - 'updated': Number of transactions updated
                - 'skipped': Number of transactions skipped
                - 'failed': Number of failed transactions
                - 'duration': Time taken in seconds
                - 'transactions_per_second': Insert rate
                - 'details': List of failed transaction details
                
        Raises:
            Exception: If critical database operation fails (all changes rolled back)
        """
        start_time = time.time()
        stats = {
            'inserted': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
            'details': []
        }
        
        try:
            # Begin transaction for atomicity
            cursor = self.connection.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            for idx, transaction in enumerate(transactions):
                try:
                    result = self.insert_transaction(transaction, mode=mode)
                    
                    if result['status'] == 'inserted':
                        stats['inserted'] += 1
                    elif result['status'] == 'updated':
                        stats['updated'] += 1
                    elif result['status'] == 'skipped':
                        stats['skipped'] += 1
                        
                except Exception as e:
                    stats['failed'] += 1
                    stats['details'].append({
                        'index': idx,
                        'transaction': transaction,
                        'error': str(e)
                    })
                    self.logger.warning(
                        f"Failed to process transaction at index {idx}: {str(e)}"
                    )
            
            # Commit all changes
            self.connection.commit()
            
            # Calculate performance metrics
            duration = time.time() - start_time
            total_processed = stats['inserted'] + stats['updated'] + stats['skipped']
            tps = total_processed / duration if duration > 0 else 0
            
            stats['duration'] = round(duration, 3)
            stats['transactions_per_second'] = round(tps, 2)
            
            self.logger.info(
                f"Bulk insert completed: {stats['inserted']} inserted, "
                f"{stats['updated']} updated, {stats['skipped']} skipped, "
                f"{stats['failed']} failed in {duration:.2f}s ({tps:.2f} TPS)"
            )
            
            return stats
            
        except Exception as e:
            # Rollback all changes on critical failure
            self.connection.rollback()
            self.logger.error(f"Bulk insert failed, rolled back all changes: {str(e)}")
            raise
    
    def get_summary_by_month(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate monthly summary aggregations for dashboard visualization.
        
        Aggregates total spend by:
        - Category
        - Account type
        - Tag
        
        Args:
            start_date: Optional start date filter (ISO format: YYYY-MM-DD)
            end_date: Optional end date filter (ISO format: YYYY-MM-DD)
            
        Returns:
            Dictionary with monthly aggregations:
                - 'by_month': Overall monthly totals
                - 'by_category': Spending by category per month
                - 'by_account_type': Spending by account type per month
                - 'by_tag': Spending by tag per month
        """
        cursor = self.connection.cursor()
        
        # Build date filter
        date_filter = ""
        params = []
        if start_date and end_date:
            date_filter = "WHERE date >= ? AND date <= ?"
            params.extend([start_date, end_date])
        elif start_date:
            date_filter = "WHERE date >= ?"
            params.append(start_date)
        elif end_date:
            date_filter = "WHERE date <= ?"
            params.append(end_date)
        
        # Get overall monthly totals
        query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount
            FROM transactions
            {date_filter}
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month
        """
        cursor.execute(query, params)
        
        by_month = []
        for row in cursor.fetchall():
            by_month.append({
                'month': row[0],
                'transaction_count': row[1],
                'total_amount': round(row[2], 2) if row[2] else 0,
                'avg_amount': round(row[3], 2) if row[3] else 0,
                'min_amount': round(row[4], 2) if row[4] else 0,
                'max_amount': round(row[5], 2) if row[5] else 0
            })
        
        # Get spending by category per month
        query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                category,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM transactions
            {date_filter}
            GROUP BY strftime('%Y-%m', date), category
            ORDER BY month, category
        """
        cursor.execute(query, params)
        
        by_category = defaultdict(lambda: defaultdict(float))
        for row in cursor.fetchall():
            month = row[0]
            category = row[1] or 'Uncategorized'
            by_category[month][category] = {
                'transaction_count': row[2],
                'total_amount': round(row[3], 2) if row[3] else 0
            }
        
        # Convert defaultdict to regular dict
        by_category = {k: dict(v) for k, v in by_category.items()}
        
        # Get spending by account type per month
        query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                account_type,
                COUNT(*) as transaction_count,
                SUM(amount) as total_amount
            FROM transactions
            {date_filter}
            GROUP BY strftime('%Y-%m', date), account_type
            ORDER BY month, account_type
        """
        cursor.execute(query, params)
        
        by_account_type = defaultdict(lambda: defaultdict(float))
        for row in cursor.fetchall():
            month = row[0]
            account_type = row[1] or 'Unknown'
            by_account_type[month][account_type] = {
                'transaction_count': row[2],
                'total_amount': round(row[3], 2) if row[3] else 0
            }
        
        by_account_type = {k: dict(v) for k, v in by_account_type.items()}
        
        # Get spending by tag per month
        # Note: Tags are comma-separated, so we need to split them
        if date_filter:
            tag_filter = f"{date_filter} AND tags IS NOT NULL AND tags != ''"
        else:
            tag_filter = "WHERE tags IS NOT NULL AND tags != ''"
        
        query = f"""
            SELECT 
                strftime('%Y-%m', date) as month,
                tags,
                amount
            FROM transactions
            {tag_filter}
            ORDER BY month
        """
        cursor.execute(query, params)
        
        by_tag = defaultdict(lambda: defaultdict(lambda: {'transaction_count': 0, 'total_amount': 0.0}))
        for row in cursor.fetchall():
            month = row[0]
            tags = row[1]
            amount = row[2] or 0
            
            # Split tags and aggregate
            if tags:
                for tag in tags.split(','):
                    tag = tag.strip()
                    if tag:
                        by_tag[month][tag]['transaction_count'] += 1
                        by_tag[month][tag]['total_amount'] += amount
        
        # Round amounts and convert to regular dict
        by_tag_formatted = {}
        for month, tags in by_tag.items():
            by_tag_formatted[month] = {}
            for tag, data in tags.items():
                by_tag_formatted[month][tag] = {
                    'transaction_count': data['transaction_count'],
                    'total_amount': round(data['total_amount'], 2)
                }
        
        return {
            'by_month': by_month,
            'by_category': by_category,
            'by_account_type': by_account_type,
            'by_tag': by_tag_formatted
        }
