"""Consolidated unit tests for all data models."""

import pytest

from application.models import (
    Customer,
    Invoice,
    InvoiceItem,
    LineItem,
    Vendor,
)
from application.date_utils import parse_date_safely


class TestModelFromDict:
    """Test from_dict methods for all models using tool fixture."""

    def test_customer_from_dict(self, from_dict_checker):
        """Test Customer.from_dict method."""
        valid_record = {
            "id": 1,
            "name": "Test Company",
            "address": "123 Test St",
            "created_at": "2025-01-01 00:00:00",
        }
        from_dict_checker(Customer, valid_record, ["name", "address", "created_at"])

    def test_invoice_from_dict(self, from_dict_checker):
        """Test Invoice.from_dict method."""
        valid_record = {
            "id": 1,
            "customer_id": 1,
            "vendor_id": 1,
            "invoice_number": "2025.03.15",
            "invoice_date": "03/15/2025",
            "due_date": "04/14/2025",
            "total_amount": 1200.0,
            "created_at": "2025-03-15 10:30:00",
        }
        from_dict_checker(
            Invoice,
            valid_record,
            ["customer_id", "vendor_id", "invoice_number", "created_at"],
        )

    def test_invoice_item_from_dict(self, from_dict_checker):
        """Test InvoiceItem.from_dict method."""
        valid_record = {
            "id": 1,
            "invoice_id": 1,
            "work_date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 150.0,
            "amount": 1200.0,
        }
        from_dict_checker(
            InvoiceItem,
            valid_record,
            ["invoice_id", "work_date", "description", "quantity", "rate", "amount"],
        )

    def test_vendor_from_dict(self, from_dict_checker):
        """Test Vendor.from_dict method."""
        valid_record = {
            "id": 1,
            "name": "Havelick Software Solutions, LLC",
            "address": "7815 Robinson Way\nArvada CO 80004",
            "email": "tristan@havelick.com",
            "phone": "303-475-7244",
            "created_at": "2025-01-01 00:00:00",
        }
        from_dict_checker(
            Vendor, valid_record, ["name", "address", "email", "phone", "created_at"]
        )


class TestCustomerOperations:
    """Test Customer model operations."""

    def test_create_customer(self, temp_db):
        """Test creating a customer."""
        customer_id = Customer.create("Test Company", "123 Test St")
        assert isinstance(customer_id, int)
        assert customer_id > 0

    def test_get_customer_by_name(self, temp_db):
        """Test getting customer by name."""
        customer_id = Customer.create("Test Company", "123 Test St")
        customer = Customer.get_by_name("Test Company")

        assert customer is not None
        assert customer.id == customer_id
        assert customer.name == "Test Company"
        assert customer.address == "123 Test St"

    def test_get_nonexistent_customer(self, temp_db):
        """Test getting nonexistent customer returns None."""
        customer = Customer.get_by_name("Nonexistent Company")
        assert customer is None

    def test_customer_upsert_new(self, temp_db):
        """Test upsert creates new customer."""
        customer_id = Customer.upsert("New Company", "123 New St")
        assert customer_id > 0

        customer = Customer.get_by_name("New Company")
        assert customer is not None
        assert customer.address == "123 New St"

    def test_customer_upsert_existing(self, temp_db):
        """Test upsert updates existing customer."""
        original_id = Customer.create("Test Company", "123 Original St")
        updated_id = Customer.upsert("Test Company", "456 Updated St")

        assert updated_id == original_id

        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.address == "456 Updated St"

    def test_customer_list_all(self, temp_db):
        """Test listing all customers."""
        Customer.create("Company A", "123 A St")
        Customer.create("Company B", "456 B St")

        customers = Customer.list_all()
        assert len(customers) == 2
        assert customers[0].name == "Company A"  # Ordered by name
        assert customers[1].name == "Company B"


class TestInvoiceOperations:
    """Test Invoice model operations."""

    def test_create_invoice(self, temp_db, create_test_customer, create_test_invoice):
        """Test creating an invoice."""
        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)

        assert isinstance(invoice_id, int)
        assert invoice_id > 0

    def test_invoice_unique_number_constraint(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test that duplicate invoice numbers are rejected."""
        customer_id = create_test_customer()

        # First invoice should succeed
        invoice_id1 = create_test_invoice(customer_id, "2025.03.15")
        assert invoice_id1 > 0

        # Second invoice with same number should fail
        with pytest.raises(Exception):
            create_test_invoice(customer_id, "2025.03.15")

    def test_invoice_list_all(self, temp_db, create_test_customer, create_test_invoice):
        """Test listing all invoices."""
        customer_id = create_test_customer()
        create_test_invoice(customer_id, "2025.03.15", 1000.0)
        create_test_invoice(customer_id, "2025.03.16", 1500.0)

        invoices = Invoice.list_all()
        assert len(invoices) == 2
        # Check that both invoices are present (order may vary)
        invoice_numbers = [inv["invoice_number"] for inv in invoices]
        assert "2025.03.15" in invoice_numbers
        assert "2025.03.16" in invoice_numbers

    def test_invoice_list_by_customer(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test listing invoices for specific customer."""
        customer1_id = create_test_customer("Customer 1", "123 St")
        customer2_id = create_test_customer("Customer 2", "456 St")

        create_test_invoice(customer1_id, "2025.03.15")
        create_test_invoice(customer2_id, "2025.03.16")

        customer1_invoices = Invoice.list_all(customer_id=customer1_id)
        assert len(customer1_invoices) == 1
        assert customer1_invoices[0]["customer_name"] == "Customer 1"


class TestInvoiceItemOperations:
    """Test InvoiceItem model operations."""

    def test_add_invoice_item(self, temp_db, create_test_customer, create_test_invoice):
        """Test adding an invoice item."""
        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)

        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Test work",
            quantity=8.0,
            rate=150.0,
            amount=1200.0,
        )

        InvoiceItem.add(line_item)

        # Verify item was added by checking database directly
        from application import db

        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
        )
        items = cursor.fetchall()

        assert len(items) == 1
        assert items[0]["description"] == "Test work"
        assert items[0]["quantity"] == 8.0
        assert items[0]["rate"] == 150.0
        assert items[0]["amount"] == 1200.0

    def test_add_multiple_invoice_items(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test adding multiple invoice items."""
        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)

        # Add two items
        item1 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Work 1",
            quantity=4.0,
            rate=100.0,
            amount=400.0,
        )

        item2 = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/16/2025"),
            description="Work 2",
            quantity=6.0,
            rate=125.0,
            amount=750.0,
        )

        InvoiceItem.add(item1)
        InvoiceItem.add(item2)

        # Verify both items were added
        from application import db

        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY work_date",
            (invoice_id,),
        )
        items = cursor.fetchall()

        assert len(items) == 2
        assert items[0]["description"] == "Work 1"  # Earlier date
        assert items[1]["description"] == "Work 2"  # Later date

    def test_add_item_with_zero_amount(
        self, temp_db, create_test_customer, create_test_invoice
    ):
        """Test adding item with zero amount."""
        customer_id = create_test_customer()
        invoice_id = create_test_invoice(customer_id)

        line_item = LineItem(
            invoice_id=invoice_id,
            work_date=parse_date_safely("03/15/2025"),
            description="Free consultation",
            quantity=1.0,
            rate=0.0,
            amount=0.0,
        )

        InvoiceItem.add(line_item)

        # Verify item was added with zero amount
        from application import db

        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,)
        )
        items = cursor.fetchall()

        assert len(items) == 1
        assert items[0]["rate"] == 0.0
        assert items[0]["amount"] == 0.0
