from typing import Dict, Iterable, List

from db_models import BuildingDBModel, FloorDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class FloorDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = FloorDBModel
        exclude = ("plan", "building", "units")


class FloorDBHandler(BaseDBHandler):
    schema = FloorDBSchema()
    model = FloorDBModel

    @classmethod
    def find_by_site_id(
        cls, site_id: int, output_columns: Iterable[str] = None, **kwargs
    ) -> List[Dict]:
        """Returns all entities which have foreign site key equal to the site_id
        Args:
            site_id: site id e.g. 5
            kwargs: as in generic method find
            output_columns: as in generic method find

        Returns:
            MarshalResult: containing all rows with matching foreign key
        """
        with cls.begin_session(readonly=True) as session:
            query = (
                cls._query_model_with_filtered_columns(
                    output_columns=output_columns, session=session
                )
                .filter_by(**kwargs)
                .join(BuildingDBModel)
                .filter(BuildingDBModel.site_id == site_id)
            )

            return cls.schema.dump(query.all(), many=True)
