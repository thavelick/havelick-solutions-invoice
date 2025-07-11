"""Unit tests for utility functions in models."""

import pytest

from application.models import (
    validate_amount,
    parse_date_safely,
    parse_date_to_display,
    generate_invoice_metadata_from_filename,
    calculate_due_date,
)


class TestValidateAmount:
    """Test cases for validate_amount function."""

    def test_validate_basic_amounts(self):
        """Test validating basic numeric amounts."""
        assert validate_amount("150.00") == 150.0
        assert validate_amount("$150.00") == 150.0
        assert validate_amount("1,500.00") == 1500.0
        assert validate_amount("$1,500.00") == 1500.0
        assert validate_amount("  150.00  ") == 150.0
        assert validate_amount("150") == 150.0
        assert validate_amount("0.00") == 0.0

    def test_validate_amount_invalid_values(self):
        """Test validating invalid amount values."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("-150.00")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("invalid")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("")


class TestParseDateSafely:
    """Test cases for parse_date_safely function."""

    def test_parse_valid_dates(self):
        """Test parsing valid dates."""
        assert parse_date_safely("03/15/2025") == "2025-03-15"
        assert parse_date_safely("3/5/2025") == "2025-03-05"
        assert parse_date_safely("2025-03-15", "%Y-%m-%d") == "2025-03-15"

    def test_parse_invalid_dates(self):
        """Test parsing invalid dates."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("2025-03-15", "%m/%d/%Y")
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("13/45/2025")
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("")


class TestParseDateToDisplay:
    """Test cases for parse_date_to_display function."""

    def test_parse_date_to_display_formats(self):
        """Test parsing dates to display format."""
        assert parse_date_to_display("03/15/2025") == "03/15/2025"
        assert parse_date_to_display("3/5/2025") == "03/05/2025"
        assert parse_date_to_display("2025-03-15", "%Y-%m-%d") == "03/15/2025"

    def test_parse_date_to_display_invalid(self):
        """Test parsing invalid dates to display format."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("2025-03-15", "%m/%d/%Y")
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("13/45/2025")


class TestGenerateInvoiceMetadataFromFilename:
    """Test cases for generate_invoice_metadata_from_filename function."""

    def test_generate_metadata_valid_filenames(self):
        """Test generating metadata from valid filenames."""
        result = generate_invoice_metadata_from_filename("invoice-data-3-15.txt")
        assert result["invoice_number"] == "2025.03.15"
        assert result["invoice_date"] == "03/15/2025"
        assert result["due_date"] == "04/14/2025"  # 30 days after 03/15/2025

        result = generate_invoice_metadata_from_filename("invoice-data-12-31.txt")
        assert result["invoice_number"] == "2025.12.31"
        assert result["invoice_date"] == "12/31/2025"
        assert result["due_date"] == "01/30/2026"  # 30 days after 12/31/2025

    def test_generate_metadata_invalid_filename(self):
        """Test generating metadata from invalid filename."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-invalid.txt")

    def test_generate_metadata_fallback_filename(self):
        """Test generating metadata from non-standard filename."""
        result = generate_invoice_metadata_from_filename("some-other-file.txt")
        
        # Should contain all required keys
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result
        
        # Should be in correct format
        assert result["invoice_number"].startswith("2025.")
        assert "/" in result["invoice_date"]
        assert "/" in result["due_date"]


class TestCalculateDueDate:
    """Test cases for calculate_due_date function."""

    def test_calculate_due_date_basic(self):
        """Test calculating due date with basic cases."""
        assert calculate_due_date("03/15/2025") == "04/14/2025"
        assert calculate_due_date("03/15/2025", 15) == "03/30/2025"
        assert calculate_due_date("03/15/2025", 0) == "03/15/2025"
        assert calculate_due_date("01/15/2025", 30) == "02/14/2025"

    def test_calculate_due_date_year_boundary(self):
        """Test calculating due date across year boundary."""
        assert calculate_due_date("12/15/2025", 30) == "01/14/2026"

    def test_calculate_due_date_leap_year(self):
        """Test calculating due date in leap year."""
        assert calculate_due_date("02/15/2024", 30) == "03/16/2024"  # 2024 is a leap year

    def test_calculate_due_date_invalid_date(self):
        """Test calculating due date with invalid date."""
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("2025-03-15")
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("13/45/2025")
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("")