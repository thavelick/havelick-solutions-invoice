"""Unit tests for database functions."""

import os
import sqlite3
import tempfile

import pytest

from application.db import close_db, get_db_connection, init_db, reset_db


@pytest.fixture(autouse=True)
def cleanup_db():
    """Cleanup database connections before and after each test."""
    close_db()
    yield
    close_db()


class TestDatabaseOperations:
    """Test cases for core database operations."""

    def test_init_db_creates_database_with_schema(self):
        """Test that init_db creates database with proper schema."""
        with tempfile.TemporaryDirectory() as tmp_dir:
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

    def test_init_db_schema_file_missing(self):
        """Test init_db when schema file is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            original_cwd = os.getcwd()

            try:
                os.chdir(tmp_dir)  # Change to directory without schema.sql
                with pytest.raises(FileNotFoundError):
                    init_db(db_path)
            finally:
                os.chdir(original_cwd)

    def test_get_db_connection_creates_and_reuses_connection(self):
        """Test that get_db_connection creates a connection and reuses it."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)

            # Get connection
            conn1 = get_db_connection()
            assert isinstance(conn1, sqlite3.Connection)

            # Test that connection works
            cursor = conn1.cursor()
            cursor.execute("SELECT 1 as test_col")
            result = cursor.fetchone()
            assert result["test_col"] == 1

            # Get connection again - should be the same object
            conn2 = get_db_connection()
            assert conn1 is conn2

    def test_close_db_closes_connection(self):
        """Test that close_db properly closes the connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")

            init_db(db_path)
            conn = get_db_connection()
            cursor = conn.cursor()

            # Verify connection is active
            cursor.execute("SELECT 1 as test_col")
            assert cursor.fetchone()["test_col"] == 1

            close_db()

            # Connection should be closed now
            with pytest.raises(sqlite3.ProgrammingError):
                cursor.execute("SELECT 1")

    def test_close_db_no_connection(self):
        """Test that close_db handles case when no connection exists."""
        close_db()  # Should not raise an exception

    def test_reset_db_changes_path_and_closes_connection(self):
        """Test that reset_db changes the database path and closes existing
        connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path1 = os.path.join(tmp_dir, "test1.db")
            db_path2 = os.path.join(tmp_dir, "test2.db")

            # Initialize first database
            init_db(db_path1)
            conn1 = get_db_connection()
            cursor = conn1.cursor()

            # Verify connection is active
            cursor.execute("SELECT 1 as test_col")
            assert cursor.fetchone()["test_col"] == 1

            # Reset to second database
            reset_db(db_path2)
            init_db(db_path2)
            conn2 = get_db_connection()

            # Should be different connections
            assert conn1 is not conn2

            # Original connection should be closed
            with pytest.raises(sqlite3.ProgrammingError):
                cursor.execute("SELECT 1")
