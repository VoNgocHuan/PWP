import pytest
from datetime import datetime

from ticketing import db
from ticketing.models import User, Event


def test_create_user_defaults(client):
    """DB: creating a user should set status to active by default."""
    u = User(name="John Smith", email="john.smith@example.com")
    db.session.add(u)
    db.session.commit()

    assert u.id is not None
    assert u.status == "active"


def test_user_name_must_have_space(client):
    """DB: name must contain a space (check constraint)."""
    u = User(name="John", email="bad@example.com")
    db.session.add(u)
    with pytest.raises(Exception):
        db.session.commit()


def test_event_time_validation(client):
    """DB: ends_at must be after starts_at (check constraint)."""
    e = Event(
        title="Concert",
        venue="Hall",
        city="Oulu",
        starts_at=datetime(2026, 1, 2),
        ends_at=datetime(2026, 1, 1),
    )
    db.session.add(e)
    with pytest.raises(Exception):
        db.session.commit()