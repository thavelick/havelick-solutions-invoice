"""Database connection management for invoice application."""

import sqlite3

from flask import current_app, g


def init_db(db_path: str = "invoices.db"):
    """Initialize database schema from schema.sql file."""
    # Store db_path in Flask config
    current_app.config["DATABASE"] = db_path
    connection = get_db_connection()

    # Read and execute schema file
    with open("application/schema.sql", encoding="utf-8") as f:
        connection.executescript(f.read())

    connection.commit()


def get_db_connection() -> sqlite3.Connection:
    """Get database connection using Flask per-request pattern."""
    # Flask per-request connection pattern
    if "db" not in g:
        db_path = current_app.config.get("DATABASE", "invoices.db")
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(_e=None):
    """Close database connection (Flask teardown handler)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    """Initialize database with Flask app."""
    app.teardown_appcontext(close_db)
    app.config.setdefault("DATABASE", "invoices.db")
