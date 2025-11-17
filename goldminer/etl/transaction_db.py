"""Transaction database management module for persistent storage using SQLite."""
import sqlite3
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
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
