from typing import Any, Dict, List, Optional

from marshmallow import EXCLUDE, ValidationError, fields, validate
from marshmallow_enum import EnumField
from sqlalchemy import and_, false, not_

from brooks.classifications import CLASSIFICATIONS
from brooks.util.projections import get_region_crs_str
from common_utils.constants import (
    ADMIN_SIM_STATUS,
    CURRENCY,
    CURRENCY_REGION,
    DEFAULT_IFC_LOCATION,
    REGION,
    SIMULATION_VERSION,
)
from db_models import BuildingDBModel, FloorDBModel, PlanDBModel, SiteDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


def validate_lon(lon):
    if lon < -180.0 and lon != DEFAULT_IFC_LOCATION[0]:
        raise ValidationError("Longitude can't be lower than -180")
    if lon > 180.0:
        raise ValidationError("Longitude can't be bigger than 180")


def validate_lat(lat):
    if lat < -90.0 and lat != DEFAULT_IFC_LOCATION[1]:
        raise ValidationError("Latitude can't be lower than -90")
    if lat > 90.0:
        raise ValidationError("Latitude can't be bigger than 90")


class SiteDBSchemaMethods:
    def get_currency(self, obj):
        if hasattr(obj, "georef_region"):
            return CURRENCY_REGION.get(obj.georef_region, CURRENCY.EUR).value

    def get_proj_based_on_region(self, obj) -> str:
        """When there is a partial validation of the object,  it can't serialize correctly"""
        if hasattr(obj, "georef_region"):
            return get_region_crs_str(obj.georef_region)
        return ""


class SiteDBSchema(BaseDBSchema, SiteDBSchemaMethods):
    class Meta(BaseDBSchema.Meta):
        model = SiteDBModel
        exclude = ("client", "buildings", "group", "competition")
        unknown = EXCLUDE

    basic_features_status = EnumField(ADMIN_SIM_STATUS, by_value=True)
    full_slam_results = EnumField(ADMIN_SIM_STATUS, by_value=True)
    sample_surr_task_state = EnumField(ADMIN_SIM_STATUS, by_value=True)
    classification_scheme = EnumField(
        CLASSIFICATIONS, load_by=EnumField.NAME, dump_by=EnumField.NAME
    )
    lat = fields.Float(validate=validate_lat, required=True)
    lon = fields.Float(validate=validate_lon, required=True)
    georef_region = EnumField(REGION, by_value=False)
    georef_proj = fields.Method("get_proj_based_on_region")
    ready = fields.Boolean(dump_only=True, required=False)
    priority = fields.Integer(validate=validate.Range(min=1, max=10), required=False)
    simulation_version = EnumField(
        SIMULATION_VERSION, by_value=True, load_default=SIMULATION_VERSION.PH_01_2021
    )
    currency = fields.Method("get_currency")


class SiteDBHandler(BaseDBHandler):
    schema = SiteDBSchema()
    model = SiteDBModel

    @classmethod
    def get_all_by_client(cls, client_id) -> List[Dict]:
        with cls.begin_session(readonly=True) as session:
            query = session.query(cls.model).filter(cls.model.client_id == client_id)
            return cls.schema.dump(query.all(), many=True)

    @classmethod
    def get_sites_with_ready_field(
        cls,
        client_id: int,
        client_site_id: Optional[str] = None,
        group_id: Optional[str] = None,
        additional_filter=None,
    ):
        with cls.begin_session(readonly=True) as session:
            unfinished_annotations_plans = (
                session.query(PlanDBModel)
                .filter(
                    PlanDBModel.site_id == cls.model.id,
                    PlanDBModel.annotation_finished == false(),
                )
                .exists()
            )
            at_least_one_plan = (
                session.query(PlanDBModel)
                .filter(PlanDBModel.site_id == cls.model.id)
                .exists()
            )
            query = session.query(
                *cls.model.__table__.columns,
                and_(at_least_one_plan, not_(unfinished_annotations_plans)).label(
                    "ready"
                ),
            ).filter(cls.model.client_id == client_id)

            if client_site_id:
                query = query.filter(cls.model.client_site_id == client_site_id)

            if group_id:
                query = query.filter(cls.model.group_id == group_id)

            if additional_filter:
                query = query.filter(*additional_filter)

            return cls.schema.dump(query.all(), many=True)

    @classmethod
    def get_by_floor_id(cls, floor_id: int) -> Dict:
        """Get site by floor id"""
        with cls.begin_session(readonly=True) as session:
            query = (
                session.query(cls.model)
                .join(BuildingDBModel)
                .join(FloorDBModel)
                .filter(FloorDBModel.id == floor_id)
            )
            return cls.schema.dump(query.one())

    @classmethod
    def set_site_to_unprocessed(cls, site_id: int) -> Dict[str, Any]:
        return cls.update(
            item_pks={"id": site_id},
            new_values={
                "pipeline_and_qa_complete": False,
                "heatmaps_qa_complete": False,
                "basic_features_status": ADMIN_SIM_STATUS.UNPROCESSED,
                "full_slam_results": ADMIN_SIM_STATUS.UNPROCESSED,
                "sample_surr_task_state": ADMIN_SIM_STATUS.UNPROCESSED,
            },
        )
