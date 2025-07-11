"""Unit tests for database functions."""

import os
import sqlite3
import tempfile
import pytest

from application.db import init_db, get_db_connection, close_db, reset_db


@pytest.fixture(autouse=True)
def cleanup_db():
    """Cleanup database connections before and after each test."""
    close_db()
    yield
    close_db()


class TestInitDb:
    """Test cases for init_db function."""

    def test_init_db_creates_database(self):
        """Test that init_db creates database with proper schema."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            init_db(db_path)
            
            # Check that database file was created
            assert os.path.exists(db_path)
            
            # Check that tables were created
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check for expected tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['vendors', 'customers', 'invoices', 'invoice_items']
            for table in expected_tables:
                assert table in tables, f"Table {table} not found in database"
            
            conn.close()

    def test_init_db_with_default_path(self):
        """Test init_db with default database path."""
        # Clean up any existing database and connection
        close_db()
        if os.path.exists("invoices.db"):
            os.remove("invoices.db")
        
        try:
            init_db()
            assert os.path.exists("invoices.db")
        finally:
            # Clean up
            close_db()
            if os.path.exists("invoices.db"):
                os.remove("invoices.db")

    def test_init_db_schema_file_missing(self):
        """Test init_db when schema file is missing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            # Save original working directory
            original_cwd = os.getcwd()
            
            try:
                # Change to temp directory where schema.sql doesn't exist
                os.chdir(tmp_dir)
                
                with pytest.raises(FileNotFoundError):
                    init_db(db_path)
                    
            finally:
                # Restore original working directory
                os.chdir(original_cwd)


class TestGetDbConnection:
    """Test cases for get_db_connection function."""

    def test_get_db_connection_creates_connection(self):
        """Test that get_db_connection creates a valid connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            # First initialize the database
            init_db(db_path)
            
            # Get connection
            conn = get_db_connection()
            
            assert isinstance(conn, sqlite3.Connection)
            assert conn is not None
            
            # Test that connection works
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_col")
            result = cursor.fetchone()
            assert result["test_col"] == 1

    def test_get_db_connection_reuses_connection(self):
        """Test that get_db_connection reuses existing connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            init_db(db_path)
            
            # Get connection twice
            conn1 = get_db_connection()
            conn2 = get_db_connection()
            
            # Should be the same connection object
            assert conn1 is conn2


class TestCloseDb:
    """Test cases for close_db function."""

    def test_close_db_closes_connection(self):
        """Test that close_db properly closes the connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            
            init_db(db_path)
            conn = get_db_connection()
            
            # Verify connection is active
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_col")
            assert cursor.fetchone()["test_col"] == 1
            
            close_db()
            
            # Connection should be closed now
            with pytest.raises(sqlite3.ProgrammingError):
                cursor.execute("SELECT 1")

    def test_close_db_no_connection(self):
        """Test that close_db handles case when no connection exists."""
        # Should not raise an exception
        close_db()


class TestResetDb:
    """Test cases for reset_db function."""

    def test_reset_db_changes_path(self):
        """Test that reset_db changes the database path."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path1 = os.path.join(tmp_dir, "test1.db")
            db_path2 = os.path.join(tmp_dir, "test2.db")
            
            # Initialize first database
            init_db(db_path1)
            conn1 = get_db_connection()
            
            # Reset to second database
            reset_db(db_path2)
            init_db(db_path2)
            conn2 = get_db_connection()
            
            # Should be different connections
            assert conn1 is not conn2

    def test_reset_db_closes_existing_connection(self):
        """Test that reset_db closes existing connection."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path1 = os.path.join(tmp_dir, "test1.db")
            db_path2 = os.path.join(tmp_dir, "test2.db")
            
            init_db(db_path1)
            conn1 = get_db_connection()
            
            # Verify connection is active
            cursor = conn1.cursor()
            cursor.execute("SELECT 1 as test_col")
            assert cursor.fetchone()["test_col"] == 1
            
            reset_db(db_path2)
            
            # Original connection should be closed
            with pytest.raises(sqlite3.ProgrammingError):
                cursor.execute("SELECT 1")