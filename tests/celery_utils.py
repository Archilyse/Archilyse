import json
import math
import os
from datetime import datetime, timedelta
from http import HTTPStatus
from time import sleep
from typing import Dict, List, Optional, Union

import requests
from celery.states import READY_STATES, SUCCESS, UNREADY_STATES
from celery.worker.control import revoke
from contexttimer import timer
from requests.auth import HTTPBasicAuth
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_fixed,
)

from common_utils.exceptions import BaseSlamException
from common_utils.logger import logger
from common_utils.utils import running_on_docker_container
from tests.utils import TestRetryException, get_redis

TASK_PENDING_TIMEOUT = 200


def trigger_task_and_wait_for_backend(task, **kwargs):
    """Triggers a task directly and stores results in the context.

    Args:
        task (Task): The task to run.
        kwargs (**dict): Kwargs to pass to the task.
    """
    if not running_on_docker_container():
        logger.warning(
            "Running a task with CELERY_EAGER does NOT trigger tasks, "
            "any exceptions will raise immediately"
        )

    task_result = task.delay(**kwargs)

    # we want to make sure the wait for task results will have the info available in
    # the DB at the assertion point
    while True:
        tasks_ids = {x["task_id"] for x in get_celery_tasks_statuses_from_db()}
        if task_result.task_id in tasks_ids:
            return task_result.task_id


class RetryCeleryException(Exception):
    pass


class CeleryTaskOnlyInDB(Exception):
    pass


@retry(
    retry=retry_if_exception_type(RetryCeleryException),
    wait=wait_fixed(wait=0.1),
    stop=stop_after_attempt(150),
    reraise=True,
)
def get_celery_tasks_statuses_from_db(num_tasks_expected: Optional[int] = None):
    """DB task metadata is restarted for every scenario as a guarantee for asserting
    only tasks of the current scenario.
    Flower contains results from previous scenarios as it doesn't get restarted
    every time.
    If the tasks are not triggered through the method trigger_task_and_wait_for_backend
    then the parameter num_tasks_expected will be used to control the number of tasks
    expected to be inserted in the celery backend.
    """
    redis = get_redis()
    keys = []
    for _ in range(5):
        keys = redis.keys("celery-task-meta-*")
        if not keys and num_tasks_expected != 0:
            raise RetryCeleryException("no tasks has been triggered")
        elif num_tasks_expected and len(keys) < num_tasks_expected:
            raise RetryCeleryException(
                "Not all the expected tasks are in the DB yet. Existing results in the DB: "
                + "\n".join(get_detailed_info_for_keys(keys))
            )
        # get values from redis
        return [json.loads(x) for x in redis.mget(keys)]

    raise BaseSlamException(
        f"{len(keys)} have been triggered and {num_tasks_expected} were expected"
    )


def get_detailed_info_for_keys(keys: list[bytes]) -> list[str]:
    redis = get_redis()
    task_ids = [json.loads(x)["task_id"] for x in redis.mget(keys)]
    result = []

    for task_id in task_ids:
        task_metadata = get_celery_metadata_from_flower_api(task_id=task_id)
        try:
            result.append(f"{task_metadata['name']} - {task_metadata['state']}")
        except CeleryTaskOnlyInDB:
            result.append(f"{task_id} - Task only in DB")

    return result


@retry(
    retry=retry_if_exception_type(
        (requests.exceptions.ConnectionError, TestRetryException)
    ),
    wait=wait_exponential(multiplier=2, max=20),
    stop=stop_after_attempt(10),
    reraise=True,
)
def get_celery_metadata_from_flower_api(task_id: str) -> Union[List[Dict], Dict]:
    """Flower contains results from previous scenarios as it doesn't get restarted
    after each scenario but it provides additional information to the backend DB and
    sooner than the DB as it is sync with rabbitmq directly. In the version 1.0.0 of
    flower (still in development) retrieving the info by task id is fixed.

    After celery 5.x it is also the only option to understand which tasks have been really
    triggered from a chain with errors as the DB will contain the entire chain before it
    runs.

    Some retries might be necessary while the status of the task is fully synchronized
    in flower.

    Returns:
        if task_id is None:
            A list with metadata of the task in the order they were
            requested, being the last one the last sent to be executed
        else:
            a dictionary with the metadata
    """
    response = requests.get(
        f"{get_flower_address()}/api/task/info/{task_id}",
        auth=HTTPBasicAuth(os.environ["FLOWER_USER"], os.environ["FLOWER_PASSWORD"]),
    )
    if response.ok:
        task_metadata = response.json()
        if task_metadata["state"] not in READY_STATES:
            raise TestRetryException("Flower API not yet sync")
        return task_metadata
    elif response.status_code == HTTPStatus.NOT_FOUND:
        raise CeleryTaskOnlyInDB(
            "Could not get tasks information from flower api. "
            "Likely a task of a chain that wasn't executed"
        )
    else:
        raise TestRetryException("Error in flower API")


def get_flower_all_tasks_metadata(after_time: float = None) -> List[Dict]:
    response = requests.get(
        f"{get_flower_address()}/api/tasks?offset=0",
        auth=HTTPBasicAuth(os.environ["FLOWER_USER"], os.environ["FLOWER_PASSWORD"]),
    )
    tasks_metadata = response.json()
    return list(
        sorted(
            [
                t
                for t in tasks_metadata.values()
                if (after_time and t.get("received") >= after_time) or not after_time
            ],
            key=lambda x: x["received"] or -math.inf,
        )
    )


@timer(logger=logger)
def confirm_no_tasks_unfinished(num_tasks_expected=0):
    """Raises exception if there are celery tasks triggered and not controlled by the test"""
    try:
        db_tasks_results = get_celery_tasks_statuses_from_db(
            num_tasks_expected=num_tasks_expected
        )
    except Exception:
        return

    unfinished_tasks = []
    for task_result in db_tasks_results:
        task_id = task_result["task_id"]
        if task_result["status"] not in READY_STATES:
            task_metadata = get_celery_metadata_from_flower_api(task_id=task_id)
            unfinished_tasks.append(
                dict(
                    name=task_metadata["name"],
                    state=task_metadata["state"],
                    kwargs=task_metadata["kwargs"],
                )
            )

    # Check flower
    for task_metadata in get_flower_all_tasks_metadata():
        if task_metadata["state"] not in READY_STATES:
            unfinished_tasks.append(
                dict(
                    name=task_metadata["name"],
                    state=task_metadata["state"],
                    kwargs=task_metadata["kwargs"],
                )
            )

    # Check flower
    for task_metadata in get_flower_all_tasks_metadata():
        if task_metadata["state"] not in READY_STATES:
            unfinished_tasks.append(
                dict(name=task_metadata["name"], kwargs=task_metadata["kwargs"])
            )

    if len(unfinished_tasks):
        raise BaseSlamException(
            f"Following tasks are still running: {unfinished_tasks} from the previous test executed"
        )


def chords_pending():
    for task_metadata in get_flower_all_tasks_metadata():
        if (
            task_metadata["name"] == "celery.chord_unlock"
            and task_metadata["state"] != SUCCESS
        ):
            return True
    return False


def wait_for_celery_tasks(
    wait_for_subtasks=True, num_tasks_expected: Optional[int] = None
):
    """Actively waits for all tasks and optionally subtasks returning task metadata.

    Args:
        wait_for_subtasks (bool, optional): Whether to process subtasks or to kill them.

    Returns:
        List[Dict]: with task metadata
    """
    results = {}
    non_ready_tasks = set()
    ping = start = datetime.utcnow()
    while True:
        if chords_pending():
            sleep(0.1)
            continue

        db_tasks_results = get_celery_tasks_statuses_from_db(
            num_tasks_expected=num_tasks_expected
        )
        for task_result in db_tasks_results:
            task_id = task_result["task_id"]
            if task_result["status"] in READY_STATES and task_id not in results:
                try:
                    task_metadata = get_celery_metadata_from_flower_api(task_id=task_id)
                except CeleryTaskOnlyInDB:
                    continue
                while task_metadata["state"] not in READY_STATES:
                    # if flower is not updated as like the DB
                    task_metadata = get_celery_metadata_from_flower_api(task_id=task_id)

                results[task_id] = task_metadata
                sub_tasks_ids = task_metadata.get("children", [])
                _add_sub_tasks_ids(non_ready_tasks, sub_tasks_ids)

                if not wait_for_subtasks:
                    for sub_task_id in sub_tasks_ids:
                        revoke(sub_task_id, terminate=True)

                logger.debug(
                    f"Completed task: {task_id} of name {task_metadata['name']}, "
                    f"with kwargs {task_metadata['kwargs']} "
                    f"and state {task_metadata['state']}"
                )

            else:
                non_ready_tasks.add(task_id)

        # All the ready task that have been added to results will be removed from the non ready tasks set
        for ready_task_id in results:
            non_ready_tasks.discard(ready_task_id)

        if not non_ready_tasks:
            return list(results.values())

        if non_ready_tasks and datetime.utcnow() - start > timedelta(
            seconds=TASK_PENDING_TIMEOUT
        ):
            raise TimeoutError(
                f"Tasks {','.join(non_ready_tasks)} are still not ready after {TASK_PENDING_TIMEOUT} seconds, it's likely "
                "workers aren't configured correctly"
            )

        if datetime.utcnow() - ping > timedelta(minutes=1):
            flower_tasks = {x["uuid"]: x for x in get_flower_all_tasks_metadata()}
            metadatas = [flower_tasks[x["task_id"]] for x in db_tasks_results]
            logger.debug(
                f"Still waiting for the following tasks to end the execution: "
                f'{",".join([",".join((x["name"],x["uuid"],x["state"])) for x in metadatas if x["state"] in UNREADY_STATES])}'
            )
            ping = datetime.utcnow()


def _add_sub_tasks_ids(non_ready_tasks, sub_tasks_ids):
    """Avoids adding tasks from choords"""
    for child_id in sub_tasks_ids:
        sub_task_metadata = get_celery_metadata_from_flower_api(task_id=child_id)
        if sub_task_metadata.get("name") != "celery.chord_unlock":
            non_ready_tasks.add(child_id)


def get_flower_address():
    flower_port = os.environ["FLOWER_PORT"]
    flower_host = os.environ["FLOWER_HOST"]
    return f"http://{flower_host}:{flower_port}"
