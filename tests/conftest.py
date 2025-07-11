"""Pytest configuration and fixtures for invoice generator tests."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


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
        "client": test_dir / "test-client.json",
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


# Unit test fixtures

@pytest.fixture
def sample_client_data():
    """Provide sample client data for testing."""
    return {
        "client": {
            "name": "Test Company Inc",
            "address": "123 Test Street\nTest City, TS 12345"
        }
    }


@pytest.fixture
def sample_invoice_items():
    """Provide sample invoice items for testing."""
    return [
        {
            "date": "03/15/2025",
            "description": "Software development work",
            "quantity": 2.0,
            "rate": 125.0
        },
        {
            "date": "03/16/2025", 
            "description": "Code review and testing",
            "quantity": 1.5,
            "rate": 100.0
        }
    ]


@pytest.fixture
def temp_client_file(sample_client_data):
    """Create a temporary client JSON file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_client_data, f)
        filename = f.name
    
    yield filename
    
    # Cleanup
    if os.path.exists(filename):
        os.unlink(filename)


@pytest.fixture
def temp_invoice_data_file(sample_invoice_items):
    """Create a temporary invoice data file for testing."""
    content = "Date\tHours\tAmount\tDescription\n"
    for item in sample_invoice_items:
        amount = item["quantity"] * item["rate"]
        content += f"{item['date']}\t{item['quantity']}\t{amount:.2f}\t{item['description']}\n"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(content)
        filename = f.name
    
    yield filename
    
    # Cleanup
    if os.path.exists(filename):
        os.unlink(filename)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
