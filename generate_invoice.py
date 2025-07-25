#!/usr/bin/env python3
"""Invoice generator for Havelick Software Solutions.

Generates HTML and PDF invoices from client data and tab-separated invoice data files.
Enhanced with SQLite database support for storing vendors, customers, invoices, and
items.
"""

import argparse
import sys

from application import db
from application.client_parser import parse_client_data
from application.controllers.customer_controller import CustomerController
from application.controllers.generation_controller import GenerationController
from application.controllers.invoice_controller import InvoiceController
from application.invoice_parser import parse_invoice_data

# Company data (static)
COMPANY_DATA = {
    "company": {
        "name": "Havelick Software Solutions, LLC",
        "address": "7815 Robinson Way\nArvada CO 80004",
        "email": "tristan@havelick.com",
        "phone": "303-475-7244",
    }
}


def load_client_data(filepath):
    """Load and validate client data from JSON file."""
    try:
        return parse_client_data(filepath)
    except (OSError, FileNotFoundError, ValueError) as e:
        # Preserve the original exception type for compatibility
        raise e


def load_invoice_items(filepath):
    """Load invoice items from tab-separated file."""
    try:
        return parse_invoice_data(filepath)
    except (OSError, FileNotFoundError, ValueError) as e:
        raise ValueError(f"Error loading invoice items: {e}") from e


def legacy_main(client_file, invoice_data_file, output_dir, db_path="invoices.db"):
    """Legacy main function for backward compatibility."""
    try:
        # Initialize database
        db.init_db(db_path)

        # Load data using helper functions
        client_data = load_client_data(client_file)
        items = load_invoice_items(invoice_data_file)
        invoice_metadata = InvoiceController.generate_invoice_metadata_from_filename(
            invoice_data_file
        )

        # Import customer to database
        customer_id = CustomerController.import_customer_from_json(client_data)

        # Import invoice to database
        InvoiceController.import_invoice_from_files(
            customer_id, invoice_data_file, items
        )

        # Combine all data
        data = {
            **COMPANY_DATA,
            **client_data,
            **invoice_metadata,
            "items": items,
            "total": sum(item["quantity"] * item["rate"] for item in items),
        }

        # Generate output files
        GenerationController.generate_invoice_files(data, output_dir)
    except (OSError, ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_import_items(args):
    """Import invoice items from TSV file."""
    db.init_db(args.db_path)

    # Need customer ID - for now, use default or prompt
    if not args.customer_id:
        print("Error: Customer ID required for import-items command")
        sys.exit(1)

    # Import to database
    invoice_id = InvoiceController.import_invoice_from_file(args.customer_id, args.file)

    # Load items to calculate total for display
    items = load_invoice_items(args.file)
    total = sum(item["quantity"] * item["rate"] for item in items)
    print(f"Imported {len(items)} items for invoice {invoice_id} (Total: ${total:.2f})")


def cmd_import_customer(args):
    """Import customer from JSON file."""
    db.init_db(args.db_path)

    # Import to database
    customer_id = CustomerController.import_customer_from_file(args.file)

    # Load customer data to get name for display
    client_data = load_client_data(args.file)
    customer = CustomerController.get_customer_by_name(client_data["client"]["name"])
    if customer is None:
        raise ValueError(f"Failed to find customer: {client_data['client']['name']}")
    print(f"Imported customer: {customer.name} (ID: {customer_id})")


def cmd_create_customer(args):
    """Create a new customer."""
    db.init_db(args.db_path)

    customer_id = CustomerController.create_customer(args.name, args.address)
    print(f"Created customer: {args.name} (ID: {customer_id})")


def cmd_generate_invoice(args):
    """Generate invoice from database."""
    db.init_db(args.db_path)

    # Get invoice data from database
    invoice_data = InvoiceController.get_invoice_data(args.invoice_id)

    if not invoice_data:
        print(f"Error: Invoice {args.invoice_id} not found")
        sys.exit(1)

    # Generate output files
    GenerationController.generate_invoice_files(invoice_data, args.output_dir)


def cmd_list_customers(args):
    """List all customers."""
    db.init_db(args.db_path)

    customers = CustomerController.list_customers()

    if not customers:
        print("No customers found")
        return

    print("Customers:")
    print("ID | Name")
    print("-" * 30)

    for customer in customers:
        print(f"{customer.id:2d} | {customer.name}")


def cmd_list_invoices(args):
    """List invoices."""
    db.init_db(args.db_path)

    invoices = InvoiceController.list_invoices(args.customer_id)

    if not invoices:
        print("No invoices found")
        return

    print("Invoices:")
    print("ID | Invoice# | Customer | Date | Total")
    print("-" * 50)

    for invoice in invoices:
        print(
            f"{invoice['id']:2d} | {invoice['invoice_number']} | "
            f"{invoice['customer_name']:<15} | {invoice['invoice_date']} | "
            f"${invoice['total_amount']:.2f}"
        )


def cmd_one_shot(args):
    """One-shot command for legacy compatibility."""
    legacy_main(args.client_file, args.invoice_data_file, args.output_dir, args.db_path)


def main():
    """Main function with enhanced CLI support."""
    parser = argparse.ArgumentParser(
        description="Generate HTML and PDF invoices with SQLite database support"
    )

    # Global arguments
    parser.add_argument(
        "--db-path",
        default="invoices.db",
        help="Path to SQLite database file (default: invoices.db)",
    )

    # CLI mode with subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # one-shot command (replaces legacy mode)
    parser_one_shot = subparsers.add_parser(
        "one-shot", help="One-shot invoice generation (legacy compatibility)"
    )
    parser_one_shot.add_argument("client_file", help="Path to client JSON file")
    parser_one_shot.add_argument(
        "invoice_data_file", help="Path to invoice data text file"
    )
    parser_one_shot.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for generated files (default: current directory)",
    )
    parser_one_shot.set_defaults(func=cmd_one_shot)

    # import-items command
    parser_import_items = subparsers.add_parser(
        "import-items", help="Import invoice items from TSV file"
    )
    parser_import_items.add_argument("file", help="TSV file with invoice items")
    parser_import_items.add_argument(
        "--customer-id", type=int, required=True, help="Customer ID for the invoice"
    )
    parser_import_items.set_defaults(func=cmd_import_items)

    # import-customer command
    parser_import_customer = subparsers.add_parser(
        "import-customer", help="Import customer from JSON file"
    )
    parser_import_customer.add_argument("file", help="JSON file with customer data")
    parser_import_customer.set_defaults(func=cmd_import_customer)

    # create-customer command
    parser_create_customer = subparsers.add_parser(
        "create-customer", help="Create a new customer"
    )
    parser_create_customer.add_argument("name", help="Customer name")
    parser_create_customer.add_argument("address", help="Customer address")
    parser_create_customer.set_defaults(func=cmd_create_customer)

    # generate-invoice command
    parser_generate_invoice = subparsers.add_parser(
        "generate-invoice", help="Generate invoice from database"
    )
    parser_generate_invoice.add_argument("invoice_id", type=int, help="Invoice ID")
    parser_generate_invoice.add_argument(
        "--output-dir", "-o", default=".", help="Output directory for generated files"
    )
    parser_generate_invoice.set_defaults(func=cmd_generate_invoice)

    # list-customers command
    parser_list_customers = subparsers.add_parser(
        "list-customers", help="List all customers"
    )
    parser_list_customers.set_defaults(func=cmd_list_customers)

    # list-invoices command
    parser_list_invoices = subparsers.add_parser("list-invoices", help="List invoices")
    parser_list_invoices.add_argument(
        "--customer-id", type=int, help="Filter by customer ID"
    )
    parser_list_invoices.set_defaults(func=cmd_list_invoices)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
