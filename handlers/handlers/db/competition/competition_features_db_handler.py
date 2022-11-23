from common_utils.constants import TASK_TYPE
from db_models.db_entities import CompetitionFeaturesDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class CompetitionFeaturesDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = CompetitionFeaturesDBModel


class CompetitionFeaturesDBHandler(BaseDBHandler):
    schema = CompetitionFeaturesDBSchema()
    model = CompetitionFeaturesDBModel

    @classmethod
    def update_data_feature(cls, competitor_id: int, **updated_field):
        from handlers.db import SlamSimulationDBHandler

        with cls.begin_session():
            data_features = cls.get_by(
                run_id=SlamSimulationDBHandler.get_latest_run_id(
                    site_id=competitor_id, task_type=TASK_TYPE.COMPETITION
                )
            )
            cls.update(
                item_pks={"run_id": data_features["run_id"]},
                new_values={"results": {**data_features["results"], **updated_field}},
            )
