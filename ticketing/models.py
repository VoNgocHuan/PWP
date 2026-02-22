from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, OperationalError

app = Flask(__name__, static_folder="static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///development.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

class User(db.Model):
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
    #must be first name, last name 
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False,server_default=db.func.now())
    orders = db.relationship("Order", cascade="all, delete-orphan", back_populates="user", passive_deletes=True, order_by="Order.created_at")

    def __repr__(self):
        return "{} <{}> ({})".format(self.email, self.id, self.status)
    
class Event(db.Model):
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

    ticket = db.relationship("Ticket", cascade="all, delete-orphan", back_populates="event", passive_deletes=True, order_by="Ticket.id")

    def __repr__(self):
        return "{} <{}> ({})".format(self.title, self.id, self.status)
    
class Ticket(db.Model):
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
    orders = db.relationship("Order", back_populates="ticket", passive_deletes=True, order_by="Order.created_at")

    def __repr__(self):
        return "{} <{}> (Event {})".format(self.name, self.id, self.event_id)
    
class Order(db.Model):
    __tablename__ = "orders"

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('used', 'not_used')",
            name="ck_orders_status"
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="not_used")
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    user = db.relationship("User", back_populates="orders")
    ticket = db.relationship("Ticket", back_populates="orders")

    def __repr__(self):
        return "Order <{}> user={} ticket={} status={}".format(self.id, self.user_id, self.ticket_id, self.status)