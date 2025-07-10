#!/usr/bin/env python3
"""Database operations for invoice management system."""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

# Constants
HAVELICK_SOLUTIONS_VENDOR_ID = 1


def parse_date_safely(date_str: str, date_format: str = "%m/%d/%Y") -> str:
    """Parse date string with validation and convert to YYYY-MM-DD format."""
    try:
        parsed = datetime.strptime(date_str, date_format)
        return parsed.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: {date_format}"
        ) from e


def parse_date_to_display(date_str: str, date_format: str = "%m/%d/%Y") -> str:
    """Parse date string and convert to MM/DD/YYYY format for display."""
    try:
        parsed = datetime.strptime(date_str, date_format)
        return parsed.strftime("%m/%d/%Y")
    except ValueError as e:
        raise ValueError(
            f"Invalid date format: {date_str}. Expected format: {date_format}"
        ) from e


def validate_amount(amount: str) -> float:
    """Validate and convert amount string to float."""
    try:
        # Remove currency symbols and commas
        cleaned = amount.replace("$", "").replace(",", "").strip()
        value = float(cleaned)
        if value < 0:
            raise ValueError("Amount cannot be negative")
        return value
    except ValueError as e:
        raise ValueError(f"Invalid amount: {amount}") from e


def calculate_due_date(invoice_date_str: str, days_out: int = 30) -> str:
    """Calculate due date by adding specified days to invoice date."""
    try:
        invoice_date = datetime.strptime(invoice_date_str, "%m/%d/%Y")
        due_date = invoice_date + timedelta(days=days_out)
        return due_date.strftime("%m/%d/%Y")
    except ValueError as e:
        raise ValueError(f"Invalid invoice date format: {invoice_date_str}") from e


class InvoiceDB:
    """Database operations for invoice management."""

    def __init__(self, db_path: str = "invoices.db"):
        """Initialize database connection and create tables if needed."""
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema and pre-populate vendor data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create vendors table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create customers table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create invoices table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY,
                    invoice_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    vendor_id INTEGER NOT NULL,
                    invoice_date DATE NOT NULL,
                    due_date DATE NOT NULL,
                    total_amount DECIMAL(10,2) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
                )
            """
            )

            # Create invoice_items table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS invoice_items (
                    id INTEGER PRIMARY KEY,
                    invoice_id INTEGER NOT NULL,
                    work_date DATE NOT NULL,
                    description TEXT NOT NULL,
                    quantity DECIMAL(10,2) NOT NULL,
                    rate DECIMAL(10,2) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                )
            """
            )

            # Pre-populate vendor data (Havelick Solutions)
            cursor.execute(
                """
                INSERT OR IGNORE INTO vendors (id, name, address, email, phone)
                VALUES (1, 'Havelick Software Solutions, LLC', 
                        '7815 Robinson Way\nArvada CO 80004',
                        'tristan@havelick.com', '303-475-7244')
            """
            )

            conn.commit()

    def create_customer(self, name: str, address: str) -> int:
        """Create a new customer and return the customer ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO customers (name, address)
                VALUES (?, ?)
            """,
                (name, address),
            )
            return cursor.lastrowid

    def get_customer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get customer by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, address
                FROM customers WHERE name = ?
            """,
                (name,),
            )
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1], "address": row[2]}
        return None

    def upsert_customer(self, name: str, address: str) -> int:
        """Insert or update customer, return customer ID."""
        customer = self.get_customer_by_name(name)
        if customer:
            # Update existing customer
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE customers 
                    SET address = ?
                    WHERE id = ?
                """,
                    (address, customer["id"]),
                )
            return customer["id"]
        else:
            # Create new customer
            return self.create_customer(name, address)

    def import_customer_from_json(self, json_data: Dict[str, Any]) -> int:
        """Import customer from JSON data structure."""
        client_data = json_data.get("client", {})
        name = client_data.get("name", "")
        address = client_data.get("address", "")

        return self.upsert_customer(name, address)

    def list_customers(self) -> List[Dict[str, Any]]:
        """List all customers."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, address
                FROM customers ORDER BY name
            """
            )
            return [
                {"id": row[0], "name": row[1], "address": row[2]}
                for row in cursor.fetchall()
            ]

    def create_invoice(
        self,
        invoice_number: str,
        customer_id: int,
        invoice_date: str,
        due_date: str,
        total_amount: float,
    ) -> int:
        """Create a new invoice and return the invoice ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoices (invoice_number, customer_id, vendor_id, 
                                    invoice_date, due_date, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    invoice_number,
                    customer_id,
                    HAVELICK_SOLUTIONS_VENDOR_ID,
                    invoice_date,
                    due_date,
                    total_amount,
                ),
            )
            return cursor.lastrowid

    def add_invoice_item(
        self,
        invoice_id: int,
        work_date: str,
        description: str,
        quantity: float,
        rate: float,
        amount: float,
    ):
        """Add an item to an invoice."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO invoice_items (invoice_id, work_date, description, 
                                         quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (invoice_id, work_date, description, quantity, rate, amount),
            )

    def get_invoice_data(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get complete invoice data including customer, vendor, and items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Get invoice with customer and vendor data
            cursor.execute(
                """
                SELECT i.invoice_number, i.invoice_date, i.due_date, i.total_amount,
                       c.name as customer_name, c.address as customer_address, 
                       v.name as vendor_name, v.address as vendor_address,
                       v.email as vendor_email, v.phone as vendor_phone
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                JOIN vendors v ON i.vendor_id = v.id
                WHERE i.id = ?
            """,
                (invoice_id,),
            )

            invoice_row = cursor.fetchone()
            if not invoice_row:
                return None

            # Get invoice items
            cursor.execute(
                """
                SELECT work_date, description, quantity, rate, amount
                FROM invoice_items
                WHERE invoice_id = ?
                ORDER BY work_date
            """,
                (invoice_id,),
            )

            items = [
                {
                    "date": row[0],
                    "description": row[1],
                    "quantity": row[2],
                    "rate": row[3],
                    "amount": row[4],
                }
                for row in cursor.fetchall()
            ]

            return {
                "invoice_number": invoice_row[0],
                "invoice_date": invoice_row[1],
                "due_date": invoice_row[2],
                "total": invoice_row[3],
                "company": {
                    "name": invoice_row[6],
                    "address": invoice_row[7],
                    "email": invoice_row[8],
                    "phone": invoice_row[9],
                },
                "client": {"name": invoice_row[4], "address": invoice_row[5]},
                "payment_terms": "Net 30 days",
                "items": items,
            }

    def list_invoices(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List invoices, optionally filtered by customer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if customer_id:
                cursor.execute(
                    """
                    SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    WHERE i.customer_id = ?
                    ORDER BY i.invoice_date DESC
                """,
                    (customer_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    ORDER BY i.invoice_date DESC
                """
                )

            return [
                {
                    "id": row[0],
                    "invoice_number": row[1],
                    "customer_name": row[2],
                    "invoice_date": row[3],
                    "total_amount": row[4],
                }
                for row in cursor.fetchall()
            ]

    def import_invoice_from_files(
        self, customer_id: int, invoice_data_file: str, items: List[Dict[str, Any]]
    ) -> int:
        """Import invoice from TSV file data."""

        try:
            # Generate invoice metadata from filename
            base_name = os.path.splitext(os.path.basename(invoice_data_file))[0]
            if base_name.startswith("invoice-data-"):
                date_part = base_name.replace("invoice-data-", "")
                try:
                    month, day = date_part.split("-")
                    invoice_number = f"2025.{month.zfill(2)}.{day.zfill(2)}"
                    invoice_date = f"{month.zfill(2)}/{day.zfill(2)}/2025"
                    # Calculate due date 30 days out
                    due_date = calculate_due_date(invoice_date, 30)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid filename format: {invoice_data_file}. Expected format: invoice-data-M-D.txt"
                    ) from e
            else:
                # Fallback to current date
                now = datetime.now()
                invoice_number = f"2025.{now.month:02d}.{now.day:02d}"
                invoice_date = now.strftime("%m/%d/%Y")
                due_date = calculate_due_date(invoice_date, 30)

            # Validate and calculate total
            total_amount = 0.0
            for item in items:
                if (
                    not isinstance(item.get("quantity"), (int, float))
                    or item["quantity"] <= 0
                ):
                    raise ValueError(f"Invalid quantity for item: {item}")
                if not isinstance(item.get("rate"), (int, float)) or item["rate"] < 0:
                    raise ValueError(f"Invalid rate for item: {item}")
                total_amount += item["quantity"] * item["rate"]

            # Create invoice
            invoice_id = self.create_invoice(
                invoice_number, customer_id, invoice_date, due_date, total_amount
            )

            # Add items
            for item in items:
                # Convert date format from MM/DD/YYYY to YYYY-MM-DD for database
                work_date = parse_date_safely(item["date"], "%m/%d/%Y")

                amount = item["quantity"] * item["rate"]
                self.add_invoice_item(
                    invoice_id,
                    work_date,
                    item["description"],
                    item["quantity"],
                    item["rate"],
                    amount,
                )

            return invoice_id

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Error importing invoice from files: {e}") from e
