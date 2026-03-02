import os
import pytest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from ticketing.models import app, db, User, Event  
from datetime import datetime


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


def test_create_user(client):
    user = User(name="John Smith", email="john@example.com")
    db.session.add(user)
    db.session.commit()

    assert user.id is not None
    assert user.status == "active"


def test_user_name_must_have_space(client):
    user = User(name="John", email="bad@example.com")

    db.session.add(user)

    with pytest.raises(Exception):
        db.session.commit()


def test_event_time_validation(client):
    event = Event(
        title="Concert",
        venue="Hall",
        city="NYC",
        starts_at=datetime(2025, 1, 2),
        ends_at=datetime(2025, 1, 1),
    )

    db.session.add(event)

    with pytest.raises(Exception):
        db.session.commit()
