import pytest
from shapely.geometry import LineString, MultiLineString

from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import SWISSTOPO_TUNNEL_TYPES
from surroundings.v2.swisstopo.geometry_provider import (
    SwissTopoShapeFileGeometryProvider,
)
from surroundings.v2.swisstopo.streets.constants import (
    PEDESTRIAN_STREET_TYPES,
    STREETS_WO_CAR_TRAFFIC,
)
from surroundings.v2.swisstopo.streets.street_geometry_provider import (
    SwissTopoNoisyStreetsGeometryProvider,
    SwissTopoStreetsGeometryProvider,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)


class TestSwissTopoStreetsGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoStreetsGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            *[
                ({"KUNSTBAUTE": tunnel_type}, False)
                for tunnel_type in SWISSTOPO_TUNNEL_TYPES
            ],
            ({"OBJEKTART": "Verbindung"}, False),
            ({"OBJEKTART": "Platz"}, False),
            ({"OBJEKTART": "Autozug"}, False),
            ({"OBJEKTART": "Faehre"}, False),
            ({}, True),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_return_value):
        properties = {
            "OBJEKTART": "FAKE-BUT-PASSING",
            "KUNSTBAUTE": "FAKE-BUT-PASSING",
            **properties,
        }
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )

    def test_get_geometries_unpacks_multilinestrings(
        self,
        mocker,
    ):
        geometry_linestring = Geometry(
            geom=LineString([(0, 0), (1, 1)]), properties=mocker.ANY
        )
        properties = {"props": "will be repeated"}
        mocked_base_get_geometries = mocker.patch.object(
            SwissTopoShapeFileGeometryProvider,
            "get_geometries",
            return_value=[
                geometry_linestring,
                Geometry(
                    geom=MultiLineString([[(0, 0), (1, 1)], [(1, 1), (2, 2)]]),
                    properties=properties,
                ),
            ],
        )

        geometries = list(self.get_instance().get_geometries())
        assert geometries == [
            geometry_linestring,
            Geometry(geom=LineString([(0, 0), (1, 1)]), properties=properties),
            Geometry(geom=LineString([(1, 1), (2, 2)]), properties=properties),
        ]
        mocked_base_get_geometries.assert_called_once()


class TestSwissTopoNoisyStreetsGeometryProvider(TestSwissTopoStreetsGeometryProvider):
    instance_cls = SwissTopoNoisyStreetsGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            *[
                ({"KUNSTBAUTE": tunnel_type}, False)
                for tunnel_type in SWISSTOPO_TUNNEL_TYPES
            ],
            *[
                ({"VERKEHRSBE": traffic_type}, False)
                for traffic_type in STREETS_WO_CAR_TRAFFIC
            ],
            *[
                ({"OBJEKTART": street_type}, False)
                for street_type in PEDESTRIAN_STREET_TYPES
            ],
            ({"OBJEKTART": "Verbindung"}, False),
            ({"OBJEKTART": "Platz"}, False),
            ({"OBJEKTART": "Autozug"}, False),
            ({"OBJEKTART": "Faehre"}, False),
            ({}, True),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_return_value):
        properties = {
            "OBJEKTART": "FAKE-BUT-PASSING",
            "KUNSTBAUTE": "FAKE-BUT-PASSING",
            "VERKEHRSBE": "FAKE-BUT-PASSING",
            **properties,
        }
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )
