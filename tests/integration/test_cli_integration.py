"""Integration tests for CLI commands."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIIntegration:
    """Integration tests for CLI commands using subprocess to test actual CLI
    behavior."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            yield tmp.name
        # Clean up
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    @pytest.fixture
    def sample_client_file(self):
        """Create a sample client JSON file."""
        client_data = {
            "client": {
                "name": "Test Company Inc",
                "address": "123 Test Street\nTest City, TS 12345",
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
            json.dump(client_data, tmp)
            tmp.flush()
            yield tmp.name
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    @pytest.fixture
    def sample_invoice_file(self):
        """Create a sample invoice data file."""
        invoice_data = (
            "Date\tHours\t Amt \tDescription\n"
            "3/15/2025\t8\t$1200.00\tSoftware development work\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="-data-3-15.txt", delete=False
        ) as tmp:
            tmp.write(invoice_data)
            tmp.flush()
            yield tmp.name
        if os.path.exists(tmp.name):
            os.unlink(tmp.name)

    def run_cli_command(self, args, temp_db=None):
        """Helper to run CLI commands."""
        cmd = ["python", "generate_invoice.py"]
        if temp_db:
            cmd.extend(["--db-path", temp_db])
        cmd.extend(args)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        return result

    def test_cli_help(self):
        """Test that CLI help works."""
        result = self.run_cli_command(["--help"])
        assert result.returncode == 0
        assert "Generate HTML and PDF invoices" in result.stdout

    def test_cli_no_command_shows_help(self):
        """Test that running CLI without command shows help."""
        result = self.run_cli_command([])
        assert result.returncode == 0
        assert "Available commands" in result.stdout

    def test_create_customer_command(self, temp_db):
        """Test create-customer command."""
        result = self.run_cli_command(
            ["create-customer", "Test Customer", "123 Test St\nTest City, TS 12345"],
            temp_db,
        )

        assert result.returncode == 0
        assert "Created customer: Test Customer" in result.stdout
        assert "(ID: 1)" in result.stdout

    def test_import_customer_command(self, temp_db, sample_client_file):
        """Test import-customer command."""
        result = self.run_cli_command(["import-customer", sample_client_file], temp_db)

        assert result.returncode == 0
        assert "Imported customer: Test Company Inc" in result.stdout
        assert "(ID: 1)" in result.stdout

    def test_list_customers_empty(self, temp_db):
        """Test list-customers with no customers."""
        result = self.run_cli_command(["list-customers"], temp_db)

        assert result.returncode == 0
        assert "No customers found" in result.stdout

    def test_list_customers_with_data(self, temp_db):
        """Test list-customers with existing customers."""
        # First create a customer
        self.run_cli_command(
            ["create-customer", "Test Customer", "123 Test St"], temp_db
        )

        # Then list customers
        result = self.run_cli_command(["list-customers"], temp_db)

        assert result.returncode == 0
        assert "Customers:" in result.stdout
        assert "Test Customer" in result.stdout

    def test_import_items_command(self, temp_db, sample_invoice_file):
        """Test import-items command."""
        # First create a customer
        self.run_cli_command(
            ["create-customer", "Test Customer", "123 Test St"], temp_db
        )

        # Then import items
        result = self.run_cli_command(
            ["import-items", sample_invoice_file, "--customer-id", "1"], temp_db
        )

        assert result.returncode == 0
        assert "Imported 1 items for invoice" in result.stdout
        assert "Total: $1200.00" in result.stdout

    def test_import_items_missing_customer_id(self, temp_db, sample_invoice_file):
        """Test import-items command without customer ID."""
        result = self.run_cli_command(["import-items", sample_invoice_file], temp_db)

        assert result.returncode == 2
        assert "the following arguments are required: --customer-id" in result.stderr

    def test_list_invoices_empty(self, temp_db):
        """Test list-invoices with no invoices."""
        result = self.run_cli_command(["list-invoices"], temp_db)

        assert result.returncode == 0
        assert "No invoices found" in result.stdout

    def test_list_invoices_with_data(self, temp_db, sample_invoice_file):
        """Test list-invoices with existing invoices."""
        # Create customer and import items
        self.run_cli_command(
            ["create-customer", "Test Customer", "123 Test St"], temp_db
        )

        self.run_cli_command(
            ["import-items", sample_invoice_file, "--customer-id", "1"], temp_db
        )

        # List invoices
        result = self.run_cli_command(["list-invoices"], temp_db)

        assert result.returncode == 0
        assert "Invoices:" in result.stdout
        assert "Test Customer" in result.stdout

    def test_generate_invoice_command(self, temp_db, sample_invoice_file):
        """Test generate-invoice command."""
        # Setup: create customer and import items
        self.run_cli_command(
            ["create-customer", "Test Customer", "123 Test St"], temp_db
        )

        self.run_cli_command(
            ["import-items", sample_invoice_file, "--customer-id", "1"], temp_db
        )

        # Generate invoice with temp output directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli_command(
                ["generate-invoice", "1", "--output-dir", temp_dir], temp_db
            )

            assert result.returncode == 0
            # Check that files were generated
            output_files = list(Path(temp_dir).glob("*.html"))
            assert len(output_files) > 0

    def test_generate_invoice_not_found(self, temp_db):
        """Test generate-invoice with non-existent invoice ID."""
        result = self.run_cli_command(["generate-invoice", "999"], temp_db)

        assert result.returncode == 1
        assert "Error: Invoice 999 not found" in result.stdout

    def test_one_shot_command(self, temp_db, sample_client_file, sample_invoice_file):
        """Test one-shot command for legacy compatibility."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli_command(
                [
                    "one-shot",
                    sample_client_file,
                    sample_invoice_file,
                    "--output-dir",
                    temp_dir,
                ],
                temp_db,
            )

            assert result.returncode == 0
            # Check that files were generated
            output_files = list(Path(temp_dir).glob("*.html"))
            assert len(output_files) > 0

    def test_one_shot_invalid_client_file(self, temp_db, sample_invoice_file):
        """Test one-shot command with invalid client file."""
        result = self.run_cli_command(
            ["one-shot", "nonexistent.json", sample_invoice_file], temp_db
        )

        assert result.returncode == 1
        assert "Error:" in result.stdout

    def test_database_persistence(self, temp_db):
        """Test that database operations persist across command calls."""
        # Create a customer
        result1 = self.run_cli_command(
            ["create-customer", "Persistent Customer", "456 Persist Ave"], temp_db
        )
        assert result1.returncode == 0

        # Verify customer exists in a separate command call
        result2 = self.run_cli_command(["list-customers"], temp_db)
        assert result2.returncode == 0
        assert "Persistent Customer" in result2.stdout

    def test_customer_id_filtering_invoices(self, temp_db, sample_invoice_file):
        """Test filtering invoices by customer ID."""
        # Create two customers
        self.run_cli_command(
            ["create-customer", "Customer One", "111 First St"], temp_db
        )

        self.run_cli_command(
            ["create-customer", "Customer Two", "222 Second St"], temp_db
        )

        # Import items for first customer
        self.run_cli_command(
            ["import-items", sample_invoice_file, "--customer-id", "1"], temp_db
        )

        # List invoices filtered by customer ID
        result = self.run_cli_command(["list-invoices", "--customer-id", "1"], temp_db)

        assert result.returncode == 0
        assert "Customer One" in result.stdout
        assert "Customer Two" not in result.stdout

    def test_error_handling_invalid_subcommand(self, temp_db):
        """Test error handling for invalid subcommands."""
        result = self.run_cli_command(["invalid-command"], temp_db)

        # Should show help when invalid command is used
        assert result.returncode != 0 or "Available commands" in result.stdout
