import math
from datetime import datetime
from typing import Union

from common_utils.constants import TASK_TYPE


def vector_stats_key(task_type: TASK_TYPE, dimension: str, field_name: str) -> str:
    if task_type == TASK_TYPE.SUN_V2:
        date_parsed = datetime.strptime(dimension[4:20], "%Y-%m-%d %H:%M")
        date_string = datetime.strftime(date_parsed, "%Y%m%d%H%M")
        return f"sun_{date_string}_{field_name}".lower()
    elif task_type == TASK_TYPE.VIEW_SUN:
        return f"view_{dimension}_{field_name}".lower()
    elif task_type == TASK_TYPE.CONNECTIVITY:
        return f"{dimension}_{field_name}".lower()
    elif task_type == TASK_TYPE.NOISE:
        return dimension.lower()
    elif task_type == TASK_TYPE.NOISE_WINDOWS:
        return f"window_{dimension}_{field_name}".lower()
    else:
        raise Exception(f"Unsupported task type {task_type.name}")


def vector_stats_format_value(task_type: TASK_TYPE, value: Union[float, None]):
    if task_type == TASK_TYPE.VIEW_SUN and value is not None:
        return value / (4 * math.pi)
    return value
