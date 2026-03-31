"""Initialization of the ticketing application."""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .cache import cache

db = SQLAlchemy()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        REDIS_HOST="localhost",
        REDIS_PORT=6379,
        REDIS_DB=0,
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

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
