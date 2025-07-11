"""Database connection management for invoice application."""

import sqlite3
from typing import Optional


# Global connection storage (for non-Flask usage)
_db_connection: Optional[sqlite3.Connection] = None
_db_path: str = "invoices.db"


def init_db(db_path: str = "invoices.db"):
    """Initialize database schema from schema.sql file."""
    global _db_path
    _db_path = db_path
    
    connection = get_db_connection()
    
    # Read and execute schema file
    with open("application/schema.sql", "r", encoding="utf-8") as f:
        connection.executescript(f.read())
    
    connection.commit()


def get_db_connection() -> sqlite3.Connection:
    """Get database connection, creating one if it doesn't exist."""
    global _db_connection, _db_path
    
    if _db_connection is None:
        _db_connection = sqlite3.connect(
            _db_path, detect_types=sqlite3.PARSE_DECLTYPES
        )
        _db_connection.row_factory = sqlite3.Row
    
    return _db_connection


def close_db():
    """Close database connection."""
    global _db_connection
    
    if _db_connection is not None:
        _db_connection.close()
        _db_connection = None


def reset_db(db_path: str = "invoices.db"):
    """Reset database connection with new path."""
    global _db_path
    close_db()
    _db_path = db_path