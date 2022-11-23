import pytest

from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import SWISSTOPO_TRUE, SWISSTOPO_TUNNEL_TYPES
from surroundings.v2.swisstopo.railways.railway_geometry_provider import (
    SwissTopoNoisyRailwayGeometryProvider,
    SwissTopoRailwayGeometryProvider,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)


class TestSwissTopoRailwaysGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoRailwayGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            *[
                ({"KUNSTBAUTE": tunnel_type}, False)
                for tunnel_type in SWISSTOPO_TUNNEL_TYPES
            ],
            *[({"AUSSER_BET": value}, False) for value in SWISSTOPO_TRUE],
            ({}, True),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_return_value):
        properties = {
            "AUSSER_BET": "FAKE-BUT-PASSING",
            "KUNSTBAUTE": "FAKE-BUT-PASSING",
            **properties,
        }
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )


class TestSwissTopoNoisyRailwaysGeometryProvider(TestSwissTopoRailwaysGeometryProvider):
    instance_cls = SwissTopoNoisyRailwayGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            *[
                ({"KUNSTBAUTE": tunnel_type}, False)
                for tunnel_type in SWISSTOPO_TUNNEL_TYPES
            ],
            *[({"AUSSER_BET": value}, False) for value in SWISSTOPO_TRUE],
            ({}, True),
            ({"VERKEHRSMI": "Bahn"}, True),
            ({"VERKEHRSMI": "Metro"}, False),
            ({"VERKEHRSMI": "Tram"}, False),
            ({"VERKEHRSMI": "ANY"}, False),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_return_value):
        properties = {
            "AUSSER_BET": "FAKE-BUT-PASSING",
            "KUNSTBAUTE": "FAKE-BUT-PASSING",
            "VERKEHRSMI": "Bahn",
            **properties,
        }
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )
