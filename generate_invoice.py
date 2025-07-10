#!/usr/bin/env python3
"""Invoice generator for Havelick Software Solutions.

Generates HTML and PDF invoices from client data and tab-separated invoice data files.
Enhanced with SQLite database support for storing vendors, customers, invoices, and items.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from database import InvoiceDB, parse_date_safely, parse_date_to_display, validate_amount, calculate_due_date

# Company data (static)
COMPANY_DATA = {
    "company": {
        "name": "Havelick Software Solutions, LLC",
        "address": "7815 Robinson Way\nArvada CO 80004",
        "email": "tristan@havelick.com",
        "phone": "303-475-7244",
    }
}


def _parse_invoice_line(line):
    """Parse a single invoice data line."""
    parts = line.split("\t")
    if len(parts) < 4:
        return None

    try:
        date_str = parts[0].strip()
        quantity_str = parts[1].strip()
        amount_str = parts[2].strip()
        description = parts[3].strip()

        # Validate and parse quantity
        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                raise ValueError(f"Quantity must be positive: {quantity}")
        except ValueError as e:
            raise ValueError(f"Invalid quantity '{quantity_str}': {e}") from e

        # Validate and parse amount
        try:
            amount = validate_amount(amount_str)
        except ValueError as e:
            raise ValueError(f"Invalid amount '{amount_str}': {e}") from e

        # Calculate rate from amount and quantity
        rate = amount / quantity if quantity > 0 else 0

        # Parse and normalize date format
        try:
            # Handle both M/D/YYYY and MM/DD/YYYY formats
            if "/" in date_str:
                # Try parsing as is first
                try:
                    formatted_date = parse_date_to_display(date_str, "%m/%d/%Y")
                except ValueError:
                    # Try parsing with single digit month/day
                    month, day, year = date_str.split("/")
                    formatted_date = f"{month.zfill(2)}/{day.zfill(2)}/{year}"
                    # Validate the formatted date
                    parse_date_to_display(formatted_date, "%m/%d/%Y")
            else:
                raise ValueError(f"Invalid date format: {date_str}")
        except ValueError as e:
            raise ValueError(f"Invalid date '{date_str}': {e}") from e

        return {
            "date": formatted_date,
            "description": description,
            "quantity": quantity,
            "rate": rate,
        }
    except ValueError as e:
        raise ValueError(f"Error parsing invoice line '{line.strip()}': {e}") from e


def parse_invoice_data(filename):
    """Parse tab-separated invoice data file"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Invoice data file not found: {filename}")
    
    items = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Skip header row if it exists
            start_index = 1 if lines and "Date" in lines[0] and "Hours" in lines[0] else 0

            for line_num, line in enumerate(lines[start_index:], start=start_index + 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    item = _parse_invoice_line(line)
                    if item:
                        items.append(item)
                except ValueError as e:
                    raise ValueError(f"Error parsing line {line_num}: {e}") from e
    except IOError as e:
        raise IOError(f"Error reading file {filename}: {e}") from e
    
    if not items:
        raise ValueError(f"No valid invoice items found in {filename}")
    
    return items


def load_client_data(filepath):
    """Load and validate client data from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Client file not found: {filepath}")
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Validate required fields
            if "client" not in data:
                raise ValueError(f"Client data missing 'client' field in {filepath}")
            
            client = data["client"]
            if not client.get("name"):
                raise ValueError(f"Client name is required in {filepath}")
            if not client.get("address"):
                raise ValueError(f"Client address is required in {filepath}")
            
            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}") from e
    except IOError as e:
        raise IOError(f"Error reading file {filepath}: {e}") from e


def load_invoice_items(filepath):
    """Load invoice items from tab-separated file."""
    try:
        return parse_invoice_data(filepath)
    except (FileNotFoundError, ValueError, IOError) as e:
        raise ValueError(f"Error loading invoice items: {e}") from e


def generate_invoice_metadata(invoice_data_file):
    """Generate invoice number and dates from filename."""
    try:
        base_name = os.path.splitext(os.path.basename(invoice_data_file))[0]
        if base_name.startswith("invoice-data-"):
            date_part = base_name.replace("invoice-data-", "")
            try:
                # Convert M-D format to invoice number and dates
                month, day = date_part.split("-")
                invoice_number = f"2025.{month.zfill(2)}.{day.zfill(2)}"
                invoice_date = f"{month.zfill(2)}/{day.zfill(2)}/2025"
                # Calculate due date 30 days out
                due_date = calculate_due_date(invoice_date, 30)
            except ValueError as e:
                raise ValueError(f"Invalid filename format: {invoice_data_file}. Expected format: invoice-data-M-D.txt") from e
        else:
            # Fallback to current date
            now = datetime.now()
            invoice_number = f"2025.{now.month:02d}.{now.day:02d}"
            invoice_date = now.strftime("%m/%d/%Y")
            due_date = calculate_due_date(invoice_date, 30)

        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
        }
    except ValueError as e:
        raise ValueError(f"Error generating invoice metadata: {e}") from e


def generate_invoice_files(data, output_dir="."):
    """Generate HTML and PDF invoice files from data."""
    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("invoice_template.html")

    # Render template
    html_output = template.render(**data)

    # Create filename based on client company name and invoice date
    company_name = (
        data["client"]["name"]
        .lower()
        .replace(" ", "-")
        .replace(",", "")
        .replace(".", "")
    )
    invoice_date = data["invoice_date"].replace("/", ".")
    base_filename = f"{company_name}-invoice-{invoice_date}"

    # Create full paths using output directory
    html_filename = os.path.join(output_dir, f"{base_filename}.html")
    pdf_filename = os.path.join(output_dir, f"{base_filename}.pdf")

    # Write HTML output
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_output)

    # Generate PDF from HTML
    HTML(filename=html_filename).write_pdf(pdf_filename)

    print(
        f"Invoice generated: {html_filename} and {pdf_filename} (Total: ${data['total']:.2f})"
    )


def legacy_main(client_file, invoice_data_file, output_dir):
    """Legacy main function for backward compatibility."""
    try:
        # Initialize database
        db = InvoiceDB()
        
        # Load data using helper functions
        client_data = load_client_data(client_file)
        items = load_invoice_items(invoice_data_file)
        invoice_metadata = generate_invoice_metadata(invoice_data_file)

        # Import customer to database
        customer_id = db.import_customer_from_json(client_data)
        
        # Import invoice to database
        invoice_id = db.import_invoice_from_files(customer_id, invoice_data_file, items)

        # Combine all data
        data = {
            **COMPANY_DATA,
            **client_data,
            **invoice_metadata,
            "items": items,
            "total": sum(item["quantity"] * item["rate"] for item in items),
        }

        # Generate output files
        generate_invoice_files(data, output_dir)
    except (ValueError, FileNotFoundError, IOError) as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


def cmd_import_items(args):
    """Import invoice items from TSV file."""
    db = InvoiceDB()
    
    # Load and parse items
    items = load_invoice_items(args.file)
    
    # Need customer ID - for now, use default or prompt
    if not args.customer_id:
        print("Error: Customer ID required for import-items command")
        sys.exit(1)
    
    # Import to database
    invoice_id = db.import_invoice_from_files(args.customer_id, args.file, items)
    
    total = sum(item["quantity"] * item["rate"] for item in items)
    print(f"Imported {len(items)} items for invoice {invoice_id} (Total: ${total:.2f})")


def cmd_import_customer(args):
    """Import customer from JSON file."""
    db = InvoiceDB()
    
    # Load customer data
    client_data = load_client_data(args.file)
    
    # Import to database
    customer_id = db.import_customer_from_json(client_data)
    
    customer = db.get_customer_by_name(client_data["client"]["name"])
    print(f"Imported customer: {customer['name']} (ID: {customer_id})")


def cmd_create_customer(args):
    """Create a new customer."""
    db = InvoiceDB()
    
    customer_id = db.create_customer(args.name, args.address)
    print(f"Created customer: {args.name} (ID: {customer_id})")


def cmd_generate_invoice(args):
    """Generate invoice from database."""
    db = InvoiceDB()
    
    # Get invoice data from database
    invoice_data = db.get_invoice_data(args.invoice_id)
    
    if not invoice_data:
        print(f"Error: Invoice {args.invoice_id} not found")
        sys.exit(1)
    
    # Generate output files
    generate_invoice_files(invoice_data, args.output_dir)


def cmd_list_customers(args):
    """List all customers."""
    db = InvoiceDB()
    
    customers = db.list_customers()
    
    if not customers:
        print("No customers found")
        return
    
    print("Customers:")
    print("ID | Name")
    print("-" * 30)
    
    for customer in customers:
        print(f"{customer['id']:2d} | {customer['name']}")


def cmd_list_invoices(args):
    """List invoices."""
    db = InvoiceDB()
    
    invoices = db.list_invoices(args.customer_id)
    
    if not invoices:
        print("No invoices found")
        return
    
    print("Invoices:")
    print("ID | Invoice# | Customer | Date | Total")
    print("-" * 50)
    
    for invoice in invoices:
        print(f"{invoice['id']:2d} | {invoice['invoice_number']} | {invoice['customer_name']:<15} | {invoice['invoice_date']} | ${invoice['total_amount']:.2f}")


def cmd_one_shot(args):
    """One-shot command for legacy compatibility - import customer and invoice data, then generate files."""
    legacy_main(args.client_file, args.invoice_data_file, args.output_dir)


def main():
    """Main function with enhanced CLI support."""
    parser = argparse.ArgumentParser(
        description="Generate HTML and PDF invoices with SQLite database support"
    )
    
    # CLI mode with subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # one-shot command (replaces legacy mode)
    parser_one_shot = subparsers.add_parser("one-shot", help="One-shot invoice generation (legacy compatibility)")
    parser_one_shot.add_argument("client_file", help="Path to client JSON file")
    parser_one_shot.add_argument("invoice_data_file", help="Path to invoice data text file")
    parser_one_shot.add_argument(
        "--output-dir",
        "-o",
        default=".",
        help="Output directory for generated files (default: current directory)",
    )
    parser_one_shot.set_defaults(func=cmd_one_shot)
    
    # import-items command
    parser_import_items = subparsers.add_parser("import-items", help="Import invoice items from TSV file")
    parser_import_items.add_argument("file", help="TSV file with invoice items")
    parser_import_items.add_argument("--customer-id", type=int, required=True, help="Customer ID for the invoice")
    parser_import_items.set_defaults(func=cmd_import_items)
    
    # import-customer command
    parser_import_customer = subparsers.add_parser("import-customer", help="Import customer from JSON file")
    parser_import_customer.add_argument("file", help="JSON file with customer data")
    parser_import_customer.set_defaults(func=cmd_import_customer)
    
    # create-customer command
    parser_create_customer = subparsers.add_parser("create-customer", help="Create a new customer")
    parser_create_customer.add_argument("name", help="Customer name")
    parser_create_customer.add_argument("address", help="Customer address")
    parser_create_customer.set_defaults(func=cmd_create_customer)
    
    # generate-invoice command
    parser_generate_invoice = subparsers.add_parser("generate-invoice", help="Generate invoice from database")
    parser_generate_invoice.add_argument("invoice_id", type=int, help="Invoice ID")
    parser_generate_invoice.add_argument("--output-dir", "-o", default=".", help="Output directory for generated files")
    parser_generate_invoice.set_defaults(func=cmd_generate_invoice)
    
    # list-customers command
    parser_list_customers = subparsers.add_parser("list-customers", help="List all customers")
    parser_list_customers.set_defaults(func=cmd_list_customers)
    
    # list-invoices command
    parser_list_invoices = subparsers.add_parser("list-invoices", help="List invoices")
    parser_list_invoices.add_argument("--customer-id", type=int, help="Filter by customer ID")
    parser_list_invoices.set_defaults(func=cmd_list_invoices)
    
    args = parser.parse_args()
    
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()