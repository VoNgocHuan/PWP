"""Data models for the ticketing system."""
import click
from datetime import datetime
from sqlalchemy.engine import Engine
from flask.cli import with_appcontext
from sqlalchemy import event
from werkzeug.security import generate_password_hash, check_password_hash

from . import db

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints in SQLite,
     which are disabled by default."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class User(db.Model):
    """Users represent a person who can purchase tickets."""
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('active','disabled')",
            name="ck_users_status",
        ),
        db.CheckConstraint(
            "name LIKE '% %'", 
            name="ck_users_name_format"
        ),   
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False,server_default=db.func.now())
    orders = db.relationship("Order",
                            cascade="all, delete-orphan",
                            back_populates="user",
                            passive_deletes=False,
                            order_by="Order.created_at")

    def __repr__(self):
        return f"<User {self.email} ({self.id}, {self.status})>"

    def serialize(self):
        """Serialize user to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

    def deserialize(self, doc):
        """Deserialize user data from a dictionary."""
        self.name = doc["name"]
        self.email = doc["email"]
        if "password" in doc:
            self.set_password(doc["password"])
        self.status = doc.get("status", "active")

    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def json_schema():
        """JSON schema for user creation and update."""
        return {
            "type": "object",
            "required": ["name", "email", "password"],
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"},
                "password": {"type": "string", "minLength": 6},
                "status": {
                    "type": "string",
                    "enum": ["active", "disabled"]
                }
            }
        }

class Event(db.Model):
    """Events represent a specific event with a title, venue, 
    city, description, start and end time, and status."""
    __tablename__ = "events"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('active','cancelled')",
            name="ck_events_status",
        ),
        db.CheckConstraint(
            "ends_at IS NULL OR starts_at < ends_at",
            name="ck_events_time_valid"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    venue = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    starts_at = db.Column(db.DateTime, nullable=False)
    ends_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    ticket = db.relationship("Ticket",
                            cascade="all, delete-orphan",
                            back_populates="event",
                            passive_deletes=False,
                            order_by="Ticket.id")

    def __repr__(self):
        return f"<Event {self.title} ({self.id}, {self.status})>"

    def serialize(self):
        """Serialize event to a dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "venue": self.venue,
            "city": self.city,
            "description": self.description,
            "starts_at": self.starts_at.isoformat(),
            "ends_at": self.ends_at and self.ends_at.isoformat(),
            "status": self.status
        }

    def deserialize(self, doc):
        """Deserialize event data from a dictionary."""
        self.title = doc["title"]
        self.venue = doc["venue"]
        self.city = doc["city"]
        self.description = doc.get("description")
        self.starts_at = datetime.fromisoformat(doc["starts_at"])
        self.ends_at = (
            datetime.fromisoformat(doc["ends_at"])
            if doc.get("ends_at")
            else None
        )
        self.status = doc.get("status", "active")

    @staticmethod
    def json_schema():
        """JSON schema for event creation and update."""
        return {
            "type": "object",
            "required": ["title", "venue", "city", "starts_at"],
            "properties": {
                "title": {"type": "string"},
                "venue": {"type": "string"},
                "city": {"type": "string"},
                "description": {"type": "string"},
                "starts_at": {
                    "type": "string",
                    "format": "date-time"
                },
                "ends_at": {
                    "type": ["string", "null"],
                    "format": "date-time"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "cancelled"]
                }
            }
        }

class Ticket(db.Model):
    """Tickets represent a specific type of ticket for an event,
     with a name, price, and capacity."""
    __tablename__ = "tickets"

    __table_args__ = (
        db.UniqueConstraint(
            "event_id", "name",
            name="uq_ticket_event_name"
        ),
        db.CheckConstraint(
            "price >= 0",
            name="ck_ticket_price_nonneg"
        ),
        db.CheckConstraint(
            "capacity >= 0",
            name="ck_ticket_capacity_nonneg"
        ),
        db.CheckConstraint(
            "remaining >= 0",
            name="ck_ticket_remaining_nonneg"
        ),
        db.CheckConstraint(
            "remaining <= capacity",
            name="ck_ticket_remaining_le_capacity"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    remaining = db.Column(db.Integer, nullable=False)
    event = db.relationship("Event", back_populates="ticket")
    orders = db.relationship("Order", back_populates="ticket",
                            passive_deletes=True,
                            order_by="Order.created_at")

    def __repr__(self):
        """Readable string representation of the ticket."""
        return f"<Ticket {self.name} ({self.id}) for Event {self.event_id}>"

    def serialize(self):
        """Serialize ticket to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "price": float(self.price),
            "capacity": self.capacity,
            "remaining": self.remaining
        }

    def deserialize(self, doc):
        """Deserialize ticket data from a dictionary."""
        self.name = doc["name"]
        self.price = doc["price"]
        self.capacity = doc["capacity"]
        self.remaining = doc["capacity"]

    @staticmethod
    def json_schema():
        """JSON schema for ticket creation and update."""
        return {
            "type": "object",
            "required": ["name", "price", "capacity"],
            "properties": {
                "name": {"type": "string"},
                "price": {"type": "number", "minimum": 0},
                "capacity": {"type": "integer", "minimum": 0}
            }
        }

class Order(db.Model):
    """Orders represent a purchase of a ticket by a user. 
    The status field indicates whether the ticket has been used or not."""
    __tablename__ = "orders"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('used', 'not_used')",
            name="ck_orders_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="RESTRICT"),
                        nullable=False)
    status = db.Column(db.String(20), nullable=False, default="not_used")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    user = db.relationship("User", back_populates="orders")
    ticket = db.relationship("Ticket", back_populates="orders")

    def __repr__(self):
        """Readable string representation of the order."""
        return f"<Order {self.id} for User {self.user_id} and Ticket {self.ticket_id} ({self.status})>"

    def serialize(self):
        """Serialize order to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ticket_id": self.ticket_id,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

    @staticmethod
    def json_schema():
        """JSON schema for order creation."""
        return {
            "type": "object",
            "required": ["ticket_id"],
            "properties": {
                "ticket_id": {"type": "integer"}
            }
        }
