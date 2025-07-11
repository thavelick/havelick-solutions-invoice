"""Unit tests for invoice parsing functions."""

import json

import pytest

from generate_invoice import (
    _parse_invoice_line,
    generate_invoice_metadata,
    load_client_data,
    load_invoice_items,
    parse_invoice_data,
)


class TestParseInvoiceLine:
    """Test cases for _parse_invoice_line function."""

    def test_parse_valid_lines(self):
        """Test parsing valid invoice lines."""
        line = "03/15/2025\t8.0\t150.00\tSoftware development work"
        result = _parse_invoice_line(line)
        
        assert result == {
            "date": "03/15/2025",
            "description": "Software development work",
            "quantity": 8.0,
            "rate": 18.75,  # 150.00 / 8.0
        }

        line = "3/5/2025\t4.0\t200.00\tConsulting services"
        result = _parse_invoice_line(line)
        
        assert result == {
            "date": "03/05/2025",
            "description": "Consulting services",
            "quantity": 4.0,
            "rate": 50.0,  # 200.00 / 4.0
        }

    def test_parse_line_insufficient_fields(self):
        """Test parsing line with insufficient fields."""
        line = "03/15/2025\t8.0\t150.00"  # Missing description
        result = _parse_invoice_line(line)
        assert result is None

    def test_parse_line_invalid_quantity(self):
        """Test parsing line with invalid quantity."""
        line = "03/15/2025\tinvalid\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid quantity 'invalid'"):
            _parse_invoice_line(line)

    def test_parse_line_invalid_quantity_values(self):
        """Test parsing line with invalid quantity values."""
        line = "03/15/2025\t-2.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

        line = "03/15/2025\t0.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Quantity must be positive"):
            _parse_invoice_line(line)

    def test_parse_line_invalid_date(self):
        """Test parsing line with invalid date."""
        line = "2025-03-15\t8.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid date format"):
            _parse_invoice_line(line)

        line = "13/45/2025\t8.0\t150.00\tSoftware development work"
        
        with pytest.raises(ValueError, match="Invalid date"):
            _parse_invoice_line(line)


class TestParseInvoiceData:
    """Test cases for parse_invoice_data function."""

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Invoice data file not found"):
            parse_invoice_data("nonexistent_file.txt")

    def test_parse_valid_file(self, tmp_path):
        """Test parsing a valid invoice data file."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("03/15/2025\t8.0\t150.00\tSoftware development work\n")

        result = parse_invoice_data(str(test_file))

        assert len(result) == 1
        assert result[0]["date"] == "03/15/2025"
        assert result[0]["description"] == "Software development work"
        assert result[0]["quantity"] == 8.0
        assert result[0]["rate"] == 18.75

    def test_parse_multiple_lines(self, tmp_path):
        """Test parsing a file with multiple lines."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text(
            "03/15/2025\t8.0\t150.00\tWork 1\n03/16/2025\t4.0\t200.00\tWork 2\n"
        )

        result = parse_invoice_data(str(test_file))

        assert len(result) == 2
        assert result[0]["description"] == "Work 1"
        assert result[1]["description"] == "Work 2"

    def test_parse_file_with_empty_lines(self, tmp_path):
        """Test parsing a file with empty lines."""
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("03/15/2025\t8.0\t150.00\tValid work\n\n\n")

        result = parse_invoice_data(str(test_file))

        assert len(result) == 1
        assert result[0]["description"] == "Valid work"


class TestLoadClientData:
    """Test cases for load_client_data function."""

    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Client file not found"):
            load_client_data("nonexistent_client.json")

    def test_load_valid_client_data(self, tmp_path):
        """Test loading valid client data."""
        client_file = tmp_path / "client.json"
        client_data = {
            "client": {
                "name": "Acme Corp",
                "address": "123 Business St\nAnytown, CA 90210",
            },
            "payment_terms": "Net 30 days",
        }
        client_file.write_text(json.dumps(client_data))

        result = load_client_data(str(client_file))

        assert result == client_data
        assert result["client"]["name"] == "Acme Corp"
        assert result["client"]["address"] == "123 Business St\nAnytown, CA 90210"
        assert result["payment_terms"] == "Net 30 days"

    def test_load_invalid_json(self, tmp_path):
        """Test loading file with invalid JSON."""
        client_file = tmp_path / "invalid.json"
        client_file.write_text("{invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_client_data(str(client_file))

    def test_load_missing_required_fields(self, tmp_path):
        """Test loading JSON missing required fields."""
        client_file = tmp_path / "missing_client.json"
        client_data = {"payment_terms": "Net 30 days"}
        client_file.write_text(json.dumps(client_data))

        with pytest.raises(ValueError, match="Client data missing 'client' field"):
            load_client_data(str(client_file))

        # Test missing client name
        client_file = tmp_path / "missing_name.json"
        client_data = {"client": {"address": "123 Business St"}}
        client_file.write_text(json.dumps(client_data))

        with pytest.raises(ValueError, match="Client name is required"):
            load_client_data(str(client_file))

        # Test missing client address
        client_file = tmp_path / "missing_address.json"
        client_data = {"client": {"name": "Acme Corp"}}
        client_file.write_text(json.dumps(client_data))

        with pytest.raises(ValueError, match="Client address is required"):
            load_client_data(str(client_file))


class TestLoadInvoiceItems:
    """Test cases for load_invoice_items function."""

    def test_load_valid_invoice_items(self, tmp_path):
        """Test loading valid invoice items."""
        test_file = tmp_path / "invoice_items.txt"
        test_file.write_text("03/15/2025\t8.0\t150.00\tSoftware development work\n")

        result = load_invoice_items(str(test_file))

        assert len(result) == 1
        assert result[0]["date"] == "03/15/2025"
        assert result[0]["description"] == "Software development work"

    def test_load_error_handling(self, tmp_path):
        """Test error handling for loading invoice items."""
        # Test nonexistent file
        with pytest.raises(ValueError, match="Error loading invoice items"):
            load_invoice_items("nonexistent_file.txt")

        # Test invalid file content
        test_file = tmp_path / "invalid_items.txt"
        test_file.write_text("03/15/2025\tinvalid_quantity\t150.00\tWork\n")

        with pytest.raises(ValueError, match="Error loading invoice items"):
            load_invoice_items(str(test_file))

        # Test empty file
        test_file = tmp_path / "empty_items.txt"
        test_file.write_text("")

        with pytest.raises(ValueError, match="Error loading invoice items"):
            load_invoice_items(str(test_file))


class TestGenerateInvoiceMetadata:
    """Test cases for generate_invoice_metadata function."""

    def test_generate_metadata_valid_filename(self):
        """Test generating metadata from valid filename."""
        result = generate_invoice_metadata("invoice-data-3-15.txt")

        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result
        assert result["invoice_number"] == "2025.03.15"

    def test_generate_metadata_invalid_filename(self):
        """Test generating metadata from invalid filename."""
        with pytest.raises(ValueError, match="Error generating invoice metadata"):
            generate_invoice_metadata("invoice-data-invalid.txt")

    def test_generate_metadata_fallback_filename(self):
        """Test generating metadata from non-standard filename."""
        result = generate_invoice_metadata("some-other-file.txt")

        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "due_date" in result