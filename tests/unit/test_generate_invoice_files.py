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
                "address": "123 Business Ave\nAnytown, CA 90210"
            },
            "company": {
                "name": "Havelick Software Solutions, LLC",
                "address": "7815 Robinson Way\nArvada CO 80004",
                "email": "tristan@havelick.com",
                "phone": "303-475-7244"
            },
            "items": [
                {
                    "date": date(2025, 3, 15),
                    "description": "Web Development",
                    "quantity": 8.0,
                    "rate": 150.0,
                    "amount": 1200.0
                }
            ]
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
    <p>Date: {{ invoice_date }}</p>
    <p>Due: {{ due_date }}</p>
    <p>Total: ${{ "%.2f"|format(total) }}</p>
    <table>
        {% for item in items %}
        <tr>
            <td>{{ item.date }}</td>
            <td>{{ item.description }}</td>
            <td>{{ item.quantity }}</td>
            <td>${{ "%.2f"|format(item.rate) }}</td>
            <td>${{ "%.2f"|format(item.amount) }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
        """.strip()

    @pytest.fixture
    def temp_template_file(self, mock_template_html):
        """Create a temporary template file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(mock_template_html)
            template_path = f.name
        yield template_path
        os.unlink(template_path)

    def test_generate_files_basic(self, sample_invoice_data, mock_template_html):
        """Test basic file generation with valid data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template file
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            # Mock the current directory to be our temp directory
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print') as mock_print:
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            # Check that files were created
            expected_html = os.path.join(temp_dir, "acme-corporation-invoice-03.15.2025.html")
            expected_pdf = os.path.join(temp_dir, "acme-corporation-invoice-03.15.2025.pdf")
            
            assert os.path.exists(expected_html)
            assert os.path.exists(expected_pdf)
            
            # Check HTML content
            with open(expected_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert "Invoice 2025.03.15" in html_content
                assert "Acme Corporation" in html_content
                assert "03/15/2025" in html_content
                assert "Web Development" in html_content
                assert "$1200.00" in html_content
            
            # Check PDF exists and has content
            assert os.path.getsize(expected_pdf) > 0
            
            # Check print output
            mock_print.assert_called_once()
            print_args = mock_print.call_args[0][0]
            assert "Total: $1200.00" in print_args

    def test_filename_generation_company_name_normalization(self, sample_invoice_data, mock_template_html):
        """Test filename generation with various company name formats."""
        test_cases = [
            ("Acme Corporation", "acme-corporation-invoice-03.15.2025"),
            ("Smith & Associates, LLC", "smith-&-associates-llc-invoice-03.15.2025"),
            ("Tech Co.", "tech-co-invoice-03.15.2025"),
            ("ABC Company, Inc.", "abc-company-inc-invoice-03.15.2025"),
            ("Multi Word Company Name", "multi-word-company-name-invoice-03.15.2025"),
            ("Company.With.Dots", "companywithdots-invoice-03.15.2025"),
        ]
        
        for company_name, expected_base in test_cases:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create template file
                template_path = os.path.join(temp_dir, "invoice_template.html")
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(mock_template_html)
                
                # Update sample data
                test_data = sample_invoice_data.copy()
                test_data["client"]["name"] = company_name
                
                with patch('os.getcwd', return_value=temp_dir):
                    with patch('builtins.print'):
                        generate_invoice_files(test_data, temp_dir)
                
                # Check normalized filename
                expected_html = os.path.join(temp_dir, f"{expected_base}.html")
                expected_pdf = os.path.join(temp_dir, f"{expected_base}.pdf")
                
                assert os.path.exists(expected_html), f"Expected HTML file {expected_html} for company '{company_name}'"
                assert os.path.exists(expected_pdf), f"Expected PDF file {expected_pdf} for company '{company_name}'"

    def test_generate_files_different_output_directory(self, sample_invoice_data, mock_template_html):
        """Test file generation with different output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create template file in current directory
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            # Create separate output directory
            output_dir = os.path.join(temp_dir, "output")
            os.makedirs(output_dir)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print'):
                    generate_invoice_files(sample_invoice_data, output_dir)
            
            # Check that files were created in output directory
            expected_html = os.path.join(output_dir, "acme-corporation-invoice-03.15.2025.html")
            expected_pdf = os.path.join(output_dir, "acme-corporation-invoice-03.15.2025.pdf")
            
            assert os.path.exists(expected_html)
            assert os.path.exists(expected_pdf)

    def test_generate_files_with_multiple_items(self, sample_invoice_data, mock_template_html):
        """Test file generation with multiple invoice items."""
        # Add more items to the sample data
        sample_invoice_data["items"] = [
            {
                "date": date(2025, 3, 15),
                "description": "Web Development",
                "quantity": 8.0,
                "rate": 150.0,
                "amount": 1200.0
            },
            {
                "date": date(2025, 3, 16),
                "description": "Bug Fixes",
                "quantity": 2.0,
                "rate": 150.0,
                "amount": 300.0
            }
        ]
        sample_invoice_data["total"] = 1500.0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print'):
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            expected_html = os.path.join(temp_dir, "acme-corporation-invoice-03.15.2025.html")
            
            # Check HTML content includes all items
            with open(expected_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert "Web Development" in html_content
                assert "Bug Fixes" in html_content
                assert "$1500.00" in html_content

    def test_generate_files_with_zero_total(self, sample_invoice_data, mock_template_html):
        """Test file generation with zero total amount."""
        sample_invoice_data["total"] = 0.0
        sample_invoice_data["items"] = [
            {
                "date": date(2025, 3, 15),
                "description": "Free Consultation",
                "quantity": 1.0,
                "rate": 0.0,
                "amount": 0.0
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print') as mock_print:
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            # Check print output shows zero total
            print_args = mock_print.call_args[0][0]
            assert "Total: $0.00" in print_args

    def test_generate_files_with_decimal_amounts(self, sample_invoice_data, mock_template_html):
        """Test file generation with decimal amounts."""
        sample_invoice_data["total"] = 1234.56
        sample_invoice_data["items"] = [
            {
                "date": date(2025, 3, 15),
                "description": "Partial Work",
                "quantity": 2.5,
                "rate": 175.75,
                "amount": 439.375
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print') as mock_print:
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            # Check print output formats decimal correctly
            print_args = mock_print.call_args[0][0]
            assert "Total: $1234.56" in print_args

    def test_generate_files_missing_template(self, sample_invoice_data):
        """Test file generation when template file is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Don't create template file - this will use FileSystemLoader(".")
            # which will look for the template in the current directory
            # Since we're not mocking getcwd, it will look in the actual project directory
            # where invoice_template.html exists, so this test will succeed
            # Let's change this to test a different template name
            with patch('generate_invoice.Environment') as mock_env:
                mock_loader = mock_env.return_value
                mock_loader.get_template.side_effect = Exception("Template not found")
                
                with pytest.raises(Exception, match="Template not found"):
                    generate_invoice_files(sample_invoice_data, temp_dir)

    def test_generate_files_invalid_output_directory(self, sample_invoice_data, mock_template_html):
        """Test file generation with invalid output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            # Try to write to non-existent directory
            invalid_output_dir = "/non/existent/path"
            
            with patch('os.getcwd', return_value=temp_dir):
                with pytest.raises(Exception):  # Should raise file system error
                    generate_invoice_files(sample_invoice_data, invalid_output_dir)

    def test_generate_files_special_characters_in_client_name(self, sample_invoice_data, mock_template_html):
        """Test file generation with special characters in client name."""
        sample_invoice_data["client"]["name"] = "Üñícödé Çørpørätîøñ & Co."
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print'):
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            # Should create files with normalized names
            files = os.listdir(temp_dir)
            html_files = [f for f in files if f.endswith('.html') and 'invoice' in f and f != 'invoice_template.html']
            pdf_files = [f for f in files if f.endswith('.pdf') and 'invoice' in f]
            
            assert len(html_files) == 1
            assert len(pdf_files) == 1
            
            # Check that files contain the Unicode characters correctly
            html_file = os.path.join(temp_dir, html_files[0])
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Üñícödé Çørpørätîøñ & Co." in content

    def test_generate_files_empty_items_list(self, sample_invoice_data, mock_template_html):
        """Test file generation with empty items list."""
        sample_invoice_data["items"] = []
        sample_invoice_data["total"] = 0.0
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = os.path.join(temp_dir, "invoice_template.html")
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(mock_template_html)
            
            with patch('os.getcwd', return_value=temp_dir):
                with patch('builtins.print'):
                    generate_invoice_files(sample_invoice_data, temp_dir)
            
            expected_html = os.path.join(temp_dir, "acme-corporation-invoice-03.15.2025.html")
            assert os.path.exists(expected_html)
            
            # Check HTML content handles empty items
            with open(expected_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
                assert "Invoice 2025.03.15" in html_content
                assert "Acme Corporation" in html_content

    def test_generate_files_date_format_variations(self, sample_invoice_data, mock_template_html):
        """Test file generation with different date formats."""
        date_formats = [
            ("03/15/2025", "03.15.2025"),
            ("12/31/2025", "12.31.2025"),
            ("01/01/2025", "01.01.2025"),
            ("5/5/2025", "5.5.2025"),
        ]
        
        for input_date, expected_date in date_formats:
            with tempfile.TemporaryDirectory() as temp_dir:
                template_path = os.path.join(temp_dir, "invoice_template.html")
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(mock_template_html)
                
                test_data = sample_invoice_data.copy()
                test_data["invoice_date"] = input_date
                
                with patch('os.getcwd', return_value=temp_dir):
                    with patch('builtins.print'):
                        generate_invoice_files(test_data, temp_dir)
                
                expected_html = os.path.join(temp_dir, f"acme-corporation-invoice-{expected_date}.html")
                assert os.path.exists(expected_html), f"Expected file for date {input_date}"