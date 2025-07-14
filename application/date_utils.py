"""Date parsing and formatting utilities."""

from datetime import datetime, timedelta


def parse_date_safely(date_str: str, date_format: str = "%m/%d/%Y") -> str:
    """Parse date string with validation and convert to YYYY-MM-DD format."""
    try:
        parsed = datetime.strptime(date_str, date_format)
        return parsed.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: {date_format}"
        ) from e


def parse_date_to_display(date_str: str, date_format: str = "%m/%d/%Y") -> str:
    """Parse date string and convert to MM/DD/YYYY format for display."""
    try:
        parsed = datetime.strptime(date_str, date_format)
        return parsed.strftime("%m/%d/%Y")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: {date_format}"
        ) from e


def calculate_due_date(invoice_date_str: str, days_out: int = 30) -> str:
    """Calculate due date by adding specified days to invoice date."""
    try:
        invoice_date = datetime.strptime(invoice_date_str, "%m/%d/%Y")
        due_date = invoice_date + timedelta(days=days_out)
        return due_date.strftime("%m/%d/%Y")
    except ValueError as e:
        raise ValueError(f"Invalid invoice date: {invoice_date_str}") from e
