"""Invoice controller for handling invoice business logic."""

from typing import Any, Dict, List, Optional

from ..invoice_parser import parse_invoice_data
from ..models import (
    Invoice,
    InvoiceDetails,
    InvoiceItem,
    LineItem,
    generate_invoice_metadata_from_filename,
    parse_date_safely,
)


class InvoiceController:
    """Controller for invoice-related business operations."""

    @staticmethod
    def create_invoice(
        customer_id: int, metadata: Dict[str, str], items: List[Dict[str, Any]]
    ) -> int:
        """Create an invoice with the given customer, metadata, and items."""
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

        # Create invoice details
        details = InvoiceDetails(
            invoice_number=metadata["invoice_number"],
            customer_id=customer_id,
            invoice_date=parse_date_safely(metadata["invoice_date"]),
            due_date=parse_date_safely(metadata["due_date"]),
            total_amount=total_amount,
        )
        invoice_id = Invoice.create(details)

        # Add items
        for item in items:
            # Convert date format from MM/DD/YYYY to YYYY-MM-DD for database
            work_date = parse_date_safely(item["date"], "%m/%d/%Y")

            amount = item["quantity"] * item["rate"]
            line_item = LineItem(
                invoice_id=invoice_id,
                work_date=work_date,
                description=item["description"],
                quantity=item["quantity"],
                rate=item["rate"],
                amount=amount,
            )
            InvoiceItem.add(line_item)

        return invoice_id

    @staticmethod
    def import_invoice_from_files(
        customer_id: int, invoice_data_file: str, items: List[Dict[str, Any]]
    ) -> int:
        """Import invoice from TSV file data."""
        try:
            # Generate invoice metadata from filename
            metadata = generate_invoice_metadata_from_filename(invoice_data_file)

            # Create the invoice
            return InvoiceController.create_invoice(customer_id, metadata, items)

        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"Error importing invoice from files: {e}") from e

    @staticmethod
    def import_invoice_from_file(customer_id: int, invoice_data_file: str) -> int:
        """Import invoice from TSV file, parsing the file data."""
        items = parse_invoice_data(invoice_data_file)
        return InvoiceController.import_invoice_from_files(
            customer_id, invoice_data_file, items
        )

    @staticmethod
    def get_invoice_data(invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get complete invoice data including customer, vendor, and items."""
        from .. import db

        connection = db.get_db_connection()
        cursor = connection.cursor()

        # Get invoice with customer and vendor data
        cursor.execute(
            """SELECT i.invoice_number, i.invoice_date, i.due_date, i.total_amount,
                      c.name as customer_name, c.address as customer_address, 
                      v.name as vendor_name, v.address as vendor_address,
                      v.email as vendor_email, v.phone as vendor_phone
               FROM invoices i
               JOIN customers c ON i.customer_id = c.id
               JOIN vendors v ON i.vendor_id = v.id
               WHERE i.id = ?""",
            (invoice_id,),
        )

        invoice_row = cursor.fetchone()
        if not invoice_row:
            return None

        # Get invoice items
        cursor.execute(
            """SELECT work_date, description, quantity, rate, amount
               FROM invoice_items
               WHERE invoice_id = ?
               ORDER BY work_date""",
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

    @staticmethod
    def list_invoices(customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List invoices, optionally filtered by customer."""
        return Invoice.list_all(customer_id)
