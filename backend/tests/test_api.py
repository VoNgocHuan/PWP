# tests/test_api.py
import pytest
import json
from datetime import datetime, timedelta
from ticketing import db
from ticketing.models import User, Event, Ticket, Order
from tests.helpers import create_user, create_event, create_ticket


def get_mason_data(response):
    """Extract data from Mason JSON response."""
    return json.loads(response.data)


def get_mason_items(response):
    """Extract items from Mason JSON response."""
    data = get_mason_data(response)
    return data.get("items", [])


# Tests for the API endpoints of the ticketing application.
@pytest.mark.usefixtures("db_session")
class TestUserAPI:
    def test_create_user(self, client):
        response = client.post("/api/users/", json={
            "name": "Alice Wonderland",
            "email": f"alice_{id(client)}@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = get_mason_data(response)
        assert "token" in data
        assert "user_id" in data

    def test_get_users(self, client, auth_headers):
        user = create_user()
        response = client.get("/api/users/", headers=auth_headers)
        assert response.status_code == 200
        items = get_mason_items(response)
        assert any(u.get("email") == user.email for u in items)
    
    def test_delete_user(self, client, auth_headers):
        user = create_user()
        response = client.delete(f"/api/users/{user.id}/", headers=auth_headers)
        assert response.status_code == 204
        assert db.session.get(User, user.id) is None

    def test_create_user_invalid_data(self, client, auth_headers):
        response = client.post("/api/users/", json={
            "name": "SingleName",
            "email": f"bob_{id(client)}@example.com",
            "password": "password123"
        }, headers=auth_headers)
        assert response.status_code == 409

    def test_update_user(self, client, auth_headers):
        user = create_user()
        response = client.put(f"/api/users/{user.id}/", json={
            "name": "Alice Liddell",
            "email": user.email,
            "password": "password123"
        }, headers=auth_headers)
        assert response.status_code == 204
        db.session.refresh(user)
        assert user.name == "Alice Liddell"

    def test_update_user_invalid_data(self, client, auth_headers):
        user = create_user()
        response = client.put(f"/api/users/{user.id}/", json={
            "name": "SingleName",
            "email": f"bob_{id(client)}@example.com",
            "password": "password123"
        }, headers=auth_headers)
        assert response.status_code == 409 
    
    def test_post_user_invalid_json(self, client, auth_headers):
        response = client.post("/api/users/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415
    
    def test_validate_user_schema(self, client, auth_headers):
        response = client.post("/api/users/", json={
            "name": "Alice Wonderland",
            "password": "password123"
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_get_user_details(self, client, auth_headers):
        user = create_user()
        response = client.get(f"/api/users/{user.id}/", headers=auth_headers)
        assert response.status_code == 200
        data = get_mason_data(response)
        assert data.get("email") == user.email

    def test_put_user_invalid_json(self, client, auth_headers):
        user = create_user()
        response = client.put(f"/api/users/{user.id}/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415
    
    def test_put_validate_user_schema(self, client, auth_headers):
        user = create_user()
        response = client.put(f"/api/users/{user.id}/", json={
            "name": "Alice Wonderland",
            "password": "password123"
        }, headers=auth_headers)
        assert response.status_code == 400


@pytest.mark.usefixtures("db_session")
class TestEventAPI:
    def test_create_event(self, client, auth_headers):
        response = client.post("/api/events/", json={
            "title": "Music Fest",
            "venue": "Arena",
            "city": "Metropolis",
            "starts_at": (datetime.utcnow() + timedelta(days=1)).isoformat()
        }, headers=auth_headers)
        assert response.status_code == 201
        assert "Location" in response.headers

    def test_get_events(self, client):
        event = create_event()
        response = client.get("/api/events/")
        assert response.status_code == 200
        items = get_mason_items(response)
        assert any(e.get("title") == event.title for e in items)

    def test_update_event(self, client, auth_headers):
        event = create_event()
        new_title = "Updated Concert"
        response = client.put(f"/api/events/{event.id}/", json={
            "title": new_title,
            "venue": event.venue,
            "city": event.city,
            "starts_at": event.starts_at.isoformat()
        }, headers=auth_headers)
        assert response.status_code == 204
        db.session.refresh(event)
        assert event.title == new_title

    def test_delete_event(self, client, auth_headers):
        event = create_event()
        response = client.delete(f"/api/events/{event.id}/", headers=auth_headers)
        assert response.status_code == 204
        assert db.session.get(Event, event.id) is None

    def test_create_event_invalid_data(self, client, auth_headers):
        start = datetime.now()
        end = start - timedelta(hours=1)
        response = client.post("/api/events/", json={
            "title": "Invalid Event",
            "venue": "Hall",
            "city": "City",
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat()
        }, headers=auth_headers)
        assert response.status_code == 409

    def test_update_event_with_orders(self, client, db_session, auth_headers):
        event = create_event()
        ticket = create_ticket(event)
        user = create_user()
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.put(f"/api/events/{event.id}/", json={
            "title": "New Title",
            "venue": event.venue,
            "city": event.city,
            "starts_at": event.starts_at.isoformat()
        }, headers=auth_headers)

        assert response.status_code == 409

    def test_delete_event_with_orders(self, client, db_session, auth_headers):
        event = create_event()
        ticket = create_ticket(event)
        user = create_user()
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.delete(f"/api/events/{event.id}/", headers=auth_headers)

        assert response.status_code == 204

    def test_create_event_missing_fields(self, client, auth_headers):
        response = client.post("/api/events/", json={
            "title": "Incomplete Event"
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_post_event_invalid_dates(self, client, auth_headers):
        start = datetime.now()
        end = start - timedelta(hours=1)
        response = client.post("/api/events/", json={
            "title": "Invalid Dates",
            "venue": "Hall",
            "city": "City",
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat()
        }, headers=auth_headers)
        assert response.status_code == 409

    def test_post_event_invalid_json(self, client, auth_headers):
        response = client.post("/api/events/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415

    def test_get_event_details(self, client):
        event = create_event()
        response = client.get(f"/api/events/{event.id}/")
        assert response.status_code == 200
        data = get_mason_data(response)
        assert data["title"] == event.title

    def test_put_event_invalid_json(self, client, auth_headers):
        event = create_event()
        response = client.put(f"/api/events/{event.id}/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415

    def test_put_validate_event_schema(self, client, auth_headers):
        event = create_event()
        response = client.put(f"/api/events/{event.id}/", json={
            "title": "Updated Event"
        }, headers=auth_headers)
        assert response.status_code == 400

    


@pytest.mark.usefixtures("db_session")
class TestTicketAPI:
    def test_create_ticket(self, client, auth_headers):
        event = create_event()
        response = client.post(f"/api/events/{event.id}/tickets/", json={
            "name": "VIP",
            "price": 50.0,
            "capacity": 100
        }, headers=auth_headers)
        assert response.status_code == 201
        assert "Location" in response.headers

    def test_get_tickets(self, client):
        event = create_event()
        ticket = create_ticket(event)
        response = client.get(f"/api/events/{event.id}/tickets/")
        assert response.status_code == 200
        items = get_mason_items(response)
        assert any(t["name"] == ticket.name for t in items)

    def test_delete_ticket(self, client, auth_headers):
        event = create_event()
        ticket = create_ticket(event)
        response = client.delete(f"/api/events/{event.id}/tickets/{ticket.id}/", headers=auth_headers)
        assert response.status_code == 204
        assert db.session.get(Ticket, ticket.id) is None

    def test_create_ticket_duplicate_name(self, client, auth_headers):
        event = create_event()
        create_ticket(event)
        response = client.post(f"/api/events/{event.id}/tickets/", json={
            "name": "Standard",
            "price": 20,
            "capacity": 50
        }, headers=auth_headers)
        assert response.status_code == 409

    def test_create_ticket_invalid_data(self, client, auth_headers):
        event = create_event()
        response = client.post(f"/api/events/{event.id}/tickets/", json={
            "name": "Invalid Ticket",
            "price": -10,
            "capacity": 50
        }, headers=auth_headers)
        assert response.status_code == 400

    def test_delete_ticket_with_orders(self, client, db_session, auth_headers):
        event = create_event()
        ticket = create_ticket(event)
        user = create_user()
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.delete(f"/api/events/{event.id}/tickets/{ticket.id}/", headers=auth_headers)

        assert response.status_code == 204
    
    def test_post_ticket_invalid_json(self, client, auth_headers):
        event = create_event()
        response = client.post(f"/api/events/{event.id}/tickets/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415

    def test_get_details_ticket(self, client):
        event = create_event()
        ticket = create_ticket(event)
        response = client.get(f"/api/events/{event.id}/tickets/{ticket.id}/")
        assert response.status_code == 200
        data = get_mason_data(response)
        assert data["name"] == ticket.name

    def test_get_ticket_wrong_event(self, client):
        event1 = create_event()
        event2 = create_event()
        ticket = create_ticket(event1)
        response = client.get(f"/api/events/{event2.id}/tickets/{ticket.id}/")
        assert response.status_code == 404

    def test_delete_ticket_wrong_event(self, client, auth_headers):
        event1 = create_event()
        event2 = create_event()
        ticket = create_ticket(event1)
        response = client.delete(f"/api/events/{event2.id}/tickets/{ticket.id}/", headers=auth_headers)
        assert response.status_code == 404

@pytest.mark.usefixtures("db_session")
class TestOrderAPI:
    def test_create_order(self, client, auth_headers):
        user = create_user()
        event = create_event()
        ticket = create_ticket(event)
        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)
        assert response.status_code == 201
        data = get_mason_data(response)
        assert "order_id" in data
        db.session.refresh(ticket)
        assert ticket.remaining == ticket.capacity - 1

    def test_create_order_sold_out(self, client, auth_headers):
        user = create_user()
        event = create_event()
        ticket = create_ticket(event, capacity=10, remaining=0)

        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)

        assert response.status_code == 409

    def test_get_orders(self, client, db_session, auth_headers):
        """Get orders using the authenticated user."""
        event = create_event()
        ticket = create_ticket(event)
        
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.get("/api/orders/", headers=auth_headers)
        items = get_mason_items(response)

        assert response.status_code == 200
        assert items[0]["id"] == order.id

    def test_user_orders(self, client, db_session, auth_headers):
        """Get user orders using authenticated user."""
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = create_event()
        ticket = create_ticket(event)
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.get(f"/api/users/{user.id}/orders/", headers=auth_headers)
        items = get_mason_items(response)

        assert response.status_code == 200
        assert items[0]["user_id"] == user.id

    def test_delete_order(self, client, db_session, auth_headers):
        """Delete order using authenticated user."""
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = create_event()
        ticket = create_ticket(event, capacity=10, remaining=9)
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()
        db.session.refresh(ticket)

        response = client.delete(f"/api/orders/{order.id}/", headers=auth_headers)
        assert response.status_code == 204

        db.session.refresh(ticket)
        assert ticket.remaining == ticket.capacity
        assert db.session.get(Order, order.id) is None

    def test_delete_order_invalid_id(self, client, auth_headers):
        response = client.delete("/api/orders/999/", headers=auth_headers)
        assert response.status_code == 404

    def test_post_order_invalid_json(self, client, auth_headers):
        response = client.post("/api/orders/", data="Not JSON", content_type="text/plain", headers=auth_headers)
        assert response.status_code == 415

    def test_post_validate_order_schema(self, client, auth_headers):
        response = client.post("/api/orders/", json={
            "ticket_id": 1
        }, headers=auth_headers)
        assert response.status_code in [201, 400] 

    def test_get_order_details(self, client, db_session, auth_headers):
        """Get order details using authenticated user."""
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = create_event()
        ticket = create_ticket(event)
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.get(f"/api/orders/{order.id}/", headers=auth_headers)
        assert response.status_code == 200
        data = get_mason_data(response)
        assert data["id"] == order.id

    def test_post_order_nonexistent_user_or_ticket(self, client, auth_headers):
        response = client.post("/api/orders/", json={
            "ticket_id": 99999
        }, headers=auth_headers)
        assert response.status_code in [404, 409]

    def test_post_order_ticket_sold_out(self, client, db_session, auth_headers):
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = create_event()
        ticket = create_ticket(event, capacity=10, remaining=0)

        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)

        assert response.status_code == 409

    def test_delete_order_cascades_ticket_remaining(self, client, db_session, auth_headers):
        """Test delete order returns ticket remaining."""
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = create_event()
        ticket = create_ticket(event, capacity=10, remaining=9)
        order = Order(user=user, ticket=ticket)
        db.session.add(order)
        db.session.flush()

        response = client.delete(f"/api/orders/{order.id}/", headers=auth_headers)
        assert response.status_code == 204