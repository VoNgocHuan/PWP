import json

def _user_payload(name, email, status="active"):
    return {"name": name, "email": email, "status": status}


def _event_payload(title, venue, city, starts_at, status="active", ends_at=None, description=None):
    body = {
        "title": title,
        "venue": venue,
        "city": city,
        "starts_at": starts_at,
        "status": status,
    }
    if ends_at is not None:
        body["ends_at"] = ends_at
    if description is not None:
        body["description"] = description
    return body


def _ticket_payload(name, price, capacity):
    return {"name": name, "price": price, "capacity": capacity}


def _order_payload(user_id, ticket_id):
    return {"user_id": user_id, "ticket_id": ticket_id}


class TestApiIndex:
    RESOURCE_URL = "/api/"

    def test_get(self, client):
        """The API should expose a small entry point at /api/."""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = resp.get_json()
        assert "api_name" in body
        assert "api_version" in body


class TestUserCollection:
    RESOURCE_URL = "/api/users/"

    def test_get(self, client):
        """Listing users should return the two seeded users."""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)
        assert len(body) == 2

    def test_post_valid(self, client):
        """Creating a new user returns 201 and a Location header pointing to the created user."""
        payload = _user_payload("Huan Vo", "huan.vo@oulu.example")
        resp = client.post(self.RESOURCE_URL, json=payload)

        assert resp.status_code == 201
        assert "Location" in resp.headers

        follow = client.get(resp.headers["Location"])
        assert follow.status_code == 200
        assert follow.get_json()["email"] == "huan.vo@oulu.example"

    def test_post_wrong_mediatype(self, client):
        """Sending non-JSON should be rejected with 415."""
        payload = _user_payload("Niranjan Sreegith", "niranjan@oulu.example")
        resp = client.post(self.RESOURCE_URL, data=json.dumps(payload))
        assert resp.status_code == 415

    def test_post_missing_field(self, client):
        """Schema validation should catch missing required fields (400)."""
        payload = {"name": "Ferdaus"}  # no email
        resp = client.post(self.RESOURCE_URL, json=payload)
        assert resp.status_code == 400

    def test_post_conflict_duplicate_email(self, client):
        """Email is unique: reusing an existing email should return 409."""
        payload = _user_payload("Someone Else", "aino.korhonen@oulu.example")
        resp = client.post(self.RESOURCE_URL, json=payload)
        assert resp.status_code == 409


class TestUserItem:
    VALID_URL = "/api/users/1/"
    MISSING_URL = "/api/users/999/"

    def test_get_valid(self, client):
        """A seeded user should be retrievable by item URL."""
        resp = client.get(self.VALID_URL)
        assert resp.status_code == 200
        assert resp.get_json()["email"] == "matti.meikalainen@oulu.example"

    def test_put_valid(self, client):
        """A user update should stick (status flip is the simplest sanity check)."""
        payload = _user_payload("Matti Meikäläinen", "matti.meikalainen@oulu.example", status="disabled")
        resp = client.put(self.VALID_URL, json=payload)
        assert resp.status_code == 204

        after = client.get(self.VALID_URL).get_json()
        assert after["status"] == "disabled"

    def test_put_wrong_mediatype(self, client):
        """PUT with non-JSON should return 415."""
        payload = _user_payload("Matti Meikäläinen", "matti.meikalainen@oulu.example")
        resp = client.put(self.VALID_URL, data=json.dumps(payload))
        assert resp.status_code == 415

    def test_put_missing_field(self, client):
        """PUT should also validate: missing email should be 400."""
        resp = client.put(self.VALID_URL, json={"name": "Matti Meikäläinen"})
        assert resp.status_code == 400

    def test_put_conflict_duplicate_email(self, client):
        """Changing email to an existing email should return 409."""
        payload = _user_payload("Matti Meikäläinen", "aino.korhonen@oulu.example", status="active")
        resp = client.put(self.VALID_URL, json=payload)
        assert resp.status_code == 409

    def test_delete_valid(self, client):
        """Deleting a user should make subsequent GET return 404."""
        resp = client.delete(self.VALID_URL)
        assert resp.status_code == 204

        gone = client.get(self.VALID_URL)
        assert gone.status_code == 404

    def test_delete_missing(self, client):
        """Deleting a non-existent user should return 404 via converter."""
        resp = client.delete(self.MISSING_URL)
        assert resp.status_code == 404


class TestEventCollection:
    RESOURCE_URL = "/api/events/"

    def test_get(self, client):
        """Listing events should return the single seeded event."""
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body) == 1
        assert body[0]["city"] == "Oulu"

    def test_post_valid(self, client):
        """Create an event and verify it can be fetched via Location."""
        payload = _event_payload(
            title="Oulu Coffee Cupping",
            venue="Kahvila Rooster",
            city="Oulu",
            starts_at="2026-09-10T17:30:00",
            description="Short tasting session.",
        )
        resp = client.post(self.RESOURCE_URL, json=payload)
        assert resp.status_code == 201
        assert "Location" in resp.headers

        follow = client.get(resp.headers["Location"])
        assert follow.status_code == 200
        assert follow.get_json()["venue"] == "Kahvila Rooster"

    def test_post_wrong_mediatype(self, client):
        """Event POST with non-JSON should be 415."""
        payload = _event_payload("Test", "Salaastinsali", "Oulu", "2026-02-14T18:00:00")
        resp = client.post(self.RESOURCE_URL, data=json.dumps(payload))
        assert resp.status_code == 415

    def test_post_missing_field(self, client):
        """Event schema should reject incomplete payloads (400)."""
        resp = client.post(self.RESOURCE_URL, json={"title": "Only title"})
        assert resp.status_code == 400

    def test_post_conflict_invalid_time_range(self, client):
        """ends_at earlier than starts_at violates DB constraint -> 409."""
        payload = _event_payload(
            title="Time Travelling Afterparty",
            venue="45 Special",
            city="Oulu",
            starts_at="2026-03-07T22:00:00",
            ends_at="2026-03-07T20:30:00",
        )
        resp = client.post(self.RESOURCE_URL, json=payload)
        assert resp.status_code == 409


class TestEventItem:
    VALID_URL = "/api/events/1/"
    MISSING_URL = "/api/events/999/"

    def test_get_valid(self, client):
        """Seeded event should be retrievable."""
        resp = client.get(self.VALID_URL)
        assert resp.status_code == 200
        assert resp.get_json()["venue"] == "Salaastinsali"

    def test_put_valid(self, client):
        """Update an event and verify the change shows up on GET."""
        payload = _event_payload(
            title="Rotuaari Indie Night (Updated)",
            venue="Salaastinsali",
            city="Oulu",
            starts_at="2026-02-14T18:00:00",
            status="active",
        )
        resp = client.put(self.VALID_URL, json=payload)
        assert resp.status_code == 204

        after = client.get(self.VALID_URL).get_json()
        assert after["title"].endswith("(Updated)")

    def test_put_wrong_mediatype(self, client):
        """PUT with non-JSON should be 415."""
        payload = _event_payload("X", "Salaastinsali", "Oulu", "2026-02-14T18:00:00")
        resp = client.put(self.VALID_URL, data=json.dumps(payload))
        assert resp.status_code == 415

    def test_put_missing_field(self, client):
        """PUT should validate: a partial payload should be 400."""
        resp = client.put(self.VALID_URL, json={"title": "Just title"})
        assert resp.status_code == 400

    def test_delete_valid(self, client):
        """Deleting an event should make it 404 afterwards."""
        resp = client.delete(self.VALID_URL)
        assert resp.status_code == 204
        assert client.get(self.VALID_URL).status_code == 404

    def test_delete_missing(self, client):
        """Deleting a missing event should return 404 via converter."""
        resp = client.delete(self.MISSING_URL)
        assert resp.status_code == 404


class TestTicketResources:
    COLLECTION_URL = "/api/events/1/tickets/"
    ITEM_URL = "/api/events/1/tickets/1/"
    WRONG_EVENT_ITEM_URL = "/api/events/999/tickets/1/"

    def test_ticket_list_for_event(self, client):
        """Ticket listing under an event should return the two seeded ticket types."""
        resp = client.get(self.COLLECTION_URL)
        assert resp.status_code == 200
        body = resp.get_json()
        assert len(body) == 2

    def test_ticket_post_valid(self, client):
        """Create a new ticket type under the event."""
        payload = _ticket_payload("Student", 8, 10)
        resp = client.post(self.COLLECTION_URL, json=payload)
        assert resp.status_code == 201
        assert "Location" in resp.headers

        follow = client.get(resp.headers["Location"])
        assert follow.status_code == 200
        assert follow.get_json()["name"] == "Student"

    def test_ticket_post_wrong_mediatype(self, client):
        """Ticket POST with non-JSON should be 415."""
        payload = _ticket_payload("Late Door", 22, 5)
        resp = client.post(self.COLLECTION_URL, data=json.dumps(payload))
        assert resp.status_code == 415

    def test_ticket_post_missing_field(self, client):
        """Ticket schema: missing capacity should yield 400."""
        resp = client.post(self.COLLECTION_URL, json={"name": "Broken", "price": 10})
        assert resp.status_code == 400

    def test_ticket_item_mismatch(self, client):
        """Asking a ticket under the wrong event should be 404."""
        resp = client.get(self.WRONG_EVENT_ITEM_URL)
        assert resp.status_code == 404


class TestOrders:
    COLLECTION_URL = "/api/orders/"
    ITEM_URL = "/api/orders/1/"
    MISSING_ITEM_URL = "/api/orders/999/"

    def test_orders_list_empty_initially(self, client):
        """Seed does not create orders; order list should start empty."""
        resp = client.get(self.COLLECTION_URL)
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_order_post_valid_and_get(self, client):
        """Create an order and fetch it back."""
        resp = client.post(self.COLLECTION_URL, json=_order_payload(1, 2))  # user 1 buys VIP Balcony
        assert resp.status_code == 201
        assert "Location" in resp.headers

        follow = client.get(resp.headers["Location"])
        assert follow.status_code == 200
        assert follow.get_json()["user_id"] == 1
        assert follow.get_json()["ticket_id"] == 2

    def test_order_post_wrong_mediatype(self, client):
        """Non-JSON order POST should be 415."""
        resp = client.post(self.COLLECTION_URL, data=json.dumps(_order_payload(1, 1)))
        assert resp.status_code == 415

    def test_order_post_missing_field(self, client):
        """Order schema: missing ticket_id should be 400."""
        resp = client.post(self.COLLECTION_URL, json={"user_id": 1})
        assert resp.status_code == 400

    def test_order_post_missing_user_or_ticket(self, client):
        """Order POST should return 404 if user or ticket doesn't exist."""
        assert client.post(self.COLLECTION_URL, json=_order_payload(999, 1)).status_code == 404
        assert client.post(self.COLLECTION_URL, json=_order_payload(1, 999)).status_code == 404

    def test_order_sold_out(self, client):
        """Ticket with capacity 1 should sell out after one purchase."""
        # now ticket id 2 has capacity 1
        assert client.post(self.COLLECTION_URL, json=_order_payload(1, 2)).status_code == 201
        assert client.post(self.COLLECTION_URL, json=_order_payload(2, 2)).status_code == 409

    def test_order_delete_restores_remaining(self, client):
        """Deleting an order should restore ticket.remaining by one."""
        # we will create an order for ticket id 1
        create = client.post(self.COLLECTION_URL, json=_order_payload(1, 1))
        assert create.status_code == 201

        # remaining should have reduced by one
        t = client.get("/api/events/1/tickets/1/").get_json()
        assert t["remaining"] == 1

        # we then delete the order and check that remaining goes back up
        order_url = create.headers["Location"]
        delete = client.delete(order_url)
        assert delete.status_code == 204

        t2 = client.get("/api/events/1/tickets/1/").get_json()
        assert t2["remaining"] == 2

    def test_order_item_missing(self, client):
        """Non-existent order should give 404 via converter."""
        resp = client.get(self.MISSING_ITEM_URL)
        assert resp.status_code == 404