from db_models.db_entities import ClusteringSubsamplingDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class ClusteringSubsamplingDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ClusteringSubsamplingDBModel


class ClusteringSubsamplingDBHandler(BaseDBHandler):
    schema = ClusteringSubsamplingDBSchema()
    model = ClusteringSubsamplingDBModel
