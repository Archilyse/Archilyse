from collections import defaultdict
from typing import IO, Collection, Dict, Iterable, List, Optional, Tuple, Union

from methodtools import lru_cache
from numpy import ndarray
from shapely.geometry import Point

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimLayout
from brooks.models.violation import Violation, ViolationType
from brooks.unit_layout_factory import UnitLayoutFactory
from brooks.visualization.brooks_plotter import BrooksPlotter
from common_utils.constants import (
    GOOGLE_CLOUD_RESULT_IMAGES,
    SIMULATION_VERSION,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
    TASK_TYPE,
    UNIT_USAGE,
)
from common_utils.exceptions import (
    BaseSlamException,
    DBNotFoundException,
    InvalidShapeException,
    SimulationNotSuccessException,
    ValidationException,
)
from common_utils.logger import logger
from connectors.db_connector import get_db_session_scope
from handlers import (
    AreaHandler,
    ClientHandler,
    PlanLayoutHandler,
    SlamSimulationHandler,
)
from handlers.constants import GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE
from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.db.clustering_subsampling_handler import ClusteringSubsamplingDBHandler
from handlers.db.utils import retry_on_db_operational_error
from handlers.floor_handler import FloorHandler
from handlers.gcloud_storage import GCloudStorageHandler
from handlers.plan_layout_handler import PlanLayoutHandlerIDCacheMixin
from handlers.utils import get_client_bucket_name
from simulations.basic_features.basic_feature import BaseBasicFeatures
from simulations.view.meshes import GeoreferencingTransformation
from simulations.view.meshes.observation_points import get_observation_points_by_area
from simulations.view.meshes.triangulation3d import TRIANGULATOR_BY_SIMULATION_VERSION


class UnitType:
    def __init__(
        self,
        number_of_rooms: Optional[float] = None,
        unit_type: Optional[str] = None,
    ) -> None:
        self.unit_type = unit_type or number_of_rooms
        self.classification_scheme = UnifiedClassificationScheme()

    @property
    def name(self) -> str:
        return str(self.unit_type)


class UnitHandler(PlanLayoutHandlerIDCacheMixin):
    def __init__(
        self, layout_handler_by_id: Optional[Dict[int, PlanLayoutHandler]] = None
    ) -> None:
        super().__init__(layout_handler_by_id=layout_handler_by_id)
        self.plan_info: Dict[int, Dict] = {}
        self.unit_info: Dict[int, Dict] = {}

    @classmethod
    def unit_areas(cls, unit_id: int, plan_id: int) -> List[Dict]:
        unit_area_ids = {
            unit_area["area_id"]
            for unit_area in UnitAreaDBHandler.find(
                unit_id=unit_id, output_columns=["area_id"]
            )
        }

        return [
            area
            for area in PlanLayoutHandler(plan_id=plan_id).scaled_areas_db
            if area["id"] in unit_area_ids
        ]

    @staticmethod
    def group_by_client_id(units: Iterable[Dict]) -> Dict[str, List]:
        units_by_client_id = defaultdict(list)
        for u in units:
            units_by_client_id[u["client_id"]].append(u)
        return units_by_client_id

    @retry_on_db_operational_error()
    def bulk_upsert_units(
        self,
        plan_id: int,
        apartment_no: int,
        unit_type: Optional[str] = None,
    ) -> List[Dict]:
        """Add or update the existing units under a plan"""
        with get_db_session_scope():
            units_to_update = UnitDBHandler.find(
                plan_id=plan_id, apartment_no=apartment_no
            )

            if unit_type and len(units_to_update) > 0:
                UnitDBHandler.bulk_update(
                    unit_type={unit["id"]: unit_type for unit in units_to_update}
                )

            db_floors = FloorDBHandler.find(plan_id=plan_id)
            if not db_floors:
                raise ValidationException(
                    f"No floors found for plan {plan_id} while trying to create units"
                )
            updated_floor_ids = {unit["floor_id"] for unit in units_to_update}
            floors_missing = {f["id"] for f in db_floors} - updated_floor_ids
            plan_info = self._get_plan_info(plan_id)

            new_apartments = [
                {
                    "site_id": plan_info["site_id"],
                    "plan_id": plan_id,
                    "floor_id": floor_missing,
                    "apartment_no": apartment_no,
                    "unit_type": unit_type,
                    "area_ids": [],
                }
                for floor_missing in floors_missing
            ]

            UnitDBHandler.bulk_insert(items=new_apartments)
            return new_apartments + units_to_update

    @staticmethod
    def unique_heatmap_filename(unit_info: Dict, floor_info: Dict, dimension: str):
        return f"{unit_info['client_id']}-{floor_info['floor_number']}-{unit_info['id']}-heatmap-{dimension}.png"

    @staticmethod
    def unique_image_filename(
        unit_info: Dict,
        floor_info: Dict,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> str:
        client_id = unit_info["client_id"].replace(".", "-")
        return f"{client_id}-{floor_info['floor_number']}-{unit_info['id']}-floorplan-{language.name}.{file_format.name.lower()}"

    def get_unit_layouts(
        self, units_info: List[Dict], postprocessed: bool
    ) -> List[SimLayout]:
        area_ids_by_unit_id = defaultdict(list)
        for unit_area in UnitAreaDBHandler.find_in(
            unit_id=[unit["id"] for unit in units_info]
        ):
            area_ids_by_unit_id[unit_area["unit_id"]].append(unit_area["area_id"])

        return [
            self.build_unit_from_area_ids(
                plan_id=unit["plan_id"],
                area_ids=area_ids_by_unit_id[unit["id"]],
                floor_number=self._get_floor_info_by_id(floor_id=unit["floor_id"])[
                    "floor_number"
                ],
                georeference_plan_layout=False,
                postprocessed=postprocessed,
            )
            for unit in units_info
        ]

    def get_unit_layout(
        self,
        unit_id: int,
        postprocessed: bool,
        georeferenced: bool = False,
        deep_copied: bool = True,
    ) -> SimLayout:
        unit = self._get_unit_info(unit_id)
        return self.build_unit_from_area_ids(
            plan_id=unit["plan_id"],
            area_ids=[x["area_id"] for x in UnitAreaDBHandler.find(unit_id=unit_id)],
            georeference_plan_layout=georeferenced,
            postprocessed=postprocessed,
            deep_copied=deep_copied,
        )

    def validate_unit_given_area_ids(
        self,
        plan_id: int,
        new_area_ids: List[int],
        apartment_no: int,
        only_blocking: Optional[bool] = True,
    ) -> List[Violation]:
        from handlers.editor_v2 import ReactPlannerHandler
        from handlers.validators import (
            AllAreasSpacesSelectedValidator,
            AreasNotDefinedValidator,
            DoorValidator,
            ForeignPlanAreaValidator,
            SpacesConnectedValidator,
            SpacesDoorsSinglePolygonValidator,
            SpacesUnionSinglePolygonValidator,
            UnitAccessibleValidator,
            UnitKitchenCountValidator,
        )

        validators = (
            ForeignPlanAreaValidator,
            UnitAccessibleValidator,
            AreasNotDefinedValidator,
            DoorValidator,  # Always before SpacesConnectedValidator to avoid confusing messages
            SpacesConnectedValidator,
            AllAreasSpacesSelectedValidator,
            UnitKitchenCountValidator,
            SpacesDoorsSinglePolygonValidator,
            SpacesUnionSinglePolygonValidator,
        )
        violations = []

        plan_handler = ReactPlannerHandler()

        for validator in validators:
            for violation in validator(
                plan_id=plan_id,
                new_area_ids=new_area_ids,
                apartment_no=apartment_no,
                unit_handler=self,
            ).validate():
                if (not only_blocking) or (only_blocking and violation.is_blocking):
                    violations.append(
                        plan_handler.violation_position_to_pixels(
                            violation=violation,
                            plan_id=plan_id,
                        )
                    )
        return violations

    def build_unit_from_area_ids(
        self,
        plan_id: int,
        area_ids: Collection[int],
        georeference_plan_layout: bool = False,
        postprocessed: bool = False,
        floor_number: int = 0,
        deep_copied: bool = True,
    ) -> SimLayout:
        plan_layout = self.layout_handler_by_id(plan_id=plan_id).get_layout(
            classified=True,
            scaled=True,
            georeferenced=georeference_plan_layout,
            postprocessed=postprocessed,
            deep_copied=deep_copied,
        )
        db_area_to_brooks_space = {
            area.db_area_id: space.id
            for space in plan_layout.spaces
            for area in space.areas
            if area.db_area_id is not None
        }

        return UnitLayoutFactory(plan_layout=plan_layout).create_sub_layout(
            spaces_ids={
                db_area_to_brooks_space[db_area_id]
                for db_area_id in area_ids
                if db_area_id in db_area_to_brooks_space
            },
            area_db_ids=set(area_ids),
            floor_number=floor_number,
        )

    def get_unit_type(self, unit_id: int) -> UnitType:
        unit_info = self._get_unit_info(unit_id=unit_id)
        if unit_info["unit_type"]:
            return UnitType(unit_type=unit_info["unit_type"])

        basic_features_results = SlamSimulationHandler.get_results(
            unit_id=unit_id,
            site_id=unit_info["site_id"],
            task_type=TASK_TYPE.BASIC_FEATURES,
        )
        number_of_rooms = (
            basic_features_results[0]["UnitBasics.number-of-rooms"]
            if basic_features_results
            else None
        )

        return UnitType(number_of_rooms=number_of_rooms)

    def validate_unit(self, unit_id: int) -> List[Violation]:
        unit = self._get_unit_info(unit_id=unit_id)
        try:
            return self.validate_unit_given_area_ids(
                plan_id=unit["plan_id"],
                new_area_ids=[
                    a["area_id"] for a in UnitAreaDBHandler.find(unit_id=unit_id)
                ],
                apartment_no=unit["apartment_no"],
            )
        except InvalidShapeException:
            return [
                Violation(
                    violation_type=ViolationType.INVALID_AREA,
                    position=Point(0, 0),
                    human_id=unit["client_id"],
                )
            ]

    def calculate_basic_features(
        self,
        units: List[Dict],
        basic_features: BaseBasicFeatures,
    ) -> List[Tuple[int, List[Dict]]]:

        # NOTE: basic features are aggregated across all units with the same client id
        units_by_client_id = self.group_by_client_id(units=units)

        result = []
        for units_of_client in units_by_client_id.values():
            vector = [
                {
                    f"UnitBasics.{key}": new_value
                    for key, new_value in basic_features.get_basic_features(
                        unit_id_unit_layout={
                            u["id"]: self.get_unit_layout(
                                unit_id=u["id"], postprocessed=False
                            )
                            for u in units_of_client
                        }
                    ).items()
                }
            ]
            for unit in units_of_client:
                result.append((unit["id"], vector))
        return result

    def get_floorplan_image_filename(
        self,
        unit_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> str:
        unit_info = self._get_unit_info(unit_id=unit_id)
        floor_info = self._get_floor_info_by_unit_id(unit_id=unit_id)
        return self.unique_image_filename(
            unit_info=unit_info,
            floor_info=floor_info,
            language=language,
            file_format=file_format,
        )

    def generate_floorplan_image(
        self,
        unit_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> Tuple[IO, str, Dict]:
        unit_info = self._get_unit_info(unit_id)
        logger.info(
            f"Generating floorplan for unit id:{unit_info['id']}, "
            f"client_id :{unit_info['client_id']}, "
            f"plan id: {unit_info['plan_id']}, site id: {unit_info['site_id']}"
        )
        try:
            basic_features_results = SlamSimulationHandler.get_results(
                unit_id=unit_id,
                site_id=unit_info["site_id"],
                task_type=TASK_TYPE.BASIC_FEATURES,
            )
        except (DBNotFoundException, SimulationNotSuccessException) as e:
            raise BaseSlamException("Basic features are missing.") from e

        floor_info = self._get_floor_info_by_unit_id(unit_id=unit_id)
        floor_plan_layout = self.layout_handler_by_id(
            plan_id=unit_info["plan_id"]
        ).get_layout(scaled=True, classified=True, postprocessed=True)
        target_layout = self.get_unit_layout(unit_id=unit_id, postprocessed=True)

        building_info = BuildingDBHandler.get_by(id=floor_info["building_id"])
        unit_metadata = dict(
            street=building_info["street"],
            housenumber=building_info["housenumber"],
            level=floor_info["floor_number"],
            number_of_rooms=basic_features_results[0]["UnitBasics.number-of-rooms"],
            net_area=basic_features_results[0]["UnitBasics.net-area"],
            city=building_info["city"],
        )

        site_info = self._site_info(unit_id=unit_id)
        logo_content = ClientHandler.get_logo_content(client_id=site_info["client_id"])

        plotter = BrooksPlotter()
        io_image = plotter.generate_unit_plot(
            unit_target_layout=target_layout,
            angle_north=90
            - self._get_plan_info(unit_info["plan_id"])["georef_rot_angle"],
            floor_plan_layout=floor_plan_layout,
            metadata=unit_metadata,
            logo_content=logo_content,
            language=language,
            file_format=file_format,
        )

        logger.info(
            f"Generated floorplan for unit id:{unit_info['id']}, client_id :{unit_info['client_id']}, "
            f"floor number: {floor_info['floor_number']}, plan id: {floor_info['plan_id']}, "
            f"building: {floor_info['building_id']}, site {site_info['id']}"
        )

        image_filename = self.old_upload_content_to_gcs(
            file_format=file_format,
            content=io_image.read(),
            language=language,
            unit_id=unit_id,
        )
        io_image.seek(0)
        return io_image, image_filename, site_info

    def old_upload_content_to_gcs(
        self,
        file_format: SUPPORTED_OUTPUT_FILES,
        content: Union[bytes, str],
        language: SUPPORTED_LANGUAGES,
        unit_id: int,
    ) -> str:
        image_filename = self.get_floorplan_image_filename(
            unit_id=unit_id, language=language, file_format=file_format
        )
        gcs_floorplan_link = GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=get_client_bucket_name(
                client_id=self._site_info(unit_id=unit_id)["client_id"]
            ),
            destination_folder=GOOGLE_CLOUD_RESULT_IMAGES,
            destination_file_name=image_filename,
            contents=content,
        )
        UnitDBHandler.update(
            item_pks=dict(id=unit_id),
            new_values={
                GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][
                    language
                ]: gcs_floorplan_link
            },
        )
        return image_filename

    @lru_cache()
    def _get_floor_info_by_id(self, floor_id: int) -> Dict:
        return FloorDBHandler.get_by(id=floor_id)

    @lru_cache()
    def _get_floor_info_by_unit_id(self, unit_id: int) -> Dict:
        unit_info = self._get_unit_info(unit_id=unit_id)
        return FloorDBHandler.get_by(id=unit_info["floor_id"])

    @lru_cache()
    def _site_info(self, unit_id: int) -> Dict:
        unit_info = self._get_unit_info(unit_id=unit_id)
        return SiteDBHandler.get_by(id=unit_info["site_id"])

    @lru_cache()
    def _get_unit_info(self, unit_id: int) -> Dict:
        return UnitDBHandler.get_by(id=unit_id)

    @lru_cache()
    def _get_plan_info(self, plan_id: int) -> Dict:
        return PlanDBHandler.get_by(id=plan_id)

    # VIEW UTILS

    def get_layout_triangles(
        self,
        unit_id: int,
        layout: SimLayout,
        layouts_upper_floor: Iterable[SimLayout],
        building_elevation: float,
        simulation_version: SIMULATION_VERSION,
    ) -> List[ndarray]:

        unit_info = self._get_unit_info(unit_id)

        georef_transformation = GeoreferencingTransformation()
        georef_transformation.set_translation(x=0, y=0, z=building_elevation)
        georef_transformation.set_swap_dimensions(0, 1)

        triangulator = TRIANGULATOR_BY_SIMULATION_VERSION[simulation_version.name](
            layout=layout,
            georeferencing_parameters=georef_transformation,
        )
        return triangulator.create_layout_triangles(
            layouts_upper_floor=layouts_upper_floor,
            level_baseline=FloorHandler.get_level_baseline(
                floor_id=unit_info["floor_id"]
            ),
        )

    def get_obs_points_by_area(
        self,
        unit_id: int,
        grid_resolution: float,
        grid_buffer: float,
        obs_height: float,
    ) -> Dict[int, ndarray]:

        unit_info = self._get_unit_info(unit_id)
        georef_transformation = FloorHandler.get_georeferencing_transformation(
            floor_id=unit_info["floor_id"]
        )
        layout_scaled = self.get_unit_layout(
            unit_id=unit_info["id"], postprocessed=False
        )
        obs_points_by_area = get_observation_points_by_area(
            areas=layout_scaled.areas,
            level_baseline=FloorHandler.get_level_baseline(
                floor_id=unit_info["floor_id"]
            ),
            georeferencing_parameters=georef_transformation,
            resolution=grid_resolution,
            buffer=grid_buffer,
            obs_height=obs_height,
        )

        obs_points_by_db_area_id = {
            area.db_area_id: obs_points for area, obs_points in obs_points_by_area
        }

        return obs_points_by_db_area_id

    # SPLITTING UTILS

    @classmethod
    def get_new_apartment_no(cls, plan_id: int) -> int:
        return (
            max(
                UnitDBHandler.find(plan_id=plan_id, output_columns=["apartment_no"]),
                default={"apartment_no": 0},
                key=lambda z: z["apartment_no"],
            )["apartment_no"]
            + 1
        )

    @classmethod
    def get_synced_apartments(
        cls, plan_id: int, apartment_area_ids: List[List[int]]
    ) -> Tuple[Dict, Dict]:
        units_info = UnitDBHandler.find(plan_id=plan_id)
        apartment_no_to_area_ids = {
            unit["apartment_no"]: {
                unit_area["area_id"]
                for unit_area in UnitAreaDBHandler.find(
                    unit_id=unit["id"], output_columns=["area_id"]
                )
            }
            for unit in units_info
        }
        area_id_to_apartment_no = {
            area_id: apartment_no
            for apartment_no, area_ids in apartment_no_to_area_ids.items()
            for area_id in area_ids
        }

        new_apartments, synced_apartments = {}, {}
        new_apartment_no = cls.get_new_apartment_no(plan_id=plan_id)
        for area_ids in apartment_area_ids:
            apartment_nos = {
                area_id_to_apartment_no[area_id]
                for area_id in area_ids
                if area_id in area_id_to_apartment_no
            }
            if len(apartment_nos) == 0:
                new_apartments[new_apartment_no] = area_ids
                new_apartment_no += 1
            elif len(apartment_nos) == 1:
                apartment_no = apartment_nos.pop()
                synced_apartments[apartment_no] = apartment_no_to_area_ids[
                    apartment_no
                ].union(area_ids)
            else:
                ValueError(
                    f"The areas provided belong to multiple apartments: {set(apartment_nos)}"
                )

        return new_apartments, synced_apartments

    @classmethod
    def create_or_extend_units_from_areas(
        cls, plan_id: int, apartment_area_ids: List[List[int]]
    ) -> None:
        new_apartments, synced_apartments = cls.get_synced_apartments(
            plan_id=plan_id, apartment_area_ids=apartment_area_ids
        )

        with get_db_session_scope():
            for apartment_no in new_apartments.keys():
                UnitHandler().bulk_upsert_units(
                    plan_id=plan_id,
                    apartment_no=apartment_no,
                )

            for apartment_no, area_ids in {
                **new_apartments,
                **synced_apartments,
            }.items():
                AreaHandler.update_relationship_with_units(
                    plan_id=plan_id,
                    apartment_no=apartment_no,
                    area_ids=area_ids,
                )

    @classmethod
    def get_gcs_link_as_bytes(
        cls,
        unit_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> Tuple[bytes, str]:
        from handlers.utils import get_site_id_from_any_level

        site_id = get_site_id_from_any_level(params={"unit_id": unit_id})
        site_info = SiteDBHandler.get_by(
            id=site_id, output_columns=["client_id", "name"]
        )

        unit_info = UnitDBHandler.get_by(
            id=unit_id,
            output_columns=[
                GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language],
                "client_id",
            ],
        )
        file_name = (
            f"{site_info['name']}_{unit_info['client_id']}"
            f"_{language.name}.{file_format.name.lower()}"
        )
        return (
            GCloudStorageHandler().download_bytes_from_media_link(
                bucket_name=get_client_bucket_name(client_id=site_info["client_id"]),
                source_media_link=unit_info[
                    GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language]
                ],
            ),
            file_name,
        )

    @classmethod
    def update_units_representative(
        cls,
        site_id: int,
        clustering_id: Optional[str] = None,
        clustering_subsampling: Optional[Dict[str, List[str]]] = None,
    ):
        """

        Args:
            site_id:
            clustering_id: Optional; ID of the clustering subsampling data to retrieve.
                    Used if clustering_subsampling is not provided
            clustering_subsampling: Data of the clustering subsampling.

        Returns:

        """

        if clustering_subsampling is None:
            clustering_subsampling = ClusteringSubsamplingDBHandler.get_by(
                id=clustering_id
            )["results"]

        units_by_client_id = cls.group_by_client_id(
            units=UnitDBHandler.find(
                site_id=site_id, unit_usage=UNIT_USAGE.RESIDENTIAL.name
            )
        )

        for representative_client_id, cluster in clustering_subsampling.items():
            cluster_units_ids = {
                u["id"]
                for unit_client_id in cluster
                for u in units_by_client_id[unit_client_id]
            }
            UnitDBHandler.bulk_update(
                representative_unit_client_id={
                    u_id: representative_client_id for u_id in cluster_units_ids
                }
            )

    @classmethod
    def duplicate_apartments_new_floor(
        cls, plan_id: int, new_floor_ids: List[int]
    ) -> List[Dict]:
        existing_units = UnitDBHandler.find(plan_id=plan_id)

        existing_unit_ids = [x["id"] for x in existing_units]
        existing_unit_areas = list(UnitAreaDBHandler.find_in(unit_id=existing_unit_ids))

        units_to_insert = []
        area_ids_by_apartment_no = {}
        unique_apartment_nos = set()
        for unit in existing_units:
            if unit["apartment_no"] not in unique_apartment_nos:
                unique_apartment_nos.add(unit["apartment_no"])
                area_ids_by_apartment_no[unit["apartment_no"]] = [
                    unit_area["area_id"]
                    for unit_area in existing_unit_areas
                    if unit_area["unit_id"] == unit["id"]
                ]
                unit.pop("id")
                unit.pop("floor_id")
                for floor_id in new_floor_ids:
                    units_to_insert.append({**unit, "floor_id": floor_id})

        UnitDBHandler.bulk_insert(items=units_to_insert)
        cls.duplicate_unit_areas(
            area_ids_by_apartment_no=area_ids_by_apartment_no,
            new_floor_ids=new_floor_ids,
        )
        return units_to_insert

    @classmethod
    def duplicate_unit_areas(
        cls, area_ids_by_apartment_no: Dict[int, List], new_floor_ids: List[int]
    ):
        new_unit_ids_by_apartment_no = defaultdict(list)
        for new_unit in UnitDBHandler.find_in(
            floor_id=new_floor_ids, output_columns=["id", "apartment_no"]
        ):
            new_unit_ids_by_apartment_no[new_unit["apartment_no"]].append(
                new_unit["id"]
            )
        unit_areas_to_insert = []
        for apartment_no, new_unit_ids in new_unit_ids_by_apartment_no.items():
            for new_unit_id in new_unit_ids:
                for area_id in area_ids_by_apartment_no[apartment_no]:
                    unit_areas_to_insert.append(
                        {"unit_id": new_unit_id, "area_id": area_id}
                    )
        UnitAreaDBHandler.bulk_insert(items=unit_areas_to_insert)
        return unit_areas_to_insert
