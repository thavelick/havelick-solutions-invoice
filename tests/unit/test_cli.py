"""Unit tests for CLI wrapper functions."""

import json

import pytest

from application.controllers.invoice_controller import InvoiceController
from generate_invoice import (
    load_client_data,
    load_invoice_items,
)


class TestLoadInvoiceItems:
    """Test cases for load_invoice_items function."""

    def test_load_valid_invoice_items(self, tmp_path):
        """Test loading valid invoice items."""
        test_file = tmp_path / "test_invoice.txt"
        test_file.write_text("03/15/2025\t8.0\t150.00\tSoftware development work\n")

        result = load_invoice_items(str(test_file))

        assert len(result) == 1
        assert result[0]["date"] == "03/15/2025"
        assert result[0]["quantity"] == 8.0

    def test_load_error_handling(self, tmp_path):
        """Test error handling in load_invoice_items."""
        # Test with invalid file
        test_file = tmp_path / "invalid.txt"
        test_file.write_text("invalid\tdata\n")

        with pytest.raises(ValueError, match="Error loading invoice items"):
            load_invoice_items(str(test_file))


class TestLoadClientData:
    """Test cases for load_client_data function."""

    def test_load_valid_client_data(self, tmp_path):
        """Test loading valid client data."""
        client_file = tmp_path / "test_client.json"
        client_data = {
            "client": {
                "name": "Test Company",
                "address": "123 Test St\nTest City, TS 12345",
            }
        }
        client_file.write_text(json.dumps(client_data))

        result = load_client_data(str(client_file))

        assert result == client_data
        assert result["client"]["name"] == "Test Company"

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Client file not found"):
            load_client_data("nonexistent_client.json")


class TestGenerateInvoiceMetadata:
    """Test cases for generate_invoice_metadata_from_filename function."""

    def test_generate_metadata_valid_filename(self):
        """Test metadata generation from valid filenames."""
        result = InvoiceController.generate_invoice_metadata_from_filename(
            "invoice-data-3-15.txt"
        )
        assert result["invoice_number"] == "2025.03.15"
        assert result["invoice_date"] == "03/15/2025"
        assert "due_date" in result

        result = InvoiceController.generate_invoice_metadata_from_filename(
            "invoice-data-12-31.txt"
        )
        assert result["invoice_number"] == "2025.12.31"
        assert result["invoice_date"] == "12/31/2025"

    def test_generate_metadata_invalid_filename(self):
        """Test metadata generation from invalid filename format."""
        # This should still work but use fallback logic
        result = InvoiceController.generate_invoice_metadata_from_filename(
            "invalid-filename.txt"
        )
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result

    def test_generate_metadata_fallback_filename(self):
        """Test metadata generation with fallback for non-standard filenames."""
        result = InvoiceController.generate_invoice_metadata_from_filename(
            "some-other-file.txt"
        )
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result
