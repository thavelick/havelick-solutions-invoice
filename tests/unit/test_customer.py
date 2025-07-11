"""Unit tests for Customer model."""

import os
import tempfile

import pytest

from application.db import close_db, init_db
from application.models import Customer


class TestCustomerFromDict:
    """Test cases for Customer.from_dict method."""

    def test_from_dict_valid_record(self):
        """Test creating Customer from valid database record."""
        record = {
            "id": 1,
            "name": "Acme Corporation",
            "address": "123 Business Ave\nAnytown, CA 90210",
            "created_at": "2025-01-01 00:00:00",
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
            "address": "123 Test St",
            # missing created_at
        }

        with pytest.raises(KeyError):
            Customer.from_dict(record)

    def test_from_dict_none_values(self):
        """Test creating Customer from record with None values."""
        record = {"id": 1, "name": None, "address": None, "created_at": None}

        customer = Customer.from_dict(record)

        assert customer.id == 1
        assert customer.name is None
        assert customer.address is None
        assert customer.created_at is None

    def test_from_dict_empty_strings(self):
        """Test creating Customer from record with empty strings."""
        record = {"id": 1, "name": "", "address": "", "created_at": ""}

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


class TestCustomerUpsert:
    """Test cases for Customer.upsert method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    def test_upsert_new_customer(self, test_db):
        """Test upserting a new customer (insert behavior)."""
        customer_id = Customer.upsert("New Company", "123 New St")

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created
        customer = Customer.get_by_name("New Company")
        assert customer is not None
        assert customer.id == customer_id
        assert customer.name == "New Company"
        assert customer.address == "123 New St"

    def test_upsert_existing_customer(self, test_db):
        """Test upserting an existing customer (update behavior)."""
        # Create initial customer
        original_id = Customer.create("Test Company", "123 Original St")

        # Upsert with new address
        upserted_id = Customer.upsert("Test Company", "456 Updated St")

        assert upserted_id == original_id

        # Verify customer was updated
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.id == original_id
        assert customer.name == "Test Company"
        assert customer.address == "456 Updated St"

    def test_upsert_preserves_original_id(self, test_db):
        """Test that upsert preserves the original customer ID."""
        # Create initial customer
        original_id = Customer.create("Test Company", "123 Original St")

        # Upsert multiple times
        id1 = Customer.upsert("Test Company", "456 First Update")
        id2 = Customer.upsert("Test Company", "789 Second Update")

        assert id1 == original_id
        assert id2 == original_id

        # Verify final state
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.id == original_id
        assert customer.address == "789 Second Update"

    def test_upsert_case_sensitive_names(self, test_db):
        """Test that upsert treats names as case sensitive."""
        # Create customer with specific case
        id1 = Customer.upsert("Test Company", "123 First St")

        # Upsert with different case - should create new customer
        id2 = Customer.upsert("test company", "456 Second St")

        assert id1 != id2

        # Verify both customers exist
        customer1 = Customer.get_by_name("Test Company")
        customer2 = Customer.get_by_name("test company")

        assert customer1 is not None
        assert customer2 is not None
        assert customer1.id != customer2.id

    def test_upsert_empty_name(self, test_db):
        """Test upsert with empty name."""
        customer_id = Customer.upsert("", "123 Test St")
        assert customer_id > 0

        # Verify customer was created
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""

    def test_upsert_empty_address(self, test_db):
        """Test upsert with empty address."""
        customer_id = Customer.upsert("Test Company", "")
        assert customer_id > 0

        # Verify customer was created
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.address == ""

    def test_upsert_multiple_customers(self, test_db):
        """Test upsert with multiple different customers."""
        # Create several customers
        id1 = Customer.upsert("Company A", "Address A")
        id2 = Customer.upsert("Company B", "Address B")
        id3 = Customer.upsert("Company C", "Address C")

        # All should be different
        assert len({id1, id2, id3}) == 3

        # Update existing customers
        updated_id1 = Customer.upsert("Company A", "New Address A")
        updated_id2 = Customer.upsert("Company B", "New Address B")

        # IDs should remain the same
        assert updated_id1 == id1
        assert updated_id2 == id2

        # Verify updates
        customer_a = Customer.get_by_name("Company A")
        customer_b = Customer.get_by_name("Company B")

        assert customer_a is not None
        assert customer_b is not None
        assert customer_a.address == "New Address A"
        assert customer_b.address == "New Address B"


class TestCustomerImportFromJson:
    """Test cases for Customer.import_from_json method."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "test.db")
            init_db(db_path)
            yield db_path
            close_db()

    def test_import_from_json_valid_data(self, test_db):
        """Test importing customer from valid JSON data."""
        json_data = {
            "client": {
                "name": "Acme Corporation",
                "address": "123 Business Ave\nAnytown, CA 90210",
            }
        }

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created
        customer = Customer.get_by_name("Acme Corporation")
        assert customer is not None
        assert customer.id == customer_id
        assert customer.name == "Acme Corporation"
        assert customer.address == "123 Business Ave\nAnytown, CA 90210"

    def test_import_from_json_empty_client_data(self, test_db):
        """Test importing customer from JSON with empty client data."""
        json_data = {"client": {}}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty strings
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""
        assert customer.address == ""

    def test_import_from_json_missing_client_key(self, test_db):
        """Test importing customer from JSON without client key."""
        json_data = {"other_data": "some value"}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty strings
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""
        assert customer.address == ""

    def test_import_from_json_missing_name(self, test_db):
        """Test importing customer from JSON without name."""
        json_data = {"client": {"address": "123 Test St"}}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty name
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""
        assert customer.address == "123 Test St"

    def test_import_from_json_missing_address(self, test_db):
        """Test importing customer from JSON without address."""
        json_data = {"client": {"name": "Test Company"}}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty address
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.name == "Test Company"
        assert customer.address == ""

    def test_import_from_json_upsert_behavior(self, test_db):
        """Test that import_from_json uses upsert behavior."""
        json_data = {"client": {"name": "Test Company", "address": "123 Original St"}}

        # First import
        customer_id1 = Customer.import_from_json(json_data)

        # Second import with same name but different address
        json_data["client"]["address"] = "456 Updated St"
        customer_id2 = Customer.import_from_json(json_data)

        # Should be the same customer ID (upsert behavior)
        assert customer_id1 == customer_id2

        # Verify customer was updated
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.id == customer_id1
        assert customer.address == "456 Updated St"

    def test_import_from_json_none_values(self, test_db):
        """Test importing customer from JSON with None values."""
        json_data = {"client": {"name": None, "address": None}}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty strings (None gets converted)
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""
        assert customer.address == ""

    def test_import_from_json_empty_dict(self, test_db):
        """Test importing customer from empty JSON dict."""
        json_data = {}

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify customer was created with empty strings
        customer = Customer.get_by_name("")
        assert customer is not None
        assert customer.name == ""
        assert customer.address == ""

    def test_import_from_json_extra_fields(self, test_db):
        """Test importing customer from JSON with extra fields."""
        json_data = {
            "client": {
                "name": "Test Company",
                "address": "123 Test St",
                "phone": "555-1234",
                "email": "test@example.com",
                "extra_field": "ignored",
            },
            "other_data": "also ignored",
        }

        customer_id = Customer.import_from_json(json_data)

        assert isinstance(customer_id, int)
        assert customer_id > 0

        # Verify only name and address were used
        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.name == "Test Company"
        assert customer.address == "123 Test St"
