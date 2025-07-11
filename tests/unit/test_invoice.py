"""Unit tests for Invoice model."""

import pytest

from application.models import Invoice


class TestInvoiceFromDict:
    """Test cases for Invoice.from_dict method."""

    def test_from_dict_valid_record(self):
        """Test creating Invoice from valid database record."""
        record = {
            "id": 1,
            "customer_id": 1,
            "vendor_id": 1,
            "invoice_number": "2025.03.15",
            "invoice_date": "03/15/2025",
            "due_date": "04/14/2025",
            "total_amount": 1200.0,
            "created_at": "2025-03-15 10:30:00"
        }
        
        invoice = Invoice.from_dict(record)
        
        assert invoice.id == 1
        assert invoice.customer_id == 1
        assert invoice.vendor_id == 1
        assert invoice.invoice_number == "2025.03.15"
        assert invoice.invoice_date == "03/15/2025"
        assert invoice.due_date == "04/14/2025"
        assert invoice.total_amount == 1200.0
        assert invoice.created_at == "2025-03-15 10:30:00"

    def test_from_dict_missing_field(self):
        """Test creating Invoice from record with missing field."""
        record = {
            "id": 1,
            "customer_id": 1,
            "vendor_id": 1,
            "invoice_number": "2025.03.15",
            "invoice_date": "03/15/2025",
            "due_date": "04/14/2025",
            "total_amount": 1200.0
            # missing created_at
        }
        
        with pytest.raises(KeyError):
            Invoice.from_dict(record)

    def test_from_dict_none_values(self):
        """Test creating Invoice from record with None values."""
        record = {
            "id": 1,
            "customer_id": None,
            "vendor_id": None,
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "total_amount": None,
            "created_at": None
        }
        
        invoice = Invoice.from_dict(record)
        
        assert invoice.id == 1
        assert invoice.customer_id is None
        assert invoice.vendor_id is None
        assert invoice.invoice_number is None
        assert invoice.invoice_date is None
        assert invoice.due_date is None
        assert invoice.total_amount is None
        assert invoice.created_at is None

    def test_from_dict_empty_strings(self):
        """Test creating Invoice from record with empty strings."""
        record = {
            "id": 1,
            "customer_id": 1,
            "vendor_id": 1,
            "invoice_number": "",
            "invoice_date": "",
            "due_date": "",
            "total_amount": 0.0,
            "created_at": ""
        }
        
        invoice = Invoice.from_dict(record)
        
        assert invoice.id == 1
        assert invoice.customer_id == 1
        assert invoice.vendor_id == 1
        assert invoice.invoice_number == ""
        assert invoice.invoice_date == ""
        assert invoice.due_date == ""
        assert invoice.total_amount == 0.0
        assert invoice.created_at == ""