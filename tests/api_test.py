import os
import pytest
from sqlalchemy.exc import IntegrityError

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from ticketing.models import app, db, User, Event, Ticket, Order
import ticketing.api


@pytest.fixture
def client():
    """Run Flask test client backed by a fresh in-memory SQLite database per test."""
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        with app.app_context():
            db.create_all()
            yield test_client
            db.session.remove()
            db.drop_all()


def _create_user(client, name="Aino Korhonen", email="aino.korhonen@example.com", status="active"):
    """Create a user through the API with a realistic name/email pair."""
    return client.post("/api/users/", json={"name": name, "email": email, "status": status})


def _create_event(
    client,
    title="Oulu Winter Music Night",
    starts_at="2026-02-14T18:00:00",
    ends_at=None,
    status="active",
    venue="Salaastinsali",
    city="Oulu",
):
    """Create an event through the API."""
    payload = {
        "title": title,
        "venue": venue,
        "city": city,
        "starts_at": starts_at,
        "status": status,
    }
    if ends_at is not None:
        payload["ends_at"] = ends_at
    return client.post("/api/events/", json=payload)


def _create_ticket(client, event_id=1, name="Early Bird", price=15, capacity=2):
    """Create a ticket under a specific event (nested resource)."""
    return client.post(
        f"/api/events/{event_id}/tickets/",
        json={"name": name, "price": price, "capacity": capacity},
    )


def _create_order(client, user_id=1, ticket_id=1):
    """Create an order for a given user and ticket."""
    return client.post("/api/orders/", json={"user_id": user_id, "ticket_id": ticket_id})


def test_user_item_get_put_delete(client):
    """Walk a user through create > read > update > delete, and confirm it disappears."""
    assert _create_user(client, email="matti.meikalainen@example.com", name="Matti Meikäläinen").status_code == 201

    get_user = client.get("/api/users/1/")
    assert get_user.status_code == 200
    assert get_user.get_json()["email"] == "matti.meikalainen@example.com"

    update_user = client.put(
        "/api/users/1/",
        json={"name": "Matti Meikäläinen", "email": "matti.meikalainen@example.com", "status": "disabled"},
    )
    assert update_user.status_code == 204

    get_user_again = client.get("/api/users/1/")
    assert get_user_again.status_code == 200
    assert get_user_again.get_json()["status"] == "disabled"

    delete_user = client.delete("/api/users/1/")
    assert delete_user.status_code == 204

    missing_user = client.get("/api/users/1/")
    assert missing_user.status_code == 404


def test_user_post_duplicate_email(client):
    """Creating two users with the same email should be rejected as a conflict."""
    assert _create_user(client, email="info@oulu-events.example").status_code == 201
    assert _create_user(client, email="info@oulu-events.example").status_code == 409


def test_user_post_unsupported_media_type(client):
    """If the client doesn't send JSON, the API should respond with 415."""
    response = client.post("/api/users/", data="name=Aino", content_type="text/plain")
    assert response.status_code == 415


def test_user_post_schema_validation(client):
    """A user payload missing required fields should get a 400 with schema validation."""
    response = client.post("/api/users/", json={"email": "missing.name.field@example.com"})
    assert response.status_code == 400


def test_user_put_duplicate_email(client):
    """Updating a user email to an email that already exists should return 409."""
    assert _create_user(client, email="huan.vo@example.com", name="Huan Vo").status_code == 201
    assert _create_user(client, email="niranjan.sreegith@example.com", name="Niranjan Sreegith").status_code == 201

    response = client.put(
        "/api/users/1/",
        json={"name": "Huan Vo", "email": "niranjan.sreegith@example.com", "status": "active"},
    )
    assert response.status_code == 409


def test_event_get_put_delete(client):
    """Create an event, update the venue/city, and then delete it cleanly."""
    assert _create_event(client, title="Rotuaari Indie Night").status_code == 201

    list_events = client.get("/api/events/")
    assert list_events.status_code == 200
    assert len(list_events.get_json()) == 1

    get_event = client.get("/api/events/1/")
    assert get_event.status_code == 200
    assert get_event.get_json()["title"] == "Rotuaari Indie Night"

    update_event = client.put(
        "/api/events/1/",
        json={
            "title": "Rotuaari Indie Night (Updated)",
            "venue": "Salaastinsali",
            "city": "Oulu",
            "starts_at": "2026-02-14T18:00:00",
            "status": "active",
        },
    )
    assert update_event.status_code == 204

    get_event_again = client.get("/api/events/1/")
    assert get_event_again.status_code == 200
    assert get_event_again.get_json()["title"] == "Rotuaari Indie Night (Updated)"
    assert get_event_again.get_json()["venue"] == "Salaastinsali"
    assert get_event_again.get_json()["city"] == "Oulu"

    delete_event = client.delete("/api/events/1/")
    assert delete_event.status_code == 204


def test_event_post_schema_validation_error(client):
    """Trying to create an event with only a title should fail schema validation (400)."""
    response = client.post("/api/events/", json={"title": "Just a Title, Nothing Else"})
    assert response.status_code == 400


def test_event_not_found_converter(client):
    """A non-existent event ID in the URL should resolve to a 404 via the converter."""
    response = client.get("/api/events/999/")
    assert response.status_code == 404


def test_event_post_integrity_invalid_time_range(client):
    """An event that ends before it starts should be rejected as a conflict (DB constraint)."""
    response = _create_event(
        client,
        title="Afterparty That Time-Travels",
        starts_at="2026-02-14T23:30:00",
        ends_at="2026-02-14T21:00:00",
    )
    assert response.status_code == 409


def test_ticket_collection_get_and_item_mismatch(client):
    """A ticket must belong to the event in the URL, asking it under another event should 404."""
    assert _create_event(client, title="Oulu Jazz Evening", starts_at="2026-03-01T19:00:00").status_code == 201
    assert _create_event(client, title="Market Square Food Fest", starts_at="2026-03-05T12:00:00", venue="Kauppatori").status_code == 201
    assert _create_ticket(client, event_id=1, name="VIP Balcony", price=45, capacity=3).status_code == 201

    list_tickets = client.get("/api/events/1/tickets/")
    assert list_tickets.status_code == 200
    assert len(list_tickets.get_json()) == 1

    wrong_event_ticket = client.get("/api/events/2/tickets/1/")
    assert wrong_event_ticket.status_code == 404


def test_ticket_unique_name_per_event(client):
    """Ticket names are unique per event, creating the same name twice under the same event is a conflict."""
    assert _create_event(client, title="Oulu Stand-up Night", starts_at="2026-04-10T20:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Front Row", price=25, capacity=10).status_code == 201
    assert _create_ticket(client, event_id=1, name="Front Row", price=30, capacity=5).status_code == 409


def test_ticket_post_schema_validation_negative_price(client):
    """A negative ticket price is invalid and should be rejected with 400."""
    assert _create_event(client, title="Science Park Meetup", venue="Tellus", starts_at="2026-05-02T17:00:00").status_code == 201
    response = client.post(
        "/api/events/1/tickets/",
        json={"name": "Student Ticket", "price": -5, "capacity": 50},
    )
    assert response.status_code == 400


def test_ticket_delete_success(client):
    """Deleting a ticket with no orders should succeed with 204."""
    assert _create_event(client, title="Oulu Film Night", venue="Star", starts_at="2026-06-01T18:30:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Standard Seat", price=12, capacity=20).status_code == 201

    response = client.delete("/api/events/1/tickets/1/")
    assert response.status_code == 204


def test_delete_ticket_with_existing_order_conflict(client):
    """A ticket that has orders should not be deletable, the API should respond with 409."""
    assert _create_user(client, name="Salla Nieminen", email="salla.nieminen@example.com").status_code == 201
    assert _create_event(client, title="Oulu Game Dev Evening", venue="Business Kitchen", starts_at="2026-06-15T18:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="General Admission", price=0, capacity=1).status_code == 201
    assert _create_order(client, user_id=1, ticket_id=1).status_code == 201

    response = client.delete("/api/events/1/tickets/1/")
    assert response.status_code == 409


def test_orders_collection_get_empty(client):
    """With a fresh DB, listing orders should return an empty list."""
    response = client.get("/api/orders/")
    assert response.status_code == 200
    assert response.get_json() == []


def test_orders_post_unsupported_media(client):
    """If an order is submitted without JSON, the API should respond with 415."""
    response = client.post("/api/orders/", data="user_id=1&ticket_id=1", content_type="text/plain")
    assert response.status_code == 415


def test_orders_post_schema_validation(client):
    """Missing required fields in an order payload should be a 400."""
    response = client.post("/api/orders/", json={"user_id": 1})
    assert response.status_code == 400


def test_order_not_found(client):
    """Orders should return 404 if either user_id or ticket_id doesn't exist."""
    assert _create_event(client, title="Oulu Art Pop-up", venue="Valve", starts_at="2026-07-01T16:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Entry", price=5, capacity=3).status_code == 201

    missing_user = _create_order(client, user_id=999, ticket_id=1)
    assert missing_user.status_code == 404

    assert _create_user(client, name="Teemu Laine", email="teemu.laine@example.com").status_code == 201
    missing_ticket = _create_order(client, user_id=1, ticket_id=999)
    assert missing_ticket.status_code == 404


def test_ticket_sold_out(client):
    """Once a ticket capacity is exhausted, creating another order should return 409."""
    assert _create_user(client, name="Elina Mäkelä", email="elina.makela@example.com").status_code == 201
    assert _create_event(client, title="Oulu Metal Night", venue="45 Special", starts_at="2026-08-20T20:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Door Ticket", price=20, capacity=1).status_code == 201

    first_order = _create_order(client, user_id=1, ticket_id=1)
    assert first_order.status_code == 201

    second_order = _create_order(client, user_id=1, ticket_id=1)
    assert second_order.status_code == 409


def test_order_get_and_delete(client):
    """Deleting an order should restore the ticket's remaining count back by one."""
    assert _create_user(client, name="Janne Heikkinen", email="janne.heikkinen@example.com").status_code == 201
    assert _create_event(client, title="Oulu Coffee Cupping", venue="Kahvila Rooster", starts_at="2026-09-10T17:30:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Tasting Slot", price=8, capacity=1).status_code == 201

    assert _create_order(client, user_id=1, ticket_id=1).status_code == 201

    ticket_after_order = client.get("/api/events/1/tickets/1/")
    assert ticket_after_order.status_code == 200
    assert ticket_after_order.get_json()["remaining"] == 0

    delete_order = client.delete("/api/orders/1/")
    assert delete_order.status_code == 204

    ticket_after_delete = client.get("/api/events/1/tickets/1/")
    assert ticket_after_delete.status_code == 200
    assert ticket_after_delete.get_json()["remaining"] == 1


def test_delete_event_with_existing_order_conflict(client):
    """An event tied to existing orders should not be deletable; expect 409."""
    assert _create_user(client, name="Noora Salmi", email="noora.salmi@example.com").status_code == 201
    assert _create_event(client, title="Oulu Theatre Premiere", venue="Oulun Teatteri", starts_at="2026-10-01T19:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Stalls Seat", price=32, capacity=1).status_code == 201
    assert _create_order(client, user_id=1, ticket_id=1).status_code == 201

    response = client.delete("/api/events/1/")
    assert response.status_code == 409


def test_order_post_integrity_error(client, monkeypatch):
    """If the database commit blows up during order creation, we should return a clean 409."""
    assert _create_user(client, name="Arto Kinnunen", email="arto.kinnunen@example.com").status_code == 201
    assert _create_event(client, title="Oulu Hack Night", venue="Tellus Innovation Arena", starts_at="2026-11-05T18:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Seat Reservation", price=0, capacity=2).status_code == 201

    def boom():
        raise IntegrityError(None, None, None)

    monkeypatch.setattr(db.session, "commit", boom)

    response = _create_order(client, user_id=1, ticket_id=1)
    assert response.status_code == 409


def test_model_repr_methods_are_executed(client):
    """Touch __repr__ on each model so we know those paths are exercised in coverage."""
    assert _create_user(client, name="Kaisa Lehto", email="kaisa.lehto@example.com").status_code == 201
    assert _create_event(client, title="Oulu Choir Concert", venue="Tuomiokirkko", starts_at="2026-12-12T18:00:00").status_code == 201
    assert _create_ticket(client, event_id=1, name="Pew Seat", price=10, capacity=1).status_code == 201
    assert _create_order(client, user_id=1, ticket_id=1).status_code == 201

    with app.app_context():
        user = db.session.get(User, 1)
        event = db.session.get(Event, 1)
        ticket = db.session.get(Ticket, 1)
        order = db.session.get(Order, 1)

        assert "kaisa.lehto@example.com" in repr(user)
        assert "Oulu Choir Concert" in repr(event)
        assert "Pew Seat" in repr(ticket)
        assert "Order" in repr(order)

def test_event_put_rejects_partial_payload(client):
    """Updating an event with only a title is not a real update; schema should reject it (400)."""
    assert _create_event(
        client,
        title="Rotuaari Open Mic",
        venue="Salaastinsali",
        city="Oulu",
        starts_at="2026-02-20T18:00:00",
    ).status_code == 201

    response = client.put("/api/events/1/", json={"title": "Rotuaari Open Mic (just title)"})
    assert response.status_code == 400


def test_event_put_conflict_end_time_before_start(client):
    """If someone sets an end time earlier than the start time, the API should refuse it (409)."""
    assert _create_event(
        client,
        title="Late Night Jam Session",
        venue="45 Special",
        city="Oulu",
        starts_at="2026-03-07T22:00:00",
    ).status_code == 201

    response = client.put(
        "/api/events/1/",
        json={
            "title": "Late Night Jam Session",
            "venue": "45 Special",
            "city": "Oulu",
            "starts_at": "2026-03-07T22:00:00",
            "ends_at": "2026-03-07T20:30:00", 
            "status": "active",
        },
    )
    assert response.status_code == 409


def test_missing_order_id(client):
    """Asking for an order that doesn't exist should return 404 (converter path)."""
    response = client.get("/api/orders/999/")
    assert response.status_code == 404


def test_event_with_valid_end_time(client):
    """When an event has an end time, the representation should include it as an ISO timestamp."""
    create_resp = _create_event(
        client,
        title="Oulu Choir Concert",
        venue="Tuomiokirkko",
        city="Oulu",
        starts_at="2026-12-12T18:00:00",
        ends_at="2026-12-12T19:30:00",
    )
    assert create_resp.status_code == 201

    get_resp = client.get("/api/events/1/")
    assert get_resp.status_code == 200
    data = get_resp.get_json()
    assert data["ends_at"] == "2026-12-12T19:30:00"

def test_user_not_found_converter_path(client):
    """A user id that does not exist should give a clean 404."""
    response = client.get("/api/users/999/")
    assert response.status_code == 404

def test_user_put_rejects_non_json(client):
    """PUT should insist on JSON, otherwise we return 415."""
    assert _create_user(
        client,
        name="Kalle Jokinen",
        email="kalle.jokinen@oulu.example",
        status="active",
    ).status_code == 201

    response = client.put(
        "/api/users/1/",
        data="name=Kalle Jokinen",
        content_type="text/plain",
    )
    assert response.status_code == 415

def test_user_put_schema(client):
    """PUT with an incomplete payload should fail schema validation (400)."""
    assert _create_user(
        client,
        name="Saara Peltola",
        email="saara.peltola@oulu.example",
        status="active",
    ).status_code == 201

    response = client.put("/api/users/1/", json={"email": "saara.peltola@oulu.example"})
    assert response.status_code == 400