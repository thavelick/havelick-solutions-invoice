"""Unit tests for customer controller functionality."""

from application.controllers.customer_controller import CustomerController
from application.models import Customer


class TestCustomerController:
    """Test cases for customer controller operations."""

    def test_create_customer(self, temp_db):
        """Test creating a new customer."""
        customer_id = CustomerController.create_customer("Test Company", "123 Test St")
        assert customer_id > 0

        customer = Customer.get_by_name("Test Company")
        assert customer is not None
        assert customer.address == "123 Test St"

    def test_import_customer_from_json(self, temp_db):
        """Test importing customer from JSON data."""
        json_data = {
            "client": {
                "name": "JSON Company",
                "address": "123 JSON St",
            }
        }

        customer_id = CustomerController.import_customer_from_json(json_data)
        assert customer_id > 0

        customer = Customer.get_by_name("JSON Company")
        assert customer is not None
        assert customer.address == "123 JSON St"

    def test_import_customer_from_file(self, temp_db, tmp_path):
        """Test importing customer from JSON file."""
        import json

        client_file = tmp_path / "test_client.json"
        client_data = {
            "client": {
                "name": "File Company",
                "address": "123 File St",
            }
        }
        client_file.write_text(json.dumps(client_data))

        customer_id = CustomerController.import_customer_from_file(str(client_file))
        assert customer_id > 0

        customer = Customer.get_by_name("File Company")
        assert customer is not None
        assert customer.address == "123 File St"

    def test_list_customers(self, temp_db):
        """Test listing all customers."""
        # Initially empty
        customers = CustomerController.list_customers()
        assert len(customers) == 0

        # Add some customers
        CustomerController.create_customer("Company A", "Address A")
        CustomerController.create_customer("Company B", "Address B")

        customers = CustomerController.list_customers()
        assert len(customers) == 2
        assert customers[0].name in ["Company A", "Company B"]
        assert customers[1].name in ["Company A", "Company B"]
