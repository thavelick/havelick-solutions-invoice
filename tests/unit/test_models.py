"""Unit tests for application models functions."""

import pytest

from application.models import validate_amount, parse_date_safely, parse_date_to_display, generate_invoice_metadata_from_filename, calculate_due_date, Vendor, Customer, Invoice, InvoiceItem


class TestValidateAmount:
    """Test cases for validate_amount function."""

    def test_validate_simple_amount(self):
        """Test validating a simple numeric amount."""
        result = validate_amount("150.00")
        assert result == 150.0

    def test_validate_amount_with_dollar_sign(self):
        """Test validating amount with dollar sign."""
        result = validate_amount("$150.00")
        assert result == 150.0

    def test_validate_amount_with_commas(self):
        """Test validating amount with comma separators."""
        result = validate_amount("1,500.00")
        assert result == 1500.0

    def test_validate_amount_with_dollar_and_commas(self):
        """Test validating amount with both dollar sign and commas."""
        result = validate_amount("$1,500.00")
        assert result == 1500.0

    def test_validate_amount_with_whitespace(self):
        """Test validating amount with leading/trailing whitespace."""
        result = validate_amount("  150.00  ")
        assert result == 150.0

    def test_validate_integer_amount(self):
        """Test validating integer amount."""
        result = validate_amount("150")
        assert result == 150.0

    def test_validate_zero_amount(self):
        """Test validating zero amount."""
        result = validate_amount("0.00")
        assert result == 0.0

    def test_validate_negative_amount(self):
        """Test validating negative amount should raise error."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("-150.00")

    def test_validate_invalid_text(self):
        """Test validating non-numeric text should raise error."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("invalid")

    def test_validate_empty_string(self):
        """Test validating empty string should raise error."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("")

    def test_validate_multiple_decimal_points(self):
        """Test validating amount with multiple decimal points should raise error."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("150.00.00")

    def test_validate_complex_formatting(self):
        """Test validating complex formatted amount."""
        result = validate_amount("$12,345.67")
        assert result == 12345.67


class TestParseDateSafely:
    """Test cases for parse_date_safely function."""

    def test_parse_valid_date(self):
        """Test parsing valid date in MM/DD/YYYY format."""
        result = parse_date_safely("03/15/2025")
        assert result == "2025-03-15"

    def test_parse_date_single_digits(self):
        """Test parsing date with single digit month and day."""
        result = parse_date_safely("3/5/2025")
        assert result == "2025-03-05"

    def test_parse_date_different_format(self):
        """Test parsing date with different input format."""
        result = parse_date_safely("2025-03-15", "%Y-%m-%d")
        assert result == "2025-03-15"

    def test_parse_date_invalid_format(self):
        """Test parsing date with invalid format should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("2025-03-15", "%m/%d/%Y")

    def test_parse_date_invalid_date(self):
        """Test parsing invalid date should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("13/45/2025")

    def test_parse_date_empty_string(self):
        """Test parsing empty string should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("")

    def test_parse_date_non_date_string(self):
        """Test parsing non-date string should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("not a date")


class TestParseDateToDisplay:
    """Test cases for parse_date_to_display function."""

    def test_parse_valid_date_to_display(self):
        """Test parsing valid date to display format."""
        result = parse_date_to_display("03/15/2025")
        assert result == "03/15/2025"

    def test_parse_date_single_digits_to_display(self):
        """Test parsing date with single digits to display format."""
        result = parse_date_to_display("3/5/2025")
        assert result == "03/05/2025"

    def test_parse_date_different_input_format_to_display(self):
        """Test parsing date from different format to display format."""
        result = parse_date_to_display("2025-03-15", "%Y-%m-%d")
        assert result == "03/15/2025"

    def test_parse_date_invalid_format_to_display(self):
        """Test parsing date with invalid format should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("2025-03-15", "%m/%d/%Y")

    def test_parse_date_invalid_date_to_display(self):
        """Test parsing invalid date should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("13/45/2025")

    def test_parse_date_empty_string_to_display(self):
        """Test parsing empty string should raise error."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("")


class TestGenerateInvoiceMetadataFromFilename:
    """Test cases for generate_invoice_metadata_from_filename function."""

    def test_generate_metadata_valid_filename(self):
        """Test generating metadata from valid filename."""
        result = generate_invoice_metadata_from_filename("invoice-data-3-15.txt")
        
        assert result["invoice_number"] == "2025.03.15"
        assert result["invoice_date"] == "03/15/2025"
        assert result["due_date"] == "04/14/2025"  # 30 days after 03/15/2025

    def test_generate_metadata_single_digit_numbers(self):
        """Test generating metadata with single digit month and day."""
        result = generate_invoice_metadata_from_filename("invoice-data-5-1.txt")
        
        assert result["invoice_number"] == "2025.05.01"
        assert result["invoice_date"] == "05/01/2025"
        assert result["due_date"] == "05/31/2025"  # 30 days after 05/01/2025

    def test_generate_metadata_double_digit_numbers(self):
        """Test generating metadata with double digit month and day."""
        result = generate_invoice_metadata_from_filename("invoice-data-12-31.txt")
        
        assert result["invoice_number"] == "2025.12.31"
        assert result["invoice_date"] == "12/31/2025"
        assert result["due_date"] == "01/30/2026"  # 30 days after 12/31/2025

    def test_generate_metadata_full_path(self):
        """Test generating metadata from full file path."""
        result = generate_invoice_metadata_from_filename("/path/to/invoice-data-6-15.txt")
        
        assert result["invoice_number"] == "2025.06.15"
        assert result["invoice_date"] == "06/15/2025"
        assert result["due_date"] == "07/15/2025"  # 30 days after 06/15/2025

    def test_generate_metadata_invalid_filename_format(self):
        """Test generating metadata from invalid filename format."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-invalid.txt")

    def test_generate_metadata_missing_day(self):
        """Test generating metadata from filename missing day."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-3.txt")

    def test_generate_metadata_too_many_parts(self):
        """Test generating metadata from filename with too many parts."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-3-15-extra.txt")

    def test_generate_metadata_non_numeric_month(self):
        """Test generating metadata with non-numeric month."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-march-15.txt")

    def test_generate_metadata_non_numeric_day(self):
        """Test generating metadata with non-numeric day."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            generate_invoice_metadata_from_filename("invoice-data-3-fifteen.txt")

    def test_generate_metadata_fallback_to_current_date(self):
        """Test generating metadata falls back to current date for non-standard filename."""
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

    def test_calculate_due_date_default_days(self):
        """Test calculating due date with default 30 days."""
        result = calculate_due_date("03/15/2025")
        assert result == "04/14/2025"

    def test_calculate_due_date_custom_days(self):
        """Test calculating due date with custom days."""
        result = calculate_due_date("03/15/2025", 15)
        assert result == "03/30/2025"

    def test_calculate_due_date_zero_days(self):
        """Test calculating due date with zero days."""
        result = calculate_due_date("03/15/2025", 0)
        assert result == "03/15/2025"

    def test_calculate_due_date_across_month_boundary(self):
        """Test calculating due date across month boundary."""
        result = calculate_due_date("01/15/2025", 30)
        assert result == "02/14/2025"

    def test_calculate_due_date_across_year_boundary(self):
        """Test calculating due date across year boundary."""
        result = calculate_due_date("12/15/2025", 30)
        assert result == "01/14/2026"

    def test_calculate_due_date_leap_year(self):
        """Test calculating due date in leap year."""
        result = calculate_due_date("02/15/2024", 30)  # 2024 is a leap year
        assert result == "03/16/2024"

    def test_calculate_due_date_february_non_leap_year(self):
        """Test calculating due date in February non-leap year."""
        result = calculate_due_date("02/15/2025", 30)  # 2025 is not a leap year
        assert result == "03/17/2025"

    def test_calculate_due_date_invalid_date_format(self):
        """Test calculating due date with invalid date format."""
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("2025-03-15")

    def test_calculate_due_date_invalid_date(self):
        """Test calculating due date with invalid date."""
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("13/45/2025")

    def test_calculate_due_date_empty_string(self):
        """Test calculating due date with empty string."""
        with pytest.raises(ValueError, match="Invalid invoice date format"):
            calculate_due_date("")

    def test_calculate_due_date_large_number_of_days(self):
        """Test calculating due date with large number of days."""
        result = calculate_due_date("01/01/2025", 365)
        assert result == "01/01/2026"