"""Database connection management for SQLite maintenance database."""

import sqlite3
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DatabaseManager:
    """Manages SQLite database connections and operations."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with optional path."""
        if db_path is None:
            # Default to database directory relative to this file
            self.db_path = Path(__file__).parent.parent / "database" / "database.db"
        else:
            self.db_path = Path(db_path)
        
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_database_exists()
    
    def _ensure_database_exists(self) -> None:
        """Create database and tables if they don't exist."""
        if not self.db_path.exists():
            self._create_database()
    
    def _create_database(self) -> None:
        """Create database with schema and mock data."""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read schema and data files
        schema_path = self.db_path.parent / "schema.sql"
        data_path = self.db_path.parent / "mock_data.sql"
        
        with sqlite3.connect(self.db_path) as conn:
            # Create schema
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
            
            # Insert mock data
            if data_path.exists():
                with open(data_path, 'r') as f:
                    conn.executescript(f.read())
            
            conn.commit()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating if needed."""
        if self.connection is None or self._connection_closed():
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        return self.connection
    
    def _connection_closed(self) -> bool:
        """Check if connection is closed."""
        try:
            self.connection.execute('SELECT 1')
            return False
        except (sqlite3.ProgrammingError, AttributeError):
            return True
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute SELECT query and return results as list of dicts."""
        conn = self.get_connection()
        cursor = conn.execute(query, params or ())
        
        # Convert rows to list of dictionaries
        columns = [description[0] for description in cursor.description]
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        return results
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema information for a specific table."""
        query = "PRAGMA table_info(?)"
        return self.execute_query(f"PRAGMA table_info({table_name})")
    
    def get_all_tables(self) -> List[str]:
        """Get list of all table names in the database."""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        results = self.execute_query(query)
        return [row['name'] for row in results]
    
    def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a specific table."""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        tables = self.get_all_tables()
        stats = {
            'total_tables': len(tables),
            'table_stats': {}
        }
        
        for table in tables:
            row_count = self.get_table_row_count(table)
            schema = self.get_table_schema(table)
            stats['table_stats'][table] = {
                'row_count': row_count,
                'column_count': len(schema),
                'columns': [col['name'] for col in schema]
            }
        
        return stats
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global database manager instance
db_manager = DatabaseManager()