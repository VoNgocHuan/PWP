import pytest

from ticketing import create_app, db


@pytest.fixture
def app():
    """Create an application configured for testing with an in-memory SQLite DB."""
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        }
    )
    return app


@pytest.fixture
def client(app):
    """Flask test client with a new DB per test."""
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()