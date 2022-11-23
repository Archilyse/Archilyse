from typing import Dict, List, Optional

from marshmallow import fields
from marshmallow_enum import EnumField

from common_utils.constants import UNIT_USAGE
from db_models import BuildingDBModel, FloorDBModel, UnitDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class UnitDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = UnitDBModel
        exclude = ("floor", "areas")

    area_ids = fields.Raw()
    unit_usage = EnumField(UNIT_USAGE, by_value=False)


class UnitDBHandler(BaseDBHandler):

    schema = UnitDBSchema()
    model = UnitDBModel

    @classmethod
    def get_joined_by_site_building_floor_id(
        cls,
        site_id: Optional[int] = None,
        building_id: Optional[int] = None,
        floor_id: Optional[int] = None,
    ) -> List[Dict]:
        with cls.begin_session(readonly=True) as session:
            query = session.query(cls.model).join(FloorDBModel).join(BuildingDBModel)
            if site_id:
                query = query.filter(cls.model.site_id == site_id)
            if building_id:
                query = query.filter(BuildingDBModel.id == building_id)
            if floor_id:
                query = query.filter(cls.model.floor_id == floor_id)

            return cls.schema.dump(query.all(), many=True)
