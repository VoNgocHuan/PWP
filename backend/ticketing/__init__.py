"""Initialization of the ticketing application."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from .cache import cache

db = SQLAlchemy()

def create_app(test_config=None):
    """Create and configure the Flask application."""
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
