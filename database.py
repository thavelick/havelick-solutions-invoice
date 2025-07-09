#!/usr/bin/env python3
"""Database operations for invoice management system."""

import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any


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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vendors (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create customers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    address TEXT NOT NULL,
                    payment_terms TEXT DEFAULT 'Net 30 days',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create invoices table
            cursor.execute("""
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
            """)
            
            # Create invoice_items table
            cursor.execute("""
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
            """)
            
            # Pre-populate vendor data (Havelick Solutions)
            cursor.execute("""
                INSERT OR IGNORE INTO vendors (id, name, address, email, phone)
                VALUES (1, 'Havelick Software Solutions, LLC', 
                        '7815 Robinson Way\nArvada CO 80004',
                        'tristan@havelick.com', '303-475-7244')
            """)
            
            conn.commit()
    
    def create_customer(self, name: str, address: str, payment_terms: str = "Net 30 days") -> int:
        """Create a new customer and return the customer ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO customers (name, address, payment_terms)
                VALUES (?, ?, ?)
            """, (name, address, payment_terms))
            return cursor.lastrowid
    
    def get_customer_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get customer by name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, address, payment_terms
                FROM customers WHERE name = ?
            """, (name,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "name": row[1],
                    "address": row[2],
                    "payment_terms": row[3]
                }
        return None
    
    def upsert_customer(self, name: str, address: str, payment_terms: str = "Net 30 days") -> int:
        """Insert or update customer, return customer ID."""
        customer = self.get_customer_by_name(name)
        if customer:
            # Update existing customer
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE customers 
                    SET address = ?, payment_terms = ?
                    WHERE id = ?
                """, (address, payment_terms, customer["id"]))
            return customer["id"]
        else:
            # Create new customer
            return self.create_customer(name, address, payment_terms)
    
    def import_customer_from_json(self, json_data: Dict[str, Any]) -> int:
        """Import customer from JSON data structure."""
        client_data = json_data.get("client", {})
        name = client_data.get("name", "")
        address = client_data.get("address", "")
        payment_terms = json_data.get("payment_terms", "Net 30 days")
        
        return self.upsert_customer(name, address, payment_terms)
    
    def list_customers(self) -> List[Dict[str, Any]]:
        """List all customers."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, address, payment_terms
                FROM customers ORDER BY name
            """)
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "address": row[2],
                    "payment_terms": row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def create_invoice(self, invoice_number: str, customer_id: int, 
                      invoice_date: str, due_date: str, total_amount: float) -> int:
        """Create a new invoice and return the invoice ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoices (invoice_number, customer_id, vendor_id, 
                                    invoice_date, due_date, total_amount)
                VALUES (?, ?, 1, ?, ?, ?)
            """, (invoice_number, customer_id, invoice_date, due_date, total_amount))
            return cursor.lastrowid
    
    def add_invoice_item(self, invoice_id: int, work_date: str, description: str,
                        quantity: float, rate: float, amount: float):
        """Add an item to an invoice."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO invoice_items (invoice_id, work_date, description, 
                                         quantity, rate, amount)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, work_date, description, quantity, rate, amount))
    
    def get_invoice_data(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get complete invoice data including customer, vendor, and items."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get invoice with customer and vendor data
            cursor.execute("""
                SELECT i.invoice_number, i.invoice_date, i.due_date, i.total_amount,
                       c.name as customer_name, c.address as customer_address, 
                       c.payment_terms,
                       v.name as vendor_name, v.address as vendor_address,
                       v.email as vendor_email, v.phone as vendor_phone
                FROM invoices i
                JOIN customers c ON i.customer_id = c.id
                JOIN vendors v ON i.vendor_id = v.id
                WHERE i.id = ?
            """, (invoice_id,))
            
            invoice_row = cursor.fetchone()
            if not invoice_row:
                return None
            
            # Get invoice items
            cursor.execute("""
                SELECT work_date, description, quantity, rate, amount
                FROM invoice_items
                WHERE invoice_id = ?
                ORDER BY work_date
            """, (invoice_id,))
            
            items = [
                {
                    "date": row[0],
                    "description": row[1],
                    "quantity": row[2],
                    "rate": row[3],
                    "amount": row[4]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                "invoice_number": invoice_row[0],
                "invoice_date": invoice_row[1],
                "due_date": invoice_row[2],
                "total": invoice_row[3],
                "company": {
                    "name": invoice_row[7],
                    "address": invoice_row[8],
                    "email": invoice_row[9],
                    "phone": invoice_row[10]
                },
                "client": {
                    "name": invoice_row[4],
                    "address": invoice_row[5]
                },
                "payment_terms": invoice_row[6],
                "items": items
            }
    
    def list_invoices(self, customer_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List invoices, optionally filtered by customer."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if customer_id:
                cursor.execute("""
                    SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    WHERE i.customer_id = ?
                    ORDER BY i.invoice_date DESC
                """, (customer_id,))
            else:
                cursor.execute("""
                    SELECT i.id, i.invoice_number, c.name, i.invoice_date, i.total_amount
                    FROM invoices i
                    JOIN customers c ON i.customer_id = c.id
                    ORDER BY i.invoice_date DESC
                """)
            
            return [
                {
                    "id": row[0],
                    "invoice_number": row[1],
                    "customer_name": row[2],
                    "invoice_date": row[3],
                    "total_amount": row[4]
                }
                for row in cursor.fetchall()
            ]
    
    def import_invoice_from_files(self, customer_id: int, invoice_data_file: str, 
                                 items: List[Dict[str, Any]]) -> int:
        """Import invoice from TSV file data."""
        
        # Generate invoice metadata from filename
        base_name = os.path.splitext(os.path.basename(invoice_data_file))[0]
        if base_name.startswith("invoice-data-"):
            date_part = base_name.replace("invoice-data-", "")
            month, day = date_part.split("-")
            invoice_number = f"2025.{month.zfill(2)}.{day.zfill(2)}"
            invoice_date = f"{month.zfill(2)}/{day.zfill(2)}/2025"
            # Due date is 30 days later (simplified)
            due_month = int(month) + 1 if int(month) < 12 else 1
            due_year = 2025 if int(month) < 12 else 2026
            due_date = f"{due_month:02d}/{day.zfill(2)}/{due_year}"
        else:
            invoice_number = f"2025.{datetime.now().month:02d}.{datetime.now().day:02d}"
            invoice_date = datetime.now().strftime("%m/%d/%Y")
            due_date = datetime.now().strftime("%m/%d/%Y")
        
        # Calculate total
        total_amount = sum(item["quantity"] * item["rate"] for item in items)
        
        # Create invoice
        invoice_id = self.create_invoice(invoice_number, customer_id, 
                                       invoice_date, due_date, total_amount)
        
        # Add items
        for item in items:
            # Convert date format from MM/DD/YYYY to YYYY-MM-DD for database
            date_parts = item["date"].split("/")
            work_date = f"{date_parts[2]}-{date_parts[0]}-{date_parts[1]}"
            
            amount = item["quantity"] * item["rate"]
            self.add_invoice_item(invoice_id, work_date, item["description"],
                                item["quantity"], item["rate"], amount)
        
        return invoice_id