import math
from collections import defaultdict
from functools import partial
from itertools import chain
from typing import Iterable, Iterator, Optional

from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box

from brooks.models import SimLayout, SimOpening
from brooks.util.geometry_ops import get_line_strings, get_polygons
from common_utils.constants import (
    NOISE_SOURCE_TYPE,
    NOISE_SURROUNDING_TYPE,
    NOISE_TIME_TYPE,
    REGION,
    SIMULATION_VERSION,
    TASK_TYPE,
)
from common_utils.typing import AreaID, LocationTuple, NoiseAreaResultsType, UnitID
from handlers import SlamSimulationHandler
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.osm import OSMBuildingsHandler
from surroundings.swisstopo import SwissTopoBuildingSurroundingHandler


def fishnet_split(
    geometry: LineString, col_width: float, row_width: float
) -> list[LineString]:
    """Splits a LineString by a grid (fishnet) with specified column and row width."""
    x_min, y_min, x_max, y_max = geometry.bounds
    cols = math.ceil((x_max - x_min) / col_width) or 1
    rows = math.ceil((y_max - y_min) / row_width) or 1
    geoms: list[LineString] = []
    for row in range(rows):
        for col in range(cols):
            cell = box(
                x_min + col * col_width,
                y_min + row * row_width,
                x_min + (col + 1) * col_width,
                y_min + (row + 1) * row_width,
            )
            geom = geometry.intersection(cell)
            for linestring in get_line_strings(geometry=geom):
                if not any(g.equals(linestring) for g in geoms):
                    geoms.append(linestring)
    return geoms


def get_surrounding_footprints(
    site_id: int,
    location: Point,
    region: REGION,
    simulation_version: SIMULATION_VERSION,
    bounding_box_extension: int,
) -> Iterable[Polygon | MultiPolygon]:
    buildings_handler_cls = partial(OSMBuildingsHandler, region=region)
    if region == REGION.CH:
        buildings_handler_cls = SwissTopoBuildingSurroundingHandler
    buildings_handler = buildings_handler_cls(
        location=location,
        bounding_box_extension=bounding_box_extension,
        simulation_version=simulation_version,
    )

    exclusion_area = ManualExclusionSurroundingHandler(
        site_id=site_id, region=region
    ).get_footprint()
    surrounding_footprints: Iterator[Polygon] = (
        footprint_part
        for building in buildings_handler.get_buildings()
        for footprint_part in get_polygons(
            building.footprint.difference(exclusion_area)
        )
    )

    if manual_buildings := ManualBuildingSurroundingHandler(
        site_id=site_id,
        region=region,
        elevation_handler=ZeroElevationHandler(),
    ).get_footprint():
        surrounding_footprints = chain(
            surrounding_footprints, get_polygons(manual_buildings)
        )

    yield from surrounding_footprints


def get_opening_sample_location_for_noise(
    opening: SimOpening, footprint_facade: Polygon
) -> Optional[LocationTuple]:
    """Returns a window sample location slightly in front of the window/door"""
    # NOTE we use the footprint excluding balconies as otherwise
    # any ray starting from a window in front of a balcony would always
    # intersect with the balcony's footprint
    # Loggias with windows instead of railings should also work as the windows
    # of loggias are subtracted on the blocking elements
    if location_2d := (
        opening.footprint.buffer(0.5).difference(footprint_facade).centroid
    ):
        return location_2d.x, location_2d.y, opening.mid_height_point
    return None


def sample_locations_by_area(plan_layout: SimLayout, target_layout: SimLayout):
    footprint_facade = plan_layout.footprint_facade
    locations_by_area = defaultdict(list)
    for area in target_layout.areas:
        for opening in target_layout.get_windows_and_outdoor_doors(area=area):
            if location := get_opening_sample_location_for_noise(
                opening=opening, footprint_facade=footprint_facade
            ):
                locations_by_area[area.db_area_id].append(location)
    return locations_by_area


def get_noise_window_per_area(
    site_id: int,
) -> dict[UnitID, dict[AreaID, NoiseAreaResultsType]]:
    area_window_noises = SlamSimulationHandler.get_latest_results(
        site_id=site_id, task_type=TASK_TYPE.NOISE_WINDOWS
    )
    return format_area_window_noises(area_window_noises=area_window_noises)


def format_area_window_noises(
    area_window_noises: dict[str, dict[str, dict]]
) -> dict[UnitID, dict[AreaID, NoiseAreaResultsType]]:
    # iterate area_window_noises and make area_ids float and observations points lists of tuples
    formatted = {
        int(unit_id): {int(area_id): values for area_id, values in areas_info.items()}
        for unit_id, areas_info in area_window_noises.items()
    }
    for _unit_id, areas_info in formatted.items():
        for _area_id, values in areas_info.items():
            values["observation_points"] = [
                tuple(op) for op in values["observation_points"]
            ]
    return formatted  # type: ignore


def aggregate_noises(noises: list[float]) -> float:
    """Decibels are logarithmic quantities.
    Formula as per http://apps.usd.edu/coglab/schieber/psyc707/pdf/AddedNoiseLevels.pdf
    """
    return 10 * math.log(sum(pow(10, n / 10) for n in noises), 10) if noises else 0.0


def get_noise_surrounding_type(
    noise_source: NOISE_SOURCE_TYPE, noise_time: NOISE_TIME_TYPE
) -> NOISE_SURROUNDING_TYPE:
    return NOISE_SURROUNDING_TYPE[f"{noise_source.name}_{noise_time.name}"]
