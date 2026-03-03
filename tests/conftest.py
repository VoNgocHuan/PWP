# tests/conftest.py
import pytest
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import scoped_session, sessionmaker

from ticketing import create_app, db


@pytest.fixture(scope="session")
def app():
    """
    Create Flask app with in-memory SQLite DB.
    Shared for entire test session.
    """
    app = create_app(
        {
            "TESTING": True,
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
