from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterator, Tuple
from uuid import uuid4

import psycopg2
import pydot
import sqlalchemy
from celery import chord, group
from celery.canvas import Signature, _chain
from celery.result import AsyncResult
from celery.utils.graph import DependencyGraph

from brooks.util.io import BrooksJSONEncoder
from common_utils.exceptions import BasicFeaturesException
from tasks.utils.constants import CELERY_MAX_RETRIES, CELERY_RETRYBACKOFF
from workers_config.celery_app import celery_app


def create_run_id():
    return str(uuid4())


def get_celery_task_state(task_id):
    task_info = AsyncResult(task_id)
    task_info._get_task_meta()
    return task_info.state


def celery_retry_task(*args, **kwargs):
    return celery_app.task(
        *args,
        bind=True,
        retry_jitter=True,
        autoretry_for=(
            psycopg2.OperationalError,
            psycopg2.errors.SerializationFailure,
            sqlalchemy.exc.OperationalError,
        ),
        default_retry_delay=5,  # 5 seconds
        retry_backoff=CELERY_RETRYBACKOFF,
        retry_kwargs={"max_retries": CELERY_MAX_RETRIES},
        **kwargs,
    )


def format_basic_feature_errors(exc: Exception):
    if isinstance(exc, BasicFeaturesException):
        if exc.violations:
            return BrooksJSONEncoder.default({"errors": exc.violations})
        return BrooksJSONEncoder.default({"errors": str(exc)})
    return BrooksJSONEncoder.default({"errors": ["Report the error to tech", str(exc)]})


class WorkflowPlotter:
    def __init__(self, canvas):
        self.canvas = canvas
        self.task_ids = defaultdict(list)

    def _get_unique_task_name(self, task: Signature) -> str:
        task_id = id(task)
        task_str = str(task)
        if task_id not in self.task_ids[task_str]:
            self.task_ids[task_str].append(task_id)
        self.task_ids[task_str].index(task_id)
        return f"{task_str} ({self.task_ids[task_str].index(task_id)})"

    def _get_task_dependencies(self, canvas) -> Iterator[str]:
        if isinstance(canvas, _chain):
            yield from self._get_task_dependencies(canvas.tasks[-1])
        elif isinstance(canvas, chord):
            yield from self._get_task_dependencies(canvas.body)
        elif isinstance(canvas, group):
            for task in canvas.tasks:
                yield from self._get_task_dependencies(task)
        else:
            yield self._get_unique_task_name(canvas)

    def _get_dependency_graph(
        self, canvas, dependencies=None
    ) -> Iterator[Tuple[str, list[str]]]:
        dependencies = dependencies or []

        if isinstance(canvas, _chain):
            for task in canvas.tasks:
                yield from self._get_dependency_graph(task, dependencies)
                dependencies = list(self._get_task_dependencies(task))
        elif isinstance(canvas, chord):
            for task in canvas.tasks:
                yield from self._get_dependency_graph(task, dependencies)
            yield from self._get_dependency_graph(
                canvas.body,
                [d for t in canvas.tasks for d in self._get_task_dependencies(t)],
            )
        elif isinstance(canvas, group):
            for task in canvas.tasks:
                yield from self._get_dependency_graph(task, dependencies)
        else:
            yield self._get_unique_task_name(canvas), dependencies

    def as_graph(self) -> Any:
        dependency_graph = DependencyGraph(it=self._get_dependency_graph(self.canvas))
        with NamedTemporaryFile(mode="w+") as f:
            dependency_graph.to_dot(f)
            f.flush()
            (graph,) = pydot.graph_from_dot_file(f.name)
            return graph

    def to_png(self, output: str | Path):
        self.as_graph().write_png(Path(output).with_suffix(".png"))

    def to_dot(self, output: str | Path):
        dependency_graph = DependencyGraph(it=self._get_dependency_graph(self.canvas))
        with Path(output).with_suffix(".dot").open(mode="w+") as f:
            dependency_graph.to_dot(f)
