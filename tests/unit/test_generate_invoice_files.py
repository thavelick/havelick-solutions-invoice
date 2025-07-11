"""Unit tests for generate_invoice_files function."""

import os
import tempfile
from datetime import date
from unittest.mock import patch

import pytest

from generate_invoice import generate_invoice_files


class TestGenerateInvoiceFiles:
    """Test cases for generate_invoice_files function."""

    @pytest.fixture
    def sample_invoice_data(self):
        """Create sample invoice data for testing."""
        return {
            "invoice_number": "2025.03.15",
            "invoice_date": "03/15/2025",
            "due_date": "04/14/2025",
            "total": 1200.0,
            "payment_terms": "Net 30 days",
            "client": {
                "name": "Acme Corporation",
                "address": "123 Business Ave\nAnytown, CA 90210",
            },
            "company": {
                "name": "Havelick Software Solutions, LLC",
                "address": "7815 Robinson Way\nArvada CO 80004",
                "email": "tristan@havelick.com",
                "phone": "303-475-7244",
            },
            "items": [
                {
                    "date": date(2025, 3, 15),
                    "description": "Web Development",
                    "quantity": 8.0,
                    "rate": 150.0,
                    "amount": 1200.0,
                }
            ],
        }

    @pytest.fixture
    def mock_template_html(self):
        """Create mock HTML template content."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Invoice {{ invoice_number }}</title>
</head>
<body>
    <h1>Invoice {{ invoice_number }}</h1>
    <p>Client: {{ client.name }}</p>
    <p>Total: ${{ "%.2f"|format(total) }}</p>
    <table>
        {% for item in items %}
        <tr>
            <td>{{ item.description }}</td>
            <td>${{ "%.2f"|format(item.amount) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
        """.strip()

    def test_generate_files_creates_html_and_pdf(self, sample_invoice_data, mock_template_html):
        """Test that both HTML and PDF files are created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template file
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(mock_template_html)

            with patch("os.getcwd", return_value=temp_dir):
                with patch("builtins.print"):
                    generate_invoice_files(sample_invoice_data, temp_dir)

            # Check that files were created
            expected_html = os.path.join(
                temp_dir, "acme-corporation-invoice-03.15.2025.html"
            )
            expected_pdf = os.path.join(
                temp_dir, "acme-corporation-invoice-03.15.2025.pdf"
            )

            assert os.path.exists(expected_html)
            assert os.path.exists(expected_pdf)

    def test_html_content_includes_invoice_data(self, sample_invoice_data, mock_template_html):
        """Test that HTML content includes the invoice data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(mock_template_html)

            with patch("os.getcwd", return_value=temp_dir):
                with patch("builtins.print"):
                    generate_invoice_files(sample_invoice_data, temp_dir)

            expected_html = os.path.join(
                temp_dir, "acme-corporation-invoice-03.15.2025.html"
            )

            # Check HTML content includes key data
            with open(expected_html, "r", encoding="utf-8") as f:
                html_content = f.read()
                assert "Invoice 2025.03.15" in html_content
                assert "Acme Corporation" in html_content
                assert "Web Development" in html_content
                assert "$1200.00" in html_content

    def test_filename_normalization(self, sample_invoice_data, mock_template_html):
        """Test that company names are normalized for filenames."""
        test_cases = [
            ("Test Company LLC", "test-company-llc-invoice-03.15.2025"),
            ("Smith & Associates", "smith-&-associates-invoice-03.15.2025"),
        ]

        for company_name, expected_base in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                template_path = os.path.join(temp_dir, "invoice_template.html")
                with open(template_path, "w", encoding="utf-8") as f:
                    f.write(mock_template_html)

                test_data = sample_invoice_data.copy()
                test_data["client"]["name"] = company_name

                with patch("os.getcwd", return_value=temp_dir):
                    with patch("builtins.print"):
                        generate_invoice_files(test_data, temp_dir)

                expected_html = os.path.join(temp_dir, f"{expected_base}.html")
                assert os.path.exists(expected_html)

    def test_multiple_items_included(self, sample_invoice_data, mock_template_html):
        """Test that multiple invoice items are included in output."""
        sample_invoice_data["items"] = [
            {
                "date": date(2025, 3, 15),
                "description": "Web Development",
                "quantity": 8.0,
                "rate": 150.0,
                "amount": 1200.0,
            },
            {
                "date": date(2025, 3, 16),
                "description": "Bug Fixes",
                "quantity": 2.0,
                "rate": 150.0,
                "amount": 300.0,
            },
        ]
        sample_invoice_data["total"] = 1500.0

        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(mock_template_html)

            with patch("os.getcwd", return_value=temp_dir):
                with patch("builtins.print"):
                    generate_invoice_files(sample_invoice_data, temp_dir)

            expected_html = os.path.join(
                temp_dir, "acme-corporation-invoice-03.15.2025.html"
            )

            with open(expected_html, "r", encoding="utf-8") as f:
                html_content = f.read()
                assert "Web Development" in html_content
                assert "Bug Fixes" in html_content
                assert "$1500.00" in html_content

    def test_output_directory_parameter(self, sample_invoice_data, mock_template_html):
        """Test that files are created in the specified output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(mock_template_html)

            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir)

            with patch("os.getcwd", return_value=temp_dir):
                with patch("builtins.print"):
                    generate_invoice_files(sample_invoice_data, output_dir)

            expected_html = os.path.join(
                output_dir, "acme-corporation-invoice-03.15.2025.html"
            )
            assert os.path.exists(expected_html)