"""Unit tests for database utility functions."""

import pytest
from datetime import datetime

from database import (
    parse_date_safely,
    parse_date_to_display,
    validate_amount,
    calculate_due_date,
    generate_invoice_metadata_from_filename,
)

pytestmark = pytest.mark.unit


class TestParseDateSafely:
    """Test parse_date_safely function."""

    def test_valid_date_formats(self):
        """Test parsing valid date formats."""
        assert parse_date_safely("03/31/2025") == "2025-03-31"
        assert parse_date_safely("12/01/2024") == "2024-12-01"
        assert parse_date_safely("1/5/2023") == "2023-01-05"

    def test_invalid_date_formats(self):
        """Test parsing invalid date formats."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("2025-03-31")
        
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("31/03/2025")
        
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("invalid-date")

    def test_invalid_dates(self):
        """Test parsing invalid dates."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("13/31/2025")  # Invalid month
        
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("02/30/2025")  # Invalid day for February

    def test_custom_format(self):
        """Test parsing with custom format."""
        assert parse_date_safely("2025-03-31", "%Y-%m-%d") == "2025-03-31"
        assert parse_date_safely("31-03-2025", "%d-%m-%Y") == "2025-03-31"


class TestParseDateToDisplay:
    """Test parse_date_to_display function."""

    def test_valid_dates(self):
        """Test parsing valid dates for display."""
        assert parse_date_to_display("03/31/2025") == "03/31/2025"
        assert parse_date_to_display("1/5/2023") == "01/05/2023"
        assert parse_date_to_display("12/01/2024") == "12/01/2024"

    def test_invalid_dates(self):
        """Test parsing invalid dates."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("2025-03-31")
        
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("invalid-date")

    def test_custom_format(self):
        """Test parsing with custom format."""
        assert parse_date_to_display("2025-03-31", "%Y-%m-%d") == "03/31/2025"
        assert parse_date_to_display("31-03-2025", "%d-%m-%Y") == "03/31/2025"


class TestValidateAmount:
    """Test validate_amount function."""

    def test_valid_amounts(self):
        """Test validating valid amounts."""
        assert validate_amount("100") == 100.0
        assert validate_amount("100.50") == 100.50
        assert validate_amount("$100.50") == 100.50
        assert validate_amount("1,000.00") == 1000.0
        assert validate_amount("$1,234.56") == 1234.56
        assert validate_amount("0") == 0.0
        assert validate_amount("0.01") == 0.01

    def test_invalid_amounts(self):
        """Test validating invalid amounts."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("invalid")
        
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("")
        
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            validate_amount("-100")
        
        with pytest.raises(ValueError, match="Amount cannot be negative"):
            validate_amount("-0.01")

    def test_whitespace_handling(self):
        """Test handling whitespace in amounts."""
        assert validate_amount("  100.50  ") == 100.50
        assert validate_amount(" $1,000 ") == 1000.0


class TestCalculateDueDate:
    """Test calculate_due_date function."""

    def test_default_30_days(self):
        """Test default 30-day calculation."""
        assert calculate_due_date("01/01/2025") == "01/31/2025"
        assert calculate_due_date("01/31/2025") == "03/02/2025"  # February has 28 days in 2025

    def test_custom_days(self):
        """Test custom day calculations."""
        assert calculate_due_date("01/01/2025", 15) == "01/16/2025"
        assert calculate_due_date("01/01/2025", 60) == "03/02/2025"
        assert calculate_due_date("01/01/2025", 0) == "01/01/2025"

    def test_leap_year(self):
        """Test leap year calculations."""
        assert calculate_due_date("02/01/2024", 29) == "03/01/2024"  # 2024 is leap year
        assert calculate_due_date("02/01/2025", 28) == "03/01/2025"  # 2025 is not leap year

    def test_invalid_date(self):
        """Test invalid date input."""
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("invalid-date")
        
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("2025-01-01")


class TestGenerateInvoiceMetadataFromFilename:
    """Test generate_invoice_metadata_from_filename function."""

    def test_valid_invoice_data_filename(self):
        """Test generating metadata from valid invoice data filename."""
        result = generate_invoice_metadata_from_filename("invoice-data-3-31.txt")
        assert result["invoice_number"] == "2025.03.31"
        assert result["invoice_date"] == "03/31/2025"
        assert result["due_date"] == "04/30/2025"

    def test_valid_filename_single_digits(self):
        """Test generating metadata with single digit month/day."""
        result = generate_invoice_metadata_from_filename("invoice-data-1-5.txt")
        assert result["invoice_number"] == "2025.01.05"
        assert result["invoice_date"] == "01/05/2025"
        assert result["due_date"] == "02/04/2025"

    def test_invalid_filename_format(self):
        """Test invalid filename formats."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-invalid.txt")
        
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-.txt")

    def test_fallback_to_current_date(self):
        """Test fallback to current date for non-standard filenames."""
        result = generate_invoice_metadata_from_filename("random-file.txt")
        
        # Check that we get some valid metadata (format should be correct)
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result
        
        # Check format of invoice number (should be 2025.MM.DD)
        assert result["invoice_number"].startswith("2025.")
        assert len(result["invoice_number"].split(".")) == 3
        
        # Check date formats
        assert "/" in result["invoice_date"]
        assert "/" in result["due_date"]

    def test_filename_with_path(self):
        """Test filename with full path."""
        result = generate_invoice_metadata_from_filename("/path/to/invoice-data-6-15.txt")
        assert result["invoice_number"] == "2025.06.15"
        assert result["invoice_date"] == "06/15/2025"
        assert result["due_date"] == "07/15/2025"

    def test_invalid_date_in_filename(self):
        """Test invalid date in filename."""
        with pytest.raises(ValueError, match="Error generating invoice metadata"):
            generate_invoice_metadata_from_filename("invoice-data-13-32.txt")  # Invalid month/day