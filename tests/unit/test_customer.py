"""Unit tests for Customer model."""

import tempfile
import os
import pytest

from application.models import Customer
from application.db import init_db, close_db


class TestCustomerFromDict:
    """Test cases for Customer.from_dict method."""

    def test_from_dict_valid_record(self):
        """Test creating Customer from valid database record."""
        record = {
            "id": 1,
            "name": "Acme Corporation",
            "address": "123 Business Ave\nAnytown, CA 90210",
            "created_at": "2025-01-01 00:00:00"
        }
        
        customer = Customer.from_dict(record)
        
        assert customer.id == 1
        assert customer.name == "Acme Corporation"
        assert customer.address == "123 Business Ave\nAnytown, CA 90210"
        assert customer.created_at == "2025-01-01 00:00:00"

    def test_from_dict_missing_field(self):
        """Test creating Customer from record with missing field."""
        record = {
            "id": 1,
            "name": "Test Company",
            "address": "123 Test St"
            # missing created_at
        }
        
        with pytest.raises(KeyError):
            Customer.from_dict(record)

    def test_from_dict_none_values(self):
        """Test creating Customer from record with None values."""
        record = {
            "id": 1,
            "name": None,
            "address": None,
            "created_at": None
        }
        
        customer = Customer.from_dict(record)
        
        assert customer.id == 1
        assert customer.name is None
        assert customer.address is None
        assert customer.created_at is None

    def test_from_dict_empty_strings(self):
        """Test creating Customer from record with empty strings."""
        record = {
            "id": 1,
            "name": "",
            "address": "",
            "created_at": ""
        }
        
        customer = Customer.from_dict(record)
        
        assert customer.id == 1
        assert customer.name == ""
        assert customer.address == ""
        assert customer.created_at == ""


class TestCustomerCreate:
    """Test cases for Customer.create method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    def test_create_customer_valid_data(self, test_db):
        """Test creating a customer with valid data."""
        customer_id = Customer.create("Test Company", "123 Test St")
        
        assert isinstance(customer_id, int)
        assert customer_id > 0

    def test_create_customer_returns_different_ids(self, test_db):
        """Test that creating multiple customers returns different IDs."""
        id1 = Customer.create("Company 1", "123 First St")
        id2 = Customer.create("Company 2", "456 Second St")
        
        assert id1 != id2
        assert id1 > 0
        assert id2 > 0

    def test_create_customer_with_empty_name(self, test_db):
        """Test creating a customer with empty name."""
        customer_id = Customer.create("", "123 Test St")
        assert customer_id > 0

    def test_create_customer_with_empty_address(self, test_db):
        """Test creating a customer with empty address."""
        customer_id = Customer.create("Test Company", "")
        assert customer_id > 0

    def test_create_customer_with_multiline_address(self, test_db):
        """Test creating a customer with multiline address."""
        address = "123 Test St\nAnytown, CA 90210"
        customer_id = Customer.create("Test Company", address)
        assert customer_id > 0


class TestCustomerGetByName:
    """Test cases for Customer.get_by_name method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    def test_get_by_name_existing_customer(self, test_db):
        """Test getting an existing customer by name."""
        # Create a customer first
        customer_id = Customer.create("Test Company", "123 Test St")
        
        # Get the customer by name
        customer = Customer.get_by_name("Test Company")
        
        assert customer is not None
        assert customer.id == customer_id
        assert customer.name == "Test Company"
        assert customer.address == "123 Test St"
        assert customer.created_at is not None

    def test_get_by_name_nonexistent_customer(self, test_db):
        """Test getting a nonexistent customer by name."""
        customer = Customer.get_by_name("Nonexistent Company")
        assert customer is None

    def test_get_by_name_empty_string(self, test_db):
        """Test getting customer with empty string name."""
        customer = Customer.get_by_name("")
        assert customer is None

    def test_get_by_name_case_sensitive(self, test_db):
        """Test that get_by_name is case sensitive."""
        Customer.create("Test Company", "123 Test St")
        
        # Should not find with different case
        customer = Customer.get_by_name("test company")
        assert customer is None


class TestCustomerListAll:
    """Test cases for Customer.list_all method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    def test_list_all_empty_database(self, test_db):
        """Test listing all customers from empty database."""
        customers = Customer.list_all()
        assert customers == []

    def test_list_all_single_customer(self, test_db):
        """Test listing all customers with single customer."""
        Customer.create("Test Company", "123 Test St")
        
        customers = Customer.list_all()
        assert len(customers) == 1
        assert customers[0].name == "Test Company"
        assert customers[0].address == "123 Test St"

    def test_list_all_multiple_customers(self, test_db):
        """Test listing all customers with multiple customers."""
        Customer.create("Zebra Company", "999 Zoo St")
        Customer.create("Alpha Company", "111 First St")
        Customer.create("Beta Company", "222 Second St")
        
        customers = Customer.list_all()
        assert len(customers) == 3
        
        # Should be ordered by name
        assert customers[0].name == "Alpha Company"
        assert customers[1].name == "Beta Company"
        assert customers[2].name == "Zebra Company"

    def test_list_all_returns_customer_objects(self, test_db):
        """Test that list_all returns Customer objects."""
        Customer.create("Test Company", "123 Test St")
        
        customers = Customer.list_all()
        assert len(customers) == 1
        assert isinstance(customers[0], Customer)
        assert customers[0].id > 0
        assert customers[0].created_at is not None