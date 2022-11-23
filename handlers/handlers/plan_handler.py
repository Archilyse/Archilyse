import hashlib
import io
import mimetypes
import uuid
from collections import defaultdict
from dataclasses import asdict
from functools import cached_property
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Set, Tuple, Union

from marshmallow import Schema, fields
from PIL import Image as PIL_IMAGE
from shapely.geometry import Point, mapping
from wand.color import Color
from wand.image import Image

from brooks.layout_splitter import LayoutSplitter
from brooks.models import SimLayout
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.projections import project_geometry
from brooks.utils import (
    get_default_element_height,
    get_default_element_lower_edge,
    get_default_element_upper_edge,
)
from common_utils.constants import (
    DXF_IMPORT_DEFAULT_SCALE_FACTOR,
    GOOGLE_CLOUD_PLAN_IMAGES,
    PDF_TO_IMAGE_RESOLUTION,
    REGION,
    PipelineCompletedCriteria,
)
from common_utils.exceptions import DBNotFoundException, InvalidImage
from connectors.db_connector import get_db_session_scope
from handlers.cloud_convert import CloudConvertHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.db.utils import retry_on_db_operational_error
from handlers.dxf.dxf_import_handler import DXFImportHandler
from handlers.editor_v2.schema import ReactPlannerData
from handlers.plan_layout_handler import PlanLayoutHandlerIDCacheMixin
from handlers.plan_utils import create_areas_for_plan
from handlers.utils import get_client_bucket_name
from tasks.pipeline_tasks import auto_classify_areas_for_plan

if TYPE_CHECKING:
    from handlers import PlanLayoutHandler


class PipelineCriteriaSchema(Schema):
    labelled = fields.Bool()
    classified = fields.Bool()
    scaled = fields.Bool()
    splitted = fields.Bool()
    units_linked = fields.Bool()


class PipelineSchema(PipelineCriteriaSchema):
    id = fields.Int()
    created = fields.DateTime()
    updated = fields.DateTime()
    building_id = fields.Int()
    client_site_id = fields.Str()
    client_building_id = fields.Str()
    floor_numbers = fields.List(fields.Int())


def convert_pdf_to_jpeg(plan_data: bytes) -> bytes:
    pdf_pages = Image(blob=plan_data, resolution=PDF_TO_IMAGE_RESOLUTION)
    if len(pdf_pages.sequence) != 1:
        raise Exception("PDF with none or multiple pages")

    new_format = "jpeg"
    with Image(pdf_pages) as img:
        img.format = new_format
        img.background_color = Color("white")
        img.alpha_channel = "flatten"
        return img.make_blob()


class PlanHandler:
    """Service class encapsulating all the business domain methods that perform
    validations, checks or transformations of plans for all CRUD operations.
    """

    def __init__(
        self,
        plan_id: Optional[int] = None,
        plan_info: Optional[Dict] = None,
        site_info: Optional[Dict] = None,
    ):
        self._plan_info = plan_info or {}
        try:
            self.plan_id: int = plan_id or int(self._plan_info["id"])
        except KeyError:
            raise Exception(
                f"no plan id provided to plan handler: Plan id: {plan_id}. Plan info: {plan_info}"
            )
        self._site_info = site_info or {}

    @cached_property
    def plan_info(self):
        return self._plan_info or PlanDBHandler.get_by(id=self.plan_id)

    @cached_property
    def site_info(self):
        return self._site_info or SiteDBHandler.get_by(
            id=self.plan_info["site_id"],
            output_columns=["id", "client_id", "lat", "lon", "georef_region"],
        )

    @property
    def is_georeferenced(self) -> bool:
        return all(
            self.plan_info[key] is not None
            for key in (
                "georef_x",
                "georef_y",
                "georef_rot_x",
                "georef_rot_y",
                "georef_rot_angle",
            )
        )

    def get_pipeline_criteria(
        self, units: List[Dict], areas: List[Dict]
    ) -> PipelineCompletedCriteria:
        criteria = PipelineCompletedCriteria()

        criteria.labelled = bool(self.plan_info.get("annotation_finished", False))

        # At least one area classified
        criteria.classified = criteria.labelled and any(
            True for a in areas if a["area_type"] != AreaType.NOT_DEFINED.name
        )

        criteria.georeferenced = self.is_georeferenced

        criteria.splitted = bool(len(units)) or self.plan_info["without_units"]
        criteria.units_linked = (
            bool(not any(x["client_id"] is None for x in units) and units)
            or self.plan_info["without_units"]
        )

        return criteria

    def get_plan_image_as_bytes(self) -> bytes:
        from handlers import GCloudStorageHandler

        client_bucket_name = get_client_bucket_name(
            client_id=self.site_info["client_id"]
        )
        return GCloudStorageHandler().download_bytes_from_media_link(
            bucket_name=client_bucket_name,
            source_media_link=self.plan_info["image_gcs_link"],
        )

    @classmethod
    def upload_plan_image_to_google_cloud(
        cls, image_data: bytes, destination_bucket: str
    ) -> str:
        from handlers import GCloudStorageHandler

        return GCloudStorageHandler().upload_bytes_to_bucket(
            bucket_name=destination_bucket,
            destination_folder=GOOGLE_CLOUD_PLAN_IMAGES,
            destination_file_name=str(uuid.uuid4()) + ".jpeg",
            contents=image_data,
        )

    @classmethod
    def add(
        cls,
        plan_content: bytes,
        plan_mime_type: Optional[str],
        site_id: int,
        building_id: int,
        **kwargs,
    ) -> Dict:
        """Adds a new floorplan from the specified path. Additionally it performs a
        validation if a floorplan with identical content has already been added for the
        same building, by computing the hash of the provided image and
        comparing the digest with the existing database entities (known as floorplan deduplication).

        Returns:
            the plan id of the already existing plan with identical image content
            or the plan id
            of a newly created plan entity with the unique floorplan content.
        """

        inferred_react_annotation = None
        if plan_mime_type == mimetypes.types_map[".pdf"]:
            image_data = convert_pdf_to_jpeg(plan_data=plan_content)
            plan_mime_type = mimetypes.types_map[".jpeg"]
        elif plan_mime_type in {
            mimetypes.types_map[".dwg"],
            mimetypes.types_map[".dxf"],
        }:
            if plan_mime_type == mimetypes.types_map[".dwg"]:
                plan_content = CloudConvertHandler().transform_bytes(
                    source_content=plan_content, input_format="dwg", output_format="dxf"
                )
            image_data, inferred_react_annotation, georef_parameters = cls.load_dxf(
                dxf_content=plan_content, scale_factor=DXF_IMPORT_DEFAULT_SCALE_FACTOR
            )
            plan_mime_type = mimetypes.types_map[".jpeg"]
            kwargs.update(georef_parameters)
        else:
            image_data = plan_content

        digest = hashlib.sha256(image_data).hexdigest()

        if existing_plan := cls.get_existing_identical_plan(
            image_hash=digest, building_id=building_id
        ):
            return existing_plan

        image_width, image_height = cls._extract_image_parameters_for_plan(
            image_data=image_data
        )

        site = SiteDBHandler.get_by(id=site_id)
        destination_bucket = get_client_bucket_name(client_id=site["client_id"])
        image_gc_link = cls.upload_plan_image_to_google_cloud(
            image_data=image_data, destination_bucket=destination_bucket
        )

        plan_info = PlanDBHandler.add(
            site_id=site_id,
            image_width=image_width,
            image_height=image_height,
            image_gcs_link=image_gc_link,
            building_id=building_id,
            image_mime_type=plan_mime_type,
            default_wall_height=kwargs.pop(
                "default_wall_height",
                get_default_element_height(element_type=SeparatorType.WALL),
            ),
            default_window_lower_edge=kwargs.pop(
                "default_window_lower_edge",
                get_default_element_lower_edge(element_type=OpeningType.WINDOW),
            ),
            default_window_upper_edge=kwargs.pop(
                "default_window_upper_edge",
                get_default_element_upper_edge(element_type=OpeningType.WINDOW),
            ),
            default_ceiling_slab_height=kwargs.pop(
                "default_ceiling_slab_height",
                get_default_element_height(element_type="CEILING_SLAB"),
            ),
            image_hash=digest,
            **{**cls._georef_data_from_masterplan(building_id=building_id), **kwargs},
        )
        if inferred_react_annotation:
            ReactPlannerProjectsDBHandler.add(
                plan_id=plan_info["id"],
                data=asdict(inferred_react_annotation),
            )

            create_areas_for_plan(plan_id=plan_info["id"], preclassify=True)
            auto_classify_areas_for_plan(plan_id=plan_info["id"])

        return plan_info

    @staticmethod
    def get_existing_identical_plan(
        image_hash: str, building_id: int
    ) -> Optional[dict]:
        try:
            return PlanDBHandler.get_by(image_hash=image_hash, building_id=building_id)
        except DBNotFoundException:
            return None

    @classmethod
    def load_dxf(
        cls, dxf_content: bytes, scale_factor: float
    ) -> Tuple[bytes, ReactPlannerData, Dict]:
        with NamedTemporaryFile() as tmp_file:
            dxf_file_path = Path(tmp_file.name)
            with dxf_file_path.open("wb") as f:
                f.write(dxf_content)

            dxf_import_handler = DXFImportHandler(
                dxf_file_path=dxf_file_path, scale_factor=scale_factor
            )

            with io.BytesIO() as output_stream:
                react_annotation = dxf_import_handler.export_react_annotation()
                dxf_import_handler.export_image(output_stream=output_stream)
                georef_parameters = dxf_import_handler.get_georef_parameters()
                output_stream.seek(0)
                return output_stream.read(), react_annotation, georef_parameters

    @staticmethod
    def _georef_data_from_masterplan(building_id: int) -> dict:
        plans_of_same_building = PlanDBHandler.find(
            building_id=building_id,
            output_columns=[
                "id",
                "is_masterplan",
                "georef_rot_angle",
                "georef_x",
                "georef_y",
                "georef_rot_x",
                "georef_rot_y",
            ],
        )

        georef_data = {}
        if masterplan := [
            plan for plan in plans_of_same_building if plan["is_masterplan"]
        ]:
            for georef_element_key in {
                "georef_rot_angle",
                "georef_x",
                "georef_y",
                "georef_rot_x",
                "georef_rot_y",
            }:
                georef_data[georef_element_key] = masterplan[0][georef_element_key]

        return georef_data

    @staticmethod
    def _extract_image_parameters_for_plan(image_data: bytes) -> Tuple[int, int]:
        """Return image dimensions"""
        PIL_IMAGE.MAX_IMAGE_PIXELS = None
        image = PIL_IMAGE.open(io.BytesIO(image_data))
        try:
            return image.size
        except (IndexError, AttributeError):
            raise InvalidImage("Unrecognized format for the image uploaded")

    def update_rotation_point(self) -> Point:
        from handlers import PlanLayoutHandler

        raw_layout = PlanLayoutHandler(
            plan_id=self.plan_id, plan_info=self.plan_info
        ).get_layout(
            scaled=True,
        )
        rotation_point = raw_layout.footprint.centroid
        PlanDBHandler.update(
            item_pks={"id": self.plan_id},
            new_values={
                "georef_rot_x": rotation_point.x,
                "georef_rot_y": rotation_point.y,
            },
        )
        return rotation_point

    @cached_property
    def rotation_point(self) -> Point:
        """It is really the centroid of the layout in pixel coordinates"""
        if (
            self.plan_info.get("georef_rot_x") is None
            or self.plan_info.get("georef_rot_y") is None
        ):
            # Introduced to change the contract where the FE was setting the rotation point as:
            # the bounds of the footprint divided by 2 as an approximation of the centroid
            # It is placed here so that we can deploy this change without affecting live changes
            return self.update_rotation_point()

        return Point(self.plan_info["georef_rot_x"], self.plan_info["georef_rot_y"])

    @cached_property
    def translation_point(self) -> Point:
        return project_geometry(
            self.translation_point_lat_lon,
            crs_from=REGION.LAT_LON,
            crs_to=REGION[self.site_info["georef_region"]],
        )

    @cached_property
    def translation_point_lat_lon(self) -> Point:
        if (
            self.plan_info["georef_x"] is not None
            and self.plan_info["georef_y"] is not None
        ):
            plan_translation_point = Point(
                self.plan_info["georef_x"], self.plan_info["georef_y"]
            )
        else:
            # If plan is not georeferenced yet, the current location is based on the site location
            plan_translation_point = Point(self.site_info["lon"], self.site_info["lat"])
        return plan_translation_point

    def get_other_georeferenced_footprints_under_same_site(
        self,
    ) -> Iterator[Dict[str, Union[int, dict]]]:
        from handlers import PlanLayoutHandler

        other_georeferenced_plans_by_id = {
            p["id"]: p
            for p in PlanDBHandler.get_other_georeferenced_plans_by_site(
                plan_id=self.plan_id
            )
        }

        for plan_id, plan_info in other_georeferenced_plans_by_id.items():
            yield {
                "footprint": mapping(
                    project_geometry(
                        geometry=PlanLayoutHandler(
                            plan_id=plan_id, plan_info=plan_info
                        ).get_georeferenced_footprint(),
                        crs_from=REGION[self.site_info["georef_region"]],
                        crs_to=REGION.LAT_LON,
                    )
                ),
                "id": plan_id,
            }

    def pipeline_completed_criteria(self) -> PipelineCompletedCriteria:
        criteria = self.get_pipeline_criteria(
            units=UnitDBHandler.find(
                plan_id=self.plan_id, output_columns=["client_id"]
            ),
            areas=AreaDBHandler.find(
                plan_id=self.plan_id, output_columns=["area_type"]
            ),
        )
        return criteria

    @classmethod
    def get_pipelines_output(
        cls,
        plans: List[Dict],
        site: Dict,
    ) -> List[Dict]:
        result = []

        units_by_plan = defaultdict(list)
        for unit in UnitDBHandler.find_in(
            plan_id=[p["id"] for p in plans],
            output_columns=["client_id", "plan_id"],
        ):
            units_by_plan[unit["plan_id"]].append(unit)

        floor_numbers_by_plan = defaultdict(list)
        for floor in FloorDBHandler.find_in(
            plan_id=[plan["id"] for plan in plans],
            output_columns=["plan_id", "floor_number"],
        ):
            floor_numbers_by_plan[floor["plan_id"]].append(floor["floor_number"])

        buildings_by_id = {
            building["id"]: building
            for building in BuildingDBHandler.find_in(
                id=[p["building_id"] for p in plans],
                output_columns=["id", "housenumber", "client_building_id"],
            )
        }

        areas_by_plan_id = defaultdict(list)
        for area in AreaDBHandler.find_in(plan_id=[plan["id"] for plan in plans]):
            areas_by_plan_id[area["plan_id"]].append(area)

        plan_fields = (
            "id",
            "created",
            "updated",
            "building_id",
            "is_masterplan",
        )
        for plan_info in plans:
            building_info = buildings_by_id[plan_info["building_id"]]
            criteria = PlanHandler(
                plan_id=plan_info["id"], plan_info=plan_info
            ).get_pipeline_criteria(
                units=units_by_plan[plan_info["id"]],
                areas=areas_by_plan_id[plan_info["id"]],
            )
            result.append(
                {
                    **dict(vars(criteria)),
                    **{k: plan_info[k] for k in plan_fields},
                    "client_site_id": site["client_site_id"],
                    "client_building_id": building_info["client_building_id"],
                    "building_housenumber": building_info["housenumber"],
                    "floor_numbers": floor_numbers_by_plan[plan_info["id"]],
                }
            )
        return result

    def autosplit(self) -> List[List[int]]:
        from handlers import PlanLayoutHandler

        layout = PlanLayoutHandler(plan_id=self.plan_id).get_layout(
            validate=False,
            classified=True,
            scaled=True,
            raise_on_inconsistency=True,
        )
        return [
            [area.db_area_id for space in connected_component for area in space.areas]
            for connected_component in LayoutSplitter.split_layout(layout=layout)
        ]

    @classmethod
    def get_site_plans_layouts_with_building_floor_numbers(
        cls, site_id: int
    ) -> List[Dict[str, Union[SimLayout, int, List[int], "PlanLayoutHandler"]]]:
        from handlers import PlanLayoutHandler

        site_plan_layouts = []
        for plan in list(PlanDBHandler.find(site_id=site_id)):
            floor_numbers = FloorDBHandler.find(
                plan_id=plan["id"], output_columns=["floor_number"]
            )
            plan_layout_handler = PlanLayoutHandler(plan_id=plan["id"])
            plan_layout = plan_layout_handler.get_layout(
                classified=True,
                georeferenced=True,
                scaled=True,
            )
            site_plan_layouts.append(
                {
                    "id": plan["id"],
                    "plan_layout": plan_layout,
                    "building_id": plan["building_id"],
                    "floor_numbers": [x["floor_number"] for x in floor_numbers],
                    "plan_layout_handler": plan_layout_handler,
                }
            )
        return site_plan_layouts

    @retry_on_db_operational_error()
    def save_georeference_data(self, georef_data: Dict[str, float]):
        with get_db_session_scope():
            plans_of_same_building = PlanDBHandler.find(
                building_id=self.plan_info["building_id"],
                output_columns=["id", "is_masterplan"],
            )
            if any(plan["is_masterplan"] for plan in plans_of_same_building):
                self._update_building_plans_with_georef_data(
                    georef_data={
                        **georef_data,
                        "georef_rot_x": self.plan_info["georef_rot_x"],
                        "georef_rot_y": self.plan_info["georef_rot_y"],
                    },
                    plans_ids_of_same_building={
                        plan["id"] for plan in plans_of_same_building
                    },
                )
            else:
                PlanDBHandler.update(
                    item_pks={"id": self.plan_info["id"]}, new_values=georef_data
                )
            SiteDBHandler.set_site_to_unprocessed(site_id=self.plan_info["site_id"])

    @staticmethod
    def _update_building_plans_with_georef_data(
        georef_data: Dict, plans_ids_of_same_building: Set[int]
    ):

        PlanDBHandler.bulk_update(
            georef_rot_angle={
                plan_id: georef_data["georef_rot_angle"]
                for plan_id in plans_ids_of_same_building
            },
            georef_x={
                plan_id: georef_data["georef_x"]
                for plan_id in plans_ids_of_same_building
            },
            georef_y={
                plan_id: georef_data["georef_y"]
                for plan_id in plans_ids_of_same_building
            },
            georef_rot_x={
                plan_id: georef_data["georef_rot_x"]
                for plan_id in plans_ids_of_same_building
            },
            georef_rot_y={
                plan_id: georef_data["georef_rot_y"]
                for plan_id in plans_ids_of_same_building
            },
        )

    @retry_on_db_operational_error()
    def set_as_masterplan(self):
        with get_db_session_scope():
            plans_ids_of_same_building = {
                plan["id"]
                for plan in PlanDBHandler.find(
                    building_id=self.plan_info["building_id"],
                    output_columns=["id"],
                )
                if plan["id"] != self.plan_id
            }

            if self.is_georeferenced:
                self._update_building_plans_with_georef_data(
                    georef_data=self.plan_info,
                    plans_ids_of_same_building=plans_ids_of_same_building,
                )

            bulk_update_values = {self.plan_id: True}
            bulk_update_values.update(
                {other_plan_id: False for other_plan_id in plans_ids_of_same_building}
            )
            PlanDBHandler.bulk_update(is_masterplan=bulk_update_values)


class PlanHandlerSiteCacheMixin(PlanLayoutHandlerIDCacheMixin):
    def __init__(self, site_id: int = 0):
        super().__init__()
        self.site_id = site_id

    @cached_property
    def building_ids(self) -> List[int]:
        return list(BuildingDBHandler.find_ids(site_id=self.site_id))

    @cached_property
    def plan_ids(self) -> List[int]:
        return list(PlanDBHandler.find_ids(site_id=self.site_id))

    @cached_property
    def plan_ids_per_building(self) -> Dict[int, List[int]]:
        return {
            building_id: list(PlanDBHandler.find_ids(building_id=building_id))
            for building_id in self.building_ids
        }
