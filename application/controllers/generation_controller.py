"""Generation controller for handling invoice file generation."""

import os
from importlib import resources
from typing import Any, Dict

from jinja2 import Environment
from weasyprint import HTML

from .. import templates


class GenerationController:
    """Controller for invoice generation operations."""

    @staticmethod
    def generate_invoice_files(
        data: Dict[str, Any], output_dir: str = ".", output_handler=None
    ) -> None:
        """Generate HTML and PDF invoice files from data.

        Args:
            data: Invoice data dictionary
            output_dir: Directory to write files to
            output_handler: Optional callable for handling output messages (defaults to print)
        """
        if output_handler is None:
            output_handler = print

        # Load template from package resources
        template_content = resources.read_text(templates, "invoice_template.html")

        # Setup Jinja2 environment
        env = Environment()
        template = env.from_string(template_content)

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
        invoice_date = str(data["invoice_date"]).replace("-", ".").replace("/", ".")
        base_filename = f"{company_name}-invoice-{invoice_date}"

        # Create full paths using output directory
        html_filename = os.path.join(output_dir, f"{base_filename}.html")
        pdf_filename = os.path.join(output_dir, f"{base_filename}.pdf")

        # Write HTML output
        with open(html_filename, "w", encoding="utf-8") as f:
            f.write(html_output)

        # Generate PDF from HTML
        HTML(filename=html_filename).write_pdf(pdf_filename)

        output_handler(
            f"Invoice generated: {html_filename} and {pdf_filename} (Total: ${data['total']:.2f})"
        )
