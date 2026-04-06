# tests/conftest.py
import pytest
import json
import uuid
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import scoped_session, sessionmaker

from ticketing import create_app, db
from ticketing.auth import create_token


@pytest.fixture(scope="session")
def app():
    """
    Create Flask app with in-memory SQLite DB.
    Shared for entire test session.
    """
    app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key-for-testing",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
        }
    )

    ctx = app.app_context()
    ctx.push()
    db.create_all()

    yield app

    db.drop_all()
    ctx.pop()

@pytest.fixture(scope="function")
def db_session(app):
    """
    Each test runs inside a transaction.
    Automatically rolled back after the test.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    Session = scoped_session(sessionmaker(bind=connection))
    db.session = Session

    try:
        yield db.session
    finally:
        transaction.rollback()
        db.session.remove()
        connection.close()

@pytest.fixture(scope="function")
def client(app):
    """Flask test client."""
    return app.test_client()

_counter = 0

@pytest.fixture(scope="function")
def auth_headers(app, db_session):
    """Create a test user with unique email and return auth headers."""
    global _counter
    _counter += 1
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    
    from ticketing.models import User
    user = User(name="Test User", email=unique_email)
    user.set_password("password123")
    db_session.add(user)
    db_session.flush()
    
    token = create_token(user.id)
    return {"Authorization": f"Bearer {token}", "user_id": user.id}


def get_mason_data(response):
    """Extract data from Mason JSON response."""
    return json.loads(response.data)


def get_mason_items(response):
    """Extract items from Mason JSON response."""
    data = json.loads(response.data)
    return data.get("items", [])


@pytest.fixture
def mason():
    """Helper functions for Mason JSON responses."""
    return {
        "get_data": get_mason_data,
        "get_items": get_mason_items
    }
