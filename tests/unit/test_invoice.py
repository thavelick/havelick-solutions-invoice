"""Unit tests for Invoice model."""

import os
import tempfile
from datetime import date

import pytest

from application.db import close_db, init_db
from application.models import (
    Customer,
    Invoice,
    InvoiceDetails,
    InvoiceItem,
    LineItem,
    Vendor,
    parse_date_safely,
)


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
        customer_id = Customer.create(
            "Test Company", "123 Test St\nTest City, ST 12345"
        )

        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0,
        )
        invoice_id = Invoice.create(invoice_details)

        # Add invoice items
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Web Development",
            quantity=8.0,
            rate=150.0,
            amount=1200.0,
        )
        InvoiceItem.add(line_item)

        return {
            "customer_id": customer_id,
            "invoice_id": invoice_id,
            "invoice_details": invoice_details,
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
        assert (
            invoice_data["company"]["address"] == "7815 Robinson Way\nArvada CO 80004"
        )
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
            total_amount=0.0,
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
            total_amount=2000.0,
        )
        invoice_id = Invoice.create(invoice_details)

        # Add multiple items
        line_item1 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Consulting",
            quantity=4.0,
            rate=200.0,
            amount=800.0,
        )
        line_item2 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/16/2025"),
            description="Development",
            quantity=8.0,
            rate=150.0,
            amount=1200.0,
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
            "Acme Corp & Co.", "123 O'Reilly St\nSuite #100\nCity, ST 12345"
        )

        # Create invoice
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.18",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/18/2025"),
            due_date=parse_date_safely("04/17/2025"),
            total_amount=500.0,
        )
        invoice_id = Invoice.create(invoice_details)

        invoice_data = Invoice.get_data(invoice_id)

        assert invoice_data is not None
        assert invoice_data["client"]["name"] == "Acme Corp & Co."
        assert (
            invoice_data["client"]["address"]
            == "123 O'Reilly St\nSuite #100\nCity, ST 12345"
        )

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
            total_amount=375.50,
        )
        invoice_id = Invoice.create(invoice_details)

        # Add item with decimal values
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/19/2025"),
            description="Partial Day Work",
            quantity=2.5,
            rate=150.20,
            amount=375.50,
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
            total_amount=0.0,
        )
        invoice_id = Invoice.create(invoice_details)

        # Add zero amount item
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/20/2025"),
            description="Free Consultation",
            quantity=1.0,
            rate=0.0,
            amount=0.0,
        )
        InvoiceItem.add(line_item)

        invoice_data = Invoice.get_data(invoice_id)

        assert invoice_data is not None
        assert invoice_data["total"] == 0.0
        assert len(invoice_data["items"]) == 1
        assert invoice_data["items"][0]["amount"] == 0.0

    def test_get_data_invalid_invoice_id(self, test_db):
        """Test getting data with invalid invoice ID."""
        # Test with negative ID
        invoice_data = Invoice.get_data(-1)
        assert invoice_data is None

        # Test with zero ID
        invoice_data = Invoice.get_data(0)
        assert invoice_data is None


class TestInvoiceCreate:
    """Test cases for Invoice.create method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    @pytest.fixture
    def sample_customer(self, test_db):
        """Create a sample customer for testing."""
        return Customer.create("Test Company", "123 Test St")

    def test_create_valid_invoice(self, test_db, sample_customer):
        """Test creating a valid invoice with all required fields."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1500.0,
        )

        invoice_id = Invoice.create(invoice_details)

        assert isinstance(invoice_id, int)
        assert invoice_id > 0

        # Verify invoice was created in database
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.03.15"
        assert invoice_data["invoice_date"] == date(2025, 3, 15)
        assert invoice_data["due_date"] == date(2025, 4, 14)
        assert invoice_data["total"] == 1500.0

    def test_create_invoice_with_zero_amount(self, test_db, sample_customer):
        """Test creating an invoice with zero total amount."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.16",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/16/2025"),
            due_date=parse_date_safely("04/15/2025"),
            total_amount=0.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == 0.0

    def test_create_invoice_with_decimal_amount(self, test_db, sample_customer):
        """Test creating an invoice with decimal total amount."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.17",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/17/2025"),
            due_date=parse_date_safely("04/16/2025"),
            total_amount=1234.56,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == 1234.56

    def test_create_multiple_invoices(self, test_db, sample_customer):
        """Test creating multiple invoices with different IDs."""
        invoice_details1 = InvoiceDetails(
            invoice_number="2025.03.18",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/18/2025"),
            due_date=parse_date_safely("04/17/2025"),
            total_amount=1000.0,
        )

        invoice_details2 = InvoiceDetails(
            invoice_number="2025.03.19",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/19/2025"),
            due_date=parse_date_safely("04/18/2025"),
            total_amount=2000.0,
        )

        invoice_id1 = Invoice.create(invoice_details1)
        invoice_id2 = Invoice.create(invoice_details2)

        assert invoice_id1 != invoice_id2
        assert invoice_id1 > 0
        assert invoice_id2 > 0

        # Verify both invoices exist
        invoice_data1 = Invoice.get_data(invoice_id1)
        invoice_data2 = Invoice.get_data(invoice_id2)

        assert invoice_data1 is not None
        assert invoice_data2 is not None
        assert invoice_data1["invoice_number"] == "2025.03.18"
        assert invoice_data2["invoice_number"] == "2025.03.19"
        assert invoice_data1["total"] == 1000.0
        assert invoice_data2["total"] == 2000.0

    def test_create_invoice_with_same_number_different_customers(self, test_db):
        """Test creating invoices with same number for different customers fails."""
        customer1 = Customer.create("Customer One", "123 First St")
        customer2 = Customer.create("Customer Two", "456 Second St")

        invoice_details1 = InvoiceDetails(
            invoice_number="2025.03.20",
            customer_id=customer1,
            invoice_date=parse_date_safely("03/20/2025"),
            due_date=parse_date_safely("04/19/2025"),
            total_amount=1000.0,
        )

        invoice_details2 = InvoiceDetails(
            invoice_number="2025.03.20",  # Same number - should fail
            customer_id=customer2,
            invoice_date=parse_date_safely("03/20/2025"),
            due_date=parse_date_safely("04/19/2025"),
            total_amount=2000.0,
        )

        # First invoice should succeed
        invoice_id1 = Invoice.create(invoice_details1)
        assert invoice_id1 > 0

        # Second invoice with same number should fail due to UNIQUE constraint
        with pytest.raises(Exception):  # Should raise unique constraint error
            Invoice.create(invoice_details2)

        # Verify first invoice still exists
        invoice_data1 = Invoice.get_data(invoice_id1)
        assert invoice_data1 is not None
        assert invoice_data1["client"]["name"] == "Customer One"

    def test_create_invoice_unique_number_constraint(self, test_db, sample_customer):
        """Test that duplicate invoice numbers are rejected."""
        invoice_details1 = InvoiceDetails(
            invoice_number="2025.03.21",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/21/2025"),
            due_date=parse_date_safely("04/20/2025"),
            total_amount=1000.0,
        )

        invoice_details2 = InvoiceDetails(
            invoice_number="2025.03.21",  # Same number
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/22/2025"),
            due_date=parse_date_safely("04/21/2025"),
            total_amount=2000.0,
        )

        # First invoice should succeed
        invoice_id1 = Invoice.create(invoice_details1)
        assert invoice_id1 > 0

        # Second invoice with same number should fail
        with pytest.raises(Exception):  # Should raise unique constraint error
            Invoice.create(invoice_details2)

    def test_create_invoice_assigns_vendor_id(self, test_db, sample_customer):
        """Test that created invoices are assigned the correct vendor ID."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.22",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/22/2025"),
            due_date=parse_date_safely("04/21/2025"),
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(invoice_details)

        # Verify vendor information is Havelick Solutions
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["company"]["name"] == "Havelick Software Solutions, LLC"
        assert invoice_data["company"]["email"] == "tristan@havelick.com"

    def test_create_invoice_with_nonexistent_customer(self, test_db):
        """Test creating invoice with nonexistent customer ID."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.23",
            customer_id=999,  # Nonexistent customer
            invoice_date=parse_date_safely("03/23/2025"),
            due_date=parse_date_safely("04/22/2025"),
            total_amount=1000.0,
        )

        # Note: SQLite doesn't enforce foreign key constraints by default
        # So this will succeed but the invoice won't have valid customer data
        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        # When retrieving, the JOIN will fail and return None
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is None

    def test_create_invoice_with_special_characters(self, test_db):
        """Test creating invoice with special characters in number."""
        customer_id = Customer.create("Test Company", "123 Test St")

        invoice_details = InvoiceDetails(
            invoice_number="2025.03.24-SPECIAL",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/24/2025"),
            due_date=parse_date_safely("04/23/2025"),
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.03.24-SPECIAL"

    def test_create_invoice_with_large_amount(self, test_db, sample_customer):
        """Test creating invoice with large total amount."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.25",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/25/2025"),
            due_date=parse_date_safely("04/24/2025"),
            total_amount=999999.99,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == 999999.99

    def test_create_invoice_with_date_edge_cases(self, test_db, sample_customer):
        """Test creating invoice with edge case dates."""
        # Test leap year date
        invoice_details = InvoiceDetails(
            invoice_number="2024.02.29",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("02/29/2024"),
            due_date=parse_date_safely("03/30/2024"),
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_date"] == date(2024, 2, 29)
        assert invoice_data["due_date"] == date(2024, 3, 30)

    def test_create_invoice_with_empty_number(self, test_db, sample_customer):
        """Test creating invoice with empty invoice number."""
        invoice_details = InvoiceDetails(
            invoice_number="",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/26/2025"),
            due_date=parse_date_safely("04/25/2025"),
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == ""

    def test_create_invoice_with_negative_amount(self, test_db, sample_customer):
        """Test creating invoice with negative total amount."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.27",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/27/2025"),
            due_date=parse_date_safely("04/26/2025"),
            total_amount=-100.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == -100.0

    def test_create_invoice_due_date_before_invoice_date(
        self, test_db, sample_customer
    ):
        """Test creating invoice with due date before invoice date."""
        invoice_details = InvoiceDetails(
            invoice_number="2025.03.28",
            customer_id=sample_customer,
            invoice_date=parse_date_safely("03/28/2025"),
            due_date=parse_date_safely("03/15/2025"),  # Before invoice date
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(invoice_details)
        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_date"] == date(2025, 3, 28)
        assert invoice_data["due_date"] == date(2025, 3, 15)


class TestInvoiceListAll:
    """Test cases for Invoice.list_all method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    @pytest.fixture
    def sample_customers(self, test_db):
        """Create sample customers for testing."""
        customer1 = Customer.create("Company A", "123 First St")
        customer2 = Customer.create("Company B", "456 Second St")
        customer3 = Customer.create("Company C", "789 Third St")
        return {"customer1": customer1, "customer2": customer2, "customer3": customer3}

    @pytest.fixture
    def sample_invoices(self, test_db, sample_customers):
        """Create sample invoices for testing."""
        invoices = []

        # Create invoices for customer1
        invoice1 = Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.15",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("03/15/2025"),
                due_date=parse_date_safely("04/14/2025"),
                total_amount=1000.0,
            )
        )
        invoices.append(invoice1)

        invoice2 = Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.20",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("03/20/2025"),
                due_date=parse_date_safely("04/19/2025"),
                total_amount=1500.0,
            )
        )
        invoices.append(invoice2)

        # Create invoices for customer2
        invoice3 = Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.10",
                customer_id=sample_customers["customer2"],
                invoice_date=parse_date_safely("03/10/2025"),
                due_date=parse_date_safely("04/09/2025"),
                total_amount=2000.0,
            )
        )
        invoices.append(invoice3)

        invoice4 = Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.25",
                customer_id=sample_customers["customer2"],
                invoice_date=parse_date_safely("03/25/2025"),
                due_date=parse_date_safely("04/24/2025"),
                total_amount=500.0,
            )
        )
        invoices.append(invoice4)

        return invoices

    def test_list_all_no_filter(self, test_db, sample_customers, sample_invoices):
        """Test listing all invoices without filtering."""
        invoices = Invoice.list_all()

        assert len(invoices) == 4

        # Check structure of returned data
        for invoice in invoices:
            assert "id" in invoice
            assert "invoice_number" in invoice
            assert "customer_name" in invoice
            assert "invoice_date" in invoice
            assert "total_amount" in invoice

            assert isinstance(invoice["id"], int)
            assert isinstance(invoice["invoice_number"], str)
            assert isinstance(invoice["customer_name"], str)
            assert isinstance(invoice["total_amount"], (int, float))

        # Check that invoices are ordered by invoice_date DESC
        invoice_dates = [invoice["invoice_date"] for invoice in invoices]
        assert invoice_dates == sorted(invoice_dates, reverse=True)

    def test_list_all_with_customer_filter(
        self, test_db, sample_customers, sample_invoices
    ):
        """Test listing invoices filtered by customer."""
        # Get invoices for customer1
        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        assert len(invoices) == 2

        # All invoices should belong to customer1
        for invoice in invoices:
            assert invoice["customer_name"] == "Company A"

        # Check specific invoice details
        invoice_numbers = [inv["invoice_number"] for inv in invoices]
        assert "2025.03.15" in invoice_numbers
        assert "2025.03.20" in invoice_numbers

        # Check ordering by date DESC
        assert invoices[0]["invoice_date"] > invoices[1]["invoice_date"]

    def test_list_all_customer_with_no_invoices(self, test_db, sample_customers):
        """Test listing invoices for customer with no invoices."""
        invoices = Invoice.list_all(customer_id=sample_customers["customer3"])

        assert len(invoices) == 0
        assert invoices == []

    def test_list_all_empty_database(self, test_db):
        """Test listing invoices from empty database."""
        invoices = Invoice.list_all()

        assert len(invoices) == 0
        assert invoices == []

    def test_list_all_nonexistent_customer(self, test_db, sample_invoices):
        """Test listing invoices for nonexistent customer."""
        invoices = Invoice.list_all(customer_id=999)

        assert len(invoices) == 0
        assert invoices == []

    def test_list_all_invoice_data_content(
        self, test_db, sample_customers, sample_invoices
    ):
        """Test that invoice data contains correct values."""
        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        # Find the specific invoice
        invoice_2025_03_15 = next(
            inv for inv in invoices if inv["invoice_number"] == "2025.03.15"
        )

        assert invoice_2025_03_15["customer_name"] == "Company A"
        assert invoice_2025_03_15["invoice_date"] == date(2025, 3, 15)
        assert invoice_2025_03_15["total_amount"] == 1000.0
        assert invoice_2025_03_15["id"] > 0

    def test_list_all_multiple_customers_ordering(
        self, test_db, sample_customers, sample_invoices
    ):
        """Test that invoices from multiple customers are ordered correctly."""
        invoices = Invoice.list_all()

        # Should be ordered by invoice_date DESC across all customers
        expected_order = [
            ("2025.03.25", "Company B"),  # Latest date
            ("2025.03.20", "Company A"),
            ("2025.03.15", "Company A"),
            ("2025.03.10", "Company B"),  # Earliest date
        ]

        actual_order = [
            (inv["invoice_number"], inv["customer_name"]) for inv in invoices
        ]
        assert actual_order == expected_order

    def test_list_all_with_zero_amount_invoice(self, test_db, sample_customers):
        """Test listing invoices with zero amount."""
        # Create invoice with zero amount
        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.30",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("03/30/2025"),
                due_date=parse_date_safely("04/29/2025"),
                total_amount=0.0,
            )
        )

        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        zero_amount_invoice = next(
            inv for inv in invoices if inv["invoice_number"] == "2025.03.30"
        )
        assert zero_amount_invoice["total_amount"] == 0.0

    def test_list_all_with_decimal_amounts(self, test_db, sample_customers):
        """Test listing invoices with decimal amounts."""
        # Create invoice with decimal amount
        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.03.31",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("03/31/2025"),
                due_date=parse_date_safely("04/30/2025"),
                total_amount=1234.56,
            )
        )

        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        decimal_invoice = next(
            inv for inv in invoices if inv["invoice_number"] == "2025.03.31"
        )
        assert decimal_invoice["total_amount"] == 1234.56

    def test_list_all_with_negative_amount(self, test_db, sample_customers):
        """Test listing invoices with negative amounts."""
        # Create invoice with negative amount
        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.04.01",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("04/01/2025"),
                due_date=parse_date_safely("05/01/2025"),
                total_amount=-100.0,
            )
        )

        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        negative_invoice = next(
            inv for inv in invoices if inv["invoice_number"] == "2025.04.01"
        )
        assert negative_invoice["total_amount"] == -100.0

    def test_list_all_customer_name_with_special_characters(self, test_db):
        """Test listing invoices for customer with special characters."""
        customer_id = Customer.create("Üñícödé & Co.", "123 Special St")

        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.04.02",
                customer_id=customer_id,
                invoice_date=parse_date_safely("04/02/2025"),
                due_date=parse_date_safely("05/02/2025"),
                total_amount=1000.0,
            )
        )

        invoices = Invoice.list_all(customer_id=customer_id)

        assert len(invoices) == 1
        assert invoices[0]["customer_name"] == "Üñícödé & Co."

    def test_list_all_same_date_multiple_invoices(self, test_db, sample_customers):
        """Test listing invoices with same date for ordering."""
        # Create multiple invoices with same date
        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.04.03-A",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("04/03/2025"),
                due_date=parse_date_safely("05/03/2025"),
                total_amount=1000.0,
            )
        )

        Invoice.create(
            InvoiceDetails(
                invoice_number="2025.04.03-B",
                customer_id=sample_customers["customer1"],
                invoice_date=parse_date_safely("04/03/2025"),
                due_date=parse_date_safely("05/03/2025"),
                total_amount=2000.0,
            )
        )

        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        # Should have both invoices
        same_date_invoices = [
            inv for inv in invoices if inv["invoice_date"] == date(2025, 4, 3)
        ]
        assert len(same_date_invoices) == 2

    def test_list_all_large_dataset(self, test_db, sample_customers):
        """Test listing invoices with larger dataset."""
        # Create many invoices
        for i in range(10):
            Invoice.create(
                InvoiceDetails(
                    invoice_number=f"2025.05.{i+1:02d}",
                    customer_id=sample_customers["customer1"],
                    invoice_date=parse_date_safely(f"05/{i+1:02d}/2025"),
                    due_date=parse_date_safely(f"06/{i+1:02d}/2025"),
                    total_amount=float(i + 1) * 100.0,
                )
            )

        invoices = Invoice.list_all(customer_id=sample_customers["customer1"])

        assert len(invoices) == 10

        # Should be ordered by date DESC
        dates = [inv["invoice_date"] for inv in invoices]
        assert dates == sorted(dates, reverse=True)

    def test_list_all_customer_id_none_vs_no_param(self, test_db, sample_invoices):
        """Test that customer_id=None behaves same as no parameter."""
        invoices_no_param = Invoice.list_all()
        invoices_none = Invoice.list_all(customer_id=None)

        assert len(invoices_no_param) == len(invoices_none)
        assert invoices_no_param == invoices_none
