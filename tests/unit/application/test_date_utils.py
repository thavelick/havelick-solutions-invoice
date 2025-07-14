"""Unit tests for date utility functions."""

import pytest

from application.date_utils import (
    calculate_due_date,
    parse_date_safely,
    parse_date_to_display,
)


class TestParseDateSafely:
    """Test cases for parse_date_safely function."""

    def test_parse_valid_dates(self):
        """Test parsing valid date strings."""
        assert parse_date_safely("03/15/2025") == "2025-03-15"
        assert parse_date_safely("12/31/2024") == "2024-12-31"
        assert parse_date_safely("01/01/2023") == "2023-01-01"

    def test_parse_invalid_dates(self):
        """Test parsing invalid date strings."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("13/45/2025")
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("2025-03-15")
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_safely("invalid")


class TestParseDateToDisplay:
    """Test cases for parse_date_to_display function."""

    def test_parse_date_to_display_formats(self):
        """Test converting dates to display format."""
        assert parse_date_to_display("03/15/2025") == "03/15/2025"
        assert parse_date_to_display("12/31/2024") == "12/31/2024"

    def test_parse_date_to_display_invalid(self):
        """Test parsing invalid dates for display."""
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_to_display("13/45/2025")


class TestCalculateDueDate:
    """Test cases for calculate_due_date function."""

    def test_calculate_due_date_basic(self):
        """Test calculating due date with basic scenarios."""
        assert calculate_due_date("03/15/2025", 30) == "04/14/2025"
        assert calculate_due_date("01/01/2025", 30) == "01/31/2025"

    def test_calculate_due_date_year_boundary(self):
        """Test calculating due date across year boundary."""
        assert calculate_due_date("12/31/2025", 30) == "01/30/2026"

    def test_calculate_due_date_leap_year(self):
        """Test calculating due date in leap year."""
        assert (
            calculate_due_date("02/15/2024", 30) == "03/16/2024"
        )  # 2024 is a leap year

    def test_calculate_due_date_invalid_date(self):
        """Test calculating due date with invalid date."""
        with pytest.raises(ValueError, match="Invalid invoice date"):
            calculate_due_date("2025-03-15")
        with pytest.raises(ValueError, match="Invalid invoice date"):
            calculate_due_date("13/45/2025")
        with pytest.raises(ValueError, match="Invalid invoice date"):
            calculate_due_date("")
