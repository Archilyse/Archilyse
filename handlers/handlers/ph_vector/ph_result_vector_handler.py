import copy
import typing
from collections import defaultdict
from functools import cached_property
from typing import Any, Dict, List, Set, Union

from brooks.classifications import UnifiedClassificationScheme
from common_utils.constants import (
    DEFAULT_RESULT_VECTORS,
    RESULT_VECTORS,
    SUN_DIMENSION,
    TASK_TYPE,
    VIEW_DIMENSION,
)
from handlers import SiteHandler, SlamSimulationHandler, StatsHandler
from handlers.db import UnitDBHandler
from handlers.utils import aggregate_stats_dimension
from simulations.room_shapes import get_room_shapes
from simulations.suntimes.suntimes_handler import SuntimesHandler


class PHResultVectorHandler:
    STAT_FIELD_NAMES: List[str] = ["min", "max", "mean", "stddev"]
    VECTOR_FIELD_NAMES: List[str] = ["min", "max", "mean", "std"]
    RELEVANT_RESULT_VECTORS = DEFAULT_RESULT_VECTORS

    def __init__(self, site_id: int):
        self.site_id = site_id
        self.classification_scheme = UnifiedClassificationScheme()

    @cached_property
    def unit_areas(self) -> Dict[int, Dict]:
        return {
            unit_info["id"]: {area.db_area_id: area for area in layout.areas}
            for unit_info, layout in SiteHandler.get_unit_layouts(
                site_id=self.site_id, scaled=True
            )
        }

    @cached_property
    def basic_features(self) -> Dict[str, Dict]:
        return {
            self.unit_id_to_client_id[res["unit_id"]]: res["results"][0]
            for res in SlamSimulationHandler.get_all_results(
                site_id=self.site_id, task_type=TASK_TYPE.BASIC_FEATURES
            )
        }

    @cached_property
    def units(self):
        return UnitDBHandler.find(
            site_id=self.site_id, output_columns=["id", "client_id"]
        )

    @cached_property
    def client_id_to_unit_id(self):
        client_id_to_unit_id = defaultdict(list)
        for unit_info in self.units:
            client_id_to_unit_id[unit_info["client_id"]].append(unit_info["id"])
        return client_id_to_unit_id

    @cached_property
    def unit_id_to_client_id(self) -> Dict[int, str]:
        return {unit_info["id"]: unit_info["client_id"] for unit_info in self.units}

    @staticmethod
    def _get_simulation_categories(site_id: int):
        return [
            (
                "View",
                TASK_TYPE.VIEW_SUN,
                {view_dimension.value for view_dimension in VIEW_DIMENSION},
            ),
            (
                "Sun",
                TASK_TYPE.VIEW_SUN,
                {sun_dimension.value for sun_dimension in SUN_DIMENSION},
            ),
            (
                "Sun.v2",
                TASK_TYPE.SUN_V2,
                {
                    SuntimesHandler.get_sun_key_from_datetime(dt=sun_obs_date)
                    for sun_obs_date in SuntimesHandler.get_sun_times_v2(
                        site_id=site_id
                    )
                },
            ),
        ]

    @classmethod
    def _make_vector_data(
        cls,
        vector_key_prefix: str,
        dimensions: Set[str],
        stats: Dict[str, Dict[str, Union[float, int]]],
    ) -> Dict[str, float]:
        vector_data: Dict[str, float] = {}
        for d in dimensions:
            vector_values = [
                stats[d][stat_field] for stat_field in cls.STAT_FIELD_NAMES
            ]
            vector_keys = [
                f"{vector_key_prefix}.{aggr_type}.{d}"
                for aggr_type in cls.VECTOR_FIELD_NAMES
            ]
            vector_data.update(zip(vector_keys, vector_values))
        return vector_data

    def _apartment_stats(
        self,
        interior_only: bool,
        task_type: TASK_TYPE,
        dimensions: Set[str],
    ) -> Dict[str, Dict[str, Dict[str, Union[float, int]]]]:
        unit_area_stats = StatsHandler.get_area_stats(
            site_id=self.site_id,
            task_type=task_type,
            desired_dimensions=dimensions,
            fill_missing_dimensions=True,
        )
        apartment_stats: typing.DefaultDict[
            str, Dict[str, Dict[str, Union[float, int]]]
        ] = defaultdict(dict)
        for apartment_id, units_ids in self.client_id_to_unit_id.items():
            for dimension in dimensions:
                aggregated_values = aggregate_stats_dimension(
                    stats=[
                        stats[dimension]
                        for unit_id in units_ids
                        for area_id, stats in unit_area_stats[unit_id].items()
                        if not (
                            interior_only
                            and self.unit_areas[unit_id][area_id].type
                            in self.classification_scheme.BALCONY_AREAS
                        )
                    ]
                )
                apartment_stats[apartment_id][dimension] = aggregated_values
        return dict(apartment_stats)

    def _get_unit_area_stats(
        self,
        interior_only: bool,
        task_type: TASK_TYPE,
        dimensions: Set[str],
    ):
        unit_area_stats = StatsHandler.get_area_stats(
            site_id=self.site_id,
            task_type=task_type,
            desired_dimensions=dimensions,
            fill_missing_dimensions=True,
        )
        for unit_id, area_stats in unit_area_stats.items():
            for area_id, stats in area_stats.items():
                area = self.unit_areas[unit_id][area_id]
                if not (
                    interior_only
                    and area.type in self.classification_scheme.BALCONY_AREAS
                ):
                    yield unit_id, area_id, stats

    def generate_apartment_vector(
        self,
        interior_only: bool,
    ) -> Dict[str, Dict[str, Any]]:
        # get latest basic features
        vector_data = copy.deepcopy(self.basic_features)
        # get the latest sims values
        for vector_key_prefix, task_type, dimensions in self._get_simulation_categories(
            site_id=self.site_id
        ):
            for apartment_id, stats in self._apartment_stats(
                interior_only=interior_only,
                task_type=task_type,
                dimensions=dimensions,
            ).items():
                vector_data[apartment_id].update(
                    self._make_vector_data(
                        vector_key_prefix=vector_key_prefix,
                        dimensions=dimensions,
                        stats=stats,
                    )
                )
        return vector_data

    def _generate_area_vector(
        self, interior_only: bool
    ) -> Dict[str, List[Dict[str, Any]]]:
        apartment_area_vectors: typing.DefaultDict[
            str,
            Dict[int, Dict],
        ] = defaultdict(dict)
        for vector_key_prefix, task_type, dimensions in self._get_simulation_categories(
            site_id=self.site_id
        ):
            for unit_id, area_id, stats in self._get_unit_area_stats(
                interior_only=interior_only, task_type=task_type, dimensions=dimensions
            ):
                area = self.unit_areas[unit_id][area_id]
                apartment_client_id = self.unit_id_to_client_id[unit_id]
                if area.type not in self.classification_scheme.ROOM_VECTOR_NAMING:
                    if apartment_client_id not in apartment_area_vectors:
                        apartment_area_vectors[apartment_client_id] = {}
                    continue

                if area_id not in apartment_area_vectors[apartment_client_id]:
                    apartment_area_vectors[apartment_client_id][area_id] = {
                        "area_index": area_id,
                        "AreaBasics.area_type": self.classification_scheme.ROOM_VECTOR_NAMING[
                            area.type
                        ],
                        "AreaBasics.area_size": area.footprint.area,
                        **{
                            f"AreaShape.{dimension}": value
                            for dimension, value in get_room_shapes(
                                area.footprint
                            ).items()
                        },
                    }
                apartment_area_vectors[apartment_client_id][area_id].update(
                    self._make_vector_data(
                        vector_key_prefix=vector_key_prefix,
                        dimensions=dimensions,
                        stats=stats,
                    )
                )
        return {
            apartment_id: list(area_vectors.values())
            for apartment_id, area_vectors in apartment_area_vectors.items()
        }

    @staticmethod
    def _generate_full_vector(area_vector, apartment_vector):
        full_vector = dict(apartment_vector)

        # Area Vector is added such that e.g. the biggest room has dimensions
        # Room-1.View.mean.isovist, the second one Room-2.View.mean.isovist, etc.
        row_by_area_type = defaultdict(list)
        for area_row in area_vector:
            row_by_area_type[area_row["AreaBasics.area_type"]].append(area_row)

        ignore_dimensions = {"AreaBasics.area_type", "area_index"}
        for area_type, area_type_rows in row_by_area_type.items():
            area_type_rows_sorted = sorted(
                area_type_rows, key=lambda a: a["AreaBasics.area_size"], reverse=True
            )
            for row_index_by_size, row in enumerate(area_type_rows_sorted):
                for dimension, value in row.items():
                    if dimension in ignore_dimensions:
                        continue

                    full_vector[
                        f"{area_type}-{row_index_by_size + 1}.{dimension}"
                    ] = value
        return full_vector

    def generate_vectors(self) -> Dict[RESULT_VECTORS, Dict]:
        area_vector_no_balcony = self._generate_area_vector(interior_only=True)
        area_vector_with_balcony = self._generate_area_vector(interior_only=False)
        apartment_vector_with_balcony = self.generate_apartment_vector(
            interior_only=False
        )
        apartment_vector_no_balcony = self.generate_apartment_vector(interior_only=True)
        full_vector_with_balcony = {}
        full_vector_no_balcony = {}
        for apartment_id in self.client_id_to_unit_id.keys():
            full_vector_with_balcony[apartment_id] = self._generate_full_vector(
                apartment_vector=apartment_vector_with_balcony[apartment_id],
                area_vector=area_vector_with_balcony[apartment_id],
            )
            full_vector_no_balcony[apartment_id] = self._generate_full_vector(
                apartment_vector=apartment_vector_no_balcony[apartment_id],
                area_vector=area_vector_no_balcony[apartment_id],
            )

        return {
            RESULT_VECTORS.UNIT_VECTOR_WITH_BALCONY: apartment_vector_with_balcony,
            RESULT_VECTORS.UNIT_VECTOR_NO_BALCONY: apartment_vector_no_balcony,
            RESULT_VECTORS.ROOM_VECTOR_WITH_BALCONY: area_vector_with_balcony,
            RESULT_VECTORS.ROOM_VECTOR_NO_BALCONY: area_vector_no_balcony,
            RESULT_VECTORS.FULL_VECTOR_WITH_BALCONY: full_vector_with_balcony,
            RESULT_VECTORS.FULL_VECTOR_NO_BALCONY: full_vector_no_balcony,
        }
