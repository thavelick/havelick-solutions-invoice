"""Unit tests for invoice parsing functions."""

import pytest
from unittest.mock import patch, mock_open

from generate_invoice import _parse_invoice_line, parse_invoice_data


class TestParseInvoiceLine:
    """Test cases for _parse_invoice_line function."""

    def test_parse_valid_line_with_padded_date(self):
        """Test parsing a valid line with zero-padded date."""
        line = "03/15/2025\t8.0\t150.00\tSoftware development work"
        result = _parse_invoice_line(line)
        
        assert result == {
            "date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 18.75,  # 150.00 / 8.0
        }

    def test_parse_valid_line_with_single_digit_date(self):
        """Test parsing a valid line with single digit month/day."""
        line = "3/5/2025\t4.0\t200.00\tConsulting services"
        result = _parse_invoice_line(line)
        
        assert result == {
            "date": "03/05/2025",
            "description": "Consulting services", 
            "quantity": 4.0,
            "rate": 50.0,  # 200.00 / 4.0
        }

    def test_parse_line_with_insufficient_fields(self):
        """Test parsing a line with insufficient tab-separated fields."""
        line = "03/15/2025\t8.0\t150.00"  # Missing description
        result = _parse_invoice_line(line)
        
        assert result is None

    def test_parse_line_with_invalid_quantity(self):
        """Test parsing a line with invalid quantity."""
        line = "03/15/2025\tinvalid\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid quantity 'invalid'"):
            _parse_invoice_line(line)

    def test_parse_line_with_negative_quantity(self):
        """Test parsing a line with negative quantity."""
        line = "03/15/2025\t-2.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_parse_line_with_zero_quantity(self):
        """Test parsing a line with zero quantity."""
        line = "03/15/2025\t0.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_parse_line_with_invalid_date_format(self):
        """Test parsing a line with invalid date format."""
        line = "2025-03-15\t8.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid date format"):
            _parse_invoice_line(line)

    def test_parse_line_with_invalid_date(self):
        """Test parsing a line with invalid date."""
        line = "13/45/2025\t8.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid date"):
            _parse_invoice_line(line)


class TestParseInvoiceData:
    """Test cases for parse_invoice_data function."""

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Invoice data file not found"):
            parse_invoice_data("nonexistent_file.txt")

    @patch("builtins.open", new_callable=mock_open, read_data="03/15/2025\t8.0\t150.00\tSoftware development work\n")
    @patch("os.path.exists", return_value=True)
    def test_parse_valid_file(self, mock_exists, mock_file):
        """Test parsing a valid invoice data file."""
        result = parse_invoice_data("test_file.txt")
        
        assert len(result) == 1
        assert result[0]["date"] == "03/15/2025"
        assert result[0]["description"] == "Software development work"
        assert result[0]["quantity"] == 8.0
        assert result[0]["rate"] == 18.75

    @patch("builtins.open", new_callable=mock_open, read_data="03/15/2025\t8.0\t150.00\tWork 1\n03/16/2025\t4.0\t200.00\tWork 2\n")
    @patch("os.path.exists", return_value=True)
    def test_parse_multiple_lines(self, mock_exists, mock_file):
        """Test parsing a file with multiple lines."""
        result = parse_invoice_data("test_file.txt")
        
        assert len(result) == 2
        assert result[0]["description"] == "Work 1"
        assert result[1]["description"] == "Work 2"

    @patch("builtins.open", new_callable=mock_open, read_data="03/15/2025\t8.0\t150.00\tValid work\n\n# Comment line\n")
    @patch("os.path.exists", return_value=True)
    def test_parse_file_with_empty_lines_and_comments(self, mock_exists, mock_file):
        """Test parsing a file with empty lines and comments."""
        result = parse_invoice_data("test_file.txt")
        
        assert len(result) == 1
        assert result[0]["description"] == "Valid work"