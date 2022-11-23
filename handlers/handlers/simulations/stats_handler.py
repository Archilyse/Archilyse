from collections import defaultdict
from functools import cached_property
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

import numpy as np

from brooks.classifications import UnifiedClassificationScheme
from brooks.types import AreaType
from common_utils.constants import TASK_TYPE, VIEW_DIMENSION, VIEW_DIMENSION_2
from common_utils.typing import SimulationResults
from connectors.db_connector import get_db_session_scope
from handlers.db import (
    ApartmentStatsDBHandler,
    AreaDBHandler,
    SlamSimulationDBHandler,
    UnitAreaStatsDBHandler,
    UnitDBHandler,
    UnitSimulationDBHandler,
    UnitStatsDBHandler,
)
from handlers.db.utils import retry_on_db_operational_error


class StatsHandler:
    LEGACY_DIMENSIONS_MAPPER = {
        VIEW_DIMENSION.VIEW_STREETS.value: (
            VIEW_DIMENSION_2.VIEW_PRIMARY_STREETS.value,
            VIEW_DIMENSION_2.VIEW_SECONDARY_STREETS.value,
            VIEW_DIMENSION_2.VIEW_TERTIARY_STREETS.value,
            VIEW_DIMENSION_2.VIEW_PEDESTRIAN.value,
            VIEW_DIMENSION_2.VIEW_HIGHWAYS.value,
        )
    }
    OPTIONAL_DIMENSIONS = {
        TASK_TYPE.CONNECTIVITY: {"eigen_centrality", "ENTRANCE_DOOR_distance"}
    }
    _FILLING_VALUES = {
        "count": 0,
        "mean": np.nan,
        "min": np.nan,
        "max": np.nan,
        "median": np.nan,
        "p20": np.nan,
        "p80": np.nan,
        "stddev": np.nan,
    }

    def __init__(self, run_id: str, results: SimulationResults):
        self.run_id = run_id
        self.results = results

    @classmethod
    def get_area_stats(
        cls,
        site_id: int,
        task_type: TASK_TYPE,
        desired_dimensions: Set[str],
        fill_missing_dimensions: bool = False,
        legacy_dimensions_compatible: bool = False,
    ) -> Dict[int, Dict[int, Dict[str, Dict[str, Union[float, int]]]]]:
        """
        Args:
            site_id:
            task_type:
            desired_dimensions:
            fill_missing_dimensions: If some known OPTIONAL_DIMENSIONS missing, fill stats with zeros
            legacy_dimensions_compatible: Used if simulation version is PH_2022 and we want to map them
                to legacy dimensions. That is for now only streets (should be present in desired_dimensions)
        """
        unit_area_stats: Dict[
            int, Dict[int, Dict[str, Dict[str, Union[float, int]]]]
        ] = {}

        run_id = SlamSimulationDBHandler.get_latest_run_id(
            site_id=site_id, task_type=task_type
        )
        for stats in UnitAreaStatsDBHandler.find(run_id=run_id):
            unit_area_stats.setdefault(stats["unit_id"], {}).setdefault(
                stats["area_id"], {}
            )

            if stats["dimension"] in desired_dimensions:
                unit_area_stats[stats["unit_id"]][stats["area_id"]][
                    stats["dimension"]
                ] = stats

        if fill_missing_dimensions and (
            optional_dims := cls.OPTIONAL_DIMENSIONS.get(task_type)
        ):
            optional_requested_dims = optional_dims.intersection(desired_dimensions)
            for unit_id, unit_stats in unit_area_stats.items():
                for area_id, area_stats in unit_stats.items():
                    missing_dims = optional_requested_dims - set(area_stats.keys())
                    for dim in missing_dims:
                        unit_area_stats[unit_id][area_id][dim] = {
                            "unit_id": unit_id,
                            "area_id": area_id,
                            **cls._FILLING_VALUES,
                        }
        if (
            legacy_dimensions_compatible
            and VIEW_DIMENSION.VIEW_STREETS.value in desired_dimensions
        ):
            unit_area_stats = cls._map_to_legacy_dimensions(
                unit_area_stats=unit_area_stats, run_id=run_id
            )

        return unit_area_stats

    @classmethod
    def _map_to_legacy_dimensions(
        cls,
        unit_area_stats: Dict[int, Dict[int, Dict[str, Dict[str, Union[float, int]]]]],
        run_id: str,
    ) -> Dict[int, Dict[int, Dict[str, Dict[str, Union[float, int]]]]]:
        for unit_id, unit_stats in unit_area_stats.items():
            sim_results = UnitSimulationDBHandler.get_by(
                run_id=run_id, unit_id=unit_id
            )["results"]
            for area_id in unit_stats.keys():
                for (
                    dimension_to_map,
                    mapped_dims,
                ) in cls.LEGACY_DIMENSIONS_MAPPER.items():
                    relevant_sim_results = [
                        sim_results[str(area_id)][d] for d in mapped_dims
                    ]
                    new_aggregated_value = [
                        sum(values) for values in zip(*relevant_sim_results)
                    ]
                    new_stats = cls._compute_stats(new_aggregated_value)
                    unit_area_stats[unit_id][area_id][dimension_to_map] = new_stats
        return unit_area_stats

    @classmethod
    def get_unit_stats(
        cls,
        site_id: int,
        interior_only: bool,
        task_type: TASK_TYPE,
        desired_dimensions: Set[str],
    ) -> DefaultDict[int, Dict[str, Dict[str, Union[float, int]]]]:
        """Returns the latest unit stats as a dict"""
        unit_stats: DefaultDict[
            int, Dict[str, Dict[str, Union[float, int]]]
        ] = defaultdict(dict)
        for stats in UnitStatsDBHandler.find(
            run_id=SlamSimulationDBHandler.get_latest_run_id(
                site_id=site_id, task_type=task_type
            ),
            only_interior=interior_only,
        ):
            if stats["dimension"] in desired_dimensions:
                unit_stats[stats["unit_id"]][stats["dimension"]] = stats
        return unit_stats

    @classmethod
    def get_apartment_stats(
        cls,
        site_id: int,
        interior_only: bool,
        task_type: TASK_TYPE,
        desired_dimensions: Set[str],
        fill_missing_dimensions: bool = False,
    ) -> Dict[str, Dict[str, Dict[str, Union[float, int]]]]:
        apartments_stats: Dict[str, Dict[str, Dict[str, Union[float, int]]]] = {}
        for stats in ApartmentStatsDBHandler.find(
            run_id=SlamSimulationDBHandler.get_latest_run_id(
                site_id=site_id, task_type=task_type
            ),
            only_interior=interior_only,
        ):
            apartments_stats.setdefault(stats["client_id"], {})
            if stats["dimension"] in desired_dimensions:
                apartments_stats[stats["client_id"]][stats["dimension"]] = stats

        if fill_missing_dimensions and (
            optional_dims := cls.OPTIONAL_DIMENSIONS.get(task_type)
        ):
            optional_requested_dims = optional_dims.intersection(desired_dimensions)
            for client_id, apartment_stats in apartments_stats.items():
                missing_dims = optional_requested_dims - set(apartment_stats.keys())
                for dim in missing_dims:
                    apartments_stats[client_id][dim] = {
                        **cls._FILLING_VALUES,
                    }
        return apartments_stats

    # COMPUTATION METHODS
    @cached_property
    def site_id(self) -> int:
        return SlamSimulationDBHandler.get_by(
            run_id=self.run_id, output_columns=["site_id"]
        )["site_id"]

    @cached_property
    def unit_id_to_client_id(self):
        units_info = UnitDBHandler.find(
            site_id=self.site_id, output_columns=["id", "client_id"]
        )
        return {unit_info["id"]: unit_info["client_id"] for unit_info in units_info}

    @cached_property
    def exterior_areas_ids(self) -> Set[int]:
        exterior_area_types = UnifiedClassificationScheme().BALCONY_AREAS
        area_ids = set(
            area_id
            for unit_area_results in self.results.values()
            for area_id in unit_area_results.keys()
            if area_id != "resolution"
        )
        return {
            area["id"]
            for area in AreaDBHandler.find_in(
                id=area_ids,
                output_columns=["id", "area_type"],
            )
            if AreaType[area["area_type"]] in exterior_area_types
        }

    @staticmethod
    def _get_area_dimension_values(
        unit_area_results: Dict[int, Dict[str, Any]],
        area_ids_to_exclude: Optional[Set[int]] = None,
    ) -> Iterable[Tuple[int, str, List[float]]]:
        if area_ids_to_exclude is None:
            area_ids_to_exclude = set()
        yield from (
            (area_id, dimension, values)
            for area_id, dimension_values in unit_area_results.items()
            if area_id not in area_ids_to_exclude and area_id != "resolution"
            for dimension, values in dimension_values.items()
            if dimension != "observation_points"
        )

    @staticmethod
    def _compute_stats(values):
        return dict(
            p20=float(np.percentile(values, 20)),
            p80=float(np.percentile(values, 80)),
            median=float(np.median(values)),
            min=float(np.min(values)),
            max=float(np.max(values)),
            mean=float(np.mean(values)),
            stddev=float(np.std(values)),
            count=len(values),
        )

    def _compute_apartment_stats(
        self,
        area_ids_to_exclude: Set[int],
    ) -> Iterator[Dict]:
        apartment_dimension_values: DefaultDict[
            str, DefaultDict[str, List[float]]
        ] = defaultdict(lambda: defaultdict(list))
        for unit_id, unit_area_results in self.results.items():
            client_id = self.unit_id_to_client_id[int(unit_id)]
            for _, dimension, values in self._get_area_dimension_values(
                unit_area_results=unit_area_results,
                area_ids_to_exclude=area_ids_to_exclude,
            ):
                apartment_dimension_values[client_id][dimension].extend(values)

        for client_id, dimension_values in apartment_dimension_values.items():
            for dimension, values in dimension_values.items():
                yield dict(
                    client_id=client_id,
                    dimension=dimension,
                    **self._compute_stats(values=values),
                )

    def _compute_unit_stats(self, area_ids_to_exclude: Set[int]) -> Iterator[Dict]:
        for unit_id, unit_area_results in self.results.items():
            unit_dimension_values = defaultdict(list)
            for _, dimension, values in self._get_area_dimension_values(
                unit_area_results=unit_area_results,
                area_ids_to_exclude=area_ids_to_exclude,
            ):
                unit_dimension_values[dimension].extend(values)

            for dimension, values in unit_dimension_values.items():
                yield dict(
                    unit_id=unit_id,
                    dimension=dimension,
                    **self._compute_stats(values=values),
                )

    def _compute_unit_area_stats(self) -> Iterator[Dict]:
        for unit_id, unit_area_results in self.results.items():
            for area_id, dimension, values in self._get_area_dimension_values(
                unit_area_results=unit_area_results
            ):
                yield dict(
                    unit_id=unit_id,
                    area_id=area_id,
                    dimension=dimension,
                    **self._compute_stats(values=values),
                )

    def _compute_and_store_apartment_stats(
        self,
        only_interior: bool,
    ):
        area_ids_to_exclude = self.exterior_areas_ids if only_interior else set()
        apartment_stats = self._compute_apartment_stats(
            area_ids_to_exclude=area_ids_to_exclude
        )
        ApartmentStatsDBHandler.bulk_insert(
            items=[
                dict(**stats, run_id=self.run_id, only_interior=only_interior)
                for stats in apartment_stats
            ]
        )

    def _compute_and_store_unit_stats(
        self,
        only_interior: bool,
    ):
        area_ids_to_exclude = self.exterior_areas_ids if only_interior else set()
        unit_stats = self._compute_unit_stats(area_ids_to_exclude=area_ids_to_exclude)
        UnitStatsDBHandler.bulk_insert(
            items=[
                dict(**stats, run_id=self.run_id, only_interior=only_interior)
                for stats in unit_stats
            ]
        )

    def _compute_and_store_area_stats(self):
        area_stats = self._compute_unit_area_stats()
        UnitAreaStatsDBHandler.bulk_insert(
            items=[
                dict(run_id=self.run_id, **unit_area_stats)
                for unit_area_stats in area_stats
            ]
        )

    @retry_on_db_operational_error()
    def compute_and_store_stats(self):
        with get_db_session_scope():
            self._compute_and_store_area_stats()
            self._compute_and_store_unit_stats(only_interior=True)
            self._compute_and_store_unit_stats(only_interior=False)
            self._compute_and_store_apartment_stats(only_interior=True)
            self._compute_and_store_apartment_stats(only_interior=False)
