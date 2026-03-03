from sqlalchemy.exc import IntegrityError


def _create_user(client, name, email, status="active"):
    return client.post(
        "/api/users/",
        json={"name": name, "email": email, "status": status},
    )


def _create_event(client, title, venue, city, starts_at, status="active", ends_at=None):
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


def _create_ticket(client, event_id, name, price, capacity):
    return client.post(
        f"/api/events/{event_id}/tickets/",
        json={"name": name, "price": price, "capacity": capacity},
    )


def _create_order(client, user_id, ticket_id):
    return client.post("/api/orders/", json={"user_id": user_id, "ticket_id": ticket_id})


def test_api_entrypoint_exists(client):
    """GET /api/ should return an object describing the API."""
    resp = client.get("/api/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "collections" in data
    assert "users" in data["collections"]
    assert "events" in data["collections"]
    assert "orders" in data["collections"]


def test_user_create_and_fetch(client):
    """Create a user, then fetch it through the Location header."""
    resp = _create_user(client, "Matti Meikäläinen", "matti.meikalainen@example.com")
    assert resp.status_code == 201
    assert "Location" in resp.headers

    user_url = resp.headers["Location"]
    get_resp = client.get(user_url)
    assert get_resp.status_code == 200
    assert get_resp.get_json()["email"] == "matti.meikalainen@example.com"


def test_user_duplicate_email_conflict(client):
    """Duplicate emails should be rejected."""
    assert _create_user(client, "Aino Korhonen", "aino.korhonen@example.com").status_code == 201
    assert _create_user(client, "Another Aino", "aino.korhonen@example.com").status_code == 409


def test_event_create_and_list(client):
    """Create one event and confirm it appears in GET /api/events/."""
    assert _create_event(
        client,
        title="Rotuaari Indie Night",
        venue="Salaastinsali",
        city="Oulu",
        starts_at="2026-02-14T18:00:00",
    ).status_code == 201

    resp = client.get("/api/events/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["city"] == "Oulu"


def test_ticket_purchase_sold_out(client):
    """Capacity=1 should sell out after one order."""
    assert _create_user(client, "Elina Mäkelä", "elina.makela@example.com").status_code == 201
    assert _create_event(
        client,
        title="Oulu Metal Night",
        venue="45 Special",
        city="Oulu",
        starts_at="2026-08-20T20:00:00",
    ).status_code == 201
    assert _create_ticket(client, event_id=1, name="Door Ticket", price=20, capacity=1).status_code == 201

    assert _create_order(client, user_id=1, ticket_id=1).status_code == 201
    assert _create_order(client, user_id=1, ticket_id=1).status_code == 409