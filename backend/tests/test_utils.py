# tests/test_utils.py
import pytest
from types import SimpleNamespace

from werkzeug.exceptions import NotFound

from ticketing import db
from ticketing.utils import UserConverter, EventConverter, TicketConverter, OrderConverter

from tests.helpers import create_user, create_event, create_ticket

# Tests
def test_user_converter_to_python_and_to_url(app, db_session):
    user = create_user()
    conv = UserConverter(app.url_map)

    got = conv.to_python(user.id)
    assert getattr(got, "id") == user.id
    assert conv.to_url(user) == str(user.id)

    with pytest.raises(NotFound):
        conv.to_python(999_999)

def test_event_converter_to_python_and_to_url(app, db_session):
    event = create_event()
    conv = EventConverter(app.url_map)

    got = conv.to_python(event.id)
    assert getattr(got, "id") == event.id
    assert conv.to_url(event) == str(event.id)

    with pytest.raises(NotFound):
        conv.to_python(999_999)

def test_ticket_converter_to_python_and_to_url(app, db_session):
    event = create_event()
    ticket = create_ticket(event)
    conv = TicketConverter(app.url_map)

    got = conv.to_python(ticket.id)
    assert getattr(got, "id") == ticket.id
    assert conv.to_url(ticket) == str(ticket.id)

    with pytest.raises(NotFound):
        conv.to_python(999_999)

def test_order_converter_with_monkeypatch(monkeypatch, app):
    conv = OrderConverter(app.url_map)

    # simulate NotFound
    monkeypatch.setattr(db.session, "get", lambda model, pk: None)
    with pytest.raises(NotFound):
        conv.to_python(12345)

    # simulate a real object returned
    dummy = SimpleNamespace(id=555)
    monkeypatch.setattr(db.session, "get", lambda model, pk: dummy)
    got = conv.to_python(555)
    assert got is dummy
    assert conv.to_url(dummy) == "555"