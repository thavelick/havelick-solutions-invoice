"""Unit tests for InvoiceItem model."""

import os
import tempfile

import pytest

from application import db
from application.models import Customer, Invoice, InvoiceItem, LineItem


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


class TestInvoiceItemAdd:
    """Test cases for InvoiceItem.add method."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            db.init_db(db_path)
            yield db_path
            db.close_db()

    @pytest.fixture
    def sample_invoice(self, temp_db):
        """Create a sample invoice for testing."""
        # Create a customer first
        customer_id = Customer.create("Test Customer", "123 Test St")

        # Create an invoice using InvoiceDetails
        from application.models import InvoiceDetails

        details = InvoiceDetails(
            invoice_number="INV-001",
            customer_id=customer_id,
            invoice_date="2025-01-01",
            due_date="2025-01-31",
            total_amount=1000.0,
        )

        invoice_id = Invoice.create(details)

        # Return an invoice object with the ID
        class MockInvoice:
            def __init__(self, id):
                self.id = id

        return MockInvoice(invoice_id)

    def test_add_valid_line_item(self, sample_invoice):
        """Test adding a valid line item to an invoice."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Software development",
            quantity=8.0,
            rate=125.0,
            amount=1000.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added to the database
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["invoice_id"] == sample_invoice.id
        assert str(result["work_date"]) == "2025-01-15"
        assert result["description"] == "Software development"
        assert result["quantity"] == 8.0
        assert result["rate"] == 125.0
        assert result["amount"] == 1000.0

    def test_add_multiple_line_items(self, sample_invoice):
        """Test adding multiple line items to the same invoice."""
        line_item1 = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Software development",
            quantity=8.0,
            rate=125.0,
            amount=1000.0,
        )

        line_item2 = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-16",
            description="Code review",
            quantity=2.0,
            rate=125.0,
            amount=250.0,
        )

        # Add both line items
        InvoiceItem.add(line_item1)
        InvoiceItem.add(line_item2)

        # Verify both were added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id",
            (sample_invoice.id,),
        )
        results = cursor.fetchall()

        assert len(results) == 2
        assert results[0]["description"] == "Software development"
        assert results[1]["description"] == "Code review"

    def test_add_line_item_with_zero_values(self, sample_invoice):
        """Test adding a line item with zero quantity, rate, or amount."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Free consultation",
            quantity=0.0,
            rate=0.0,
            amount=0.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == "Free consultation"
        assert result["quantity"] == 0.0
        assert result["rate"] == 0.0
        assert result["amount"] == 0.0

    def test_add_line_item_with_negative_values(self, sample_invoice):
        """Test adding a line item with negative values (e.g., discounts)."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Discount",
            quantity=-1.0,
            rate=100.0,
            amount=-100.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == "Discount"
        assert result["quantity"] == -1.0
        assert result["rate"] == 100.0
        assert result["amount"] == -100.0

    def test_add_line_item_with_large_values(self, sample_invoice):
        """Test adding a line item with large decimal values."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Large project",
            quantity=999.99,
            rate=9999.99,
            amount=9999899.0001,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == "Large project"
        assert result["quantity"] == 999.99
        assert result["rate"] == 9999.99
        assert result["amount"] == 9999899.0001

    def test_add_line_item_with_special_characters(self, sample_invoice):
        """Test adding a line item with special characters in description."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Special chars: éñümlâuts & símböls!@#$%^&*()_+",
            quantity=1.0,
            rate=100.0,
            amount=100.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == "Special chars: éñümlâuts & símböls!@#$%^&*()_+"

    def test_add_line_item_with_empty_description(self, sample_invoice):
        """Test adding a line item with empty description."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="",
            quantity=1.0,
            rate=100.0,
            amount=100.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == ""

    def test_add_line_item_with_long_description(self, sample_invoice):
        """Test adding a line item with a very long description."""
        long_description = "A" * 1000  # 1000 character description
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description=long_description,
            quantity=1.0,
            rate=100.0,
            amount=100.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Verify it was added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == long_description

    def test_add_line_item_with_different_dates(self, sample_invoice):
        """Test adding line items with different valid dates."""
        # Test with different valid YYYY-MM-DD dates
        dates = ["2025-01-15", "2025-02-20", "2025-12-31", "2025-01-01"]

        for i, date in enumerate(dates):
            line_item = LineItem(
                invoice_id=sample_invoice.id,
                work_date=date,
                description=f"Work item {i+1}",
                quantity=1.0,
                rate=100.0,
                amount=100.0,
            )

            # Add the line item
            InvoiceItem.add(line_item)

        # Verify all were added
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY id",
            (sample_invoice.id,),
        )
        results = cursor.fetchall()

        assert len(results) == len(dates)
        for i, result in enumerate(results):
            assert str(result["work_date"]) == dates[i]

    def test_add_line_item_commits_transaction(self, sample_invoice):
        """Test that adding a line item commits the transaction."""
        line_item = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="Test transaction",
            quantity=1.0,
            rate=100.0,
            amount=100.0,
        )

        # Add the line item
        InvoiceItem.add(line_item)

        # Open a new connection to verify the data was committed
        new_connection = db.get_db_connection()
        cursor = new_connection.cursor()
        cursor.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ?", (sample_invoice.id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result["description"] == "Test transaction"

    def test_add_line_item_increments_id(self, sample_invoice):
        """Test that adding multiple line items increments the ID."""
        line_item1 = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-15",
            description="First item",
            quantity=1.0,
            rate=100.0,
            amount=100.0,
        )

        line_item2 = LineItem(
            invoice_id=sample_invoice.id,
            work_date="2025-01-16",
            description="Second item",
            quantity=2.0,
            rate=100.0,
            amount=200.0,
        )

        # Add both line items
        InvoiceItem.add(line_item1)
        InvoiceItem.add(line_item2)

        # Verify IDs are incremented
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM invoice_items WHERE invoice_id = ? ORDER BY id",
            (sample_invoice.id,),
        )
        results = cursor.fetchall()

        assert len(results) == 2
        assert results[1]["id"] > results[0]["id"]
