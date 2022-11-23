from typing import Optional

from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape, to_shape
from marshmallow import fields
from marshmallow_enum import EnumField
from shapely.geometry import Point, Polygon, box
from sqlalchemy.orm.exc import MultipleResultsFound

from common_utils.constants import (
    POTENTIAL_LAYOUT_MODE,
    POTENTIAL_SIMULATION_STATUS,
    REGION,
    SIMULATION_TYPE,
    SIMULATION_VERSION,
    SURROUNDING_SOURCES,
)
from common_utils.exceptions import DBMultipleResultsException
from db_models.db_entities import PotentialSimulationDBModel
from handlers.db import BaseDBHandler
from handlers.db.serialization import BaseDBSchema

SRID = 4326


class PotentialSimulationDBSchema(BaseDBSchema):
    class Meta(BaseDBSchema.Meta):
        model = PotentialSimulationDBModel

    type = EnumField(SIMULATION_TYPE, by_value=True)
    status = EnumField(POTENTIAL_SIMULATION_STATUS, by_value=True)
    source_surr = EnumField(SURROUNDING_SOURCES, by_value=True)
    layout_mode = EnumField(POTENTIAL_LAYOUT_MODE, by_value=True)
    simulation_version = EnumField(SIMULATION_VERSION, by_value=True)
    region = EnumField(REGION, load_default=REGION.LAT_LON.name, by_value=False)
    building_footprint = fields.Method(
        "get_building_footprint", deserialize="shapely_to_WKBElement", required=False
    )

    def get_building_footprint(self, obj):
        if hasattr(obj, "building_footprint") and obj.building_footprint is not None:
            return to_shape(obj.building_footprint).wkt

    def shapely_to_WKBElement(self, value: Polygon):
        if not isinstance(value, Polygon):
            raise TypeError("Potential building_footprint must be a Polygon")
        return from_shape(value, srid=SRID)


class PotentialSimulationDBHandler(BaseDBHandler):
    schema = PotentialSimulationDBSchema()
    model = PotentialSimulationDBModel

    ISOLATION_LEVEL = "READ COMMITTED"

    @classmethod
    def get_by_location(
        cls,
        lat: float,
        lon: float,
        floor_number: int,
        sim_type: SIMULATION_TYPE,
    ) -> dict:
        """Layout Mode is ignored as currently is always WITH_WINDOWS"""
        # Inverted as polygons are stored as lon lat
        location = Point(lon, lat)
        try:
            with cls.begin_session(readonly=True) as s:
                return cls._serialize_one(
                    s.query(cls.model).filter(
                        cls.model.building_footprint.ST_Contains(
                            WKBElement(data=location.wkb, srid=SRID)
                        ),
                        cls.model.floor_number == floor_number,
                        cls.model.type == sim_type,
                        cls.model.identifier.is_(None),  # exclude nightly simulations
                    )
                )
        except MultipleResultsFound as e:
            # Not controlled in order for us to review what is going on in this case
            raise DBMultipleResultsException from e

    @classmethod
    def get_simulations_list(
        cls,
        bounding_box: Optional[dict[str, float]] = None,
        simulation_type: Optional[SIMULATION_TYPE] = None,
        limit_query=True,
    ) -> list[dict]:
        with cls.begin_session(readonly=True) as session:
            query = cls._query_model_with_filtered_columns(
                session=session,
                output_columns=[
                    "id",
                    "floor_number",
                    "type",
                    "status",
                    "building_footprint",
                    "result",
                ],
            )
            query = query.filter(
                cls.model.status == POTENTIAL_SIMULATION_STATUS.SUCCESS.name,
            )
            if simulation_type:
                query = query.filter(cls.model.type == simulation_type.name)
            if bounding_box:
                bounding_box_pol = box(
                    bounding_box["min_lon"],
                    bounding_box["min_lat"],
                    bounding_box["max_lon"],
                    bounding_box["max_lat"],
                )
                query = query.filter(
                    WKBElement(data=bounding_box_pol.wkb, srid=SRID).ST_Contains(
                        cls.model.building_footprint
                    )
                )

            query = query.order_by(cls.model.created.desc())
            if limit_query:
                query = query.limit(100)

            return cls.schema.dump(query, many=True)
