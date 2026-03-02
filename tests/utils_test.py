import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from werkzeug.exceptions import BadRequest
from ticketing.utils import load_schema, validate_json


def test_load_schema_success():
    schema = load_schema("user")
    assert schema["title"] == "User"
    assert schema["type"] == "object"


def test_load_schema_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema("does_not_exist")


def test_validate_json_accepts_valid_user():
    validate_json({"name": "Jane Doe", "email": "jane@example.com"}, "user")


def test_validate_json_rejects_missing_required_field():
    with pytest.raises(BadRequest):
        validate_json({"name": "Jane Doe"}, "user")


def test_validate_json_rejects_additional_properties():
    with pytest.raises(BadRequest):
        validate_json(
            {"name": "Jane Doe", "email": "jane@example.com", "extra": "nope"},
            "user",
        )
