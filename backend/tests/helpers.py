# tests/helpers.py
from datetime import datetime, timedelta
from decimal import Decimal
from ticketing import db
from ticketing.models import User, Event, Ticket

def create_user(password="password123"):
    user = User(name="John Doe", email="john@example.com")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user

def create_event():
    event = Event(
        title="Concert",
        venue="Hall",
        city="City",
        description="desc",
        starts_at=datetime.utcnow() + timedelta(days=1),
        status="active"
    )
    db.session.add(event)
    db.session.flush()
    return event

def create_ticket(event=None, capacity=100, remaining=100):
    if event is None:
        event = create_event()
    ticket = Ticket(
        event=event,
        name="Standard",
        price=Decimal("10.00"),
        capacity=capacity,
        remaining=remaining
    )
    db.session.add(ticket)
    db.session.flush()
    return ticket
