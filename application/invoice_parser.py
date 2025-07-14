"""Invoice data parsing utilities."""

import os

from .models import parse_date_to_display, validate_amount


def _parse_invoice_line(line):
    """Parse a single invoice data line."""
    parts = line.split("\t")
    if len(parts) < 4:
        return None

    try:
        date_str = parts[0].strip()
        quantity_str = parts[1].strip()
        amount_str = parts[2].strip()
        description = parts[3].strip()

        # Validate and parse quantity
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError(f"Quantity must be positive: {quantity}")
        except ValueError as e:
            raise ValueError(f"Invalid quantity '{quantity_str}': {e}") from e

        # Validate and parse amount
        try:
            amount = validate_amount(amount_str)
        except ValueError as e:
            raise ValueError(f"Invalid amount '{amount_str}': {e}") from e

        # Calculate rate from amount and quantity
        rate = amount / quantity if quantity > 0 else 0

        # Parse and normalize date format
        try:
            # Handle both M/D/YYYY and MM/DD/YYYY formats
            if "/" in date_str:
                # Try parsing as is first
                try:
                    formatted_date = parse_date_to_display(date_str, "%m/%d/%Y")
                except ValueError:
                    # Try parsing with single digit month/day
                    month, day, year = date_str.split("/")
                    formatted_date = f"{month.zfill(2)}/{day.zfill(2)}/{year}"
                    # Validate the formatted date
                    parse_date_to_display(formatted_date, "%m/%d/%Y")
            else:
                raise ValueError(f"Invalid date format: {date_str}")
        except ValueError as e:
            raise ValueError(f"Invalid date '{date_str}': {e}") from e

        return {
            "date": formatted_date,
            "description": description,
            "quantity": quantity,
            "rate": rate,
        }
    except ValueError as e:
        raise ValueError(f"Error parsing invoice line '{line.strip()}': {e}") from e


def parse_invoice_data(filename):
    """Parse tab-separated invoice data file"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Invoice data file not found: {filename}")

    items = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Skip header row if it exists
            start_index = (
                1 if lines and "Date" in lines[0] and "Hours" in lines[0] else 0
            )

            for line_num, line in enumerate(lines[start_index:], start=start_index + 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    item = _parse_invoice_line(line)
                    if item:
                        items.append(item)
                except ValueError as e:
                    raise ValueError(f"Error parsing line {line_num}: {e}") from e
    except IOError as e:
        raise IOError(f"Error reading file {filename}: {e}") from e

    if not items:
        raise ValueError(f"No valid invoice items found in {filename}")

    return items
