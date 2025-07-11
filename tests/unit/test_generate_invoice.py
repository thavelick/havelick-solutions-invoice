"""Unit tests for generate_invoice.py functions."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, mock_open

from generate_invoice import (
    _parse_invoice_line,
    parse_invoice_data,
    load_client_data,
    load_invoice_items,
    generate_invoice_metadata,
    generate_invoice_files,
)

pytestmark = pytest.mark.unit


class TestParseInvoiceLine:
    """Test _parse_invoice_line function."""

    def test_valid_line(self):
        """Test parsing a valid invoice line."""
        line = "3/15/2025\t2.5\t250.00\tSoftware development work"
        result = _parse_invoice_line(line)
        
        assert result is not None
        assert result["date"] == "03/15/2025"
        assert result["quantity"] == 2.5
        assert result["rate"] == 100.0  # 250/2.5
        assert result["description"] == "Software development work"

    def test_valid_line_single_digit_date(self):
        """Test parsing line with single digit month/day."""
        line = "1/5/2025\t1\t50\tTesting work"
        result = _parse_invoice_line(line)
        
        assert result["date"] == "01/05/2025"
        assert result["quantity"] == 1.0
        assert result["rate"] == 50.0

    def test_valid_line_with_currency_symbol(self):
        """Test parsing line with currency symbol in amount."""
        line = "3/15/2025\t1\t$100.50\tConsulting"
        result = _parse_invoice_line(line)
        
        assert result["rate"] == 100.50

    def test_invalid_line_not_enough_parts(self):
        """Test parsing line with insufficient parts."""
        line = "3/15/2025\t2.5\t250.00"  # Missing description
        result = _parse_invoice_line(line)
        
        assert result is None

    def test_invalid_quantity(self):
        """Test parsing line with invalid quantity."""
        line = "3/15/2025\tinvalid\t250.00\tWork"
        
        with pytest.raises(ValueError, match="Invalid quantity"):
            _parse_invoice_line(line)

    def test_negative_quantity(self):
        """Test parsing line with negative quantity."""
        line = "3/15/2025\t-1\t250.00\tWork"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_zero_quantity(self):
        """Test parsing line with zero quantity."""
        line = "3/15/2025\t0\t250.00\tWork"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_invalid_amount(self):
        """Test parsing line with invalid amount."""
        line = "3/15/2025\t1\tinvalid\tWork"
        
        with pytest.raises(ValueError, match="Invalid amount"):
            _parse_invoice_line(line)

    def test_invalid_date(self):
        """Test parsing line with invalid date."""
        line = "invalid-date\t1\t100\tWork"
        
        with pytest.raises(ValueError, match="Invalid date"):
            _parse_invoice_line(line)

    def test_date_format_validation(self):
        """Test various date format validations."""
        # Valid formats should work
        valid_line = "12/31/2025\t1\t100\tWork"
        result = _parse_invoice_line(valid_line)
        assert result["date"] == "12/31/2025"
        
        # Invalid formats should fail
        invalid_formats = [
            "2025-12-31\t1\t100\tWork",  # Wrong format
            "31/12/2025\t1\t100\tWork",  # Wrong order
            "13/01/2025\t1\t100\tWork",  # Invalid month
            "01/32/2025\t1\t100\tWork",  # Invalid day
        ]
        
        for line in invalid_formats:
            with pytest.raises(ValueError):
                _parse_invoice_line(line)


class TestParseInvoiceData:
    """Test parse_invoice_data function."""

    def test_valid_file(self):
        """Test parsing a valid invoice data file."""
        content = """Date\tHours\tAmount\tDescription
3/15/2025\t2.5\t250.00\tSoftware development
3/16/2025\t1.0\t100.00\tTesting"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filename = f.name
        
        try:
            items = parse_invoice_data(filename)
            
            assert len(items) == 2
            assert items[0]["description"] == "Software development"
            assert items[1]["description"] == "Testing"
        finally:
            os.unlink(filename)

    def test_file_without_header(self):
        """Test parsing file without header row."""
        content = """3/15/2025\t2.5\t250.00\tSoftware development
3/16/2025\t1.0\t100.00\tTesting"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filename = f.name
        
        try:
            items = parse_invoice_data(filename)
            
            assert len(items) == 2
            assert items[0]["description"] == "Software development"
        finally:
            os.unlink(filename)

    def test_file_with_empty_lines(self):
        """Test parsing file with empty lines."""
        content = """3/15/2025\t2.5\t250.00\tSoftware development

3/16/2025\t1.0\t100.00\tTesting
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filename = f.name
        
        try:
            items = parse_invoice_data(filename)
            
            assert len(items) == 2  # Empty lines should be ignored
        finally:
            os.unlink(filename)

    def test_nonexistent_file(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError, match="Invoice data file not found"):
            parse_invoice_data("nonexistent.txt")

    def test_empty_file(self):
        """Test parsing empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("")
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="No valid invoice items found"):
                parse_invoice_data(filename)
        finally:
            os.unlink(filename)

    def test_file_with_invalid_line(self):
        """Test parsing file with invalid line."""
        content = """3/15/2025\t2.5\t250.00\tSoftware development
invalid-line
3/16/2025\t1.0\t100.00\tTesting"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="Error parsing line"):
                parse_invoice_data(filename)
        finally:
            os.unlink(filename)


class TestLoadClientData:
    """Test load_client_data function."""

    def test_valid_client_file(self):
        """Test loading valid client data."""
        data = {
            "client": {
                "name": "Test Company",
                "address": "123 Test St\nTest City, ST 12345"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filename = f.name
        
        try:
            result = load_client_data(filename)
            
            assert result["client"]["name"] == "Test Company"
            assert "123 Test St" in result["client"]["address"]
        finally:
            os.unlink(filename)

    def test_nonexistent_file(self):
        """Test loading non-existent client file."""
        with pytest.raises(FileNotFoundError, match="Client file not found"):
            load_client_data("nonexistent.json")

    def test_invalid_json(self):
        """Test loading file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_client_data(filename)
        finally:
            os.unlink(filename)

    def test_missing_client_field(self):
        """Test loading file missing client field."""
        data = {"other": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="Client data missing 'client' field"):
                load_client_data(filename)
        finally:
            os.unlink(filename)

    def test_missing_client_name(self):
        """Test loading file with missing client name."""
        data = {
            "client": {
                "address": "123 Test St"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="Client name is required"):
                load_client_data(filename)
        finally:
            os.unlink(filename)

    def test_missing_client_address(self):
        """Test loading file with missing client address."""
        data = {
            "client": {
                "name": "Test Company"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            filename = f.name
        
        try:
            with pytest.raises(ValueError, match="Client address is required"):
                load_client_data(filename)
        finally:
            os.unlink(filename)


class TestLoadInvoiceItems:
    """Test load_invoice_items function."""

    def test_valid_items(self):
        """Test loading valid invoice items."""
        content = "3/15/2025\t2.5\t250.00\tSoftware development"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            filename = f.name
        
        try:
            items = load_invoice_items(filename)
            
            assert len(items) == 1
            assert items[0]["description"] == "Software development"
        finally:
            os.unlink(filename)

    def test_file_error(self):
        """Test handling file errors."""
        with pytest.raises(ValueError, match="Error loading invoice items"):
            load_invoice_items("nonexistent.txt")


class TestGenerateInvoiceMetadata:
    """Test generate_invoice_metadata function."""

    def test_valid_filename(self):
        """Test generating metadata from valid filename."""
        result = generate_invoice_metadata("invoice-data-3-31.txt")
        
        assert result["invoice_number"] == "2025.03.31"
        assert result["invoice_date"] == "03/31/2025"
        assert result["due_date"] == "04/30/2025"

    def test_invalid_filename(self):
        """Test handling invalid filename."""
        with pytest.raises(ValueError, match="Error generating invoice metadata"):
            generate_invoice_metadata("invalid-file.txt")


class TestGenerateInvoiceFiles:
    """Test generate_invoice_files function."""

    @patch('generate_invoice.Environment')
    @patch('generate_invoice.HTML')
    @patch('builtins.open', new_callable=mock_open)
    def test_generate_files(self, mock_file, mock_html, mock_env):
        """Test generating invoice files."""
        # Setup mocks
        mock_template = mock_env.return_value.get_template.return_value
        mock_template.render.return_value = "<html>Invoice</html>"
        
        data = {
            "client": {"name": "Test Company"},
            "invoice_date": "03/31/2025",
            "total": 100.0
        }
        
        # Call function
        generate_invoice_files(data, "/tmp")
        
        # Verify template was rendered
        mock_template.render.assert_called_once_with(**data)
        
        # Verify HTML file was written
        mock_file.assert_called()
        
        # Verify PDF generation was attempted
        mock_html.assert_called()

    def test_filename_generation(self):
        """Test that filenames are generated correctly."""
        data = {
            "client": {"name": "Test Company, Inc."},
            "invoice_date": "03/31/2025",
            "total": 100.0
        }
        
        with patch('generate_invoice.Environment') as mock_env, \
             patch('generate_invoice.HTML') as mock_html, \
             patch('builtins.open', new_callable=mock_open) as mock_file:
            
            mock_template = mock_env.return_value.get_template.return_value
            mock_template.render.return_value = "<html>Invoice</html>"
            
            generate_invoice_files(data, "/tmp")
            
            # Check that the file was opened with the correct filename
            # Company name should be cleaned: "Test Company, Inc." -> "test-company-inc"
            # Date should be cleaned: "03/31/2025" -> "03.31.2025"
            expected_base = "test-company-inc-invoice-03.31.2025"
            
            calls = mock_file.call_args_list
            html_call = calls[0][0][0]  # First call, first argument
            
            assert expected_base in html_call
            assert html_call.endswith('.html')