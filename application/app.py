"""Flask application factory for invoice web interface."""

import logging
import os

from flask import Flask

from . import db, routes


def create_app() -> Flask:
    """Create and configure Flask application."""
    app = Flask(__name__)

    # Basic configuration
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Configure logging
    configure_logging(app)

    # Initialize database
    db.init_app(app)

    # Register routes
    app.register_blueprint(routes.bp)

    return app


def configure_logging(app: Flask) -> None:
    """Set up application logging."""
    if app.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
