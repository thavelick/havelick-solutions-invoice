"""Unit tests for client parser functions."""

import json

import pytest

from application.client_parser import parse_client_data


class TestParseClientData:
    """Test cases for parse_client_data function."""

    def test_parse_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Client file not found"):
            parse_client_data("nonexistent_client.json")

    def test_parse_valid_client_data(self, tmp_path):
        """Test loading valid client data."""
        client_file = tmp_path / "test_client.json"
        client_data = {
            "client": {
                "name": "Test Company",
                "address": "123 Test St\nTest City, TS 12345",
            }
        }
        client_file.write_text(json.dumps(client_data))

        result = parse_client_data(str(client_file))

        assert result == client_data
        assert result["client"]["name"] == "Test Company"
        assert "Test City" in result["client"]["address"]

    def test_parse_invalid_json(self, tmp_path):
        """Test loading invalid JSON."""
        client_file = tmp_path / "invalid.json"
        client_file.write_text("{ invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_client_data(str(client_file))

    def test_parse_missing_required_fields(self, tmp_path):
        """Test loading client data missing required fields."""
        client_file = tmp_path / "incomplete.json"

        # Missing 'client' field
        client_file.write_text(json.dumps({"other": "data"}))
        with pytest.raises(ValueError, match="Client data missing 'client' field"):
            parse_client_data(str(client_file))

        # Missing 'name' field
        client_data = {"client": {"address": "123 Test St"}}
        client_file.write_text(json.dumps(client_data))
        with pytest.raises(ValueError, match="Client name is required"):
            parse_client_data(str(client_file))

        # Missing 'address' field
        client_data = {"client": {"name": "Test Company"}}
        client_file.write_text(json.dumps(client_data))
        with pytest.raises(ValueError, match="Client address is required"):
            parse_client_data(str(client_file))
