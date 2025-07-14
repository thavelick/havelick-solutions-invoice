"""Customer controller for handling customer business logic."""

from typing import Any, Dict, List

from ..client_parser import parse_client_data
from ..models import Customer


class CustomerController:
    """Controller for customer-related business operations."""

    @staticmethod
    def create_customer(name: str, address: str) -> int:
        """Create a new customer and return the customer ID."""
        return Customer.create(name, address)

    @staticmethod
    def import_customer_from_json(json_data: Dict[str, Any]) -> int:
        """Import customer from JSON data structure."""
        client_data = json_data.get("client", {})
        name = client_data.get("name", "") or ""
        address = client_data.get("address", "") or ""

        return Customer.upsert(name, address)

    @staticmethod
    def import_customer_from_file(filepath: str) -> int:
        """Import customer from JSON file."""
        json_data = parse_client_data(filepath)
        return CustomerController.import_customer_from_json(json_data)

    @staticmethod
    def list_customers() -> List[Customer]:
        """List all customers."""
        return Customer.list_all()
