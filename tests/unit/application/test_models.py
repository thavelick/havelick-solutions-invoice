"""Unit tests for data models."""

import sqlite3
from datetime import datetime

import pytest

from application.controllers.invoice_controller import InvoiceController
from application.date_utils import parse_date_safely
from application.models import (
    Customer,
    Invoice,
    InvoiceItem,
    LineItem,
)


class TestCustomerOperations:
    """Test customer database operations."""

    def test_create_customer(self, temp_db):
        """Test creating a new customer."""
        customer_id = Customer.create("Test Company", "123 Test St")
        assert customer_id > 0

    def test_get_customer_by_name(self, temp_db):
        """Test getting customer by name."""
        Customer.create("Test Company", "123 Test St")
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.name == "Test Company"
        assert customer.address == "123 Test St"

    def test_get_nonexistent_customer(self, temp_db):
        """Test getting nonexistent customer returns None."""
        customer = Customer.get_by_name("Nonexistent")
        assert customer is None

    def test_customer_upsert_new(self, temp_db):
        """Test upserting new customer."""
        customer_id = Customer.upsert("New Company", "456 New Ave")
        assert customer_id > 0
        customer = Customer.get_by_name("New Company")
        assert customer is not None
        assert customer.address == "456 New Ave"

    def test_customer_upsert_existing(self, temp_db):
        """Test upserting existing customer updates address."""
        # Create initial customer
        original_id = Customer.create("Update Company", "Original Address")
        # Upsert with new address
        upsert_id = Customer.upsert("Update Company", "New Address")
        assert upsert_id == original_id  # Should return same ID
        # Verify address was updated
        customer = Customer.get_by_name("Update Company")
        assert customer is not None
        assert customer.address == "New Address"

    def test_customer_list_all(self, temp_db):
        """Test listing all customers."""
        Customer.create("Company A", "Address A")
        Customer.create("Company B", "Address B")
        customers = Customer.list_all()
        assert len(customers) == 2
        names = [c.name for c in customers]
        assert "Company A" in names
        assert "Company B" in names


class TestInvoiceOperations:
    """Test invoice database operations."""

    def test_create_invoice(self, temp_db, create_test_customer, create_test_invoice):
        """Test creating an invoice."""
        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)
        assert invoice_id > 0

    def test_invoice_unique_number_constraint(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test that duplicate invoice numbers are not allowed."""
        customer_id = create_test_customer()
        create_test_invoice(customer_id, "2025.03.15")
        # Attempting to create another invoice with same number should raise error
        with pytest.raises(sqlite3.IntegrityError):
            create_test_invoice(customer_id, "2025.03.15")

    def test_invoice_list_all(self, temp_db, create_test_customer, create_test_invoice):
        """Test listing all invoices."""
        customer_id = create_test_customer()
        create_test_invoice(customer_id, "2025.03.15")
        create_test_invoice(customer_id, "2025.03.16")
        invoices = Invoice.list_all()
        assert len(invoices) == 2

    def test_invoice_list_by_customer(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test listing invoices filtered by customer."""
        customer_id1 = create_test_customer("Customer 1", "Address 1")
        customer_id2 = create_test_customer("Customer 2", "Address 2")
        create_test_invoice(customer_id1, "2025.03.15")
        create_test_invoice(customer_id2, "2025.03.16")
        # Test filtering by customer
        customer1_invoices = Invoice.list_all(customer_id1)
        assert len(customer1_invoices) == 1
        customer2_invoices = Invoice.list_all(customer_id2)
        assert len(customer2_invoices) == 1

    def test_invoice_get_recent(self, temp_db, create_test_customer):
        """Test getting N most recent invoices with limit."""
        from application.date_utils import parse_date_safely
        from application.models import Invoice, InvoiceDetails

        customer_id = create_test_customer()
        # Create invoices with different dates manually to test ordering

        # Create invoice from 2025.03.20
        details1 = InvoiceDetails(
            invoice_number="2025.03.20",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/20/2025"),
            due_date=parse_date_safely("04/19/2025"),
            total_amount=1000.0,
        )
        Invoice.create(details1)

        # Create invoice from 2025.03.15
        details2 = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0,
        )
        Invoice.create(details2)

        # Create invoice from 2025.03.25
        details3 = InvoiceDetails(
            invoice_number="2025.03.25",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/25/2025"),
            due_date=parse_date_safely("04/24/2025"),
            total_amount=800.0,
        )
        Invoice.create(details3)

        # Test getting recent invoices with limit
        recent_invoices = Invoice.get_recent(3)
        assert len(recent_invoices) == 3

        # Should be ordered by invoice_date DESC (most recent first)
        invoice_numbers = [inv["invoice_number"] for inv in recent_invoices]
        assert invoice_numbers == ["2025.03.25", "2025.03.20", "2025.03.15"]

        # Test getting more than available
        all_recent = Invoice.get_recent(10)
        assert len(all_recent) == 3  # Only 3 invoices exist

        # Test getting zero invoices
        zero_invoices = Invoice.get_recent(0)
        assert len(zero_invoices) == 0

    def test_invoice_get_recent_empty_database(self, temp_db):
        """Test getting recent invoices from empty database."""
        recent_invoices = Invoice.get_recent(3)
        assert len(recent_invoices) == 0

    def test_invoice_get_recent_data_structure(self, temp_db, create_test_customer):
        """Test that get_recent returns expected data structure."""
        from application.date_utils import parse_date_safely
        from application.models import Invoice, InvoiceDetails

        customer_id = create_test_customer("Test Customer", "123 Test St")

        details = InvoiceDetails(
            invoice_number="2025.03.15",
            customer_id=customer_id,
            invoice_date=parse_date_safely("03/15/2025"),
            due_date=parse_date_safely("04/14/2025"),
            total_amount=1200.0,
        )
        Invoice.create(details)

        recent_invoices = Invoice.get_recent(1)
        assert len(recent_invoices) == 1

        invoice = recent_invoices[0]
        assert "id" in invoice
        assert "invoice_number" in invoice
        assert "customer_name" in invoice
        assert "invoice_date" in invoice
        assert "total_amount" in invoice

        assert invoice["invoice_number"] == "2025.03.15"
        assert invoice["customer_name"] == "Test Customer"
        assert invoice["total_amount"] == 1200.0


class TestInvoiceItemOperations:
    """Test invoice item database operations."""

    def test_add_invoice_item(self, temp_db, create_test_customer, create_test_invoice):
        """Test adding an item to an invoice."""
        from application import db

        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)
        current_year = datetime.now().year
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely(f"03/15/{current_year}"),
            description="Test Work",
            quantity=8.0,
            rate=150.0,
            amount=1200.0,
        )
        InvoiceItem.add(line_item)
        # Verify item was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
        )
        items = cursor.fetchall()
        assert len(items) == 1
        # work_date might be returned as datetime.date object
        work_date = items[0][2]
        expected_date = f"{current_year}-03-15"
        if hasattr(work_date, "strftime"):
            assert work_date.strftime("%Y-%m-%d") == expected_date
        else:
            assert work_date == expected_date
        assert items[0][3] == "Test Work"  # description

    def test_add_multiple_invoice_items(
        self,
        temp_db,
        create_test_customer,
        create_test_invoice,
        create_test_invoice_item,
    ):
        """Test adding multiple items to an invoice."""
        from application import db

        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)
        # Add first item
        create_test_invoice_item(invoice_id, "First task", 4.0, 150.0)
        # Add second item
        create_test_invoice_item(invoice_id, "Second task", 6.0, 125.0)
        # Verify both items were added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT description, quantity, rate FROM invoice_items "
            "WHERE invoice_id = ? ORDER BY description",
            (invoice_id,),
        )
        items = cursor.fetchall()
        assert len(items) == 2
        assert items[0][0] == "First task"
        assert items[0][1] == 4.0
        assert items[1][0] == "Second task"
        assert items[1][2] == 125.0

    def test_add_item_with_zero_amount(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test adding an item with zero amount."""
        from application import db

        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)
        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Free Work",
            quantity=1.0,
            rate=0.0,
            amount=0.0,
        )
        InvoiceItem.add(line_item)
        # Verify item was added with zero amount
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT amount FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
        )
        items = cursor.fetchall()
        assert len(items) == 1
        assert items[0][0] == 0.0


class TestGenerateInvoiceMetadataFromFilename:
    """Test cases for generate_invoice_metadata_from_filename function."""

    def test_generate_metadata_valid_filenames(self):
        """Test generating metadata from valid filenames."""
        result = InvoiceController.generate_invoice_metadata_from_filename(
            "invoice-data-3-15.txt"
        )
        assert result["invoice_number"] == "2025.03.15"
        assert result["invoice_date"] == "03/15/2025"
        assert result["due_date"] == "04/14/2025"  # 30 days after 03/15/2025

        result = InvoiceController.generate_invoice_metadata_from_filename(
            "invoice-data-12-31.txt"
        )
        assert result["invoice_number"] == "2025.12.31"
        assert result["invoice_date"] == "12/31/2025"
        assert result["due_date"] == "01/30/2026"  # 30 days after 12/31/2025

    def test_generate_metadata_invalid_filename(self):
        """Test generating metadata from invalid filename."""
        with pytest.raises(ValueError, match="Invalid filename format"):
            InvoiceController.generate_invoice_metadata_from_filename(
                "invoice-data-invalid.txt"
            )

    def test_generate_metadata_fallback_filename(self):
        """Test generating metadata from non-standard filename."""
        result = InvoiceController.generate_invoice_metadata_from_filename(
            "some-other-file.txt"
        )

        # Should contain all required keys
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result

        # Should be in correct format
        assert result["invoice_number"].startswith("2025.")
        assert "/" in result["invoice_date"]
        assert "/" in result["due_date"]
