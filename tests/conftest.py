"""Pytest configuration and fixtures for invoice generator tests."""

import pytest


@pytest.fixture(scope="session")
def playwright_config():
    """Configure playwright for tests."""
    return {
        "headless": True,
        "timeout": 30000,
    }