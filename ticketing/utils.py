import json
from pathlib import Path
from jsonschema import validate, ValidationError, Draft202012Validator
from werkzeug.exceptions import BadRequest

SCHEMA_DIR = Path(__file__).parent / "static" / "schema"

def load_schema(name: str) -> dict:
    path = SCHEMA_DIR / f"{name}_schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Schema file {path} not found")
    with open(path, "r") as f:
        return json.load(f)

def validate_json(data: dict, schema_name: str):
    schema = load_schema(schema_name)
    try:
        Draft202012Validator(schema).validate(data)
    except ValidationError as e:
        raise BadRequest(f"Invalid request: {e.message}")