"""Ticketing API Application Package.

This package contains the core application components:
- models: Database models (User, Event, Ticket, Order)
- resources: REST API resource endpoints
- auth: JWT authentication utilities
- cache: Redis caching layer
- utils: MasonBuilder and helper functions
- views: Entry point and profile pages
- seed: Database seeding functionality
"""
import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from .cache import cache

db = SQLAlchemy()
"""SQLAlchemy database instance."""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ticketing")
"""Application logger."""


def create_app(test_config=None):
    """Create and configure the Flask application.

    This factory function creates and configures the Flask app,
    initializes extensions (SQLAlchemy, CORS, Redis cache),
    registers URL converters, and registers the API blueprint.

    Args:
        test_config: Optional configuration dict for testing

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    env = os.environ.get("FLASK_ENV", "development")
    if test_config is None:
        import config
        app.config.from_object(config.config.get(env, config.config["default"]))
    else:
        app.config.from_mapping(test_config)

    CORS(app)
    db.init_app(app)
    cache.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()
        from .seed import seed_database
        seed_database()

    from . import api
    from .utils import UserConverter, EventConverter, TicketConverter, OrderConverter
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["event"] = EventConverter
    app.url_map.converters["ticket"] = TicketConverter
    app.url_map.converters["order"] = OrderConverter

    app.register_blueprint(api.api_bp)

    return app
