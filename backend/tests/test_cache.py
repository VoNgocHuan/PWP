# tests/test_cache.py
import pytest
from datetime import datetime, timedelta
from ticketing import db
from ticketing.models import User, Event, Ticket, Order
from ticketing.cache import get_cache


@pytest.mark.usefixtures("db_session")
class TestCacheBehavior:
    """Tests for cache behavior - Redis may not be available in test environment."""

    def test_cache_returns_none_when_redis_unavailable(self, app):
        """Test that cache returns None when Redis is not available."""
        cache = get_cache()
        
        result = cache.get("test_key")
        assert result is None

    def test_cache_set_returns_false_when_redis_unavailable(self, app):
        """Test that cache.set returns False when Redis is not available."""
        cache = get_cache()
        
        result = cache.set("test_key", {"data": "value"}, 60)
        assert result is False

    def test_cache_delete_returns_false_when_redis_unavailable(self, app):
        """Test that cache.delete handles gracefully when Redis unavailable."""
        cache = get_cache()
        
        result = cache.delete("nonexistent")
        assert result is False

    def test_cache_invalidate_pattern_returns_false_when_redis_unavailable(self, app):
        """Test that cache.invalidate_pattern handles gracefully."""
        cache = get_cache()
        
        result = cache.invalidate_pattern("test:*")
        assert result is False


@pytest.mark.usefixtures("db_session")
class TestCacheIntegration:
    """Integration tests for cache with endpoints."""

    def test_events_endpoint_works_without_cache(self, client):
        """Test that events endpoint works even without Redis."""
        response = client.get("/api/events/")

        assert response.status_code == 200

    def test_order_creation_works_without_cache(self, client, auth_headers):
        """Test that order creation works without Redis cache."""
        event = Event(title="Event", venue="Venue", city="City",
                      description="desc", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db.session.add(event)
        db.session.flush()

        ticket = Ticket(event=event, name="Ticket", price=25.00,
                        capacity=10, remaining=10)
        db.session.add(ticket)
        db.session.flush()

        initial_remaining = ticket.remaining

        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)

        assert response.status_code == 201

        db.session.refresh(ticket)
        assert ticket.remaining == initial_remaining - 1

    def test_tickets_remaining_updates_after_purchase(self, client, auth_headers):
        """Test that ticket remaining count updates after purchase."""
        event = Event(title="Cache Test Event", venue="Hall", city="City",
                      description="test", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db.session.add(event)
        db.session.flush()

        ticket = Ticket(event=event, name="VIP", price=100.00,
                        capacity=5, remaining=5)
        db.session.add(ticket)
        db.session.flush()

        assert ticket.remaining == 5

        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)

        assert response.status_code == 201

        db.session.refresh(ticket)
        assert ticket.remaining == 4

    def test_multiple_orders_reduce_remaining(self, client, auth_headers):
        """Test that multiple orders correctly reduce remaining count."""
        event = Event(title="Multi Event", venue="Arena", city="NYC",
                      description="test", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db.session.add(event)
        db.session.flush()

        ticket = Ticket(event=event, name="General", price=50.00,
                        capacity=3, remaining=3)
        db.session.add(ticket)
        db.session.flush()

        assert ticket.remaining == 3

        for i in range(3):
            response = client.post("/api/orders/", json={
                "ticket_id": ticket.id
            }, headers=auth_headers)
            assert response.status_code == 201

        db.session.refresh(ticket)
        assert ticket.remaining == 0

    def test_sold_out_ticket_prevents_purchase(self, client, auth_headers):
        """Test that sold out tickets cannot be purchased."""
        event = Event(title="Sold Out Event", venue="Hall", city="City",
                      description="test", starts_at=datetime.utcnow() + timedelta(days=1),
                      status="active")
        db.session.add(event)
        db.session.flush()

        ticket = Ticket(event=event, name="Last", price=10.00,
                        capacity=1, remaining=0)
        db.session.add(ticket)
        db.session.flush()

        response = client.post("/api/orders/", json={
            "ticket_id": ticket.id
        }, headers=auth_headers)

        assert response.status_code == 409