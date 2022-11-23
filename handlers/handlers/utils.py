import math
import os
from collections import defaultdict
from typing import Any, Callable, Iterable, Optional, TypedDict

from sqlalchemy import inspect

from common_utils.constants import (
    NOISE_SURROUNDING_TYPE,
    SIMULATION_VALUE_TYPE,
    SUN_DAYTIMES,
    SUN_DIMENSION,
    UNIT_BASICS_DIMENSION,
    VIEW_DIMENSION,
    VIEW_DIMENSION_2,
)
from common_utils.exceptions import ValidationException


def get_client_bucket_name(client_id: int) -> str:
    return f"{os.environ['GCLOUD_CLIENT_BUCKET_PREFIX']}{client_id}"


def get_simulation_name(
    dimension: VIEW_DIMENSION
    | SUN_DIMENSION
    | UNIT_BASICS_DIMENSION
    | SUN_DAYTIMES
    | NOISE_SURROUNDING_TYPE,
    value_type: Optional[SIMULATION_VALUE_TYPE] = None,
) -> str:
    simulation_db_name_prefix_map = {
        VIEW_DIMENSION: "View",
        VIEW_DIMENSION_2: "View",
        SUN_DIMENSION: "Sun",
        SUN_DAYTIMES: "SunByDaytime",
        UNIT_BASICS_DIMENSION: "UnitBasics",
        NOISE_SURROUNDING_TYPE: "Noise",
    }

    if (
        isinstance(dimension, (VIEW_DIMENSION, VIEW_DIMENSION_2, SUN_DIMENSION))
        and value_type is not None
    ):
        return (
            f"{simulation_db_name_prefix_map[type(dimension)]}."
            f"{value_type.value}."
            f"{dimension.value}"
        )
    elif isinstance(dimension, UNIT_BASICS_DIMENSION):
        return f"{simulation_db_name_prefix_map[type(dimension)]}.{dimension.value}"
    elif (
        isinstance(dimension, (SUN_DAYTIMES, NOISE_SURROUNDING_TYPE))
        and value_type is not None
    ):
        return f"{simulation_db_name_prefix_map[type(dimension)]}.{value_type.value}.{dimension.name.lower()}"

    raise ValidationException(f"Invalid dimension requested: {dimension}")


def group_by(
    entities: Iterable[dict],
    key: Callable,
) -> Any:
    groups = defaultdict(list)
    for entity in entities:
        groups[key(entity)].append(entity)
    return groups


def aggregate_stats_dimension(
    stats: list[dict[str, float | int]]
) -> dict[str, float | int]:
    min_value = min((u["min"] for u in stats), default=0)
    max_value = max((u["max"] for u in stats), default=0)

    n = 0.0
    sum_of_squares = 0.0
    for u in stats:
        n += u["count"]
        sum_of_squares += pow(u["stddev"], 2) * u["count"] + u["count"] * pow(
            u["mean"], 2
        )

    if n > 0:
        mean_value = sum(u["mean"] * u["count"] for u in stats) / sum(
            (u["count"] for u in stats)
        )
        variance = (sum_of_squares - n * pow(mean_value, 2)) / n
    else:
        mean_value = 0.0
        variance = 0.0

    if variance > 0.0:
        stddev_value = math.sqrt(variance)
    else:
        stddev_value = 0.0

    return {
        "min": min_value,
        "max": max_value,
        "mean": mean_value,
        "stddev": stddev_value,
        "count": int(n),
    }


def get_site_id_from_any_level(params: dict) -> int | None:
    from handlers.db import PlanDBHandler, UnitDBHandler

    if params.get("plan_id") is not None:
        return PlanDBHandler.get_by(id=params.get("plan_id"))["site_id"]

    elif params.get("floor_id") is not None:
        from handlers.db import SiteDBHandler

        return SiteDBHandler.get_by_floor_id(params["floor_id"])["id"]

    elif params.get("building_id") is not None:
        from handlers.db import BuildingDBHandler

        return BuildingDBHandler.get_by(id=params.get("building_id"))["site_id"]

    elif params.get("site_id") is not None:
        return params["site_id"]

    elif params.get("unit_id") is not None:
        return UnitDBHandler.get_by(id=params.get("unit_id"))["site_id"]

    else:
        return None


class PartialUnitInfo(TypedDict):
    id: int
    client_id: str
    floor_id: int
    unit_usage: str


def sql_object_as_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}
