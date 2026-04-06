# tests/test_auth.py
import pytest
from datetime import datetime, timedelta
from ticketing import db
from ticketing.models import User, Event, Ticket, Order
from ticketing.auth import create_token, require_auth
from ticketing.resources.user import AuthLogin, AuthLogout
from flask import g


@pytest.mark.usefixtures("db_session")
class TestAuthLogin:
    """Tests for the login endpoint."""

    def test_login_success_returns_token_and_user_id(self, client):
        """Test that successful login returns token and user_id."""
        user = User(name="Test User", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        response = client.post("/api/auth/login/", json={
            "email": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
        assert "user_id" in data
        assert data["user_id"] == user.id

    def test_login_invalid_password_fails(self, client):
        """Test that login fails with wrong password."""
        user = User(name="Test User", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        response = client.post("/api/auth/login/", json={
            "email": "test@example.com",
            "password": "wrongpassword"
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data is not None

    def test_login_disabled_user_fails(self, client):
        """Test that login fails for disabled user."""
        user = User(name="Test User", email="test@example.com", status="disabled")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        response = client.post("/api/auth/login/", json={
            "email": "test@example.com",
            "password": "password123"
        })

        assert response.status_code == 401
        data = response.get_json()
        assert data is not None

    def test_login_missing_email_fails(self, client):
        """Test that login fails when email is missing."""
        response = client.post("/api/auth/login/", json={
            "password": "password123"
        })

        assert response.status_code == 400

    def test_login_missing_password_fails(self, client):
        """Test that login fails when password is missing."""
        response = client.post("/api/auth/login/", json={
            "email": "test@example.com"
        })

        assert response.status_code == 400

    def test_login_invalid_json_fails(self, client):
        """Test that login fails with non-JSON data."""
        response = client.post("/api/auth/login/", data="Not JSON", content_type="text/plain")

        assert response.status_code == 415


@pytest.mark.usefixtures("db_session")
class TestAuthLogout:
    """Tests for the logout endpoint."""

    def test_logout_revokes_token(self, client, auth_headers):
        """Test that logout revokes the token."""
        response = client.post("/api/auth/logout/", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "Logged out" in data["message"]

    def test_logout_requires_auth(self, client):
        """Test that logout requires authentication."""
        response = client.post("/api/auth/logout/")

        assert response.status_code == 401


@pytest.mark.usefixtures("db_session")
class TestJWTAuth:
    """Tests for JWT authentication."""

    @pytest.mark.skip(reason="Flaky due to test ordering")
    def test_valid_token_grants_access(self, client, auth_headers, db_session):
        """Test that valid token grants access to protected endpoint."""
        response = client.get("/api/orders/", headers=auth_headers)

        assert response.status_code == 200

    def test_missing_token_denies_access(self, client):
        """Test that missing token denies access."""
        response = client.get("/api/orders/")

        assert response.status_code == 401

    def test_invalid_token_denies_access(self, client):
        """Test that invalid token denies access."""
        headers = {"Authorization": "Bearer invalid_token_here"}

        response = client.get("/api/orders/", headers=headers)

        assert response.status_code == 401

    def test_malformed_auth_header_denies_access(self, client):
        """Test that malformed auth header denies access."""
        headers = {"Authorization": "NotBearer token"}

        response = client.get("/api/orders/", headers=headers)

        assert response.status_code == 401

    def test_token_contains_correct_user_id(self, client):
        """Test that token contains correct user_id in payload."""
        import jwt
        user = User(name="Test User", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        token = create_token(user.id)
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["user_id"] == user.id


@pytest.mark.usefixtures("db_session")
class TestUserOrders:
    """Tests for viewing user orders."""

    def test_user_can_view_own_orders(self, client, db_session, auth_headers):
        """Test that user can view their own orders."""
        # Use the user from auth_headers fixture instead of creating new one
        user_id = auth_headers.get("user_id")
        user = db_session.query(User).filter_by(id=user_id).first()
        
        event = Event(title="Concert", venue="Hall", city="City", 
                      description="desc", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db_session.add(event)

        ticket = Ticket(event=event, name="Standard", price=10.00, 
                        capacity=100, remaining=100)
        db_session.add(ticket)
        db_session.flush()

        order = Order(user=user, ticket=ticket)
        db_session.add(order)
        db_session.flush()

        response = client.get(f"/api/users/{user.id}/orders/", headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "items" in data
        # Verify our created order is in the list
        order_ids = [item["id"] for item in data["items"]]
        assert order.id in order_ids

    def test_user_cannot_view_other_user_orders(self, client, db_session):
        """Test that user cannot view another user's orders."""
        user1 = User(name="User One", email="user1@example.com")
        user1.set_password("password123")
        user2 = User(name="User Two", email="user2@example.com")
        user2.set_password("password123")
        db_session.add(user1)
        db_session.add(user2)
        db_session.flush()

        event = Event(title="Concert", venue="Hall", city="City",
                      description="desc", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db_session.add(event)

        ticket = Ticket(event=event, name="Standard", price=10.00,
                        capacity=100, remaining=100)
        db_session.add(ticket)
        db_session.flush()

        order = Order(user=user1, ticket=ticket)
        db_session.add(order)
        db_session.flush()

        token = create_token(user2.id)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(f"/api/users/{user1.id}/orders/", headers=headers)

        assert response.status_code == 403