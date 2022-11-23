import json
from collections import defaultdict
from functools import cached_property
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

import simplejson
from google.cloud import exceptions as gcloud_exceptions
from shapely.geometry import Polygon

from brooks.models import SimLayout
from brooks.util.projections import project_geometry
from common_utils.constants import (
    GOOGLE_CLOUD_3D_TRIANGLES,
    REGION,
    SIMULATION_VERSION,
    UNIT_USAGE,
)
from common_utils.exceptions import BaseElevationException, GCSLinkEmptyException
from common_utils.logger import logger
from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_client_bucket_name

LayoutTrianglesType = Iterator[Tuple[str, Iterable[List[Tuple[float, float, float]]]]]


class BuildingHandler:
    def __init__(self, building_id: int):
        self.building_id = building_id

    @cached_property
    def units_by_ids(self) -> Dict[int, Dict]:
        return {
            unit["id"]: unit
            for unit in UnitDBHandler.get_joined_by_site_building_floor_id(
                building_id=self.building_id
            )
        }

    @cached_property
    def building_info(self) -> Dict:
        return BuildingDBHandler.get_by(id=self.building_id)

    @cached_property
    def site_info(self) -> Dict:
        return SiteDBHandler.get_by(id=self.building_info["site_id"])

    @cached_property
    def unit_handler(self):
        from handlers import UnitHandler

        return UnitHandler()

    @cached_property
    def client_bucket_name(self):
        return get_client_bucket_name(client_id=self.site_info["client_id"])

    @cached_property
    def elevation(self):
        elevation = (
            self.building_info["elevation_override"]
            if self.building_info["elevation_override"] is not None
            else self.building_info["elevation"]
        )
        if elevation is None:
            raise BaseElevationException(
                f"Building {self.building_id} does not have elevation yet"
            )
        return elevation

    @staticmethod
    def triangle_filename_gcs(building_id: int):
        return Path(f"{building_id}.json")

    @staticmethod
    def _project_triangles_to_lat_lon(
        triangles_by_client_id: LayoutTrianglesType,
        crs_from: REGION,
    ) -> LayoutTrianglesType:
        """triangles_by_client_id are expected to be in local crs with coordinates being flipped i.e. as y, x"""
        for client_id, triangles_yx in triangles_by_client_id:
            triangles_lat_lon = []
            for triangle_yx in triangles_yx:
                # flip to x, y
                triangle_xy = Polygon((x, y, z) for y, x, z in triangle_yx)
                # project to lon, lat
                triangle_lon_lat = project_geometry(
                    geometry=triangle_xy,
                    crs_from=crs_from,
                    crs_to=REGION.LAT_LON,
                ).exterior.coords[:-1]
                # flip to lat, lon
                triangle_lat_lon = [(lat, lon, z) for lon, lat, z in triangle_lon_lat]
                triangles_lat_lon.append(triangle_lat_lon)
            yield client_id, triangles_lat_lon

    def generate_and_upload_triangles_to_gcs(
        self, simulation_version: SIMULATION_VERSION
    ):
        triangles_lat_lon: Dict[str, Union[str, LayoutTrianglesType]] = {
            "georef_region": REGION.LAT_LON.name,
            "triangles": self._project_triangles_to_lat_lon(
                triangles_by_client_id=self.generate_layout_triangles(
                    simulation_version=simulation_version, by_unit=True
                ),
                crs_from=REGION[self.site_info["georef_region"]],
            ),
        }
        return self._upload_triangles_to_gcs(triangles=triangles_lat_lon)

    def _upload_triangles_to_gcs(
        self,
        triangles: Dict[
            str,
            Union[str, LayoutTrianglesType],
        ],
    ):
        from handlers import GCloudStorageHandler

        uploaded_link = GCloudStorageHandler().upload_bytes_to_bucket(
            destination_folder=GOOGLE_CLOUD_3D_TRIANGLES,
            destination_file_name=self.triangle_filename_gcs(
                building_id=self.building_id
            ).name,
            contents=simplejson.dumps(triangles, iterable_as_array=True),
            bucket_name=self.client_bucket_name,
        )
        return BuildingDBHandler.update(
            item_pks={"id": self.building_id},
            new_values={"triangles_gcs_link": uploaded_link},
        )

    def _get_triangles_from_gcs(self) -> bytes:
        from handlers import GCloudStorageHandler

        with NamedTemporaryFile() as temp_file:
            try:
                GCloudStorageHandler().download_file_from_media_link(
                    source_media_link=self.building_info["triangles_gcs_link"],
                    destination_file=Path(temp_file.name),
                    bucket_name=self.client_bucket_name,
                )
                return temp_file.read()
            except gcloud_exceptions.NotFound:
                raise GCSLinkEmptyException()

    def get_triangles_from_gcs_lat_lon(self) -> Iterable:
        triangles = json.loads(self._get_triangles_from_gcs())
        # convert to new file format if required
        if "georef_region" not in triangles:
            triangles = {
                "georef_region": self.site_info["georef_region"],
                "triangles": triangles,
            }
        # project to lat lon if required
        georef_region = REGION[triangles["georef_region"]]
        if georef_region != REGION.LAT_LON:
            logger.error(
                f"Building id {self.building_id} still does not have the triangles in lat/lon"
            )
            return list(
                self._project_triangles_to_lat_lon(
                    triangles_by_client_id=triangles["triangles"],
                    crs_from=georef_region,
                )
            )
        return triangles["triangles"]

    @classmethod
    def calculate_elevation(
        cls, building_id: int, region: REGION, simulation_version: SIMULATION_VERSION
    ):
        from handlers import PlanLayoutHandler
        from surroundings.base_elevation_handler import get_elevation_handler

        plan_id = PlanDBHandler.find(building_id=building_id)[0]["id"]
        georeferenced_layout_footprint = PlanLayoutHandler(
            plan_id=plan_id
        ).get_georeferenced_footprint()
        centroid_georeferenced_layout = georeferenced_layout_footprint.centroid

        building_elevation = get_elevation_handler(
            region=region,
            location=centroid_georeferenced_layout,
            simulation_version=simulation_version,
        ).get_elevation(point=centroid_georeferenced_layout)

        BuildingDBHandler.update(
            item_pks={"id": building_id}, new_values={"elevation": building_elevation}
        )

    @classmethod
    def create_unit_types_per_building(cls, building_id: int):
        from handlers import UnitHandler

        units = []
        for plan in PlanDBHandler.find(building_id=building_id):
            units.extend(UnitDBHandler.find(plan_id=plan["id"]))

        deduplicated_units = defaultdict(list)
        for unit in units:
            deduplicated_units[(unit["plan_id"], unit["apartment_no"])].append(
                unit["id"]
            )

        for _, unit_ids in deduplicated_units.items():
            unit_type = UnitHandler().get_unit_type(unit_id=unit_ids[0]).name
            for unit_id in unit_ids:
                UnitDBHandler.update(
                    item_pks={"id": unit_id}, new_values={"unit_type": unit_type}
                )

    def generate_layout_triangles(
        self,
        simulation_version: SIMULATION_VERSION,
        by_unit: bool,
    ) -> LayoutTrianglesType:
        """
        Args:
            simulation_version: SIMULATION_VERSION
            by_unit: If false, instead of yielding triangles per unit,
                     these are yielded per whole floor tagged with building name
        """
        if by_unit:
            # if there's a floor that doesn't have units, fall back to getting floor triangles
            plans_without_units = PlanDBHandler.find(
                building_id=self.building_id, without_units=True
            )
            if plans_without_units:
                yield from self.get_floor_triangles(
                    simulation_version=simulation_version,
                    from_plans=plans_without_units,
                )
            yield from self.get_unit_triangles(simulation_version=simulation_version)

        else:
            yield from self.get_floor_triangles(
                simulation_version=simulation_version, exclude_underground=True
            )
            # Triangulate units of underground floors
            yield from self.get_unit_triangles(
                simulation_version=simulation_version, only_underground=True
            )

    def get_unit_triangles(
        self, simulation_version: SIMULATION_VERSION, only_underground: bool = False
    ):
        layouts_sorted_by_floor_numbers = self._unit_layouts_by_floor_number(
            only_underground=only_underground
        )
        for (
            floor_number,
            layouts_by_unit_id,
        ) in layouts_sorted_by_floor_numbers.items():
            for unit_id, unit_layout in layouts_by_unit_id.items():
                yield self.units_by_ids[unit_id][
                    "client_id"
                ], self.unit_handler.get_layout_triangles(
                    unit_id=unit_id,
                    layout=unit_layout,
                    layouts_upper_floor=layouts_sorted_by_floor_numbers.get(
                        floor_number + 1, {}
                    ).values(),
                    building_elevation=self.elevation,
                    simulation_version=simulation_version,
                )

    def get_floor_triangles(
        self,
        simulation_version: SIMULATION_VERSION,
        from_plans: Optional[List[Dict]] = None,
        exclude_underground: bool = False,
    ):
        from handlers import FloorHandler

        floor_handler = FloorHandler()

        layouts_sorted_by_floor_numbers = self._plan_layouts_by_floor_number()
        applicable_floors = FloorDBHandler.find(
            building_id=self.building_id,
            output_columns=["id", "plan_id", "floor_number"],
        )
        if from_plans:
            applicable_floors = [
                f
                for f in applicable_floors
                if f["plan_id"] in {p["id"] for p in from_plans}
            ]
        if exclude_underground:
            applicable_floors = [f for f in applicable_floors if f["floor_number"] >= 0]

        for floor_info in sorted(
            applicable_floors,
            key=lambda f: f["floor_number"],
        ):
            triangles = floor_handler.get_layout_triangles(
                layout=layouts_sorted_by_floor_numbers[floor_info["floor_number"]],
                layout_upper_floor=layouts_sorted_by_floor_numbers.get(
                    floor_info["floor_number"] + 1, None
                ),
                floor_info=floor_info,
                building_elevation=self.elevation,
                simulation_version=simulation_version,
            )
            if len(triangles):
                yield floor_info["floor_number"], triangles

    def _unit_layouts_by_floor_number(
        self, only_underground: bool = False
    ) -> Dict[int, Dict[int, SimLayout]]:
        layouts_per_floor_number: Dict[int, Dict[int, SimLayout]] = defaultdict(dict)
        floor_number_by_id = {
            floor["id"]: floor["floor_number"]
            for floor in FloorDBHandler.find(
                building_id=self.building_id, output_columns=["floor_number", "id"]
            )
        }
        for unit in self.units_by_ids.values():
            floor_number = floor_number_by_id[unit["floor_id"]]
            if only_underground and floor_number >= 0:
                continue

            layouts_per_floor_number[floor_number][
                unit["id"]
            ] = self.unit_handler.get_unit_layout(
                unit_id=unit["id"], georeferenced=True, postprocessed=False
            )
        return layouts_per_floor_number

    def _plan_layouts_by_floor_number(
        self,
        classified: bool = True,
        georeferenced: bool = True,
        plan_ids: Optional[Set[int]] = None,
    ) -> Dict[int, SimLayout]:
        from handlers import PlanLayoutHandler

        plan_layouts_by_id = {
            plan["id"]: PlanLayoutHandler(
                plan_id=plan["id"], plan_info=plan
            ).get_layout(
                scaled=True, classified=classified, georeferenced=georeferenced
            )
            for plan in PlanDBHandler.find(building_id=self.building_id)
            if plan_ids is None or plan["id"] in plan_ids
        }

        return {
            floor["floor_number"]: plan_layouts_by_id[floor["plan_id"]]
            for floor in FloorDBHandler.find(
                building_id=self.building_id,
                output_columns=["floor_number", "plan_id"],
            )
            if floor["plan_id"] in plan_layouts_by_id
        }

    def _area_usage_by_floor_number(self) -> Dict[int, Dict[int, UNIT_USAGE]]:
        from connectors.db_connector import get_db_session_scope
        from db_models import (
            AreaDBModel,
            FloorDBModel,
            PlanDBModel,
            UnitDBModel,
            UnitsAreasDBModel,
        )

        with get_db_session_scope(readonly=True) as session:
            unit_usage_subquery = (
                session.query(
                    AreaDBModel.id.label("area_id"),
                    FloorDBModel.id.label("floor_id"),
                    UnitDBModel.unit_usage,
                )
                .join(UnitsAreasDBModel, AreaDBModel.id == UnitsAreasDBModel.area_id)
                .join(UnitDBModel)
                .join(FloorDBModel)
                .filter(FloorDBModel.building_id == self.building_id)
                .subquery("unit_usages")
            )

            floors = (
                session.query(
                    PlanDBModel.id.label("plan_id"),
                    FloorDBModel.id.label("floor_id"),
                    FloorDBModel.floor_number.label("floor_number"),
                )
                .join(PlanDBModel)
                .filter(PlanDBModel.building_id == self.building_id)
                .subquery("floors")
            )

            query = (
                session.query(
                    floors.c.floor_number,
                    AreaDBModel.id,
                    unit_usage_subquery.c.unit_usage,
                )
                .join(floors, AreaDBModel.plan_id == floors.c.plan_id)
                .join(
                    unit_usage_subquery,
                    (unit_usage_subquery.c.area_id == AreaDBModel.id)
                    & (unit_usage_subquery.c.floor_id == floors.c.floor_id),
                    isouter=True,
                )
            )

            area_usage_by_floor_number: Dict[int, Dict[int, UNIT_USAGE]] = defaultdict(
                dict
            )
            for floor_number, area_id, area_usage in query.all():
                area_usage_by_floor_number[floor_number][area_id] = area_usage

            return area_usage_by_floor_number
