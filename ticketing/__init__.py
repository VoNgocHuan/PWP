import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        #CACHE_TYPE="FileSystemCache",
        #CACHE_DIR=os.path.join(app.instance_path, "cache"),
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

    from . import models
    from . import api
    from .utils import UserConverter, EventConverter, TicketConverter, OrderConverter
    app.url_map.converters["user"] = UserConverter
    app.url_map.converters["event"] = EventConverter
    app.url_map.converters["ticket"] = TicketConverter
    app.url_map.converters["order"] = OrderConverter
    
    app.register_blueprint(api.api_bp)

    return app


