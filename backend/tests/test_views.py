# tests/test_views.py
import pytest
import json
from ticketing.views import entry

def test_entry_view(client):
    """Test the API entry point returns expected Mason format."""
    response = client.get("/api/")
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert "@controls" in data
    assert "ticketing:users-all" in data["@controls"]
    assert "ticketing:events-all" in data["@controls"]
    assert "ticketing:orders" in data["@controls"]
    assert "ticketing:login" in data["@controls"]