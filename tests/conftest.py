import os
import tempfile
from datetime import datetime

import pytest

from ticketing import create_app, db
from ticketing.models import User, Event, Ticket


def _seed_db():
    u1 = User(name="Matti Meikäläinen", email="matti.meikalainen@oulu.example", status="active")
    u2 = User(name="Aino Korhonen", email="aino.korhonen@oulu.example", status="active")

    e1 = Event(
        title="Rotuaari Indie Night",
        venue="Salaastinsali",
        city="Oulu",
        description="Small live night in the city centre.",
        starts_at=datetime.fromisoformat("2026-02-14T18:00:00"),
        ends_at=None,
        status="active",
    )

    t1 = Ticket(name="Early Bird", price=15, capacity=2, remaining=2)
    t2 = Ticket(name="VIP Balcony", price=45, capacity=1, remaining=1)

    e1.ticket.append(t1)
    e1.ticket.append(t2)

    db.session.add_all([u1, u2, e1])
    db.session.commit()


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_path,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )

    ctx = app.app_context()
    ctx.push()

    db.create_all()
    _seed_db()

    with app.test_client() as test_client:
        yield test_client

    db.session.rollback()
    db.drop_all()
    db.session.remove()

    db.engine.dispose()

    ctx.pop()

    os.close(db_fd)
    os.unlink(db_path)