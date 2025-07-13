"""Shared test helpers to reduce redundancy across test files."""

import os
import tempfile
from typing import Any, Dict, Type

import pytest

from application.db import close_db, init_db


def check_from_dict_method(
    model_class: Type, valid_record: Dict[str, Any], required_fields: list
):
    """
    Generic test helper for from_dict() methods.

    Args:
        model_class: The model class to test
        valid_record: A valid record dictionary
        required_fields: List of required field names
    """
    # Test valid record
    instance = model_class.from_dict(valid_record)
    for field, value in valid_record.items():
        assert getattr(instance, field) == value

    # Test missing field
    for field in required_fields:
        incomplete_record = valid_record.copy()
        del incomplete_record[field]
        with pytest.raises(KeyError):
            model_class.from_dict(incomplete_record)

    # Test None values
    none_record: Dict[str, Any] = {field: None for field in valid_record.keys()}
    none_record["id"] = 1  # Keep ID as valid
    none_instance = model_class.from_dict(none_record)
    for field, value in none_record.items():
        assert getattr(none_instance, field) == value


# This is a helper function, not a test - remove the test_ prefix to prevent pytest from running it


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test.db")
        init_db(db_path)
        yield db_path
        close_db()


def create_test_customer(name: str = "Test Company", address: str = "123 Test St"):
    """Helper to create a test customer."""
    from application.models import Customer

    return Customer.create(name, address)


def create_test_invoice(
    customer_id: int, invoice_number: str = "2025.03.15", total_amount: float = 1000.0
):
    """Helper to create a test invoice."""
    from application.models import Invoice, InvoiceDetails, parse_date_safely

    details = InvoiceDetails(
        invoice_number=invoice_number,
        customer_id=customer_id,
        invoice_date=parse_date_safely("03/15/2025"),
        due_date=parse_date_safely("04/14/2025"),
        total_amount=total_amount,
    )
    return Invoice.create(details)


def create_test_invoice_item(
    invoice_id: int,
    description: str = "Test Work",
    quantity: float = 8.0,
    rate: float = 150.0,
):
    """Helper to create a test invoice item."""
    from application.models import InvoiceItem, LineItem, parse_date_safely

    line_item = LineItem(
        invoice_id=invoice_id,
        work_date=parse_date_safely("03/15/2025"),
        description=description,
        quantity=quantity,
        rate=rate,
        amount=quantity * rate,
    )
    InvoiceItem.add(line_item)
    return line_item
