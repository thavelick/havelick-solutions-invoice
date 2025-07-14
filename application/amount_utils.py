"""Amount validation and parsing utilities."""


def validate_amount(amount: str) -> float:
    """Validate and convert amount string to float."""
    try:
        # Remove currency symbols and commas
        cleaned = amount.replace("$", "").replace(",", "").strip()
        value = float(cleaned)
        if value < 0:
            raise ValueError("Amount cannot be negative")
        return value
    except ValueError as e:
        raise ValueError(f"Invalid amount: {amount}") from e
