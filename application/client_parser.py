"""Client data parsing utilities."""

import json
import os


def parse_client_data(filepath):
    """Load and validate client data from JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Client file not found: {filepath}")

    try:
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)

            # Validate required fields
            if "client" not in data:
                raise ValueError(f"Client data missing 'client' field in {filepath}")

            client = data["client"]
            if not client.get("name"):
                raise ValueError(f"Client name is required in {filepath}")
            if not client.get("address"):
                raise ValueError(f"Client address is required in {filepath}")

            return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}") from e
    except OSError as e:
        raise OSError(f"Error reading file {filepath}: {e}") from e
