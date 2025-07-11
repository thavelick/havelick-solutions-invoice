"""Unit tests for Customer model."""

import pytest

from application.models import Customer


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