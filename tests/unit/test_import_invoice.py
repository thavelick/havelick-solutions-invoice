"""Unit tests for import_invoice_from_files function."""

import os
import tempfile
from datetime import date

import pytest

from application.db import close_db, init_db
from application.models import Customer, Invoice, import_invoice_from_files


class TestImportInvoiceFromFiles:
    """Test cases for import_invoice_from_files function."""

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

    @pytest.fixture
    def sample_items(self):
        """Create sample invoice items for testing."""
        return [
            {
                "date": "03/15/2025",
                "description": "Web Development",
                "quantity": 8.0,
                "rate": 150.0,
            },
            {
                "date": "03/16/2025",
                "description": "Bug Fixes",
                "quantity": 2.0,
                "rate": 150.0,
            },
        ]

    def test_import_valid_invoice(self, test_db, sample_customer, sample_items):
        """Test importing a valid invoice with multiple items."""
        filename = "invoice-data-3-15.txt"

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=sample_items
        )

        assert isinstance(invoice_id, int)
        assert invoice_id > 0

        # Verify invoice was created with correct metadata
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.03.15"
        assert invoice_data["invoice_date"] == date(2025, 3, 15)
        assert invoice_data["due_date"] == date(2025, 4, 14)  # 30 days later
        assert invoice_data["total"] == 1500.0  # 8*150 + 2*150

        # Verify items were added
        assert len(invoice_data["items"]) == 2
        assert invoice_data["items"][0]["description"] == "Web Development"
        assert invoice_data["items"][0]["quantity"] == 8.0
        assert invoice_data["items"][0]["rate"] == 150.0
        assert invoice_data["items"][0]["amount"] == 1200.0

    def test_import_single_item_invoice(self, test_db, sample_customer):
        """Test importing an invoice with a single item."""
        filename = "invoice-data-12-25.txt"
        items = [
            {
                "date": "12/25/2025",
                "description": "Holiday Consulting",
                "quantity": 4.0,
                "rate": 200.0,
            }
        ]

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=items
        )

        assert invoice_id > 0

        # Verify invoice metadata from filename
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["invoice_number"] == "2025.12.25"
        assert invoice_data["invoice_date"] == date(2025, 12, 25)
        assert invoice_data["total"] == 800.0  # 4*200

        # Verify single item
        assert len(invoice_data["items"]) == 1
        assert invoice_data["items"][0]["description"] == "Holiday Consulting"

    def test_import_with_decimal_quantities(self, test_db, sample_customer):
        """Test importing invoice with decimal quantities and rates."""
        filename = "invoice-data-6-30.txt"
        items = [
            {
                "date": "06/30/2025",
                "description": "Partial Day Work",
                "quantity": 2.5,
                "rate": 175.50,
            },
            {
                "date": "06/30/2025",
                "description": "Consultation",
                "quantity": 0.5,
                "rate": 300.0,
            },
        ]

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=items
        )

        assert invoice_id > 0

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == 588.75  # 2.5*175.50 + 0.5*300.0

        # Verify decimal precision is preserved
        assert invoice_data["items"][0]["quantity"] == 2.5
        assert invoice_data["items"][0]["rate"] == 175.50
        assert invoice_data["items"][0]["amount"] == 438.75

    def test_import_filename_formats(self, test_db, sample_customer):
        """Test different filename formats."""
        items = [
            {
                "date": "05/05/2025",
                "description": "Test",
                "quantity": 1.0,
                "rate": 100.0,
            }
        ]

        # Test single digit month and day
        invoice_id1 = import_invoice_from_files(
            customer_id=sample_customer,
            invoice_data_file="invoice-data-5-5.txt",
            items=items,
        )
        invoice_data1 = Invoice.get_data(invoice_id1)
        assert invoice_data1 is not None
        assert invoice_data1["invoice_number"] == "2025.05.05"

        # Test double digit month and day
        invoice_id2 = import_invoice_from_files(
            customer_id=sample_customer,
            invoice_data_file="invoice-data-12-31.txt",
            items=items,
        )
        invoice_data2 = Invoice.get_data(invoice_id2)
        assert invoice_data2 is not None
        assert invoice_data2["invoice_number"] == "2025.12.31"

    def test_import_invalid_quantity(self, test_db, sample_customer):
        """Test import with invalid quantity values."""
        filename = "invoice-data-3-15.txt"

        # Test negative quantity
        items = [
            {
                "date": "03/15/2025",
                "description": "Test",
                "quantity": -1.0,
                "rate": 100.0,
            }
        ]
        with pytest.raises(ValueError, match="Invalid quantity"):
            import_invoice_from_files(sample_customer, filename, items)

        # Test zero quantity
        items = [
            {
                "date": "03/15/2025",
                "description": "Test",
                "quantity": 0.0,
                "rate": 100.0,
            }
        ]
        with pytest.raises(ValueError, match="Invalid quantity"):
            import_invoice_from_files(sample_customer, filename, items)

    def test_import_invalid_rate(self, test_db, sample_customer):
        """Test import with invalid rate values."""
        filename = "invoice-data-3-15.txt"

        # Test negative rate
        items = [
            {
                "date": "03/15/2025",
                "description": "Test",
                "quantity": 1.0,
                "rate": -50.0,
            }
        ]
        with pytest.raises(ValueError, match="Invalid rate"):
            import_invoice_from_files(sample_customer, filename, items)

    def test_import_invalid_filename_format(self, test_db, sample_customer):
        """Test import with invalid filename formats."""
        items = [
            {
                "date": "03/15/2025",
                "description": "Test",
                "quantity": 1.0,
                "rate": 100.0,
            }
        ]

        # Test invalid filename format
        with pytest.raises(ValueError, match="Invalid filename format"):
            import_invoice_from_files(
                sample_customer, "invoice-data-invalid.txt", items
            )

    def test_import_empty_items_list(self, test_db, sample_customer):
        """Test import with empty items list."""
        filename = "invoice-data-3-15.txt"
        items = []

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=items
        )

        assert invoice_id > 0

        # Verify empty invoice was created
        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == 0.0
        assert len(invoice_data["items"]) == 0

    def test_import_calculates_total_correctly(self, test_db, sample_customer):
        """Test that import calculates total amount correctly."""
        filename = "invoice-data-3-15.txt"
        items = [
            {
                "date": "03/15/2025",
                "description": "Work 1",
                "quantity": 3.5,
                "rate": 120.0,
            },
            {
                "date": "03/15/2025",
                "description": "Work 2",
                "quantity": 2.0,
                "rate": 175.50,
            },
        ]

        # Calculate expected total: 3.5*120 + 2*175.50 = 420 + 351 = 771
        expected_total = 771.0

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=items
        )

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None
        assert invoice_data["total"] == expected_total

    def test_import_preserves_item_order(self, test_db, sample_customer):
        """Test that import preserves item order by work date."""
        filename = "invoice-data-3-15.txt"
        items = [
            {
                "date": "03/17/2025",
                "description": "Later Work",
                "quantity": 1.0,
                "rate": 100.0,
            },
            {
                "date": "03/15/2025",
                "description": "Earlier Work",
                "quantity": 1.0,
                "rate": 100.0,
            },
            {
                "date": "03/16/2025",
                "description": "Middle Work",
                "quantity": 1.0,
                "rate": 100.0,
            },
        ]

        invoice_id = import_invoice_from_files(
            customer_id=sample_customer, invoice_data_file=filename, items=items
        )

        invoice_data = Invoice.get_data(invoice_id)
        assert invoice_data is not None

        # Items should be ordered by work_date (ascending)
        assert invoice_data["items"][0]["description"] == "Earlier Work"
        assert invoice_data["items"][1]["description"] == "Middle Work"
        assert invoice_data["items"][2]["description"] == "Later Work"
