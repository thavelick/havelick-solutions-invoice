"""Unit tests for Invoice model."""

import os
import tempfile
from datetime import date

import pytest

from application.db import close_db, init_db
from application.models import Customer, Invoice, InvoiceDetails, InvoiceItem, LineItem, Vendor, parse_date_safely


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
            "created_at": "2025-03-15 10:30:00",
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
            "total_amount": 1200.0,
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
            "created_at": None,
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
            "created_at": "",
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


class TestInvoiceGetData:
    """Test cases for Invoice.get_data method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    @pytest.fixture
    def sample_data(self, test_db):
        """Create sample data for testing."""
        # Create customer
        customer_id = Customer.create("Test Company", "123 Test St\nTest City, ST 12345")
        
        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0
        )
        invoice_id = Invoice.create(invoice_details)
        
        # Add invoice items
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Web Development",
            quantity=8.0,
            rate=150.0,
            amount=1200.0
        )
        InvoiceItem.add(line_item)
        
        return {
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "invoice_details": invoice_details
        }

    def test_get_data_valid_invoice(self, test_db, sample_data):
        """Test getting data for a valid invoice."""
        invoice_data = Invoice.get_data(sample_data["invoice_id"])
        
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.03.15"
        assert invoice_data["invoice_date"] == date(2025, 3, 15)
        assert invoice_data["due_date"] == date(2025, 4, 14)
        assert invoice_data["total"] == 1200.0
        assert invoice_data["payment_terms"] == "Net 30 days"
        
        # Check customer data
        assert invoice_data["client"]["name"] == "Test Company"
        assert invoice_data["client"]["address"] == "123 Test St\nTest City, ST 12345"
        
        # Check vendor data (should be Havelick Software Solutions, LLC)
        assert invoice_data["company"]["name"] == "Havelick Software Solutions, LLC"
        assert invoice_data["company"]["address"] == "7815 Robinson Way\nArvada CO 80004"
        assert invoice_data["company"]["email"] == "tristan@havelick.com"
        assert invoice_data["company"]["phone"] == "303-475-7244"
        
        # Check items
        assert len(invoice_data["items"]) == 1
        item = invoice_data["items"][0]
        assert item["date"] == date(2025, 3, 15)
        assert item["description"] == "Web Development"
        assert item["quantity"] == 8.0
        assert item["rate"] == 150.0
        assert item["amount"] == 1200.0

    def test_get_data_nonexistent_invoice(self, test_db):
        """Test getting data for a nonexistent invoice."""
        invoice_data = Invoice.get_data(99999)
        assert invoice_data is None

    def test_get_data_invoice_with_no_items(self, test_db):
        """Test getting data for an invoice with no items."""
        # Create customer
        customer_id = Customer.create("Test Company", "123 Test St")
        
        # Create invoice without items
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.16",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/16/2025"),
            due_date=parse_date_safely("04/15/2025"),
            total_amount=0.0
        )
        invoice_id = Invoice.create(invoice_details)
        
        invoice_data = Invoice.get_data(invoice_id)
        
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.03.16"
        assert invoice_data["total"] == 0.0
        assert invoice_data["items"] == []

    def test_get_data_invoice_with_multiple_items(self, test_db):
        """Test getting data for an invoice with multiple items."""
        # Create customer
        customer_id = Customer.create("Multi Items Corp", "456 Multi St")
        
        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.17",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/17/2025"),
            due_date=parse_date_safely("04/16/2025"),
            total_amount=2000.0
        )
        invoice_id = Invoice.create(invoice_details)
        
        # Add multiple items
        line_item1 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Consulting",
            quantity=4.0,
            rate=200.0,
            amount=800.0
        )
        line_item2 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/16/2025"),
            description="Development",
            quantity=8.0,
            rate=150.0,
            amount=1200.0
        )
        InvoiceItem.add(line_item1)
        InvoiceItem.add(line_item2)
        
        invoice_data = Invoice.get_data(invoice_id)
        
        assert invoice_data is not None
        assert len(invoice_data["items"]) == 2
        
        # Items should be ordered by work_date
        assert invoice_data["items"][0]["date"] == date(2025, 3, 15)
        assert invoice_data["items"][0]["description"] == "Consulting"
        assert invoice_data["items"][1]["date"] == date(2025, 3, 16)
        assert invoice_data["items"][1]["description"] == "Development"

    def test_get_data_customer_with_special_characters(self, test_db):
        """Test getting data for customer with special characters in name/address."""
        # Create customer with special characters
        customer_id = Customer.create(
            "Acme Corp & Co.", 
            "123 O'Reilly St\nSuite #100\nCity, ST 12345"
        )
        
        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.18",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/18/2025"),
            due_date=parse_date_safely("04/17/2025"),
            total_amount=500.0
        )
        invoice_id = Invoice.create(invoice_details)
        
        invoice_data = Invoice.get_data(invoice_id)
        
        assert invoice_data is not None
        assert invoice_data["client"]["name"] == "Acme Corp & Co."
        assert invoice_data["client"]["address"] == "123 O'Reilly St\nSuite #100\nCity, ST 12345"

    def test_get_data_items_with_decimals(self, test_db):
        """Test getting data for items with decimal quantities and rates."""
        # Create customer
        customer_id = Customer.create("Decimal Corp", "789 Decimal Ave")
        
        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.19",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/19/2025"),
            due_date=parse_date_safely("04/18/2025"),
            total_amount=375.50
        )
        invoice_id = Invoice.create(invoice_details)
        
        # Add item with decimal values
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/19/2025"),
            description="Partial Day Work",
            quantity=2.5,
            rate=150.20,
            amount=375.50
        )
        InvoiceItem.add(line_item)
        
        invoice_data = Invoice.get_data(invoice_id)
        
        assert invoice_data is not None
        assert len(invoice_data["items"]) == 1
        item = invoice_data["items"][0]
        assert item["quantity"] == 2.5
        assert item["rate"] == 150.20
        assert item["amount"] == 375.50

    def test_get_data_zero_amount_invoice(self, test_db):
        """Test getting data for an invoice with zero amount."""
        # Create customer
        customer_id = Customer.create("Zero Corp", "000 Zero St")
        
        # Create invoice with zero amount
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.20",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/20/2025"),
            due_date=parse_date_safely("04/19/2025"),
            total_amount=0.0
        )
        invoice_id = Invoice.create(invoice_details)
        
        # Add zero amount item
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/20/2025"),
            description="Free Consultation",
            quantity=1.0,
            rate=0.0,
            amount=0.0
        )
        InvoiceItem.add(line_item)
        
        invoice_data = Invoice.get_data(invoice_id)
        
        assert invoice_data is not None
        assert invoice_data["total"] == 0.0
        assert len(invoice_data["items"]) == 1
        assert invoice_data["items"][0]["amount"] == 0.0

    def test_get_data_invalid_invoice_id(self, test_db):
        """Test getting data with invalid invoice ID types."""
        # Test with None
        invoice_data = Invoice.get_data(None)
        assert invoice_data is None
        
        # Test with negative ID
        invoice_data = Invoice.get_data(-1)
        assert invoice_data is None
        
        # Test with zero ID
        invoice_data = Invoice.get_data(0)
        assert invoice_data is None
