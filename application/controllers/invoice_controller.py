"""Invoice controller for handling invoice business logic."""

from typing import Any, Dict, List, Optional

from ..invoice_parser import parse_invoice_data
from ..models import (
    Invoice,
    InvoiceDetails,
    InvoiceItem,
    LineItem,
)
from ..date_utils import calculate_due_date, parse_date_safely


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
            metadata = InvoiceController.generate_invoice_metadata_from_filename(
                invoice_data_file
            )

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
        return Invoice.get_complete_data(invoice_id)

    @staticmethod
    def list_invoices(customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List invoices, optionally filtered by customer."""
        return Invoice.list_all(customer_id)

    @staticmethod
    def generate_invoice_metadata_from_filename(
        invoice_data_file: str,
    ) -> Dict[str, str]:
        """Generate invoice number and dates from filename."""
        import os
        from datetime import datetime

        try:
            # Generate invoice metadata from filename
            base_name = os.path.splitext(os.path.basename(invoice_data_file))[0]
            current_year = datetime.now().year
            if base_name.startswith("invoice-data-"):
                date_part = base_name.replace("invoice-data-", "")
                try:
                    month, day = date_part.split("-")
                    invoice_number = f"{current_year}.{month.zfill(2)}.{day.zfill(2)}"
                    invoice_date = f"{month.zfill(2)}/{day.zfill(2)}/{current_year}"
                    # Calculate due date 30 days out
                    due_date = calculate_due_date(invoice_date, 30)
                except ValueError as e:
                    raise ValueError(
                        f"Invalid filename format: {invoice_data_file}. "
                        f"Expected format: invoice-data-M-D.txt"
                    ) from e
            else:
                # Fallback to current date
                now = datetime.now()
                invoice_number = f"{now.year}.{now.month:02d}.{now.day:02d}"
                invoice_date = now.strftime("%m/%d/%Y")
                due_date = calculate_due_date(invoice_date, 30)

            return {
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "due_date": due_date,
            }
        except (ValueError, IndexError) as e:
            raise ValueError(f"Error generating invoice metadata: {e}") from e
