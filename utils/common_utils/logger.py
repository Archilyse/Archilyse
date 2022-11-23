import logging.config
import os
from distutils.util import strtobool

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.tornado import TornadoIntegration

from .logging_config import configure_logging

# NOTE fallback logging config
# in case logging was not configured yet
configure_logging()

if strtobool(os.environ.get("PRODUCTION_SENTRY_LOGGING", "False")):

    def ignore_basic_features_exception(event, hint):
        from common_utils.exceptions import BasicFeaturesException

        if "exc_info" in hint:
            exc_type, exc_value, tb = hint["exc_info"]
            if isinstance(exc_value, BasicFeaturesException):
                return None
        return event

    try:
        for logger_to_ignore in ["fiona._env", "shapely.geos"]:
            ignore_logger(logger_to_ignore)
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            release=f'slam@{os.environ.get("SLAM_VERSION")}',
            dsn=os.environ["SENTRY_DSN"],
            integrations=[
                sentry_logging,
                CeleryIntegration(),
                FlaskIntegration(),
                SqlalchemyIntegration(),
                TornadoIntegration(),
            ],
            environment="python",
            before_send=ignore_basic_features_exception,
        )
    except KeyError as e:
        raise KeyError("Sentry logging is activated but no DSN is specified") from e


logger = logging.getLogger(os.environ.get("LOGGER_SERVICE_NAME", "slam"))
