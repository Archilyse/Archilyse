import math
from collections import defaultdict
from datetime import datetime
from itertools import product
from pathlib import Path
from typing import Any, Dict, Iterator, List, Tuple

import fiona
from geoalchemy2 import WKBElement
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon, box

from brooks.util.geometry_ops import get_polygons
from common_utils.chunker import chunker
from common_utils.constants import ADMIN_SIM_STATUS, SIMULATION_TYPE
from handlers.db.potential_simulation_handler import SRID, PotentialSimulationDBHandler
from surroundings.utils import Bounds

Entity = Dict[str, Any]

SUN_SCHEMA = {
    "geometry": "3D Point",
    "properties": {
        "footprint_id": "str",
        "level": "int",
        "201803210800": "float",
        "201803211000": "float",
        "201803211200": "float",
        "201803211400": "float",
        "201803211600": "float",
        "201803211800": "float",
        "201806210600": "float",
        "201806210800": "float",
        "201806211000": "float",
        "201806211200": "float",
        "201806211400": "float",
        "201806211600": "float",
        "201806211800": "float",
        "201806212000": "float",
        "201812211000": "float",
        "201812211200": "float",
        "201812211400": "float",
        "201812211600": "float",
    },
}
VIEW_SCHEMA = {
    "geometry": "3D Point",
    "properties": {
        "footprint_id": "str",
        "level": "int",
        "ground": "float",
        "greenery": "float",
        "buildings": "float",
        "sky": "float",
        "site": "float",
        "water": "float",
        "isovist": "float",
        "railway_tracks": "float",
        "highways": "float",
        "pedestrians": "float",
        "primary_streets": "float",
        "secondary_streets": "float",
        "tertiary_streets": "float",
        "mountains_class_1": "float",
        "mountains_class_2": "float",
        "mountains_class_3": "float",
        "mountains_class_4": "float",
        "mountains_class_5": "float",
        "mountains_class_6": "float",
    },
}
SIMULATION_TYPE_SCHEMA = {
    SIMULATION_TYPE.VIEW: VIEW_SCHEMA,
    SIMULATION_TYPE.SUN: SUN_SCHEMA,
}
VECTOR_TILE_SIZE_EXPONENT = -2
VECTOR_TILE_SIZE = float(f"1e{VECTOR_TILE_SIZE_EXPONENT}")
VECTOR_TILE_DRIVER = "FlatGeobuf"
VECTOR_TILE_FILE_EXTENSION = "fgb"


class PotentialEntityProvider:
    @staticmethod
    def get_simulation_ids(
        simulation_type: SIMULATION_TYPE, query_shape: Polygon | MultiPolygon
    ) -> List[int]:
        simulations = list(
            PotentialSimulationDBHandler.find(
                type=simulation_type.name,
                status=ADMIN_SIM_STATUS.SUCCESS.name,
                identifier=None,
                special_filter=(
                    WKBElement(data=query_shape.wkb, srid=SRID).ST_Intersects(
                        PotentialSimulationDBHandler.model.building_footprint
                    ),
                ),
                output_columns=["id"],
            )
        )
        return [simulation["id"] for simulation in simulations]

    @staticmethod
    def get_key(simulation_type: SIMULATION_TYPE, dimension: str) -> str:
        if simulation_type == SIMULATION_TYPE.SUN.value:
            date_parsed = datetime.strptime(dimension[4:20], "%Y-%m-%d %H:%M")
            return datetime.strftime(date_parsed, "%Y%m%d%H%M")
        return dimension

    @classmethod
    def make_entities(cls, simulation_info: Dict) -> Iterator[Entity]:
        simulation_values_by_obs_point: Dict[
            Tuple[float, float, float], Dict[str, Any]
        ] = defaultdict(dict)
        for obs_point, dimension, obs_value in (
            (obs_point, cls.get_key(simulation_info["type"], dimension), obs_value)
            for dimension, obs_values in simulation_info["result"].items()
            if dimension != "observation_points"
            for obs_point, obs_value in zip(
                simulation_info["result"]["observation_points"], obs_values
            )
        ):
            obs_point = (obs_point["lon"], obs_point["lat"], obs_point["height"])
            simulation_values_by_obs_point[obs_point]["level"] = simulation_info[
                "floor_number"
            ]
            simulation_values_by_obs_point[obs_point]["footprint_id"] = wkt.loads(
                simulation_info["building_footprint"]
            ).centroid.wkt
            simulation_values_by_obs_point[obs_point][dimension] = obs_value

        for obs_point, properties in simulation_values_by_obs_point.items():
            yield {
                "geometry": {"type": "Point", "coordinates": obs_point},
                "properties": dict(properties),
            }

    @classmethod
    def get_entities(
        cls, simulation_type: SIMULATION_TYPE, query_shape: Polygon | MultiPolygon
    ) -> Iterator[Entity]:
        simulation_ids = cls.get_simulation_ids(
            simulation_type=simulation_type, query_shape=query_shape
        )
        for sim_ids in chunker(simulation_ids, 100):
            simulations = list(
                PotentialSimulationDBHandler.find_in(
                    id=sim_ids,
                    output_columns=[
                        "floor_number",
                        "building_footprint",
                        "result",
                        "type",
                    ],
                )
            )
            yield from (
                entity
                for simulation in simulations
                for entity in cls.make_entities(simulation_info=simulation)
            )


class PotentialTileExporter:
    @staticmethod
    def get_tile_bounds(polygon: Polygon) -> Iterator[Bounds]:
        minx, miny, maxx, maxy = [
            math.floor(dimension * 1 / VECTOR_TILE_SIZE) for dimension in polygon.bounds
        ]
        tile_bottom_left: Iterator[Tuple[int, int]] = product(
            range(miny, maxy + 1),
            range(minx, maxx + 1),
        )
        for bottom, left in tile_bottom_left:
            bottom_float = bottom * VECTOR_TILE_SIZE
            left_float = left * VECTOR_TILE_SIZE
            tile_bounds = (
                left_float,
                bottom_float,
                left_float + VECTOR_TILE_SIZE,
                bottom_float + VECTOR_TILE_SIZE,
            )
            if box(*tile_bounds).intersection(polygon).area:
                yield tile_bounds

    @staticmethod
    def _get_dump_filename(
        simulation_type: SIMULATION_TYPE, bottom: float, left: float
    ) -> str:
        v_prefix = "N" if bottom >= 0 else "S"
        h_prefix = "E" if left >= 0 else "W"
        v_value, h_value = [
            str(abs(round(c * 1 / VECTOR_TILE_SIZE))).zfill(
                3 - VECTOR_TILE_SIZE_EXPONENT
            )
            for c in [bottom, left]
        ]
        return f"{simulation_type.value}_{v_prefix}{v_value}_{h_prefix}{h_value}.{VECTOR_TILE_FILE_EXTENSION}"

    @staticmethod
    def _get_tile_shape(dump_shape: Polygon | MultiPolygon, tile_bounds: Bounds):
        tile_shape = box(*tile_bounds).intersection(dump_shape)
        return MultiPolygon(get_polygons(tile_shape))

    @staticmethod
    def _dump_to_shapefile(
        filename: Path, schema: Dict[str, Any], entities: Iterator[Entity]
    ):
        with fiona.open(
            filename,
            mode="w",
            schema=schema,
            driver=VECTOR_TILE_DRIVER,
            crs=f"EPSG:{SRID}",
        ) as c:
            c.writerecords(entities)

    @staticmethod
    def _get_filtered_entities(
        simulation_type: SIMULATION_TYPE,
        tile_shape: Polygon | MultiPolygon,
        tile_bounds: Bounds,
    ):
        left, bottom, right, top = tile_bounds
        yield from (
            entity
            for entity in PotentialEntityProvider.get_entities(
                simulation_type=simulation_type,
                query_shape=tile_shape,
            )
            if left <= entity["geometry"]["coordinates"][0] < right
            and bottom < entity["geometry"]["coordinates"][1] <= top
        )

    @classmethod
    def dump_to_vector_tile(
        cls, directory: Path, tile_bounds: Bounds, dump_shape: Polygon
    ):
        tile_shape = cls._get_tile_shape(dump_shape=dump_shape, tile_bounds=tile_bounds)
        left, bottom = tile_bounds[:2]
        for simulation_type in SIMULATION_TYPE:
            filename = directory.joinpath(
                cls._get_dump_filename(
                    simulation_type=simulation_type, bottom=bottom, left=left
                )
            )
            entities = cls._get_filtered_entities(
                simulation_type=simulation_type,
                tile_shape=tile_shape,
                tile_bounds=tile_bounds,
            )
            cls._dump_to_shapefile(
                filename=filename,
                schema=SIMULATION_TYPE_SCHEMA[simulation_type],
                entities=entities,
            )
