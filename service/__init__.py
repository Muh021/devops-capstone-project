"""
Package: service
Package for the application models and service routes
This module creates and configures the Flask app and sets up logging
and the SQL database.
"""
import sys

from flask import Flask
from flask_talisman import Talisman
from flask_cors import CORS

from service import config
from service.common import log_handlers


# Create Flask application
app = Flask(__name__)
app.config.from_object(config)
talisman = Talisman(app, force_https=False)
CORS(app)

# Set up logging for production
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info(70 * "*")
app.logger.info("  A C C O U N T   S E R V I C E   R U N N I N G  ".center(70, "*"))
app.logger.info(70 * "*")


try:
    from service import models  # noqa: F401
    models.init_db(app)
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    sys.exit(4)

app.logger.info("Service initialized!")

from service import routes  # noqa: F401
from service.common import error_handlers, cli_commands  # noqa: F401
