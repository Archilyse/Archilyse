import json

import pytest
from shapely.geometry import Point, Polygon

from common_utils.constants import REGION, SurroundingType
from dufresne.polygon.utils import as_multipolygon
from surroundings.base_elevation_handler import ZeroElevationHandler
from surroundings.extruded_polygon_triangulator_mixin import (
    ExtrudedPolygonTriangulatorMixin,
)


class TestExtrudedPolygonTriangulatorMixin:
    @pytest.fixture
    def building_footprint_triangulated(self, fixtures_path):
        with open(
            fixtures_path.joinpath("building_footprint_triangulated.json"), "r"
        ) as f:
            return [(SurroundingType.BUILDINGS, triangle) for triangle in json.load(f)]

    @pytest.mark.parametrize("footprint_as_multipolygon", [True, False])
    def test_extrude_and_triangulate(
        self, mocker, building_footprint_triangulated, footprint_as_multipolygon
    ):
        class DummySurroundingHandler(ExtrudedPolygonTriangulatorMixin):
            surrounding_type = SurroundingType.BUILDINGS

            def __init__(self):
                self.elevation_handler = ZeroElevationHandler(
                    location=Point(-999, -999),
                    region=REGION.LAT_LON,
                    simulation_version=mocker.ANY,
                )

        height = 100
        footprint = Polygon(
            [
                [24.9114990234375, 62.22443627918698],
                [24.960937499999996, 62.02925839440776],
                [25.7354736328125, 62.127004481188195],
                [25.477294921874996, 62.29091943105252],
                [24.9114990234375, 62.22443627918698],
            ]
        )
        if footprint_as_multipolygon:
            footprint = as_multipolygon(footprint)

        assert (
            list(
                DummySurroundingHandler().extrude_and_triangulate(
                    height=height, footprint=footprint
                )
            )
            == building_footprint_triangulated
        )
