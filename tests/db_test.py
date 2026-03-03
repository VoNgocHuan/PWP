import pytest
from datetime import datetime

from ticketing import db
from ticketing.models import User, Event, Ticket


class TestDatabaseConstraints:
    def test_user_name_needs_space(self, client):
        """User names must include a space (first + last)."""
        u = User(name="Prince", email="prince@oulu.example", status="active")
        db.session.add(u)
        with pytest.raises(Exception):
            db.session.commit()

    def test_event_end_before_start_is_rejected(self, client):
        """ends_at earlier than starts_at violates the event time constraint."""
        e = Event(
            title="Broken schedule",
            venue="Salaastinsali",
            city="Oulu",
            starts_at=datetime.fromisoformat("2026-02-14T18:00:00"),
            ends_at=datetime.fromisoformat("2026-02-14T17:00:00"),
            status="active",
        )
        db.session.add(e)
        with pytest.raises(Exception):
            db.session.commit()

    def test_ticket_remaining_cannot_exceed_capacity(self, client):
        """Ticket remaining must not be greater than capacity."""
        t = Ticket(name="Impossible", price=10, capacity=1, remaining=2, event_id=1)
        db.session.add(t)
        with pytest.raises(Exception):
            db.session.commit()