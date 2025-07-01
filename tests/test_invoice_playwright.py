"""Playwright tests for invoice generator."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from playwright.sync_api import Page


def test_invoice_generation_and_content(page: Page):
    """Test that invoice generation creates HTML file with expected content."""
    
    # Get paths to test data files
    test_dir = Path(__file__).parent
    client_file = test_dir / "test-client.json"
    invoice_data_file = test_dir / "invoice-data-3-15.txt"
    
    # Run invoice generation in the project root directory
    original_cwd = os.getcwd()
    
    # Run invoice generation
    result = subprocess.run([
        "uv", "run", "python", 
        "generate_invoice.py",
        str(client_file),
        str(invoice_data_file)
    ], capture_output=True, text=True, cwd=original_cwd)
    
    # Check that command succeeded
    assert result.returncode == 0, f"Invoice generation failed: {result.stderr}\nStdout: {result.stdout}"
    
    try:
        # Find generated HTML file in the project root
        html_files = list(Path(original_cwd).glob("*.html"))
        html_files = [f for f in html_files if f.name != "invoice_template.html"]
        assert len(html_files) >= 1, f"Expected at least 1 HTML file, found {len(html_files)}: {html_files}"
        
        # Find the most recently created HTML file (should be our test file)
        generated_html = max(html_files, key=lambda f: f.stat().st_mtime)
        
        # Use playwright to open and examine the HTML file
        page.goto(f"file://{generated_html.absolute()}")
        
        # Check that the page contains "invoice" (case-insensitive)
        page_content = page.content().lower()
        assert "invoice" in page_content, "Generated HTML does not contain the word 'invoice'"
        
        # Additional checks
        assert "acme corp" in page_content, "Client name not found in generated invoice"
        assert "website development" in page_content, "Invoice item not found in generated invoice"
        
    finally:
        # Clean up - remove any test-generated files
        for html_file in Path(original_cwd).glob("acme-corp-invoice-*.html"):
            html_file.unlink()
        for pdf_file in Path(original_cwd).glob("acme-corp-invoice-*.pdf"):
            pdf_file.unlink()