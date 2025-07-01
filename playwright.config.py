"""Playwright configuration for invoice generator tests."""

# Basic playwright configuration
PLAYWRIGHT_CONFIG = {
    "headless": True,
    "timeout": 30000,
    "viewport": {"width": 1280, "height": 720},
}
