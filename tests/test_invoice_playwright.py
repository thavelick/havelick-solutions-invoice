"""Playwright tests for invoice generator."""

import pytest
from playwright.sync_api import Page


@pytest.mark.integration
def test_invoice_generation_and_content(
    tmp_path, test_data_files, invoice_generator, page: Page
):
    """Test that invoice generation creates HTML file with expected content."""
    result, html_file, pdf_file = invoice_generator(
        test_data_files["client"], test_data_files["invoice_data"], tmp_path
    )

    assert (
        result.returncode == 0
    ), f"Invoice generation failed: {result.stderr}\nStdout: {result.stdout}"

    assert html_file.exists(), f"Expected HTML file not found: {html_file}"
    assert pdf_file.exists(), f"Expected PDF file not found: {pdf_file}"

    page.goto(f"file://{html_file.absolute()}")

    page_content = page.content().lower()
    assert (
        "invoice" in page_content
    ), "Generated HTML does not contain the word 'invoice'"

    assert "acme corp" in page_content, "Client name not found in generated invoice"
    assert (
        "software development work" in page_content
    ), "Invoice item not found in generated invoice"
