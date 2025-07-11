"""Unit tests for Vendor model."""

import pytest

from application.models import Vendor


class TestVendorFromDict:
    """Test cases for Vendor.from_dict method."""

    def test_from_dict_valid_record(self):
        """Test creating Vendor from valid database record."""
        record = {
            "id": 1,
            "name": "Havelick Software Solutions, LLC",
            "address": "7815 Robinson Way\nArvada CO 80004",
            "email": "tristan@havelick.com",
            "phone": "303-475-7244",
            "created_at": "2025-01-01 00:00:00",
        }

        vendor = Vendor.from_dict(record)

        assert vendor.id == 1
        assert vendor.name == "Havelick Software Solutions, LLC"
        assert vendor.address == "7815 Robinson Way\nArvada CO 80004"
        assert vendor.email == "tristan@havelick.com"
        assert vendor.phone == "303-475-7244"
        assert vendor.created_at == "2025-01-01 00:00:00"

    def test_from_dict_missing_field(self):
        """Test creating Vendor from record with missing field."""
        record = {
            "id": 1,
            "name": "Test Company",
            "address": "123 Test St",
            "email": "test@example.com",
            "phone": "555-1234",
            # missing created_at
        }

        with pytest.raises(KeyError):
            Vendor.from_dict(record)

    def test_from_dict_none_values(self):
        """Test creating Vendor from record with None values."""
        record = {
            "id": 1,
            "name": None,
            "address": None,
            "email": None,
            "phone": None,
            "created_at": None,
        }

        vendor = Vendor.from_dict(record)

        assert vendor.id == 1
        assert vendor.name is None
        assert vendor.address is None
        assert vendor.email is None
        assert vendor.phone is None
        assert vendor.created_at is None

    def test_from_dict_empty_strings(self):
        """Test creating Vendor from record with empty strings."""
        record = {
            "id": 1,
            "name": "",
            "address": "",
            "email": "",
            "phone": "",
            "created_at": "",
        }

        vendor = Vendor.from_dict(record)

        assert vendor.id == 1
        assert vendor.name == ""
        assert vendor.address == ""
        assert vendor.email == ""
        assert vendor.phone == ""
        assert vendor.created_at == ""
