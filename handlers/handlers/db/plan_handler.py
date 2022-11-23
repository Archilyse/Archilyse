from typing import Dict, List

from marshmallow import fields, validate

from db_models import FloorDBModel, PlanDBModel, SiteDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class PlanDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = PlanDBModel
        exclude = ("floors", "building", "annotations")

    georef_x = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(
            min=-180, max=180, min_inclusive=True, max_inclusive=True
        ),
    )
    georef_y = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(
            min=-90, max=90, min_inclusive=True, max_inclusive=True
        ),
    )


class PlanDBHandler(BaseDBHandler):
    schema = PlanDBSchema()
    model = PlanDBModel

    @classmethod
    def get_other_georeferenced_plans_by_site(cls, plan_id: int) -> List[Dict]:
        from sqlalchemy import func

        georef_keys = (
            "georef_x",
            "georef_y",
            "georef_rot_angle",
            "georef_scale",
            "georef_rot_x",
            "georef_rot_y",
        )
        with cls.begin_session(readonly=True) as session:
            plan = (
                session.query(cls.model, FloorDBModel.floor_number)
                .join(FloorDBModel, isouter=True)
                .filter(cls.model.id == plan_id)
                .order_by(FloorDBModel.floor_number)
                .limit(1)
                .subquery("p")
            )
            query = (
                session.query(cls.model)
                .distinct()
                .join(SiteDBModel)
                .join(FloorDBModel, isouter=True)
                .filter(cls.model.site_id == plan.c.site_id, cls.model.id != plan_id)
                .order_by(
                    (cls.model.building_id == plan.c.building_id).desc(),
                    (func.abs(plan.c.floor_number - FloorDBModel.floor_number)),
                    FloorDBModel.floor_number,
                    PlanDBModel.building_id,
                )
            )
            for k in georef_keys:
                query = query.filter(getattr(cls.model, k).isnot(None))

            return cls.schema.dump(query.all(), many=True)
