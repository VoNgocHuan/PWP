# tests/test_models.py
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError

from ticketing import db
from ticketing.models import User, Event, Ticket, Order
from tests.helpers import create_user, create_event, create_ticket


# User tests
def test_user_name_must_contain_space(db_session):
    with pytest.raises(IntegrityError):
        db.session.add(User(name="SingleName", email="a@a.com"))
        db.session.flush()

def test_user_status_constraint(db_session):
    with pytest.raises(IntegrityError):
        db.session.add(User(name="Jane Doe", email="b@b.com", status="wrong"))
        db.session.flush()

def test_user_serialize(db_session):
    user = create_user()
    data = user.serialize()

    assert data["email"] == "john@example.com"
    assert data["status"] == "active"

# Event tests
def test_event_time_constraint(db_session):
    now = datetime.now()

    with pytest.raises(IntegrityError):
        db.session.add(
            Event(
                title="Bad",
                venue="X",
                city="Y",
                starts_at=now,
                ends_at=now - timedelta(hours=1),
            )
        )
        db.session.flush()

def test_event_serialize(db_session):
    event = create_event()
    data = event.serialize()

    assert data["title"] == "Concert"
    assert data["status"] == "active"


# Ticket tests
def test_ticket_price_non_negative(db_session):
    event = create_event()

    with pytest.raises(IntegrityError):
        db.session.add(
            Ticket(
                event=event,
                name="Bad",
                price=-1,
                capacity=10,
                remaining=10,
            )
        )
        db.session.flush()

def test_ticket_unique_name_per_event(db_session):
    event = create_event()
    create_ticket(event)

    with pytest.raises(IntegrityError):
        db.session.add(
            Ticket(
                event=event,
                name="Standard",
                price=Decimal("10.00"),
                capacity=10,
                remaining=10,
            )
        )
        db.session.flush()


# Order tests
def test_order_creation_and_relationship(db_session):
    user = create_user()
    event = create_event()
    ticket = create_ticket(event)

    order = Order(user=user, ticket=ticket)
    db.session.add(order)
    db.session.flush()

    assert order.user_id == user.id
    assert order.ticket_id == ticket.id


def test_order_status_constraint(db_session):
    user = create_user()
    event = create_event()
    ticket = create_ticket(event)

    with pytest.raises(IntegrityError):
        db.session.add(Order(user=user, ticket=ticket, status="bad"))
        db.session.flush()

def test_cascade_delete_user(db_session):
    user = create_user()
    event = create_event()
    ticket = create_ticket(event)

    order = Order(user=user, ticket=ticket)
    db.session.add(order)
    db.session.flush()

    db.session.delete(user)
    db.session.flush()

    assert db.session.get(Order, order.id) is None

def test_restrict_delete_ticket(db_session):
    user = create_user()
    event = create_event()
    ticket = create_ticket(event)

    order = Order(user=user, ticket=ticket)
    db.session.add(order)
    db.session.flush()

    with pytest.raises(IntegrityError):
        db.session.delete(ticket)
        db.session.flush()
