"""Pytest configuration and fixtures for invoice generator tests."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from application.db import close_db, init_db


@pytest.fixture(scope="session")
def playwright_config():
    """Configure playwright for tests."""
    return {
        "headless": True,
        "timeout": 30000,
    }


@pytest.fixture
def test_data_files():
    """Provide paths to test data files."""
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    return {
        "client": test_dir / "etc" / "test-client.json",
        "invoice_data": project_root / "invoice-data-3-31.txt",
    }


def calculate_expected_filename(client_name, invoice_date):
    """Calculate expected output filename based on client name and invoice date."""
    company_name = (
        client_name.lower().replace(" ", "-").replace(",", "").replace(".", "")
    )
    formatted_date = invoice_date.replace("/", ".")
    return f"{company_name}-invoice-{formatted_date}"


@pytest.fixture
def invoice_generator():
    """Provide invoice generation helper function."""

    def _generate(client_file, invoice_data_file, output_dir):
        """Generate invoice and return subprocess result and expected file paths."""
        # Create temporary database file for this test
        test_db = output_dir / "test_invoices.db"

        # Run invoice generation with output directory using one-shot command
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "generate_invoice.py",
                "--db-path",
                str(test_db),
                "one-shot",
                str(client_file),
                str(invoice_data_file),
                "--output-dir",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # Calculate expected filenames
        # For test data: Acme Corp, invoice date from filename: 03/31/2025
        base_filename = calculate_expected_filename("Acme Corp", "03/31/2025")
        expected_html = output_dir / f"{base_filename}.html"
        expected_pdf = output_dir / f"{base_filename}.pdf"

        return result, expected_html, expected_pdf

    return _generate


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        init_db(db_path)
        yield db_path
        close_db()


@pytest.fixture
def create_test_customer():
    """Fixture to create test customers."""

    def _create_customer(name: str = "Test Company", address: str = "123 Test St"):
        from application.models import Customer

        return Customer.create(name, address)

    return _create_customer


@pytest.fixture
def create_test_invoice():
    """Fixture to create test invoices."""

    def _create_invoice(
        customer_id: int,
        invoice_number: str = "2025.03.15",
        total_amount: float = 1000.0,
    ):
        from application.models import Invoice, InvoiceDetails, parse_date_safely

        details = InvoiceDetails(
            invoice_number=invoice_number,
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=total_amount,
        )
        return Invoice.create(details)

    return _create_invoice


@pytest.fixture
def create_test_invoice_item():
    """Fixture to create test invoice items."""

    def _create_invoice_item(
        invoice_id: int,
        description: str = "Test Work",
        quantity: float = 8.0,
        rate: float = 150.0,
    ):
        from application.models import InvoiceItem, LineItem, parse_date_safely

        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description=description,
            quantity=quantity,
            rate=rate,
            amount=quantity * rate,
        )
        InvoiceItem.add(line_item)
        return line_item

    return _create_invoice_item


@pytest.fixture
def from_dict_checker():
    """Fixture that provides a tool for testing from_dict methods."""
    from typing import Any, Dict, Type

    def check(model_class: Type, valid_record: Dict[str, Any], required_fields: list):
        """
        Test a model's from_dict method.

        Args:
            model_class: The model class to test
            valid_record: A valid record dictionary
            required_fields: List of required field names
        """
        # Test valid record
        instance = model_class.from_dict(valid_record)
        for field, value in valid_record.items():
            assert getattr(instance, field) == value

        # Test missing field
        for field in required_fields:
            incomplete_record = valid_record.copy()
            del incomplete_record[field]
            with pytest.raises(KeyError):
                model_class.from_dict(incomplete_record)

        # Test None values
        none_record: Dict[str, Any] = {field: None for field in valid_record.keys()}
        none_record["id"] = 1  # Keep ID as valid
        none_instance = model_class.from_dict(none_record)
        for field, value in none_record.items():
            assert getattr(none_instance, field) == value

    return check
