"""Unit tests for InvoiceDB class."""

import os
import sqlite3
import tempfile
import pytest
from unittest.mock import patch

from database import InvoiceDB, InvoiceDetails, LineItem

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def invoice_db(temp_db):
    """Create an InvoiceDB instance with temporary database."""
    return InvoiceDB(temp_db)


class TestInvoiceDBInit:
    """Test InvoiceDB initialization."""

    def test_init_creates_database_file(self, temp_db):
        """Test that initialization creates the database file."""
        db = InvoiceDB(temp_db)
        assert os.path.exists(temp_db)

    def test_init_creates_tables(self, temp_db):
        """Test that initialization creates required tables."""
        db = InvoiceDB(temp_db)
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            
            # Check that all required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            expected_tables = {"vendors", "customers", "invoices", "invoice_items"}
            assert expected_tables.issubset(tables)

    def test_init_populates_vendor_data(self, temp_db):
        """Test that initialization populates vendor data."""
        db = InvoiceDB(temp_db)
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM vendors WHERE id = 1")
            row = cursor.fetchone()
            
            assert row is not None
            assert row[0] == 1
            assert "Havelick Software Solutions" in row[1]


class TestCustomerOperations:
    """Test customer-related operations."""

    def test_create_customer(self, invoice_db):
        """Test creating a new customer."""
        customer_id = invoice_db.create_customer("Test Company", "123 Test St")
        
        assert customer_id is not None
        assert customer_id > 0

    def test_create_customer_returns_different_ids(self, invoice_db):
        """Test that creating multiple customers returns different IDs."""
        id1 = invoice_db.create_customer("Company 1", "Address 1")
        id2 = invoice_db.create_customer("Company 2", "Address 2")
        
        assert id1 != id2

    def test_get_customer_by_name_existing(self, invoice_db):
        """Test getting an existing customer by name."""
        name = "Test Company"
        address = "123 Test St"
        customer_id = invoice_db.create_customer(name, address)
        
        customer = invoice_db.get_customer_by_name(name)
        
        assert customer is not None
        assert customer["id"] == customer_id
        assert customer["name"] == name
        assert customer["address"] == address

    def test_get_customer_by_name_nonexistent(self, invoice_db):
        """Test getting a non-existent customer by name."""
        customer = invoice_db.get_customer_by_name("Nonexistent Company")
        assert customer is None

    def test_upsert_customer_new(self, invoice_db):
        """Test upserting a new customer."""
        name = "New Company"
        address = "456 New St"
        
        customer_id = invoice_db.upsert_customer(name, address)
        
        assert customer_id is not None
        customer = invoice_db.get_customer_by_name(name)
        assert customer["id"] == customer_id
        assert customer["address"] == address

    def test_upsert_customer_existing(self, invoice_db):
        """Test upserting an existing customer (should update)."""
        name = "Existing Company"
        old_address = "123 Old St"
        new_address = "456 New St"
        
        # Create customer
        original_id = invoice_db.create_customer(name, old_address)
        
        # Upsert with new address
        upsert_id = invoice_db.upsert_customer(name, new_address)
        
        assert upsert_id == original_id
        customer = invoice_db.get_customer_by_name(name)
        assert customer["address"] == new_address

    def test_import_customer_from_json(self, invoice_db):
        """Test importing customer from JSON data."""
        json_data = {
            "client": {
                "name": "JSON Company",
                "address": "789 JSON St"
            }
        }
        
        customer_id = invoice_db.import_customer_from_json(json_data)
        
        assert customer_id is not None
        customer = invoice_db.get_customer_by_name("JSON Company")
        assert customer["address"] == "789 JSON St"

    def test_import_customer_from_json_invalid_data(self, invoice_db):
        """Test importing customer from invalid JSON data."""
        json_data = {"invalid": "data"}
        
        customer_id = invoice_db.import_customer_from_json(json_data)
        
        # Should still work but with empty data
        assert customer_id is not None

    def test_list_customers_empty(self, invoice_db):
        """Test listing customers when none exist."""
        customers = invoice_db.list_customers()
        assert customers == []

    def test_list_customers_with_data(self, invoice_db):
        """Test listing customers with data."""
        # Create test customers
        id1 = invoice_db.create_customer("Company A", "Address A")
        id2 = invoice_db.create_customer("Company B", "Address B")
        
        customers = invoice_db.list_customers()
        
        assert len(customers) == 2
        assert any(c["id"] == id1 and c["name"] == "Company A" for c in customers)
        assert any(c["id"] == id2 and c["name"] == "Company B" for c in customers)


class TestInvoiceOperations:
    """Test invoice-related operations."""

    def test_create_invoice(self, invoice_db):
        """Test creating a new invoice."""
        # Create a customer first
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        details = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=100.0
        )
        
        invoice_id = invoice_db.create_invoice(details)
        
        assert invoice_id is not None
        assert invoice_id > 0

    def test_create_invoice_duplicate_number(self, invoice_db):
        """Test creating invoice with duplicate number should fail."""
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        details = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=100.0
        )
        
        # Create first invoice
        invoice_db.create_invoice(details)
        
        # Try to create second with same number
        with pytest.raises(Exception):  # Should raise an exception due to UNIQUE constraint
            invoice_db.create_invoice(details)

    def test_add_invoice_item(self, invoice_db):
        """Test adding an item to an invoice."""
        # Create customer and invoice
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        details = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=100.0
        )
        invoice_id = invoice_db.create_invoice(details)
        
        # Add item
        item = LineItem(
            invoice_id=invoice_id,
            work_date="2025-01-01",
            description="Test work",
            quantity=1.0,
            rate=100.0,
            amount=100.0
        )
        
        # Should not raise exception
        invoice_db.add_invoice_item(item)

    def test_get_invoice_data_existing(self, invoice_db):
        """Test getting complete invoice data."""
        # Create customer and invoice
        customer_id = invoice_db.create_customer("Test Customer", "123 Test St")
        details = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=150.0
        )
        invoice_id = invoice_db.create_invoice(details)
        
        # Add items
        item1 = LineItem(
            invoice_id=invoice_id,
            work_date="2025-01-01",
            description="Work item 1",
            quantity=1.0,
            rate=100.0,
            amount=100.0
        )
        item2 = LineItem(
            invoice_id=invoice_id,
            work_date="2025-01-02",
            description="Work item 2",
            quantity=0.5,
            rate=100.0,
            amount=50.0
        )
        invoice_db.add_invoice_item(item1)
        invoice_db.add_invoice_item(item2)
        
        # Get complete data
        data = invoice_db.get_invoice_data(invoice_id)
        
        assert data is not None
        assert data["invoice_number"] == "2025.01.01"
        assert data["client"]["name"] == "Test Customer"
        assert data["company"]["name"] == "Havelick Software Solutions, LLC"
        assert len(data["items"]) == 2
        assert data["items"][0]["description"] == "Work item 1"
        assert data["items"][1]["description"] == "Work item 2"

    def test_get_invoice_data_nonexistent(self, invoice_db):
        """Test getting data for non-existent invoice."""
        data = invoice_db.get_invoice_data(999)
        assert data is None

    def test_list_invoices_empty(self, invoice_db):
        """Test listing invoices when none exist."""
        invoices = invoice_db.list_invoices()
        assert invoices == []

    def test_list_invoices_with_data(self, invoice_db):
        """Test listing invoices with data."""
        # Create customer and invoices
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        details1 = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=100.0
        )
        details2 = InvoiceDetails(
            invoice_number="2025.01.02",
            customer_id=customer_id,
            invoice_date="01/02/2025",
            due_date="02/01/2025",
            total_amount=200.0
        )
        
        id1 = invoice_db.create_invoice(details1)
        id2 = invoice_db.create_invoice(details2)
        
        invoices = invoice_db.list_invoices()
        
        assert len(invoices) == 2
        # Should be ordered by date DESC
        assert invoices[0]["invoice_number"] == "2025.01.02"
        assert invoices[1]["invoice_number"] == "2025.01.01"

    def test_list_invoices_filtered_by_customer(self, invoice_db):
        """Test listing invoices filtered by customer."""
        # Create two customers
        customer1_id = invoice_db.create_customer("Customer 1", "Address 1")
        customer2_id = invoice_db.create_customer("Customer 2", "Address 2")
        
        # Create invoices for each customer
        details1 = InvoiceDetails(
            invoice_number="2025.01.01",
            customer_id=customer1_id,
            invoice_date="01/01/2025",
            due_date="01/31/2025",
            total_amount=100.0
        )
        details2 = InvoiceDetails(
            invoice_number="2025.01.02",
            customer_id=customer2_id,
            invoice_date="01/02/2025",
            due_date="02/01/2025",
            total_amount=200.0
        )
        
        invoice_db.create_invoice(details1)
        invoice_db.create_invoice(details2)
        
        # Filter by customer 1
        invoices = invoice_db.list_invoices(customer1_id)
        
        assert len(invoices) == 1
        assert invoices[0]["customer_name"] == "Customer 1"


class TestImportInvoiceFromFiles:
    """Test importing invoice from files."""

    def test_import_invoice_valid_data(self, invoice_db):
        """Test importing invoice with valid data."""
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        items = [
            {
                "date": "01/01/2025",
                "description": "Work item 1",
                "quantity": 2.0,
                "rate": 50.0
            },
            {
                "date": "01/02/2025", 
                "description": "Work item 2",
                "quantity": 1.5,
                "rate": 100.0
            }
        ]
        
        invoice_id = invoice_db.import_invoice_from_files(
            customer_id, "invoice-data-1-1.txt", items
        )
        
        assert invoice_id is not None
        
        # Verify the invoice was created correctly
        data = invoice_db.get_invoice_data(invoice_id)
        assert data["total"] == 250.0  # 2*50 + 1.5*100
        assert len(data["items"]) == 2

    def test_import_invoice_invalid_quantity(self, invoice_db):
        """Test importing invoice with invalid quantity."""
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        items = [
            {
                "date": "01/01/2025",
                "description": "Invalid work",
                "quantity": -1.0,  # Invalid quantity
                "rate": 50.0
            }
        ]
        
        with pytest.raises(ValueError, match="Invalid quantity"):
            invoice_db.import_invoice_from_files(
                customer_id, "invoice-data-1-1.txt", items
            )

    def test_import_invoice_invalid_rate(self, invoice_db):
        """Test importing invoice with invalid rate."""
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        items = [
            {
                "date": "01/01/2025",
                "description": "Invalid work",
                "quantity": 1.0,
                "rate": -50.0  # Invalid rate
            }
        ]
        
        with pytest.raises(ValueError, match="Invalid rate"):
            invoice_db.import_invoice_from_files(
                customer_id, "invoice-data-1-1.txt", items
            )

    def test_import_invoice_missing_data(self, invoice_db):
        """Test importing invoice with missing required data."""
        customer_id = invoice_db.create_customer("Test Customer", "Test Address")
        
        items = [
            {
                "date": "01/01/2025",
                "description": "Incomplete work",
                # Missing quantity and rate
            }
        ]
        
        with pytest.raises(ValueError, match="Error importing invoice"):
            invoice_db.import_invoice_from_files(
                customer_id, "invoice-data-1-1.txt", items
            )