import hashlib
from dataclasses import asdict
from functools import cached_property
from typing import Any, Collection, Dict, Optional, Set

import pandas as pd
from shapely import wkt
from shapely.geometry import Polygon
from shapely.ops import unary_union

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout
from brooks.types import AreaType, FeatureType, OpeningType
from brooks.util.geometry_ops import get_line_strings
from common_utils.constants import (
    CONNECTIVITY_DIMENSIONS,
    FIXED_SUN_DIMENSIONS,
    NOISE_SURROUNDING_TYPE,
    TASK_TYPE,
    UNIT_USAGE,
    VIEW_DIMENSION_2,
)
from dufresne.polygon import get_sides_as_lines_by_length
from handlers import PlanLayoutHandler, SiteHandler, SlamSimulationHandler, StatsHandler
from handlers.competition import CompetitionFeaturesCalculator
from handlers.db import BuildingDBHandler, FloorDBHandler, UnitDBHandler
from handlers.ph_vector.ph2022.area_vector_schema import (
    AreaVectorSchema,
    AreaVectorStatsSchema,
    BiggestRectangleSchema,
    FloorFeaturesSchema,
    LayoutFeaturesSchema,
    NeufertAreaVectorSchema,
    NeufertGeometryVectorSchema,
)
from handlers.ph_vector.ph2022.utils import vector_stats_format_value, vector_stats_key
from simulations.room_shapes import get_room_shapes

VECTOR_MIN_CORRIDOR_WIDTH = 1.2
VECTOR_STATS_DEFAULT_FIELDS = {"min", "max", "stddev", "mean", "median", "p20", "p80"}


class LayoutFeatures:
    def __init__(self, layouts: Collection[SimLayout]):
        self._layouts = layouts
        self._classification_scheme = UnifiedClassificationScheme()

    def _area_is_navigable(self, area: SimArea, layout: SimLayout) -> bool:
        space = next(space for space in layout.spaces if area in space.areas)
        opening_footprints = [
            opening.footprint
            for opening in layout.spaces_openings[space.id]
            if opening.is_door
        ]
        return CompetitionFeaturesCalculator(
            classification_schema=self._classification_scheme
        ).is_navigable(
            space_footprint=space.footprint,
            opening_footprints=opening_footprints,
            corridor_width=VECTOR_MIN_CORRIDOR_WIDTH,
        )

    @staticmethod
    def _area_element_counts(area: SimArea, layout: SimLayout) -> Dict[str, Any]:
        return {
            "layout_number_of_windows": sum(
                opening.type == OpeningType.WINDOW
                for opening in layout.areas_openings[area.id]
            ),
            "layout_number_of_doors": sum(
                opening.is_door for opening in layout.areas_openings[area.id]
            ),
            "layout_has_bathtub": any(
                feature.type == FeatureType.BATHTUB for feature in area.features
            ),
            "layout_has_shower": any(
                feature.type == FeatureType.SHOWER for feature in area.features
            ),
            "layout_has_sink": any(
                feature.type == FeatureType.SINK for feature in area.features
            ),
            "layout_has_stairs": any(
                feature.type == FeatureType.STAIRS for feature in area.features
            ),
            "layout_has_toilet": any(
                feature.type == FeatureType.TOILET for feature in area.features
            ),
        }

    @staticmethod
    def _area_perimeter_intersection(
        area_footprint: Polygon, sim_element_footprints: Collection[Polygon]
    ) -> float:
        safety_buffer = 0.001
        area_footprint_perimeter = [area_footprint.exterior, *area_footprint.interiors]
        elements_footprint = unary_union(sim_element_footprints).buffer(safety_buffer)
        return sum(
            line.length
            for linear_ring in area_footprint_perimeter
            for line in get_line_strings(linear_ring.intersection(elements_footprint))
        )

    @classmethod
    def _area_perimeter_features(
        cls, area: SimArea, layout: SimLayout
    ) -> Dict[str, float]:
        return {
            "layout_perimeter": area.footprint.length,
            "layout_window_perimeter": cls._area_perimeter_intersection(
                area_footprint=area.footprint,
                sim_element_footprints=[
                    element.footprint
                    for element in layout.openings_by_type[OpeningType.WINDOW]
                ],
            ),
            "layout_door_perimeter": cls._area_perimeter_intersection(
                area_footprint=area.footprint,
                sim_element_footprints=[element.footprint for element in layout.doors],
            ),
            "layout_open_perimeter": cls._area_perimeter_intersection(
                area_footprint=area.footprint,
                sim_element_footprints=[
                    element.footprint for element in layout.area_splitters
                ],
            ),
            "layout_railing_perimeter": cls._area_perimeter_intersection(
                area_footprint=area.footprint,
                sim_element_footprints=[
                    element.footprint for element in layout.railings
                ],
            ),
        }

    @staticmethod
    def _area_has_entrance_door(area: SimArea, layout: SimLayout) -> bool:
        return any(
            opening.type == OpeningType.ENTRANCE_DOOR
            for opening in layout.areas_openings[area.id]
        )

    @staticmethod
    def _area_connects_to_area_type(
        area: SimArea, layout: SimLayout, target_types: Set[AreaType]
    ) -> bool:
        other_areas = layout.areas - {area}
        for opening in layout.areas_openings[area.id]:
            if opening.is_door:
                for other_area in other_areas:
                    if (
                        other_area.type in target_types
                        and opening in layout.areas_openings[other_area.id]
                    ):
                        return True
        return False

    def _get_net_area(self, area: SimArea) -> float:
        return (
            self._classification_scheme.NET_AREA_CONTRIBUTIONS.get(area.type, 0.0)
            * area.footprint.area
        )

    def _get_room_count(self, area: SimArea) -> float:
        return self._classification_scheme.ROOM_COUNTS.get(area.type, 0.0)

    def _make_layout_features(
        self, area: SimArea, layout: SimLayout
    ) -> LayoutFeaturesSchema:
        room_shapes: Dict[str, Any] = {
            f"layout_{dimension}": value
            for dimension, value in get_room_shapes(area.footprint).items()
        }
        perimeter_features: Dict[str, Any] = self._area_perimeter_features(
            area=area, layout=layout
        )
        return LayoutFeaturesSchema(
            layout_area_type=self._classification_scheme.ROOM_VECTOR_NAMING[area.type],
            layout_area=area.footprint.area,
            layout_has_entrance_door=self._area_has_entrance_door(
                area=area, layout=layout
            ),
            layout_is_navigable=self._area_is_navigable(area=area, layout=layout),
            layout_connects_to_bathroom=self._area_connects_to_area_type(
                area=area, layout=layout, target_types={AreaType.BATHROOM}
            ),
            layout_connects_to_private_outdoor=self._area_connects_to_area_type(
                area=area,
                layout=layout,
                target_types=self._classification_scheme.OUTDOOR_AREAS,
            ),
            layout_room_count=self._get_room_count(area=area),
            layout_net_area=self._get_net_area(area=area),
            **self._area_element_counts(area=area, layout=layout),
            **perimeter_features,
            **room_shapes,
        )

    def get_area_features(self) -> Dict[int, LayoutFeaturesSchema]:
        return {
            area.db_area_id: self._make_layout_features(area=area, layout=layout)
            for layout in self._layouts
            for area in layout.areas
            if area.type in self._classification_scheme.ROOM_VECTOR_NAMING
        }


class AreaVectorStats:
    @staticmethod
    def _get_area_vector_stats_config():
        return [
            dict(
                task_type=TASK_TYPE.SUN_V2,
                dimensions=FIXED_SUN_DIMENSIONS,
            ),
            dict(
                task_type=TASK_TYPE.VIEW_SUN,
                dimensions=set(
                    dimension.value
                    for dimension in VIEW_DIMENSION_2
                    if dimension != VIEW_DIMENSION_2.MOUNTAINS_CLASS_1
                ),
            ),
            dict(
                task_type=TASK_TYPE.CONNECTIVITY,
                dimensions={f"connectivity_{d}" for d in CONNECTIVITY_DIMENSIONS},
            ),
            dict(
                task_type=TASK_TYPE.NOISE,
                dimensions=set(dimension.value for dimension in NOISE_SURROUNDING_TYPE),
                stats_fields={"mean"},
            ),
            dict(
                task_type=TASK_TYPE.NOISE_WINDOWS,
                dimensions=set(dimension.value for dimension in NOISE_SURROUNDING_TYPE),
                stats_fields={"min", "max"},
            ),
        ]

    @staticmethod
    def _get_area_vector_stats(
        site_id: int,
        task_type: TASK_TYPE,
        dimensions: Set[str],
        stats_fields: Optional[Set[str]] = None,
    ) -> Dict[int, Dict[int, Dict[str, float]]]:
        vector_stats: Dict[int, Dict[int, Dict[str, float]]] = {}
        unit_area_stats = StatsHandler.get_area_stats(
            site_id=site_id, task_type=task_type, desired_dimensions=dimensions
        )
        for unit_id, area_stats in unit_area_stats.items():
            vector_stats[unit_id] = {}
            for area_id, dimension_stats in area_stats.items():
                vector_stats[unit_id][area_id] = {
                    vector_stats_key(
                        task_type, dimension, field_name
                    ): vector_stats_format_value(task_type, value)
                    for dimension, stats in dimension_stats.items()
                    for field_name, value in stats.items()
                    if field_name in (stats_fields or VECTOR_STATS_DEFAULT_FIELDS)
                }
        return vector_stats

    @classmethod
    def get_vector_stats(
        cls, site_id: int
    ) -> Dict[int, Dict[int, AreaVectorStatsSchema]]:
        vector_stats: Dict[int, Dict[int, Dict[str, float]]] = {}
        for config in cls._get_area_vector_stats_config():
            for unit_id, area_stats in cls._get_area_vector_stats(
                site_id=site_id, **config
            ).items():
                vector_stats.setdefault(unit_id, {})
                for area_id, dimension_stats in area_stats.items():
                    vector_stats[unit_id].setdefault(area_id, {}).update(
                        dimension_stats
                    )
        return {
            unit_id: {
                area_id: AreaVectorStatsSchema(**vector_stats)
                for area_id, vector_stats in area_vector_stats.items()
            }
            for unit_id, area_vector_stats in vector_stats.items()
        }


class BiggestRectangles:
    @staticmethod
    def get_biggest_rectangles(site_id: int) -> Dict[int, BiggestRectangleSchema]:
        biggest_rectangles = {}
        for unit_results in SlamSimulationHandler.get_all_results(
            site_id=site_id, task_type=TASK_TYPE.BIGGEST_RECTANGLE
        ):
            for area_id, biggest_rectangle_wkt in unit_results["results"].items():
                biggest_rectangle = wkt.loads(biggest_rectangle_wkt)
                small_side, long_side = get_sides_as_lines_by_length(
                    polygon=biggest_rectangle
                )[1:3]
                biggest_rectangles[int(area_id)] = BiggestRectangleSchema(
                    layout_biggest_rectangle_length=long_side.length,
                    layout_biggest_rectangle_width=small_side.length,
                )
        return biggest_rectangles


class FloorFeatures:
    def __init__(
        self,
        floors_info: Dict[int, Dict[str, Any]],
        floors_public_layout: Dict[int, SimLayout],
    ):
        self._floors_info = floors_info
        self._floors_public_layout = floors_public_layout

    def _has_elevator(self, floor_id: int) -> bool:
        layout = self._floors_public_layout[floor_id]
        return any(area.type == AreaType.ELEVATOR for area in layout.areas) or any(
            feature.type == FeatureType.ELEVATOR for feature in layout.features
        )

    def get_floor_features(self):
        return {
            floor_id: FloorFeaturesSchema(
                floor_number=self._floors_info[floor_id]["floor_number"],
                floor_has_elevator=self._has_elevator(floor_id=floor_id),
            )
            for floor_id in self._floors_info.keys()
        }


class AreaVector:
    def __init__(self, site_id: int):
        self._site_id = site_id
        self._classification_scheme = UnifiedClassificationScheme()

    def _get_units_info(self, representative_units_only: bool):
        return (
            unit_info
            for unit_info in UnitDBHandler.find(
                site_id=self._site_id,
                unit_usage=UNIT_USAGE.RESIDENTIAL.name,
                output_columns=[
                    "id",
                    "floor_id",
                    "client_id",
                    "representative_unit_client_id",
                ],
            )
            if (unit_info["client_id"] == unit_info["representative_unit_client_id"])
            or not representative_units_only
        )

    @cached_property
    def _units_layout(self):
        return {
            unit_info["id"]: unit_layout
            for unit_info, unit_layout in SiteHandler.get_unit_layouts(
                site_id=self._site_id, scaled=True
            )
        }

    @cached_property
    def _floors_info(self):
        return {
            floor_info["id"]: floor_info
            for floor_info in FloorDBHandler.find_in(
                building_id=list(BuildingDBHandler.find_ids(site_id=self._site_id)),
                output_columns=["id", "floor_number", "plan_id"],
            )
        }

    def _get_floors_public_layouts(self):
        plan_ids = {f["plan_id"] for f in self._floors_info.values()}
        plans_public_layouts = {
            plan_id: PlanLayoutHandler(plan_id=plan_id).get_public_layout()
            for plan_id in plan_ids
        }
        return {
            floor_id: plans_public_layouts[floor_info["plan_id"]]
            for floor_id, floor_info in self._floors_info.items()
        }

    def get_vector(self, representative_units_only: bool):
        vector_stats = AreaVectorStats.get_vector_stats(site_id=self._site_id)
        vector_stats_default_values = AreaVectorStatsSchema()
        biggest_rectangles = BiggestRectangles.get_biggest_rectangles(
            site_id=self._site_id
        )
        biggest_rectangles_default_values = BiggestRectangleSchema()
        layout_features = LayoutFeatures(
            layouts=self._units_layout.values()
        ).get_area_features()
        floor_features = FloorFeatures(
            floors_info=self._floors_info,
            floors_public_layout=self._get_floors_public_layouts(),
        ).get_floor_features()
        return [
            AreaVectorSchema(
                apartment_id=unit_info["client_id"],
                **asdict(floor_features[unit_info["floor_id"]]),
                **asdict(layout_features[area.db_area_id]),
                **asdict(
                    biggest_rectangles.get(
                        area.db_area_id, biggest_rectangles_default_values
                    )
                ),
                **asdict(
                    vector_stats.get(unit_info["id"], {}).get(
                        area.db_area_id, vector_stats_default_values
                    )
                ),
            )
            for unit_info in self._get_units_info(
                representative_units_only=representative_units_only
            )
            for area in self._units_layout[unit_info["id"]].areas
            if area.type in self._classification_scheme.ROOM_VECTOR_NAMING
        ]


class NeufertAreaVector(AreaVector):
    """Our vector for simulation version PH_2022_H1 which also includes the internal
    identifiers of site, building, floor, unit and area. The apartment ids are
    anonymized.

    Used for https://zenodo.org/record/7070952
    """

    @cached_property
    def _floors_info(self):
        return {
            floor_info["id"]: floor_info
            for floor_info in FloorDBHandler.find_in(
                building_id=list(BuildingDBHandler.find_ids(site_id=self._site_id)),
                output_columns=[
                    "id",
                    "floor_number",
                    "plan_id",
                    "building_id",
                    "floor_number",
                ],
            )
        }

    def get_vector(self, representative_units_only: bool, anonymized: bool = True):
        vector_stats = AreaVectorStats.get_vector_stats(site_id=self._site_id)
        vector_stats_default_values = AreaVectorStatsSchema()
        biggest_rectangles = BiggestRectangles.get_biggest_rectangles(
            site_id=self._site_id
        )
        biggest_rectangles_default_values = BiggestRectangleSchema()
        layout_features = LayoutFeatures(
            layouts=self._units_layout.values()
        ).get_area_features()
        floor_features = FloorFeatures(
            floors_info=self._floors_info,
            floors_public_layout=self._get_floors_public_layouts(),
        ).get_floor_features()
        return [
            NeufertAreaVectorSchema(
                site_id=self._site_id,
                building_id=self._floors_info[unit_info["floor_id"]]["building_id"],
                floor_id=unit_info["floor_id"],
                unit_id=unit_info["id"],
                area_id=area.db_area_id,
                apartment_id=hashlib.md5(
                    unit_info["client_id"].encode("utf-8")
                ).hexdigest()
                if anonymized
                else unit_info["client_id"],
                **asdict(floor_features[unit_info["floor_id"]]),
                **asdict(layout_features[area.db_area_id]),
                **asdict(
                    biggest_rectangles.get(
                        area.db_area_id, biggest_rectangles_default_values
                    )
                ),
                **asdict(
                    vector_stats.get(unit_info["id"], {}).get(
                        area.db_area_id, vector_stats_default_values
                    )
                ),
            )
            for unit_info in self._get_units_info(
                representative_units_only=representative_units_only
            )
            for area in self._units_layout[unit_info["id"]].areas
            if area.type in self._classification_scheme.ROOM_VECTOR_NAMING
        ]


class NeufertGeometryVector(NeufertAreaVector):
    """Vector that includes the geometries of separators, openings, features and areas of a unit as WKT.
    Geometry is in the site's coordinate system (but without the correct geolocation). I.e. scaling
    and rotation is correct but translation is not.

    Used for https://zenodo.org/record/7070952
    """

    @cached_property
    def _units_layout(self):
        return {
            unit_info["id"]: unit_layout
            for unit_info, unit_layout in SiteHandler.get_unit_layouts(
                site_id=self._site_id, scaled=True, georeferenced=True, anonymized=True
            )
        }

    def get_geometry(self, unit_layout):
        areas = [
            (area.db_area_id, "area", area.type.name, wkt.dumps(area.footprint))
            for area in unit_layout.areas
        ]

        features = [
            (
                area.db_area_id,
                "feature",
                feature.type.name,
                wkt.dumps(feature.footprint),
            )
            for area in unit_layout.areas
            for feature in area.features
            if feature.type.name != "SHAFT"
        ]
        separators = [
            (None, "separator", separator.type.name, wkt.dumps(separator.footprint))
            for separator in unit_layout.separators
        ]

        openings = [
            (None, "opening", opening.type.name, wkt.dumps(opening.footprint))
            for opening in unit_layout.openings
        ]

        return pd.DataFrame(
            areas + features + separators + openings,
            columns=["area_id", "entity_type", "entity_subtype", "geometry"],
        )

    def get_vector(self, representative_units_only: bool, anonymized: bool = True):
        return [
            NeufertGeometryVectorSchema(
                site_id=self._site_id,
                building_id=self._floors_info[unit_info["floor_id"]]["building_id"],
                floor_id=unit_info["floor_id"],
                unit_id=unit_info["id"],
                apartment_id=hashlib.md5(
                    unit_info["client_id"].encode("utf-8")
                ).hexdigest()
                if anonymized
                else unit_info["client_id"],
                **geometry_row.to_dict(),
            )
            for unit_info in self._get_units_info(
                representative_units_only=representative_units_only
            )
            for _, geometry_row in self.get_geometry(
                unit_layout=self._units_layout[unit_info["id"]]
            ).iterrows()
        ]
