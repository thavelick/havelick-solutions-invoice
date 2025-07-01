# Havelick Solutions Invoice Generator

A Python-based invoice generator using Jinja2 templates and uv for dependency management.

## Setup

1. Install dependencies:
   ```bash
   make setup
   ```

## Usage

Generate an invoice using:
```bash
make generate CLIENT=<client-name> DATA=<invoice-data-file>
```

Example:
```bash
make generate CLIENT=acme-corp DATA=invoice-data-3-31
```

## File Structure

### Client Files (`<client-name>.json`)
Contains client information and payment terms:
```json
{
  "client": {
    "name": "Acme Corp",
    "address": "456 Business Blvd\nAnytown, CA 90210"
  },
  "payment_terms": "Net 30 days"
}
```

### Invoice Data Files (`invoice-data-<M-D>.txt`)
Tab-separated format (no header required):
```
3/15/2025	2	$250.00	Website development
3/18/2025	1.5	$187.50	Code review and testing
3/22/2025	3	$375.00	Database optimization
```

Format: `Date	Quantity	Amount	Description`

The filename format `invoice-data-<M-D>.txt` automatically generates:
- Invoice number: `2025.MM.DD`
- Invoice date: `MM/DD/2025`
- Due date: 30 days later

### Generated Output
- Creates `invoice.html` with complete invoice
- Creates `invoice.pdf` automatically using WeasyPrint
- Uses company information from `generate_invoice.py`
- Calculates totals automatically

## Make Commands

- `make setup` - Install dependencies
- `make generate CLIENT=<name> DATA=<file>` - Generate invoice
- `make update` - Update dependencies
- `make lint` - Run linters (isort, black, pyright, pylint)
- `make help` - Show available commands