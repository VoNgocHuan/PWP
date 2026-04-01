# tests/test_views.py
import pytest
from ticketing.views import entry

def test_entry_view(client):
    """Test the API entry point returns expected structure."""
    response = client.get("/api/")  # <-- use /api/ instead of /
    assert response.status_code == 200

    data = response.get_json()
    assert data["api_name"] == "ticketing"
    assert data["api_version"] == "1.0"
    assert "users" in data["collections"]
    assert "events" in data["collections"]
    assert "orders" in data["collections"]
    assert data["collections"]["users"] == "/api/users/"
    