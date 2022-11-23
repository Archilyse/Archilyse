from typing import Dict

from brooks.types import AreaType
from common_utils.exceptions import DBNotFoundException
from connectors.db_connector import get_db_session_scope
from db_models import (
    AnnotationDBModel,
    AreaDBModel,
    BuildingDBModel,
    ExpectedClientDataDBModel,
    FloorDBModel,
    PlanDBModel,
    ReactPlannerProjectDBModel,
    SiteDBModel,
    UnitDBModel,
)
from handlers import PlanHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.db.utils import retry_on_db_operational_error

required_site_columns = [
    SiteDBModel.name.name,
    SiteDBModel.georef_region.name,
    SiteDBModel.region.name,
    SiteDBModel.lat.name,
    SiteDBModel.lon.name,
    SiteDBModel.simulation_version.name,
]

required_building_columns = [
    BuildingDBModel.client_building_id.name,
    BuildingDBModel.housenumber.name,
    BuildingDBModel.city.name,
    BuildingDBModel.zipcode.name,
    BuildingDBModel.street.name,
    BuildingDBModel.elevation.name,
    BuildingDBModel.labels.name,
]

required_plan_columns = [
    PlanDBModel.default_wall_height.name,
    PlanDBModel.default_window_lower_edge.name,
    PlanDBModel.default_ceiling_slab_height.name,
    PlanDBModel.default_window_upper_edge.name,
    PlanDBModel.georef_x.name,
    PlanDBModel.georef_y.name,
    PlanDBModel.georef_scale.name,
    PlanDBModel.georef_rot_x.name,
    PlanDBModel.georef_rot_y.name,
    PlanDBModel.georef_rot_angle.name,
    PlanDBModel.image_mime_type.name,
    PlanDBModel.annotation_finished.name,
    PlanDBModel.is_masterplan.name,
    PlanDBModel.without_units.name,
]

required_floor_columns = [
    FloorDBModel.floor_number.name,
    FloorDBModel.georef_z.name,
    FloorDBModel.labels.name,
]

required_annotation_columns = [AnnotationDBModel.data.name]
required_react_annotation_columns = [ReactPlannerProjectDBModel.data.name]

required_area_columns = [
    AreaDBModel.coord_x.name,
    AreaDBModel.coord_y.name,
    AreaDBModel.scaled_polygon.name,
    AreaDBModel.area_type.name,
]

required_unit_columns = [
    UnitDBModel.apartment_no.name,
    UnitDBModel.client_id.name,
    UnitDBModel.ph_net_area.name,
    UnitDBModel.ph_final_gross_rent_annual_m2.name,
    UnitDBModel.ph_final_gross_rent_adj_factor.name,
    UnitDBModel.ph_final_sale_price_m2.name,
    UnitDBModel.ph_final_sale_price_adj_factor.name,
    UnitDBModel.unit_type.name,
    UnitDBModel.unit_usage.name,
    UnitDBModel.labels.name,
    UnitDBModel.representative_unit_client_id.name,
]

required_units_areas_column = ["labels"]

required_qa_columns = [
    ExpectedClientDataDBModel.data.name,
]


class CopySite:
    def __init__(self):
        self.new_site_id: int = None
        self.building_mapping: Dict[int, int] = {}
        self.plan_mapping: Dict[int, int] = {}
        self.floor_mapping: Dict[int, int] = {}
        self.area_mapping: Dict[int, int] = {}
        self.unit_mapping: Dict[int, int] = {}

    @retry_on_db_operational_error()
    def copy_site(
        self,
        target_client_id: int,
        site_id_to_copy: int,
        copy_area_types: bool,
        target_existing_site_id: int | None = None,
    ) -> int:
        """
        target_client_id: client id to which the copy of the site should be added
        site_id_to_cop: Id of site which should be copied
        copy_area_types: If set to False, area_type of copied areas is set to not defined
        """
        with get_db_session_scope():
            if target_existing_site_id is not None:
                self.new_site_id = target_existing_site_id
            else:
                self.new_site_id = self._copy_site_info(
                    target_client_id=target_client_id, site_id=site_id_to_copy
                )["id"]
                self._copy_qa_data(
                    target_client_id=target_client_id, site_id=site_id_to_copy
                )

            for building in BuildingDBHandler.find(
                site_id=site_id_to_copy, output_columns=["id"]
            ):
                self._copy_building_info(building_id=building["id"])
                for plan in PlanDBHandler.find(
                    building_id=building["id"], output_columns=["id", "building_id"]
                ):
                    self._copy_plan_info(plan=plan)
                    self._copy_annotation(plan=plan, site_id=site_id_to_copy)
                    self._copy_areas(plan=plan, copy_area_types=copy_area_types)

                for floor in FloorDBHandler.find(
                    building_id=building["id"],
                    output_columns=["id", "plan_id", "building_id"],
                ):
                    self._copy_floor_info(floor=floor)
                    self._copy_units(floor=floor)
        return self.new_site_id

    def _copy_site_info(self, target_client_id: int, site_id: int):
        old_site = SiteDBHandler.get_by(
            id=site_id, output_columns=required_site_columns
        )
        old_site[SiteDBModel.name.name] = f"COPY_{old_site[SiteDBModel.name.name]}"
        old_site.pop("georef_proj", None)
        site_copy = SiteDBHandler.add(client_id=target_client_id, **old_site)
        return site_copy

    def _copy_qa_data(self, target_client_id: int, site_id: int):
        try:
            qa_data = QADBHandler.get_by(
                site_id=site_id, output_columns=required_qa_columns
            )
            QADBHandler.add(
                site_id=self.new_site_id, client_id=target_client_id, **qa_data
            )
        except DBNotFoundException:
            pass

    def _copy_building_info(self, building_id: int):
        old_building = BuildingDBHandler.get_by(
            id=building_id, output_columns=required_building_columns
        )
        old_building["site_id"] = self.new_site_id
        building_copy = BuildingDBHandler.add(**old_building)
        self.building_mapping[building_id] = building_copy["id"]

    def _copy_plan_info(self, plan: Dict):
        old_plan = PlanDBHandler.get_by(
            id=plan["id"], output_columns=required_plan_columns
        )
        plan_content = PlanHandler(plan_id=plan["id"]).get_plan_image_as_bytes()
        plan_copy = PlanHandler.add(
            plan_content=plan_content,
            plan_mime_type=old_plan.pop(PlanDBModel.image_mime_type.name),
            site_id=self.new_site_id,
            building_id=self.building_mapping[plan["building_id"]],
            **old_plan,
        )
        self.plan_mapping[plan["id"]] = plan_copy["id"]

    def _copy_floor_info(self, floor: Dict):
        floor_data = FloorDBHandler.get_by(
            id=floor["id"], output_columns=required_floor_columns
        )
        floor_copy = FloorDBHandler.add(
            plan_id=self.plan_mapping[floor["plan_id"]],
            building_id=self.building_mapping[floor["building_id"]],
            **floor_data,
        )
        self.floor_mapping[floor["id"]] = floor_copy["id"]

    def _copy_annotation(self, plan: Dict, site_id: int):
        db_handler, required_columns = (
            ReactPlannerProjectsDBHandler,
            required_react_annotation_columns,
        )

        try:
            annotation_data = db_handler.get_by(
                plan_id=plan["id"], output_columns=required_columns
            )
            db_handler.add(plan_id=self.plan_mapping[plan["id"]], **annotation_data)
        except DBNotFoundException:
            pass

    def _copy_areas(self, plan: Dict, copy_area_types: bool):
        areas_data = AreaDBHandler.find(
            plan_id=plan["id"], output_columns=required_area_columns + ["id"]
        )
        if not copy_area_types:
            for area in areas_data:
                area["area_type"] = AreaType.NOT_DEFINED.name
        for area in areas_data:
            old_area_id = area.pop("id")
            area_copy = AreaDBHandler.add(
                plan_id=self.plan_mapping[plan["id"]],
                **area,
            )
            self.area_mapping[old_area_id] = area_copy["id"]

    def _copy_units(self, floor: Dict):
        units_data = UnitDBHandler.find(
            floor_id=floor["id"], output_columns=required_unit_columns + ["id"]
        )
        for unit in units_data:
            old_unit_id = unit.pop("id")
            unit_copy = UnitDBHandler.add(
                site_id=self.new_site_id,
                plan_id=self.plan_mapping[floor["plan_id"]],
                floor_id=self.floor_mapping[floor["id"]],
                **unit,
            )
            self.unit_mapping[old_unit_id] = unit_copy["id"]
            unit_areas_data = UnitAreaDBHandler.find(
                unit_id=old_unit_id,
                output_columns=required_units_areas_column + ["area_id"],
            )
            for unit_area in unit_areas_data:
                old_area_id = unit_area.pop("area_id")
                UnitAreaDBHandler.add(
                    unit_id=unit_copy["id"],
                    area_id=self.area_mapping[old_area_id],
                    **unit_area,
                )
