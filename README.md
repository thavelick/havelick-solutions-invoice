# Havelick Solutions Invoice Manager

A Python-based invoice management system with both CLI and web interfaces, using Jinja2 templates and uv for dependency management.

## Setup

1. Install dependencies:
   ```bash
   make setup
   ```

## Usage

### CLI Interface

Generate an invoice using:
```bash
make generate CLIENT=<client-name> DATA=<invoice-data-file>
```

Example:
```bash
make generate CLIENT=acme-corp DATA=invoice-data-3-31
```

### Web Interface

Start the web development server:
```bash
make dev
```

Then visit http://localhost:5000 to access the dashboard with:
- Recent invoices display
- Navigation for future features
- Health check at http://localhost:5000/status

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
Tab-separated format with optional header:
```
Date	Hours	 Amt 	Description
3/15/2025	2	$250.00	Website development
3/18/2025	1.5	$187.50	Code review and testing
3/22/2025	3	$375.00	Database optimization
```

Format: `Date	Quantity	Amount	Description`

Note: Header row is optional and will be automatically skipped if detected.

The filename format `invoice-data-<M-D>.txt` automatically generates:
- Invoice number: `2025.MM.DD`
- Invoice date: `MM/DD/2025`
- Due date: 30 days later

### Generated Output
- Creates `<client-name>-invoice-<MM.DD.YYYY>.html` with complete invoice
- Creates `<client-name>-invoice-<MM.DD.YYYY>.pdf` automatically using WeasyPrint
- Uses company information from `generate_invoice.py`
- Calculates totals automatically

## Make Commands

- `make setup` - Install dependencies
- `make generate CLIENT=<name> DATA=<file>` - Generate invoice (CLI)
- `make dev` - Start Flask web development server
- `make update` - Update dependencies
- `make lint` - Run linters (ruff, pyright, pylint)
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-integration` - Run integration tests only
- `make test-dist` - Run tests distributed across CPU cores (faster)
- `make test-with-coverage` - Run tests with coverage reporting
- `make help` - Show available commands

## Dependencies

Core dependencies:
- **Flask** - Web framework for dashboard interface
- **Jinja2** - Template engine for both CLI and web
- **WeasyPrint** - PDF generation
- **uv** - Python package manager

Development dependencies include pytest, pylint, pyright, ruff, and playwright for testing.