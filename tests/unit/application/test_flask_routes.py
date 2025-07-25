"""Unit tests for Flask routes."""

import json
import sqlite3
from unittest.mock import patch

from application.date_utils import parse_date_safely
from application.models import Invoice, InvoiceDetails


class TestDashboardRoute:
    """Test dashboard route functionality."""

    def test_dashboard_with_invoices(self, flask_app, create_test_customer):
        """Test dashboard displays recent invoices."""
        # Create test data
        customer_id = create_test_customer("Test Customer", "123 Test St")

        details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0,
        )
        Invoice.create(details)

        # Test dashboard route
        response = flask_app.get("/")
        assert response.status_code == 200
        assert b"Welcome to Invoice Manager" in response.data
        assert b"2025.03.15" in response.data
        assert b"Test Customer" in response.data
        assert b"$1200.00" in response.data

    def test_dashboard_with_empty_database(self, flask_app):
        """Test dashboard with no invoices shows friendly message."""
        response = flask_app.get("/")
        assert response.status_code == 200
        assert b"Welcome to Invoice Manager" in response.data
        assert b"No invoices yet" in response.data

    def test_dashboard_limits_to_three_invoices(self, flask_app, create_test_customer):
        """Test dashboard only shows 3 most recent invoices."""
        customer_id = create_test_customer("Test Customer", "123 Test St")

        # Create 5 invoices with different dates
        dates = ["03/10/2025", "03/15/2025", "03/20/2025", "03/25/2025", "03/30/2025"]
        for i, date in enumerate(dates):
            details = InvoiceDetails(
                invoice_number=f"2025.03.{10 + i * 5}",
                customer_id=customer_id,
                invoice_date=parse_date_safely(date),
                due_date=parse_date_safely(date),
                total_amount=1000.0 + i * 100,
            )
            Invoice.create(details)

        response = flask_app.get("/")
        assert response.status_code == 200

        # Should show the 3 most recent (03/30, 03/25, 03/20)
        assert b"2025.03.30" in response.data
        assert b"2025.03.25" in response.data
        assert b"2025.03.20" in response.data

        # Should not show the older ones
        assert b"2025.03.15" not in response.data
        assert b"2025.03.10" not in response.data

    def test_dashboard_database_error(self, flask_app):
        """Test dashboard handles database errors gracefully."""
        with patch("application.models.Invoice.get_recent") as mock_get_recent:
            mock_get_recent.side_effect = sqlite3.Error("Database connection failed")

            response = flask_app.get("/")
            assert response.status_code == 200
            assert b"Welcome to Invoice Manager" in response.data
            assert b"Unable to load invoices. Please try again later." in response.data


class TestStatusRoute:
    """Test status/health check route functionality."""

    def test_status_healthy(self, flask_app, create_test_customer):
        """Test status endpoint returns healthy with database connectivity."""
        # Create some test data
        customer_id = create_test_customer()
        details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0,
        )
        Invoice.create(details)

        response = flask_app.get("/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["total_invoices"] == 1

    def test_status_with_empty_database(self, flask_app):
        """Test status endpoint with empty database."""
        response = flask_app.get("/status")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["total_invoices"] == 0

    def test_status_content_type(self, flask_app):
        """Test status endpoint returns JSON content type."""
        response = flask_app.get("/status")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_status_database_error(self, flask_app):
        """Test status endpoint handles database errors and returns 503."""
        with patch("application.db.get_db_connection") as mock_get_connection:
            error_msg = "Database connection failed"
            mock_get_connection.side_effect = sqlite3.Error(error_msg)

            response = flask_app.get("/status")
            assert response.status_code == 503
            assert response.content_type == "application/json"

            data = json.loads(response.data)
            assert data["status"] == "unhealthy"
            assert "Database connection failed" in data["error"]

    def test_status_database_query_error(self, flask_app):
        """Test status endpoint handles database query errors."""
        with patch("application.db.get_db_connection") as mock_get_connection:
            # Mock connection that fails on execute
            mock_connection = mock_get_connection.return_value
            mock_connection.execute.side_effect = sqlite3.Error("Table not found")

            response = flask_app.get("/status")
            assert response.status_code == 503

            data = json.loads(response.data)
            assert data["status"] == "unhealthy"
            assert "Table not found" in data["error"]


class TestTemplateRendering:
    """Test template rendering functionality."""

    def test_dashboard_template_inheritance(self, flask_app):
        """Test dashboard template extends base template properly."""
        response = flask_app.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data
        assert b"<title>Dashboard - Invoice Manager</title>" in response.data
        assert b"Invoice Manager</a>" in response.data  # Navigation title
        assert b"&copy; 2025 Havelick Software Solutions" in response.data  # Footer

    def test_static_file_references(self, flask_app):
        """Test that templates reference static files correctly."""
        response = flask_app.get("/")
        assert response.status_code == 200
        assert b"/static/css/main.css" in response.data


class TestImportStructure:
    """Test that Flask app can import from application modules correctly."""

    def test_flask_app_starts_without_import_errors(self, flask_app):
        """Test that Flask app can be created without import errors."""
        # If we got this far in the tests, imports are working
        response = flask_app.get("/")
        assert response.status_code == 200

    def test_flask_can_import_models(self, flask_app):
        """Test that Flask routes can import and use models."""
        # This test passes if the status route works, proving imports work
        response = flask_app.get("/status")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "total_invoices" in data  # Proves Invoice model was imported and used
