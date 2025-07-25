"""Unit tests for database functions."""

import os
import sqlite3
import tempfile

import pytest

from application.app import create_app
from application.db import close_db, get_db_connection, init_db


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = create_app()
    return app


@pytest.fixture(autouse=True)
def cleanup_db():
    """Cleanup database connections before and after each test."""
    # Nothing to cleanup with per-request connections
    yield


class TestDatabaseOperations:
    """Test cases for core database operations."""

    def test_init_db_creates_database_with_schema(self, app):
        """Test that init_db creates database with proper schema."""
        with app.app_context(), tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")

            init_db(db_path)

            # Check that database file was created
            assert os.path.exists(db_path)

            # Check that tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = ["vendors", "customers", "invoices", "invoice_items"]
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"

            conn.close()

    def test_init_db_schema_file_missing(self, app):
        """Test init_db when schema file is missing."""
        with app.app_context(), tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            original_cwd = os.getcwd()

            try:
                os.chdir(tmp_dir)  # Change to directory without schema.sql
                with pytest.raises(FileNotFoundError):
                    init_db(db_path)
            finally:
                os.chdir(original_cwd)

    def test_get_db_connection_creates_connection(self, app):
        """Test that get_db_connection creates a connection in Flask context."""
        with app.app_context(), tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            app.config["DATABASE"] = db_path
            init_db(db_path)

            # Get connection - should work in Flask context
            conn1 = get_db_connection()
            assert isinstance(conn1, sqlite3.Connection)

            # Test that connection works
            cursor = conn1.cursor()
            cursor.execute("SELECT 1 as test_col")
            result = cursor.fetchone()
            assert result["test_col"] == 1

    def test_close_db_no_connection(self, app):
        """Test close_db handles case with no connection in Flask context."""
        # Should not raise an exception even if no connection exists
        close_db()
