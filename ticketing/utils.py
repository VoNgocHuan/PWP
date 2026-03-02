"""Utility functions for the ticketing application."""
import json
from pathlib import Path
from jsonschema import ValidationError, Draft202012Validator
from werkzeug.exceptions import BadRequest

SCHEMA_DIR = Path(__file__).parent / "static" / "schema"

def load_schema(name: str) -> dict:
    """Load a JSON schema from a file."""
    path = SCHEMA_DIR / f"{name}_schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema file {path} not found")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def validate_json(data: dict, schema_name: str):
    """Validate JSON data against a schema loaded from a file."""
    schema = load_schema(schema_name)
    try:
        Draft202012Validator(schema).validate(data)
    except ValidationError as e:
        raise BadRequest(f"Invalid request: {e.message}") from e
