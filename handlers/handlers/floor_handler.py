from pathlib import Path
from typing import IO, Dict, List, Optional, Set, Tuple, Union

from methodtools import lru_cache
from sqlalchemy.exc import IntegrityError
from werkzeug.datastructures import FileStorage

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimLayout
from brooks.utils import get_floor_height
from brooks.visualization.brooks_plotter import BrooksPlotter
from common_utils.constants import (
    SIMULATION_VERSION,
    SUPPORTED_LANGUAGES,
    SUPPORTED_OUTPUT_FILES,
)
from common_utils.exceptions import DBValidationException, ValidationException
from common_utils.logger import logger
from connectors.db_connector import get_db_session_scope
from handlers import DMSUnitDeliverableHandler
from handlers.constants import (
    GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE,
    GCS_DIRECTORY_BY_FILE_FORMAT,
)
from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.db.utils import retry_on_db_operational_error
from handlers.plan_layout_handler import PlanLayoutHandlerIDCacheMixin
from handlers.utils import get_client_bucket_name, get_site_id_from_any_level
from simulations.view.meshes import GeoreferencingTransformation
from simulations.view.meshes.triangulation3d import TRIANGULATOR_BY_SIMULATION_VERSION


class FloorHandler(PlanLayoutHandlerIDCacheMixin):
    @classmethod
    @retry_on_db_operational_error()
    def create_floors_from_plan_file(
        cls, floorplan: FileStorage, building_id: int, new_floor_numbers: Set[int]
    ):
        from handlers import PlanHandler

        # Make sure that file hasn't been read in any other place
        floorplan.stream.seek(0)

        with get_db_session_scope():
            site_id = BuildingDBHandler.get_by(id=building_id)["site_id"]

            plan_id = PlanHandler.add(
                plan_content=floorplan.stream.read(),
                plan_mime_type=floorplan.content_type,
                site_id=site_id,
                building_id=building_id,
            )["id"]

            existing_floor_numbers = {
                floor["floor_number"]
                for floor in FloorDBHandler.find(
                    plan_id=plan_id, output_columns=["floor_number"]
                )
            }

            return cls.upsert_floor_numbers(
                building_id=building_id,
                plan_id=plan_id,
                floor_numbers=new_floor_numbers.union(existing_floor_numbers),
            )

    @staticmethod
    def get_floor_numbers_from_floor_range(
        floor_lower_range: int,
        floor_upper_range: Optional[int] = None,
    ) -> Set[int]:
        floor_upper_range = (
            floor_lower_range if floor_upper_range is None else floor_upper_range
        ) + 1
        if floor_lower_range > floor_upper_range:
            raise ValidationException(
                f"Requested a range of floors between {floor_lower_range} and {floor_upper_range}"
            )
        return set(range(floor_lower_range, floor_upper_range))

    @classmethod
    @retry_on_db_operational_error()
    def upsert_floor_numbers(
        cls,
        building_id: int,
        plan_id: int,
        floor_numbers: Set[int],
    ) -> List[Dict]:

        existing_floors = FloorDBHandler.find(
            plan_id=plan_id, output_columns=["id", "floor_number"]
        )
        floor_id_by_floor_number = {
            floor["floor_number"]: floor["id"] for floor in existing_floors
        }
        existing_floor_numbers = set(floor_id_by_floor_number.keys())
        missing_floor_numbers = floor_numbers - existing_floor_numbers

        floors_to_insert = [
            {"building_id": building_id, "floor_number": fn, "plan_id": plan_id}
            for fn in missing_floor_numbers
        ]
        try:
            FloorDBHandler.bulk_insert(items=floors_to_insert)
        except IntegrityError:
            raise DBValidationException(
                f"Some of the floor numbers requested to be created {missing_floor_numbers} "
                f"already exist for the building"
            )
        if floors_to_insert:
            from handlers import UnitHandler

            floors = FloorDBHandler.find_in(
                floor_number=[f["floor_number"] for f in floors_to_insert],
                plan_id=[plan_id],
                output_columns=["id"],
            )
            UnitHandler.duplicate_apartments_new_floor(
                plan_id=plan_id,
                new_floor_ids=[floor["id"] for floor in floors],
            )

        floor_nums_to_remove = existing_floor_numbers - floor_numbers
        floor_ids_to_remove = [
            floor_id_by_floor_number[floor_number]
            for floor_number in floor_nums_to_remove
        ]
        if floor_ids_to_remove:
            FloorDBHandler.delete_in(id=floor_ids_to_remove)
        return FloorDBHandler.find(plan_id=plan_id, building_id=building_id)

    @staticmethod
    def get_gcs_floorplan_image_filename(
        site_id: int,
        building_id: int,
        floor_number: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> str:
        filename = Path(
            f"{site_id}-{building_id}-{floor_number}-full_floorplan_{language.name}.{file_format.name}"
        )
        if file_format == SUPPORTED_OUTPUT_FILES.DWG:
            return filename.with_suffix(
                f".{DMSUnitDeliverableHandler.suffix_normalization(extension=file_format.name)}"
            ).as_posix()
        return filename.as_posix()

    def generate_floorplan_image(
        self,
        floor_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> Tuple[IO, str, Dict]:
        from handlers import ClientHandler, UnitHandler

        floor_info = FloorDBHandler.get_by(id=floor_id)
        building_info = BuildingDBHandler.get_by(id=floor_info["building_id"])
        units_info = UnitDBHandler.find(floor_id=floor_info["id"])

        unit_layouts = UnitHandler(
            layout_handler_by_id=self._layout_handler_by_id
        ).get_unit_layouts(
            units_info=units_info,
            postprocessed=True,
        )
        metadata = dict(
            street=building_info["street"],
            housenumber=building_info["housenumber"],
            level=floor_info["floor_number"],
            zipcode=building_info["zipcode"],
            city=building_info["city"],
        )

        site_info = SiteDBHandler.get_by(id=building_info["site_id"])
        logo_content = ClientHandler.get_logo_content(client_id=site_info["client_id"])
        layout_handler = self.layout_handler_by_id(plan_id=floor_info["plan_id"])
        georef_rot_angle = PlanDBHandler.get_by(
            id=floor_info["plan_id"], output_columns=["georef_rot_angle"]
        )["georef_rot_angle"]
        floor_plan_layout_scaled = layout_handler.get_layout(
            scaled=True, classified=True, postprocessed=True, georeferenced=False
        )

        io_image = BrooksPlotter().generate_floor_plot(
            angle_north=90 - georef_rot_angle,
            floor_plan_layout=floor_plan_layout_scaled,
            unit_layouts=unit_layouts,
            unit_ids=[unit["client_id"] for unit in units_info],
            metadata=metadata,
            logo_content=logo_content,
            language=language,
            file_format=file_format,
        )
        logger.info(
            f"Generated floorplan for floor id:{floor_info['id']}, "
            f"floor number:{floor_info['floor_number']}, plan id:{floor_info['plan_id']}, "
            f"building {building_info['id']}, site {building_info['site_id']} "
            f"in language {language.name}"
        )
        image_filename = self.old_upload_content_to_gcs(
            site_id=building_info["site_id"],
            building_id=building_info["id"],
            floor_id=floor_id,
            floor_number=floor_info["floor_number"],
            contents=io_image.read(),
            file_format=file_format,
            language=language,
        )
        io_image.seek(0)
        return io_image, image_filename, site_info

    @classmethod
    def old_upload_content_to_gcs(
        cls,
        site_id: int,
        building_id: int,
        file_format: SUPPORTED_OUTPUT_FILES,
        floor_id: int,
        floor_number: int,
        contents: Union[bytes, str],
        language: SUPPORTED_LANGUAGES,
    ) -> str:
        from handlers import GCloudStorageHandler

        image_filename = cls.get_gcs_floorplan_image_filename(
            site_id=site_id,
            building_id=building_id,
            floor_number=floor_number,
            language=language,
            file_format=file_format,
        )
        gcs_link = GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=get_client_bucket_name(
                client_id=SiteDBHandler.get_by(id=site_id)["client_id"]
            ),
            destination_folder=GCS_DIRECTORY_BY_FILE_FORMAT[file_format],
            destination_file_name=image_filename,
            contents=contents,
        )
        FloorDBHandler.update(
            item_pks=dict(id=floor_id),
            new_values={
                GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language]: gcs_link
            },
        )
        return image_filename

    @classmethod
    def get_georeferencing_transformation(cls, floor_id: int):
        from handlers import PlanLayoutHandler

        floor_info = FloorDBHandler.get_by(id=floor_id)
        building_info = BuildingDBHandler.get_by(
            id=floor_info["building_id"],
            output_columns=["elevation", "elevation_override"],
        )
        elevation = (
            building_info["elevation_override"]
            if building_info["elevation_override"] is not None
            else building_info["elevation"]
        ) or 0.0

        georef_transformation = PlanLayoutHandler(
            plan_id=floor_info["plan_id"]
        ).get_georeferencing_transformation(
            to_georeference=True,
            z_off=elevation,
        )
        georef_transformation.set_swap_dimensions(0, 1)
        return georef_transformation

    @classmethod
    def get_gcs_link_as_bytes(
        cls,
        floor_id: int,
        language: SUPPORTED_LANGUAGES,
        file_format: SUPPORTED_OUTPUT_FILES,
    ) -> Tuple[bytes, str]:
        from handlers import GCloudStorageHandler

        site_id = get_site_id_from_any_level(params={"floor_id": floor_id})
        site_info = SiteDBHandler.get_by(
            id=site_id, output_columns=["client_id", "name"]
        )

        floor_info = FloorDBHandler.get_by(
            id=floor_id,
            output_columns=[
                GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language],
                "building_id",
                "floor_number",
            ],
        )
        file_name = (
            f"{site_info['name']}_building_{floor_info['building_id']}_floor_{floor_info['floor_number']}"
            f"_{language.name}.{file_format.name.lower()}"
        )
        return (
            GCloudStorageHandler().download_bytes_from_media_link(
                bucket_name=get_client_bucket_name(client_id=site_info["client_id"]),
                source_media_link=floor_info[
                    GCS_DB_COLUMN_LINK_BY_FORMAT_LANGUAGE[file_format][language]
                ],
            ),
            file_name,
        )

    @lru_cache()
    @staticmethod
    def get_floor_number_heights(building_id: int) -> Dict[int, float]:
        from handlers import PlanLayoutHandler

        floors = FloorDBHandler.find(
            building_id=building_id, output_columns=["floor_number", "plan_id"]
        )
        unique_plan_ids = {floor["plan_id"] for floor in floors}
        plan_ids_to_heights = {
            plan_id: get_floor_height(
                default=PlanLayoutHandler(plan_id=plan_id).plan_element_heights
            )
            for plan_id in unique_plan_ids
        }

        return {
            floor["floor_number"]: plan_ids_to_heights[floor["plan_id"]]
            for floor in floors
        }

    @classmethod
    def get_level_baseline(cls, floor_id: int) -> float:
        floor_info = FloorDBHandler.get_by(
            id=floor_id, output_columns=["floor_number", "building_id"]
        )

        floor_number_to_height = cls.get_floor_number_heights(
            building_id=floor_info["building_id"]
        )

        if floor_info["floor_number"] < 0:
            return -sum(
                [
                    floor_number_to_height.get(f, get_floor_height())
                    for f in range(floor_info["floor_number"], 0)
                ]
            )
        return sum(
            [
                floor_number_to_height.get(f, get_floor_height())
                for f in range(0, floor_info["floor_number"])
            ]
        )

    def get_layout_triangles(
        self,
        layout: SimLayout,
        floor_info: Dict,
        building_elevation: float,
        simulation_version=SIMULATION_VERSION,
        layout_upper_floor: Optional[SimLayout] = None,
    ):
        georef_transformation = GeoreferencingTransformation()
        georef_transformation.set_translation(x=0, y=0, z=building_elevation)
        georef_transformation.set_swap_dimensions(0, 1)

        triangulator = TRIANGULATOR_BY_SIMULATION_VERSION[simulation_version.name](
            layout=layout,
            georeferencing_parameters=georef_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        )

        return triangulator.create_layout_triangles(
            layouts_upper_floor=[layout_upper_floor] if layout_upper_floor else [],
            level_baseline=self.get_level_baseline(floor_id=floor_info["id"]),
        )
