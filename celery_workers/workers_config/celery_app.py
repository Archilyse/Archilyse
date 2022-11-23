import logging
import os
from distutils.util import strtobool

import scout_apm.celery
from celery import Celery
from celery._state import get_current_task
from celery.signals import setup_logging
from scout_apm.api import Config

from common_utils.logging_config import DefaultLogFormatter, configure_logging

celery_app = Celery("workers")
celery_app.config_from_object("workers_config.celery_config")


if not strtobool(os.environ.get("TEST_ENVIRONMENT", "False")):
    Config.set(
        key=os.environ["SCOUT_KEY"],
        name="Archilyse API",
        monitor=True,
    )
    scout_apm.celery.install(celery_app)


class TaskLogFormatter(DefaultLogFormatter):
    def format(self, record: logging.LogRecord):
        task = get_current_task()
        if task and task.request:
            record.__dict__.update(task_id=task.request.id, task_name=task.name)
        return super().format(record)


@setup_logging.connect
def setup_logger(*args, **kwargs):
    configure_logging(formatter=TaskLogFormatter)
