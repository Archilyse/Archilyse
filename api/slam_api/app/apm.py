import os
from distutils.util import strtobool

from flask import Flask
from scout_apm.flask import ScoutApm


def setup_apm(_app: Flask):
    if not strtobool(os.environ.get("TEST_ENVIRONMENT", "False")):
        # Attach ScoutApm to the Flask App
        ScoutApm(_app)

        # Scout settings
        _app.config["SCOUT_MONITOR"] = True
        _app.config["SCOUT_KEY"] = os.environ["SCOUT_KEY"]
        _app.config["SCOUT_NAME"] = "Archilyse API"
