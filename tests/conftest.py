"""Pytest configuration and fixtures for invoice generator tests."""

import subprocess
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
    return {
        "client": test_dir / "test-client.json",
        "invoice_data": test_dir / "invoice-data-3-15.txt",
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
        # For test data: Acme Corp, invoice date 03/15/2025
        base_filename = calculate_expected_filename("Acme Corp", "03/15/2025")
        expected_html = output_dir / f"{base_filename}.html"
        expected_pdf = output_dir / f"{base_filename}.pdf"

        return result, expected_html, expected_pdf

    return _generate
