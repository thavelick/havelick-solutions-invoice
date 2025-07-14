"""Unit tests for amount utility functions."""

import pytest

from application.amount_utils import validate_amount


class TestValidateAmount:
    """Test cases for validate_amount function."""

    def test_validate_basic_amounts(self):
        """Test validating basic numeric amounts."""
        assert validate_amount("150.00") == 150.0
        assert validate_amount("$150.00") == 150.0
        assert validate_amount("1200") == 1200.0
        assert validate_amount("0") == 0.0
        assert validate_amount("0.01") == 0.01

    def test_validate_amount_invalid_values(self):
        """Test validation fails for invalid amounts."""
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("abc")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("$")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("-50.00")
        with pytest.raises(ValueError, match="Invalid amount"):
            validate_amount("$-25.00")
