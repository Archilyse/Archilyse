from typing import Collection

from db_models import AreaDBModel, UnitAreaStatsDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema


class UnitAreaStatsDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = UnitAreaStatsDBModel


class UnitAreaStatsDBHandler(BaseDBHandler):
    schema = UnitAreaStatsDBSchema()
    model = UnitAreaStatsDBModel

    @classmethod
    def unit_area_stats_with_area_types(cls, run_ids: Collection[str]):
        with cls.begin_session(readonly=True) as s:
            unit_area_stats = (
                s.query(cls.model).filter(cls.model.run_id.in_(run_ids)).all()
            )

            area_types = {
                a.id: a.area_type
                for a in s.query(AreaDBModel.id, AreaDBModel.area_type)
                .filter(AreaDBModel.id.in_({s.area_id for s in unit_area_stats}))
                .all()
            }

        return [
            {
                "run_id": s.run_id,
                "unit_id": s.unit_id,
                "area_id": s.area_id,
                "dimension": s.dimension,
                "min": s.min,
                "max": s.max,
                "mean": s.mean,
                "stddev": s.stddev,
                "count": s.count,
                "area_type": area_types[s.area_id].name,
            }
            for s in unit_area_stats
        ]
