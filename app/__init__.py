from flask import Flask

from app.api.routes import api_bp
from app.core.config import Settings
from app.core.errors import register_error_handlers
from app.db import init_db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False

    settings = Settings()
    app.config["APP_SETTINGS"] = settings

    init_db()
    app.register_blueprint(api_bp)
    register_error_handlers(app)

    return app
