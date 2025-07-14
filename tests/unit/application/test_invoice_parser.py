"""Unit tests for invoice parser functions."""

import pytest

from application.invoice_parser import _parse_invoice_line, parse_invoice_data


class TestParseInvoiceLine:
    """Test cases for _parse_invoice_line function."""

    def test_parse_valid_lines(self):
        """Test parsing valid invoice lines."""
        line = "03/15/2025\t8.0\t150.00\tSoftware development work"
        result = _parse_invoice_line(line)

        assert result == {
            "date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 18.75,  # 150.00 / 8.0
        }

        line = "3/5/2025\t4.0\t200.00\tConsulting services"
        result = _parse_invoice_line(line)

        assert result == {
            "date": "03/05/2025",  # Zero-padded
            "description": "Consulting services",
            "quantity": 4.0,
            "rate": 50.0,
        }

    def test_parse_line_insufficient_fields(self):
        """Test parsing lines with insufficient fields."""
        line = "03/15/2025\t8.0\t150.00"  # Missing description
        result = _parse_invoice_line(line)
        assert result is None

    def test_parse_line_invalid_quantity(self):
        """Test parsing lines with invalid quantity."""
        line = "03/15/2025\tinvalid\t150.00\tDescription"
        with pytest.raises(ValueError, match="Invalid quantity"):
            _parse_invoice_line(line)

    def test_parse_line_invalid_quantity_values(self):
        """Test parsing lines with invalid quantity values."""
        # Test negative quantity
        line = "03/15/2025\t-5.0\t150.00\tDescription"
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

        # Test zero quantity
        line = "03/15/2025\t0\t150.00\tDescription"
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_parse_line_invalid_date(self):
        """Test parsing lines with invalid date formats."""
        # Test completely invalid date
        line = "invalid-date\t8.0\t150.00\tDescription"
        with pytest.raises(ValueError, match="Invalid date"):
            _parse_invoice_line(line)

        # Test invalid month
        line = "13/15/2025\t8.0\t150.00\tDescription"
        with pytest.raises(ValueError, match="Invalid date"):
            _parse_invoice_line(line)

        # Test missing slashes
        line = "03152025\t8.0\t150.00\tDescription"
        with pytest.raises(ValueError, match="Invalid date format"):
            _parse_invoice_line(line)


class TestParseInvoiceData:
    """Test cases for parse_invoice_data function."""

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Invoice data file not found"):
            parse_invoice_data("nonexistent_file.txt")

    def test_parse_valid_file(self, tmp_path):
        """Test parsing a valid invoice data file."""
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text("03/15/2025\t8.0\t150.00\tSoftware development work\n")

        result = parse_invoice_data(str(test_file))

        assert len(result) == 1
        assert result[0]["date"] == "03/15/2025"
        assert result[0]["quantity"] == 8.0
        assert result[0]["rate"] == 18.75

    def test_parse_multiple_lines(self, tmp_path):
        """Test parsing a file with multiple invoice lines."""
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text(
            "03/15/2025\t8.0\t150.00\tSoftware development\n"
            "03/16/2025\t4.0\t200.00\tConsulting\n"
        )

        result = parse_invoice_data(str(test_file))

        assert len(result) == 2
        assert result[0]["description"] == "Software development"
        assert result[1]["description"] == "Consulting"

    def test_parse_file_with_empty_lines(self, tmp_path):
        """Test parsing a file with empty lines (should be skipped)."""
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text(
            "03/15/2025\t8.0\t150.00\tSoftware development\n"
            "\n"  # Empty line
            "03/16/2025\t4.0\t200.00\tConsulting\n"
            "   \n"  # Whitespace only
        )

        result = parse_invoice_data(str(test_file))

        assert len(result) == 2
        assert result[0]["description"] == "Software development"
        assert result[1]["description"] == "Consulting"
