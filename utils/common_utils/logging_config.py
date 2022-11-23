import logging
import logging.config
import os
from distutils.util import strtobool
from pathlib import Path
from typing import Any, Dict, Type

from logstash_formatter import LogstashFormatterV1


def configure_logging(formatter: Type[logging.Formatter] | None = None):
    app_name = os.environ.get("LOGGER_SERVICE_NAME", "slam")
    log_level = os.environ.get("LOGGER_LEVEL", "INFO")

    standard_formatter: Dict[str, Any] = (
        {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
        if (not formatter or strtobool(os.environ.get("TEST_ENVIRONMENT", "False")))
        else {
            "()": formatter,
        }
    )

    handlers = {}
    if logs_destination_folder_str := os.environ.get("LOGS_DESTINATION_FOLDER"):
        logs_destination_folder = Path(logs_destination_folder_str).joinpath(
            f"{app_name}"
        )
        logs_destination_folder.mkdir(parents=True, exist_ok=True)
        log_filename = logs_destination_folder.joinpath(f"{app_name}.log")
        handlers["rotating_file_handler"] = {
            "formatter": "standard",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_filename,
            "maxBytes": 1024 * 1024 * 1024,
            "backupCount": 5,
        }

    if strtobool(os.environ.get("LOGGER_STDOUT_STREAM", "true")):
        handlers["stream_handler"] = {
            "formatter": "standard",
            "class": "logging.StreamHandler",
        }

    logging.config.dictConfig(
        config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": standard_formatter},
            "handlers": handlers,
            "loggers": {
                "": {
                    # NOTE for 3rd party loggers
                    "handlers": list(handlers.keys()),
                    "level": "WARNING",
                    "propagate": False,
                },
                app_name: {
                    "handlers": list(handlers.keys()),
                    "level": log_level,
                    "propagate": False,
                },
            },
        }
    )


class DefaultLogFormatter(LogstashFormatterV1):
    level_to_severity_map = {
        logging.ERROR: "ERROR",
        logging.WARNING: "WARNING",
        logging.WARN: "WARNING",
        logging.INFO: "INFO",
        logging.DEBUG: "DEBUG",
        logging.CRITICAL: "CRITICAL",
        logging.NOTSET: "DEFAULT",
    }

    def format(self, record):
        record.severity = self.level_to_severity_map.get(record.levelno, "DEFAULT")
        return super(DefaultLogFormatter, self).format(record)
