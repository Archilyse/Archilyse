import inspect
import os
import sys
import types
from contextlib import contextmanager
from http import HTTPStatus
from itertools import tee, zip_longest
from typing import Iterator, Tuple, Type, Union

import requests

from common_utils.constants import SIMULATION_VERSION, VIEW_DIMENSION, VIEW_DIMENSION_2
from common_utils.logger import logger


def running_on_docker_container():
    return os.path.exists("/.dockerenv")


def decorate_all_public_methods(decorator):
    def decorate(cls):
        for name, public_method in get_class_public_methods(cls):
            setattr(cls, name, decorator(public_method))
        return cls

    return decorate


def get_class_public_methods(
    cls,
) -> Iterator[Tuple[str, Union[types.MethodType, types.FunctionType]]]:
    for name, method in inspect.getmembers(cls):
        if isinstance(
            method, (types.MethodType, types.FunctionType)
        ) and not name.startswith("_"):
            yield name, method


@contextmanager
def recursionlimit(limit):
    old_limit = sys.getrecursionlimit()

    try:
        yield sys.setrecursionlimit(limit)
    finally:
        sys.setrecursionlimit(old_limit)


def pairwise(iterable):
    """https://docs.python.org/3/library/itertools.html s -> (s0,s1), (s1,s2), (s2, s3), ..."""
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def grouper(iterable, n, fillvalue=None):
    """https://docs.python.org/3/library/itertools.html -> Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def post_message_to_slack(text: str, channel: str = "#view-alerts"):
    response = requests.post(
        "https://slack.com/api/chat.postMessage",
        {
            "token": os.environ.get("VIEW_ALERTS_SLACK_AUTH_TOKEN", ""),
            "channel": channel,
            "text": text,
        },
    )

    if response.status_code != HTTPStatus.OK or not response.json().get("ok"):
        logger.error(f"Cant connect to slack: {response.json()}")


def get_view_dimension(
    simulation_version: SIMULATION_VERSION,
) -> Union[Type[VIEW_DIMENSION_2], Type[VIEW_DIMENSION]]:
    if simulation_version in {
        SIMULATION_VERSION.EXPERIMENTAL,
        SIMULATION_VERSION.PH_2022_H1,
    }:
        return VIEW_DIMENSION_2
    return VIEW_DIMENSION
