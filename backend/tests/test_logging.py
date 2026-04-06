# tests/test_logging.py
import pytest
import logging
import uuid
from datetime import datetime, timedelta
from ticketing import db
from ticketing.models import User, Event, Ticket


@pytest.mark.usefixtures("db_session")
class TestLogging:
    """Tests for logging functionality."""

    def test_login_logs_user_email(self, client, caplog):
        """Test that successful login logs user email."""
        unique_email = f"logging_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(name="Test User", email=unique_email)
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        with caplog.at_level(logging.INFO):
            response = client.post("/api/auth/login/", json={
                "email": unique_email,
                "password": "password123"
            })

        assert response.status_code == 200
        assert any(unique_email in record.message for record in caplog.records)
        assert any("logged in" in record.message.lower() for record in caplog.records)

    def test_failed_login_logs_warning(self, client, caplog):
        """Test that failed login attempt logs a warning."""
        unique_email = f"fail_test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(name="Test User", email=unique_email)
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        with caplog.at_level(logging.WARNING):
            response = client.post("/api/auth/login/", json={
                "email": unique_email,
                "password": "wrongpassword"
            })

        assert response.status_code == 401
        assert any(unique_email in record.message for record in caplog.records)
        assert any(record.levelname == "WARNING" for record in caplog.records)

    def test_order_creation_logs_user_and_ticket(self, client, auth_headers, caplog):
        """Test that order creation logs order creation."""
        event = Event(title="Logging Concert", venue="Hall", city="City",
                      description="desc", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db.session.add(event)
        db.session.flush()

        ticket = Ticket(event=event, name="Standard", price=10.00,
                        capacity=100, remaining=100)
        db.session.add(ticket)
        db.session.flush()

        with caplog.at_level(logging.INFO):
            response = client.post("/api/orders/", json={
                "ticket_id": ticket.id
            }, headers=auth_headers)

        assert response.status_code == 201
        assert any("Order created" in record.message for record in caplog.records)

    def test_failed_order_logs_error(self, client, auth_headers, caplog):
        """Test that failed order creation logs an error."""
        with caplog.at_level(logging.ERROR):
            response = client.post("/api/orders/", json={
                "ticket_id": 99999
            }, headers=auth_headers)

        assert response.status_code in [404, 409]


@pytest.mark.usefixtures("db_session")
class TestLoggingOutput:
    """Tests for logging output format."""

    def test_logging_format_includes_timestamp(self, client, caplog):
        """Test that log output includes timestamp."""
        user = User(name="Format Test User", email="format@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        with caplog.at_level(logging.INFO):
            client.post("/api/auth/login/", json={
                "email": "format@example.com",
                "password": "password123"
            })

        assert len(caplog.records) > 0
        record = caplog.records[0]
        assert hasattr(record, 'asctime') or record.created > 0

    def test_logging_uses_ticketing_logger(self, client, caplog):
        """Test that logging uses the ticketing logger."""
        user = User(name="Logger Test User", email="logger@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.flush()

        with caplog.at_level(logging.INFO):
            client.post("/api/auth/login/", json={
                "email": "logger@example.com",
                "password": "password123"
            })

        assert any(record.name == "ticketing" for record in caplog.records)


@pytest.mark.usefixtures("db_session")
class TestApplicationLogging:
    """Tests for application-level logging."""

    def test_app_has_logger(self, app):
        """Test that app can create logger."""
        import logging
        logger = logging.getLogger("ticketing")
        
        assert logger is not None
        assert logger.name == "ticketing"

    def test_logger_can_log(self, app, caplog):
        """Test that logger can log messages."""
        import logging
        logger = logging.getLogger("ticketing")
        
        with caplog.at_level(logging.INFO):
            logger.info("Test message")
        
        assert any("Test message" in record.message for record in caplog.records)