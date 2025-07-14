"""Data models for invoice management system."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from . import db


# Constants
HAVELICK_SOLUTIONS_VENDOR_ID = 1


@dataclass
class InvoiceDetails:
    """Details needed to create an invoice."""

    invoice_number: str
    customer_id: int
    invoice_date: str
    due_date: str
    total_amount: float


@dataclass
class LineItem:
    """Details for an invoice line item."""

    invoice_id: int
    work_date: str
    description: str
    quantity: float
    rate: float
    amount: float


class Vendor:
    """Vendor model for managing company information."""

    def __init__(
        self, id: int, name: str, address: str, email: str, phone: str, created_at: str
    ):
        self.id = id
        self.name = name
        self.address = address
        self.email = email
        self.phone = phone
        self.created_at = created_at

    @staticmethod
    def from_dict(record) -> "Vendor":
        """Create Vendor from database record."""
        return Vendor(
            id=record["id"],
            name=record["name"],
            address=record["address"],
            email=record["email"],
            phone=record["phone"],
            created_at=record["created_at"],
        )


class Customer:
    """Customer model for managing client information."""

    def __init__(self, id: int, name: str, address: str, created_at: str):
        self.id = id
        self.name = name
        self.address = address
        self.created_at = created_at

    @staticmethod
    def from_dict(record) -> "Customer":
        """Create Customer from database record."""
        return Customer(
            id=record["id"],
            name=record["name"],
            address=record["address"],
            created_at=record["created_at"],
        )

    @staticmethod
    def create(name: str, address: str) -> int:
        """Create a new customer and return the customer ID."""
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO customers (name, address) VALUES (?, ?)", (name, address)
        )
        connection.commit()

        customer_id = cursor.lastrowid
        if customer_id is None:
            raise ValueError("Failed to create customer")
        return customer_id

    @staticmethod
    def get_by_name(name: str) -> Optional["Customer"]:
        """Get customer by name."""
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customers WHERE name = ?", (name,))
        record = cursor.fetchone()

        if record:
            return Customer.from_dict(record)
        return None

    @staticmethod
    def upsert(name: str, address: str) -> int:
        """Insert or update customer, return customer ID."""
        customer = Customer.get_by_name(name)
        if customer:
            # Update existing customer
            connection = db.get_db_connection()
            cursor = connection.cursor()
            cursor.execute(
                "UPDATE customers SET address = ? WHERE id = ?", (address, customer.id)
            )
            connection.commit()
            return customer.id

        # Create new customer
        return Customer.create(name, address)

    @staticmethod
    def list_all() -> List["Customer"]:
        """List all customers."""
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customers ORDER BY name")
        records = cursor.fetchall()

        return [Customer.from_dict(record) for record in records]


class Invoice:
    """Invoice model for managing invoice information."""

    def __init__(
        self,
        id: int,
        invoice_number: str,
        customer_id: int,
        vendor_id: int,
        invoice_date: str,
        due_date: str,
        total_amount: float,
        created_at: str,
    ):
        self.id = id
        self.invoice_number = invoice_number
        self.customer_id = customer_id
        self.vendor_id = vendor_id
        self.invoice_date = invoice_date
        self.due_date = due_date
        self.total_amount = total_amount
        self.created_at = created_at

    @staticmethod
    def from_dict(record) -> "Invoice":
        """Create Invoice from database record."""
        return Invoice(
            id=record["id"],
            invoice_number=record["invoice_number"],
            customer_id=record["customer_id"],
            vendor_id=record["vendor_id"],
            invoice_date=record["invoice_date"],
            due_date=record["due_date"],
            total_amount=record["total_amount"],
            created_at=record["created_at"],
        )

    @staticmethod
    def create(details: InvoiceDetails) -> int:
        """Create a new invoice and return the invoice ID."""
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO invoices (invoice_number, customer_id, vendor_id, 
                                   invoice_date, due_date, total_amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                details.invoice_number,
                details.customer_id,
                HAVELICK_SOLUTIONS_VENDOR_ID,
                details.invoice_date,
                details.due_date,
                details.total_amount,
            ),
        )
        connection.commit()

        invoice_id = cursor.lastrowid
        if invoice_id is None:
            raise ValueError("Failed to create invoice")
        return invoice_id

    @staticmethod
    def list_all(customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List invoices, optionally filtered by customer."""
        connection = db.get_db_connection()
        cursor = connection.cursor()

        if customer_id:
            cursor.execute(
                """SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                   FROM invoices i
                   JOIN customers c ON i.customer_id = c.id
                   WHERE i.customer_id = ?
                   ORDER BY i.invoice_date DESC""",
                (customer_id,),
            )
        else:
            cursor.execute(
                """SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                   FROM invoices i
                   JOIN customers c ON i.customer_id = c.id
                   ORDER BY i.invoice_date DESC"""
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

    @staticmethod
    def get_complete_data(invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get complete invoice data including customer, vendor, and items."""
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


class InvoiceItem:
    """Invoice item model for managing line items."""

    def __init__(
        self,
        id: int,
        invoice_id: int,
        work_date: str,
        description: str,
        quantity: float,
        rate: float,
        amount: float,
    ):
        self.id = id
        self.invoice_id = invoice_id
        self.work_date = work_date
        self.description = description
        self.quantity = quantity
        self.rate = rate
        self.amount = amount

    @staticmethod
    def from_dict(record) -> "InvoiceItem":
        """Create InvoiceItem from database record."""
        return InvoiceItem(
            id=record["id"],
            invoice_id=record["invoice_id"],
            work_date=record["work_date"],
            description=record["description"],
            quantity=record["quantity"],
            rate=record["rate"],
            amount=record["amount"],
        )

    @staticmethod
    def add(item: LineItem):
        """Add an item to an invoice."""
        connection = db.get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO invoice_items (invoice_id, work_date, description, 
                                        quantity, rate, amount)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                item.invoice_id,
                item.work_date,
                item.description,
                item.quantity,
                item.rate,
                item.amount,
            ),
        )
        connection.commit()
