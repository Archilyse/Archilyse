from db_models import ReactPlannerProjectDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class ReactPlannerProjectsDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = ReactPlannerProjectDBModel


class ReactPlannerProjectsDBHandler(BaseDBHandler):
    schema = ReactPlannerProjectsDBSchema()
    model = ReactPlannerProjectDBModel
