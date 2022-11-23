from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, SQLAlchemyAutoSchemaOpts
from marshmallow_sqlalchemy.fields import Nested

from connectors.db_connector import get_scoped_session


class BaseOpts(SQLAlchemyAutoSchemaOpts):
    """
    Check the library recipes
    https://marshmallow-sqlalchemy.readthedocs.io/en/latest/recipes.html#base-schema-i
    """

    def __init__(self, meta, ordered=False):
        if not hasattr(meta, "sql_session"):
            meta.sqla_session = get_scoped_session()()
        super(BaseOpts, self).__init__(meta, ordered=ordered)
        self.include_fk = True


class BaseDBSchema(SQLAlchemyAutoSchema):
    class Meta:
        load_instance = True
        include_relationships = True

    OPTIONS_CLASS = BaseOpts

    @classmethod
    def nested_field(cls) -> str:
        for field_name, field in cls._declared_fields.items():
            if isinstance(field, SmartNested):
                return field_name
        else:
            return ""


class SmartNested(Nested):
    def serialize(self, attr, obj, accessor=None, **kwargs):
        if attr not in obj.__dict__:
            return {"id": int(getattr(obj, attr + "_id"))}
        return super(SmartNested, self).serialize(attr, obj, accessor)
