import io
import json
import typing
import uuid
from collections import defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union

import numpy as np
from contexttimer import timer
from shapely import wkt
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union
from werkzeug.datastructures import FileStorage

from brooks.models import SimLayout
from brooks.util.projections import project_geometry
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    BUILDING_SURROUNDINGS_DIR,
    DEFAULT_IFC_LOCATION,
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_BUILDING_SURROUNDINGS,
    GOOGLE_CLOUD_DELIVERABLES,
    GOOGLE_CLOUD_SITE_IFC_FILES,
    GOOGLE_CLOUD_VIEW_SURROUNDINGS,
    REGION,
    SIMULATION_VERSION,
    SURROUNDINGS_DIR,
    TASK_TYPE,
    UNIT_BASICS_DIMENSION,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import (
    BasicFeaturesException,
    GCSLinkEmptyException,
    NetAreaDistributionUnsetException,
    SiteCheckException,
)
from common_utils.logger import logger
from connectors.db_connector import get_db_session_scope
from db_models.db_entities import AreaDBModel, SiteDBModel, UnitsAreasDBModel
from handlers import GCloudStorageHandler, PlanHandler, PlanLayoutHandler
from handlers.db import (
    FloorDBHandler,
    PlanDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.geo_location import GeoLocator
from handlers.utils import PartialUnitInfo, get_client_bucket_name, get_simulation_name
from simulations.basic_features import CustomValuatorBasicFeatures2
from surroundings.utils import SurrTrianglesType
from tasks.surroundings_tasks import generate_geo_referencing_surroundings_for_site_task


class SiteHandler:
    SET_SITE_TO_UNPROCESSED_ON_UPDATE_COLUMNS = {
        SiteDBModel.classification_scheme.name,
        SiteDBModel.lon.name,
        SiteDBModel.lat.name,
        SiteDBModel.georef_region.name,
        SiteDBModel.region.name,
        SiteDBModel.client_site_id.name,
        SiteDBModel.name.name,
        SiteDBModel.sub_sampling_number_of_clusters.name,
        SiteDBModel.simulation_version.name,
    }

    @staticmethod
    def get_deliverable_zipfile_path(site_id, client_id) -> Path:
        """Calculate the zipfile location in the GCP bucket"""
        return Path(GOOGLE_CLOUD_DELIVERABLES.joinpath(f"{client_id}/{site_id}.zip"))

    @staticmethod
    def get_building_json_surroundings_path(lv95_location: Point) -> Path:
        return BUILDING_SURROUNDINGS_DIR.joinpath(
            f"{lv95_location.x}_{lv95_location.y}.json"
        )

    @staticmethod
    def get_projected_location(
        site_id: Optional[int] = None, site_info: Optional[Dict[str, Any]] = None
    ) -> Point:
        if site_info is None:
            site_info = SiteDBHandler.get_by(id=site_id)

        return project_geometry(
            geometry=Point(site_info["lon"], site_info["lat"]),
            crs_from=REGION.LAT_LON,
            crs_to=REGION[site_info["georef_region"]],
        )

    @staticmethod
    def get_lat_lon_location(site_info: dict) -> Point:
        return Point(site_info["lon"], site_info["lat"])

    @classmethod
    def location_is_inside_switzerland(cls, site_info: Dict[str, Any]) -> bool:
        if Point(site_info["lon"], site_info["lat"]) == Point(*DEFAULT_IFC_LOCATION):
            # NOTE: IFC location is added from file asynchronously after site creation
            return False

        return site_info["georef_region"] == REGION.CH.name

    @classmethod
    def generate_basic_features(cls, site_id) -> List[Tuple[int, List[Dict]]]:
        """Generate features of the entire site given.

        Raises:
            BasicFeaturesException with the violations if basic features can't be calculated
        """
        from handlers import UnitHandler

        db_units = UnitDBHandler.find(
            site_id=site_id, output_columns=["id", "client_id"]
        )
        unit_handler = UnitHandler()
        violations = []
        for unit in db_units:
            violations.extend(unit_handler.validate_unit(unit_id=unit["id"]))

        if violations:
            raise BasicFeaturesException(violations=violations)

        return unit_handler.calculate_basic_features(
            units=db_units,
            basic_features=CustomValuatorBasicFeatures2(),
        )

    @classmethod
    def pipeline_completed_criteria(cls, site_id: int) -> PipelineCompletedCriteria:
        plans = PlanDBHandler.find(site_id=site_id)
        if plans:
            site_criteria = PipelineCompletedCriteria(
                labelled=True,
                classified=True,
                units_linked=True,
                splitted=True,
                georeferenced=True,
            )
        else:
            site_criteria = PipelineCompletedCriteria()

        for plan_info in plans:
            plan_criteria = PlanHandler(
                plan_id=plan_info["id"],
                plan_info=plan_info,
            ).pipeline_completed_criteria()
            for field_name in plan_criteria.__annotations__.keys():
                if getattr(plan_criteria, field_name) is False:
                    setattr(site_criteria, field_name, False)
        return site_criteria

    @classmethod
    @timer(logger=logger)
    def generate_georeferencing_surroundings_slam(cls, site_id: int):
        from surroundings.constants import BOUNDING_BOX_EXTENSION_GEOREFERENCING
        from surroundings.swisstopo import SwissTopoBuildingSurroundingHandler

        site = SiteDBHandler.get_by(id=site_id)
        lv95_location = cls.get_projected_location(site_info=site)
        buildings_surroundings_path = cls.get_building_json_surroundings_path(
            lv95_location=lv95_location
        )
        buildings_surroundings_path.parent.mkdir(parents=True, exist_ok=True)
        with buildings_surroundings_path.open(mode="w") as f:
            json.dump(
                {
                    "buildings": [
                        wkt.dumps(building.footprint)
                        for building in SwissTopoBuildingSurroundingHandler(
                            location=lv95_location,
                            bounding_box_extension=BOUNDING_BOX_EXTENSION_GEOREFERENCING,
                            simulation_version=SIMULATION_VERSION(
                                site["simulation_version"]
                            ),
                        ).get_buildings()
                    ]
                },
                f,
            )

        gcs_buildings_link = GCloudStorageHandler().upload_file_to_bucket(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            destination_folder=GOOGLE_CLOUD_BUILDING_SURROUNDINGS,
            local_file_path=buildings_surroundings_path,
            delete_local_after_upload=True,
        )
        SiteDBHandler.update(
            item_pks=dict(id=site_id),
            new_values=dict(gcs_buildings_link=gcs_buildings_link),
        )

    @classmethod
    def get_surr_buildings_footprints_for_site(
        cls, site_id: int, as_lat_lon: bool
    ) -> Iterable[Union[Polygon, MultiPolygon]]:
        """
        Raises:
            - GCSLinkEmptyException: when the surroundings task is not finished yet
            - SiteCheckException: When there are no building around the selected location
        """
        site_info = SiteDBHandler.get_by(id=site_id)
        lv95_location = cls.get_projected_location(site_id=site_id, site_info=site_info)
        try:
            with io.BytesIO(
                GCloudStorageHandler().download_bytes_from_media_link(
                    source_media_link=SiteDBHandler.get_by(id=site_id)[
                        "gcs_buildings_link"
                    ],
                    bucket_name=GOOGLE_CLOUD_BUCKET,
                )
            ) as building_surroundings_file:
                building_entries = json.loads(building_surroundings_file.read())
                if not building_entries:
                    raise SiteCheckException(
                        f"There are no Swisstopo buildings in the selected location {lv95_location} for georeferencing"
                    )

                buildings = []
                for footprint in building_entries["buildings"]:
                    if as_lat_lon:
                        buildings.append(
                            project_geometry(
                                geometry=wkt.loads(footprint),
                                crs_from=REGION[site_info["georef_region"]],
                                crs_to=REGION.LAT_LON,
                            )
                        )
                    else:
                        buildings.append(wkt.loads(footprint))

                return buildings
        except GCSLinkEmptyException as e:
            raise GCSLinkEmptyException(
                "The surroundings file is not ready yet, if this continues to be the case report the error to an admin"
            ) from e

    @classmethod
    def get_surroundings_path(cls, lv95_location: Point) -> Path:
        return SURROUNDINGS_DIR.joinpath(f"{lv95_location.x}_{lv95_location.y}.zip")

    @classmethod
    def get_surroundings_sample_path(cls, site_id: int) -> str:
        return f"{site_id}_sample_surroundings.html"

    @classmethod
    def get_view_surroundings(cls, site_info: dict):
        from surroundings.surrounding_handler import SurroundingStorageHandler

        yield from SurroundingStorageHandler.read_from_cloud(
            remote_path=GOOGLE_CLOUD_VIEW_SURROUNDINGS.joinpath(
                cls.get_surroundings_path(
                    lv95_location=cls.get_projected_location(site_info=site_info)
                ).name
            )
        )

    @classmethod
    def update_location_based_on_geoereferenced_layouts(cls, site_info: dict):
        plan_footprints_per_building = cls._plan_footprints_per_building(
            site_id=site_info["id"],
            with_underground=True,
        )
        if plan_footprints_per_building:
            xoffs = []
            yoffs = []

            for footprints in plan_footprints_per_building.values():
                for footprint in footprints:
                    centroid = footprint.centroid
                    xoffs.append(centroid.x)
                    yoffs.append(centroid.y)

            site_region = REGION[site_info["georef_region"]]
            new_location = project_geometry(
                geometry=Point(np.mean(xoffs), np.mean(yoffs)),
                crs_from=site_region,
                crs_to=REGION.LAT_LON,
            )
            SiteDBHandler.update(
                item_pks={"id": site_info["id"]},
                new_values={"lon": new_location.x, "lat": new_location.y},
            )

    @classmethod
    def generate_view_surroundings(
        cls,
        site_info: dict,
        sample: bool = False,
        simulation_version: SIMULATION_VERSION = None,
    ) -> Iterator[SurrTrianglesType]:
        from surroundings.surrounding_handler import generate_view_surroundings

        building_footprints = list(
            map(
                unary_union,
                cls._plan_footprints_per_building(site_id=site_info["id"]).values(),
            )
        )
        return generate_view_surroundings(
            site_id=site_info["id"],
            region=REGION[site_info["georef_region"]],
            location=cls.get_projected_location(site_info=site_info),
            simulation_version=simulation_version
            or SIMULATION_VERSION(site_info["simulation_version"]),
            building_footprints=building_footprints,
            sample=sample,
        )

    @classmethod
    def _plan_footprints_per_building(
        cls,
        site_id: int,
        with_underground: bool = False,
    ) -> Dict[int, List[Union[Polygon, MultiPolygon]]]:
        plan_footprints_per_building = defaultdict(list)
        for plan_info in PlanDBHandler.find(site_id=site_id):
            floors = FloorDBHandler.find(plan_id=plan_info["id"])
            # Exclude the plans underground if any
            if not with_underground and all(
                floor["floor_number"] < 0 for floor in floors
            ):
                continue
            plan_footprints_per_building[plan_info["building_id"]].append(
                PlanLayoutHandler(plan_id=plan_info["id"]).get_georeferenced_footprint()
            )
        return plan_footprints_per_building

    @classmethod
    def upload_view_surroundings(cls, site_id: int):
        from surroundings.surrounding_handler import SurroundingStorageHandler

        site_info = SiteDBHandler.get_by(id=site_id)

        SurroundingStorageHandler.upload(
            triangles=cls.generate_view_surroundings(site_info=site_info),
            remote_path=cls.get_surroundings_path(
                lv95_location=cls.get_projected_location(site_info=site_info)
            ),
        )

    # VIEW UTILS

    @classmethod
    def get_layout_triangles(
        cls, site_id: int, simulation_version: SIMULATION_VERSION, by_unit: bool
    ) -> Iterator[Tuple[str, np.ndarray]]:
        from handlers import BuildingHandler
        from handlers.db import BuildingDBHandler

        for building in BuildingDBHandler.find(output_columns=["id"], site_id=site_id):
            yield from BuildingHandler(
                building_id=building["id"]
            ).generate_layout_triangles(
                simulation_version=simulation_version, by_unit=by_unit
            )

    @classmethod
    @timer(logger=logger)
    def get_obs_points_by_unit_and_area(
        cls, site_id: int, grid_resolution: float, grid_buffer: float, obs_height: float
    ) -> Dict[Union[int], Dict[int, np.ndarray]]:
        from handlers import UnitHandler

        units = UnitDBHandler.get_joined_by_site_building_floor_id(site_id=site_id)
        unit_handler = UnitHandler()

        results = {}
        for unit in sorted(units, key=lambda z: z["id"]):
            results[unit["id"]] = unit_handler.get_obs_points_by_area(
                unit_id=unit["id"],
                grid_resolution=grid_resolution,
                grid_buffer=grid_buffer,
                obs_height=obs_height,
            )
        return results

    @classmethod
    def add(
        cls,
        ifc: Optional[List[FileStorage]] = None,
        **kwargs,
    ):
        if ifc:
            ifc_gcs_links = {}
            for ifc_filestorage in ifc:
                with NamedTemporaryFile() as tmp_file:
                    ifc_filepath = Path(tmp_file.name)
                    with ifc_filepath.open("wb") as f:
                        f.write(ifc_filestorage.read())

                    ifc_file_link = GCloudStorageHandler().upload_file_to_bucket(
                        bucket_name=get_client_bucket_name(
                            client_id=kwargs["client_id"]
                        ),
                        destination_folder=GOOGLE_CLOUD_SITE_IFC_FILES,
                        local_file_path=ifc_filepath,
                        destination_file_name=str(uuid.uuid4()) + ".ifc",
                    )
                    ifc_gcs_links[Path(ifc_filestorage.filename).stem] = ifc_file_link  # type: ignore

            kwargs["lon"] = kwargs.get("lon", DEFAULT_IFC_LOCATION[0])
            kwargs["lat"] = kwargs.get("lat", DEFAULT_IFC_LOCATION[1])
            kwargs["georef_region"] = REGION.CH.name
            kwargs["gcs_ifc_file_links"] = ifc_gcs_links

        if "lat" in kwargs and "lon" in kwargs and "georef_region" not in kwargs:
            kwargs["georef_region"] = GeoLocator.get_region_from_lat_lon(
                lat=kwargs["lat"], lon=kwargs["lon"]
            ).name

        qa_id = kwargs.pop("qa_id")
        site_info = SiteDBHandler.add(**kwargs)
        QADBHandler.update(
            item_pks={"id": qa_id},
            new_values={
                "site_id": site_info["id"],
                "client_site_id": site_info["client_site_id"],
            },
        )

        # run tasks
        if ifc:
            from tasks.site_ifc_tasks import get_ifc_import_task_chain

            # with the IFC we still don't know the location, so we can't decide if it is inside of CH
            get_ifc_import_task_chain(site_id=site_info["id"]).delay()
        elif cls.location_is_inside_switzerland(site_info=site_info):
            generate_geo_referencing_surroundings_for_site_task.delay(
                site_id=site_info["id"]
            )

        return site_info

    @classmethod
    def _new_lat_lon(cls, site_id: int, **kwargs) -> Dict:
        existing_site = SiteDBHandler.get_by(id=site_id)
        lat, lon = kwargs.get("lat"), kwargs.get("lon")

        if lat is None and lon is None:
            return {}
        lat = lat or existing_site["lat"]
        lon = lon or existing_site["lon"]
        if (existing_site["lat"], existing_site["lon"]) != (
            lat,
            lon,
        ):
            return {"lat": lat, "lon": lon}
        return {}

    @classmethod
    def update(cls, site_id: int, **kwargs) -> Dict:
        if new_lat_lon := cls._new_lat_lon(site_id=site_id, **kwargs):
            kwargs.update(**new_lat_lon)
            kwargs["georef_region"] = GeoLocator.get_region_from_lat_lon(
                lat=kwargs["lat"], lon=kwargs["lon"]
            ).name

        if kwargs.keys() & cls.SET_SITE_TO_UNPROCESSED_ON_UPDATE_COLUMNS:
            SiteDBHandler.set_site_to_unprocessed(site_id=site_id)

        updated_site = SiteDBHandler.update(
            item_pks=dict(id=site_id), new_values=kwargs
        )
        if new_lat_lon and cls.location_is_inside_switzerland(site_info=updated_site):
            generate_geo_referencing_surroundings_for_site_task.delay(site_id=site_id)
        return updated_site

    @classmethod
    def _get_area_sizes(cls, units: Iterable[Dict]) -> Dict[int, Dict[int, float]]:
        """Returns area sizes by area id"""
        with get_db_session_scope(readonly=True) as session:
            areas = (
                session.query(AreaDBModel, UnitsAreasDBModel)
                .join(UnitsAreasDBModel)
                .filter(UnitsAreasDBModel.unit_id.in_({unit["id"] for unit in units}))
                .all()
            )
            return {
                area.id: wkt.loads(area.scaled_polygon).area
                for area, _unit_area in areas
            }

    @classmethod
    def _get_net_area_distribution(
        cls, units: List[Dict], index: str
    ) -> typing.DefaultDict[str, int]:
        """All units must be from the same site"""
        from handlers import SlamSimulationHandler

        result: typing.DefaultDict[str, int] = defaultdict(int)
        if units:
            basic_features = SlamSimulationHandler.get_latest_results(
                site_id=units[0]["site_id"],
                task_type=TASK_TYPE.BASIC_FEATURES,
                success_only=True,
            )
            for unit in units:
                try:
                    net_area = basic_features[unit["id"]][0][
                        get_simulation_name(dimension=UNIT_BASICS_DIMENSION.NET_AREA)
                    ]
                    result[unit[index]] += net_area
                except (TypeError, KeyError):
                    result[unit[index]] += 0
        return result

    @classmethod
    def get_net_area_distribution(
        cls,
        units: List[Dict],
        site_id: Optional[int] = None,
        building_id: Optional[int] = None,
        floor_id: Optional[int] = None,
        unit_id: Optional[int] = None,
    ):
        if site_id:
            # Aggregate units by building
            index = "building_id"
            for floor in FloorDBHandler.find_in(
                id=[unit["floor_id"] for unit in units],
                output_columns=["id", "building_id"],
            ):
                for unit in units:
                    if unit["floor_id"] == floor["id"]:
                        unit["building_id"] = floor["building_id"]
        elif building_id:
            index = "floor_id"
        elif floor_id:
            index = "id"
        elif unit_id:
            return cls._get_area_sizes(units=units)
        else:
            raise NetAreaDistributionUnsetException(
                "get_net_area_distribution should have defined one of "
                "site_id, building_id, floor_id, unit_id"
            )

        return cls._get_net_area_distribution(units=units, index=index)

    @classmethod
    def generate_store_qa_validation(cls, site_id: int):
        from handlers import QAHandler

        qa_validation = QAHandler(site_id=site_id).qa_validation()
        SiteDBHandler.update(
            item_pks={"id": site_id}, new_values={"qa_validation": qa_validation}
        )

    @staticmethod
    def _floor_ids_by_plan(site_id: int) -> typing.DefaultDict[int, List[int]]:
        floor_ids_by_plan = defaultdict(list)
        for floor in FloorDBHandler.find_by_site_id(site_id=site_id):
            floor_ids_by_plan[floor["plan_id"]].append(floor["id"])
        return floor_ids_by_plan

    @classmethod
    def get_unit_layouts(
        cls,
        site_id: int,
        scaled: bool = False,
        georeferenced: bool = False,
        anonymized: bool = False,
    ) -> Iterator[Tuple[PartialUnitInfo, SimLayout]]:
        for plan_id, floor_ids in cls._floor_ids_by_plan(site_id=site_id).items():
            layout_handler = PlanLayoutHandler(plan_id=plan_id)
            for floor_id in floor_ids:
                yield from layout_handler.get_unit_layouts(
                    floor_id=floor_id,
                    scaled=scaled,
                    georeferenced=georeferenced,
                    anonymized=anonymized,
                )

    @classmethod
    def get_public_layouts(
        cls,
        site_id: int,
        scaled: bool = False,
        georeferenced: bool = False,
    ) -> Iterator[Tuple[int, SimLayout]]:
        for plan_id, floor_ids in cls._floor_ids_by_plan(site_id=site_id).items():
            public_layout = PlanLayoutHandler(plan_id=plan_id).get_public_layout(
                scaled=scaled,
                georeferenced=georeferenced,
            )
            for floor_id in floor_ids:
                yield floor_id, public_layout

    @classmethod
    def get_dms_sites(
        cls,
        client_id: int,
        dms_limited_sql_filter: Optional[str] = None,
    ):
        output_columns = [
            "id",
            "name",
            "labels",
            "created",
            "lat",
            "lon",
            "client_site_id",
        ]
        return SiteDBHandler.find(
            client_id=client_id,
            full_slam_results=ADMIN_SIM_STATUS.SUCCESS,
            heatmaps_qa_complete=True,
            output_columns=output_columns,
            special_filter=dms_limited_sql_filter,
        )

    @classmethod
    def get_plan_ids_with_annotation_ready(cls, site_id: int) -> typing.Set[int]:
        plan_ids = [
            plan["id"]
            for plan in PlanDBHandler.find(site_id=site_id, output_columns=["id"])
        ]
        return {
            x["plan_id"]
            for x in ReactPlannerProjectsDBHandler.find_in(
                plan_id=plan_ids, output_columns=["plan_id"]
            )
        }
