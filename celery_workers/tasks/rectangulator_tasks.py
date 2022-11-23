from typing import Dict

from brooks.types import AreaType
from tasks.utils.utils import celery_retry_task

AREA_TYPES_TO_EXCLUDE = {
    AreaType.NOT_DEFINED,
    AreaType.VOID,
    AreaType.OUTDOOR_VOID,
    AreaType.SHAFT,
    AreaType.ELEVATOR,
    AreaType.STAIRCASE,
}


@celery_retry_task
def biggest_rectangle_task(self, site_id: int, run_id: str):
    from common_utils.constants import UNIT_USAGE
    from handlers import SiteHandler, SlamSimulationHandler
    from handlers.db import UnitDBHandler
    from simulations.rectangulator import get_max_rectangle_in_convex_polygon

    residential_unit_ids = set(
        UnitDBHandler.find_ids(
            site_id=site_id,
            unit_usage=UNIT_USAGE.RESIDENTIAL.name,
        )
    )

    residential_unit_layouts = [
        (unit_info, layout)
        for unit_info, layout in SiteHandler.get_unit_layouts(
            site_id=site_id, scaled=True
        )
        if unit_info["id"] in residential_unit_ids
    ]

    biggest_rectangle_by_area: Dict[int, str] = {}
    for _, unit_layout in residential_unit_layouts:
        for area in unit_layout.areas:
            if (
                area.type not in AREA_TYPES_TO_EXCLUDE
                and area.db_area_id not in biggest_rectangle_by_area
            ):
                biggest_rectangle_by_area[
                    area.db_area_id
                ] = get_max_rectangle_in_convex_polygon(
                    target_convex_polygon=area.footprint, generations=500
                ).wkt

    SlamSimulationHandler.store_results(
        run_id=run_id,
        results={
            unit_info["id"]: {
                area.db_area_id: biggest_rectangle_by_area[area.db_area_id]
                for area in unit_layout.areas
                if area.type not in AREA_TYPES_TO_EXCLUDE
            }
            for unit_info, unit_layout in residential_unit_layouts
        },
    )
