from sqlalchemy import distinct, true
from sqlalchemy.sql.functions import count

from common_utils.constants import ADMIN_SIM_STATUS
from db_models import ClientDBModel, SiteDBModel, UnitDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class ClientDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ClientDBModel
        exclude = ("sites",)


class ClientDBHandler(BaseDBHandler):
    schema = ClientDBSchema()
    model = ClientDBModel

    @classmethod
    def get_by_site_id(cls, site_id: int):
        with cls.begin_session(readonly=True) as session:
            query = (
                session.query(cls.model)
                .join(SiteDBModel, SiteDBModel.client_id == cls.model.id)
                .filter(SiteDBModel.id == site_id)
            )
            return cls.schema.dump(query.first())

    @classmethod
    def get_total_unit_number_by_site_id_completed(cls, client_id: int):
        with cls.begin_session(readonly=True) as session:
            query = (
                session.query(SiteDBModel.id, count(distinct(UnitDBModel.client_id)))
                .join(UnitDBModel, SiteDBModel.id == UnitDBModel.site_id, isouter=True)
                .filter(
                    SiteDBModel.client_id == client_id,
                    SiteDBModel.full_slam_results == ADMIN_SIM_STATUS.SUCCESS.value,
                    SiteDBModel.heatmaps_qa_complete == true(),
                )
                .group_by(SiteDBModel.id)
            )
            return {site_id: unit_number for (site_id, unit_number) in query}
