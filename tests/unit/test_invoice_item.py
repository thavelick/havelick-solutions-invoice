"""Unit tests for InvoiceItem model."""

import pytest

from application.models import InvoiceItem


class TestInvoiceItemFromDict:
    """Test cases for InvoiceItem.from_dict method."""

    def test_from_dict_valid_record(self):
        """Test creating InvoiceItem from valid database record."""
        record = {
            "id": 1,
            "invoice_id": 1,
            "work_date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 150.0,
            "amount": 1200.0,
        }

        item = InvoiceItem.from_dict(record)

        assert item.id == 1
        assert item.invoice_id == 1
        assert item.work_date == "03/15/2025"
        assert item.description == "Software development work"
        assert item.quantity == 8.0
        assert item.rate == 150.0
        assert item.amount == 1200.0

    def test_from_dict_missing_field(self):
        """Test creating InvoiceItem from record with missing field."""
        record = {
            "id": 1,
            "invoice_id": 1,
            "work_date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 150.0,
            # missing amount
        }

        with pytest.raises(KeyError):
            InvoiceItem.from_dict(record)

    def test_from_dict_none_values(self):
        """Test creating InvoiceItem from record with None values."""
        record = {
            "id": 1,
            "invoice_id": None,
            "work_date": None,
            "description": None,
            "quantity": None,
            "rate": None,
            "amount": None,
        }

        item = InvoiceItem.from_dict(record)

        assert item.id == 1
        assert item.invoice_id is None
        assert item.work_date is None
        assert item.description is None
        assert item.quantity is None
        assert item.rate is None
        assert item.amount is None

    def test_from_dict_empty_strings(self):
        """Test creating InvoiceItem from record with empty strings."""
        record = {
            "id": 1,
            "invoice_id": 1,
            "work_date": "",
            "description": "",
            "quantity": 0.0,
            "rate": 0.0,
            "amount": 0.0,
        }

        item = InvoiceItem.from_dict(record)

        assert item.id == 1
        assert item.invoice_id == 1
        assert item.work_date == ""
        assert item.description == ""
        assert item.quantity == 0.0
        assert item.rate == 0.0
        assert item.amount == 0.0
