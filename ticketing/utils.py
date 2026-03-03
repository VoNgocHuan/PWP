"""Utility functions for the ticketing application."""
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter

from . import db
from .models import User, Event, Ticket, Order

# SCHEMA_DIR = Path(__file__).parent / "static" / "schema"

# def load_schema(name: str) -> dict:
#     """Load a JSON schema from a file."""
#     path = SCHEMA_DIR / f"{name}_schema.json"
#     if not path.exists():
#         raise FileNotFoundError(f"Schema file {path} not found")
#     with open(path, encoding="utf-8") as f:
#         return json.load(f)

# def validate_json(data: dict, schema_name: str):
#     """Validate JSON data against a schema loaded from a file."""
#     schema = load_schema(schema_name)
#     try:
#         Draft202012Validator(schema).validate(data)
#     except ValidationError as e:
#         raise BadRequest(f"Invalid request: {e.message}") from e

class UserConverter(BaseConverter):
    def to_python(self, value):
        user = db.session.get(User, value)
        if user is None:
            raise NotFound
        return user

    def to_url(self, value):
        return str(value.id)


class EventConverter(BaseConverter):
    def to_python(self, value):
        event = db.session.get(Event, value)
        if event is None:
            raise NotFound
        return event

    def to_url(self, value):
        return str(value.id)


class TicketConverter(BaseConverter):
    def to_python(self, value):
        ticket = db.session.get(Ticket, value)
        if ticket is None:
            raise NotFound
        return ticket

    def to_url(self, value):
        return str(value.id)


class OrderConverter(BaseConverter):
    def to_python(self, value):
        order = db.session.get(Order, value)
        if order is None:
            raise NotFound
        return order

    def to_url(self, value):
        return str(value.id)