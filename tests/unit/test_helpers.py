"""Shared test helpers to reduce redundancy across test files."""

from typing import Any, Dict, Type

import pytest


def check_from_dict_method(
    model_class: Type, valid_record: Dict[str, Any], required_fields: list
):
    """
    Generic test helper for from_dict() methods.

    Args:
        model_class: The model class to test
        valid_record: A valid record dictionary
        required_fields: List of required field names
    """
    # Test valid record
    instance = model_class.from_dict(valid_record)
    for field, value in valid_record.items():
        assert getattr(instance, field) == value

    # Test missing field
    for field in required_fields:
        incomplete_record = valid_record.copy()
        del incomplete_record[field]
        with pytest.raises(KeyError):
            model_class.from_dict(incomplete_record)

    # Test None values
    none_record: Dict[str, Any] = {field: None for field in valid_record.keys()}
    none_record["id"] = 1  # Keep ID as valid
    none_instance = model_class.from_dict(none_record)
    for field, value in none_record.items():
        assert getattr(none_instance, field) == value
