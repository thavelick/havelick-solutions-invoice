#!/usr/bin/env python3

import json
import os
import sys

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


def parse_invoice_data(filename):
    """Parse tab-separated invoice data file"""
    items = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 4:
                continue

            date_str = parts[0].strip()
            quantity = float(parts[1].strip())
            amount_str = parts[2].strip().replace("$", "").replace(",", "")
            description = parts[3].strip()

            # Calculate rate from amount and quantity
            amount = float(amount_str)
            rate = amount / quantity if quantity > 0 else 0

            # Convert date format from M/D/YYYY to MM/DD/YYYY
            month, day, year = date_str.split("/")
            formatted_date = f"{month.zfill(2)}/{day.zfill(2)}/{year}"

            items.append(
                {
                    "date": formatted_date,
                    "description": description,
                    "quantity": quantity,
                    "rate": rate,
                }
            )

    return items


def main():
    # Check for arguments
    if len(sys.argv) < 3:
        print("Usage: python generate_invoice.py <client_file.json> <invoice_data.txt>")
        sys.exit(1)

    client_file = sys.argv[1]
    invoice_data_file = sys.argv[2]

    # Load client data
    try:
        with open(client_file, "r", encoding="utf-8") as f:
            client_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Client file '{client_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in '{client_file}'")
        sys.exit(1)

    # Load invoice data
    try:
        items = parse_invoice_data(invoice_data_file)
    except FileNotFoundError:
        print(f"Error: Invoice data file '{invoice_data_file}' not found")
        sys.exit(1)
    except (ValueError, IndexError) as e:
        print(f"Error parsing invoice data: {e}")
        sys.exit(1)

    # Company data (static)
    company_data = {
        "company": {
            "name": "Havelick Software Solutions, LLC",
            "address": "7815 Robinson Way\nArvada CO 80004",
            "email": "tristan@havelick.com",
            "phone": "303-475-7244",
        }
    }

    # Generate invoice metadata from filename
    base_name = os.path.splitext(os.path.basename(invoice_data_file))[0]
    if base_name.startswith("invoice-data-"):
        date_part = base_name.replace("invoice-data-", "")
        # Convert M-D format to invoice number and dates
        month, day = date_part.split("-")
        invoice_number = f"2025.{month.zfill(2)}.{day.zfill(2)}"
        invoice_date = f"{month.zfill(2)}/{day.zfill(2)}/2025"
        # Due date is 30 days later (simplified)
        due_month = int(month) + 1 if int(month) < 12 else 1
        due_year = 2025 if int(month) < 12 else 2026
        due_date = f"{due_month:02d}/{day.zfill(2)}/{due_year}"
    else:
        invoice_number = "2025.XX.XX"
        invoice_date = "XX/XX/2025"
        due_date = "XX/XX/2025"

    # Combine data
    data = {
        **company_data,
        **client_data,
        "items": items,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "due_date": due_date,
    }

    # Calculate total
    total = sum(item["quantity"] * item["rate"] for item in data["items"])
    data["total"] = total

    # Setup Jinja2 environment
    env = Environment(loader=FileSystemLoader("."))
    template = env.get_template("invoice_template.html")

    # Render template
    html_output = template.render(**data)

    # Write HTML output
    with open("invoice.html", "w", encoding="utf-8") as f:
        f.write(html_output)

    # Generate PDF from HTML
    HTML(filename="invoice.html").write_pdf("invoice.pdf")

    print(f"Invoice generated: invoice.html and invoice.pdf (Total: ${total:.2f})")


if __name__ == "__main__":
    main()
