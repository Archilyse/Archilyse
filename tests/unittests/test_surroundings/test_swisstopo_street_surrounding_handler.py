import json

import pytest
from shapely.geometry import MultiPolygon, Point, shape

from common_utils.constants import SIMULATION_VERSION, SurroundingType
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.swisstopo.street_surrounding_handler import (
    SwissTopoStreetSurroundingHandler,
)
from tests.utils import check_surr_triangles, random_simulation_version


class TestStreetSurroundingHandler:
    @pytest.mark.parametrize(
        "location,expected_triangle_num,expected_area,elevation",
        [
            (
                Point(2692204.05, 1276649.37),
                346,
                19362.528,
                408.339,
            )
        ],
    )
    def test_get_street_triangles(
        self,
        mocker,
        fixtures_swisstopo_path,
        location,
        expected_triangle_num,
        expected_area,
        elevation,
    ):

        with fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        ).open() as f:
            mocker.patch.object(
                SwissTopoStreetSurroundingHandler,
                "load_entities",
                return_value=json.load(f),
            )

        street_surrounding_handler = SwissTopoStreetSurroundingHandler(
            location=location, simulation_version=SIMULATION_VERSION.PH_01_2021
        )
        street_triangles = list(street_surrounding_handler.get_triangles())

        # Content checks
        assert street_triangles is not None
        check_surr_triangles(
            expected_area=expected_area,
            first_elem_height=elevation,
            expected_num_triangles=expected_triangle_num,
            surr_triangles=street_triangles,
            expected_surr_type={SurroundingType.STREETS},
        )

    def test_get_triangles_street_geometry_is_none(
        self, mocker, fixtures_swisstopo_path
    ):
        triangulate_polygon_mock = mocker.patch(
            "dufresne.polygon.polygon_triangulate.triangulate_polygon"
        )

        width_extension_mock = mocker.spy(
            SwissTopoStreetSurroundingHandler,
            SwissTopoStreetSurroundingHandler.add_width.__name__,
        )

        street_segment_path = fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        )

        with street_segment_path.open() as f:
            street_segment = json.load(f)[0]

        street_segment["properties"]["OBJEKTART"] = "Verbindung"
        mocked_fiona = mocker.patch.object(
            SwissTopoStreetSurroundingHandler,
            "load_entities",
            return_value=[street_segment],
        )

        handler = SwissTopoStreetSurroundingHandler(
            location=Point(2692204.0517202704, 1276649.3754272335),
            simulation_version=random_simulation_version(),
        )
        triangles = list(handler.get_triangles())

        assert triangles is not None
        assert len(triangles) == 0
        mocked_fiona.assert_called_once()
        width_extension_mock.assert_not_called()
        triangulate_polygon_mock.assert_not_called()

    @pytest.mark.parametrize(
        "sim_version, expected",
        [
            (SIMULATION_VERSION.PH_01_2021, 19362.528),
            (SIMULATION_VERSION.EXPERIMENTAL, 19365.716),
        ],
    )
    def test_get_street_geometry(
        self, mocker, fixtures_swisstopo_path, sim_version, expected
    ):
        mocker.patch.object(
            SwissTopoStreetSurroundingHandler, "load_entities", return_value=[]
        )

        width_extension_mock = mocker.spy(
            SwissTopoStreetSurroundingHandler,
            SwissTopoStreetSurroundingHandler.add_width.__name__,
        )

        street_segment_path = fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        )
        with street_segment_path.open() as f:
            street_segment = json.load(f)[0]
        lv95_location = Point(2692204.0517202704, 1276649.3754272335)

        handler = SwissTopoStreetSurroundingHandler(
            location=lv95_location, simulation_version=sim_version
        )
        street_geometry = handler._get_geometry(entity=street_segment)

        assert street_geometry is not None
        assert isinstance(street_geometry, MultiPolygon)
        assert street_geometry.area == pytest.approx(expected, abs=1e-3)
        width_extension_mock.assert_called_once_with(
            handler,
            line=shape(street_segment["geometry"]),
            width=7,
            extension_type=LINESTRING_EXTENSION.RIGHT,
        )

    def test_get_street_geometry_unsupported_type_should_be_excluded(
        self, fixtures_swisstopo_path, mocker
    ):
        mocker.patch.object(
            SwissTopoStreetSurroundingHandler, "load_entities", return_value=[]
        )

        street_segment_path = fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        )
        with street_segment_path.open() as f:
            street_segment = json.load(f)[0]

        street_segment["properties"]["OBJEKTART"] = "Faehre"
        lv95_location = Point(2692204.0517202704, 1276649.3754272335)

        handler = SwissTopoStreetSurroundingHandler(
            location=lv95_location, simulation_version=random_simulation_version()
        )

        street = handler._get_geometry(entity=street_segment)

        assert street is None

    def test_get_street_geometry_not_within_boundingbox_should_be_excluded(
        self, fixtures_swisstopo_path, mocker
    ):
        mocker.patch.object(
            SwissTopoStreetSurroundingHandler, "load_entities", return_value=[]
        )

        street_segment_path = fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        )
        with street_segment_path.open() as f:
            street_segment = json.load(f)[0]

        lv95_location = Point(2614896.8, 1268188.6)

        handler = SwissTopoStreetSurroundingHandler(
            location=lv95_location, simulation_version=random_simulation_version()
        )

        street = handler._get_geometry(entity=street_segment)

        assert street is None

    def test_get_street_geometry_one_way_should_be_widened_in_one_direction(
        self, mocker, fixtures_swisstopo_path
    ):
        mocker.patch.object(
            SwissTopoStreetSurroundingHandler,
            SwissTopoStreetSurroundingHandler.load_entities.__name__,
            return_value=[],
        )

        width_extension_mock = mocker.spy(
            SwissTopoStreetSurroundingHandler,
            SwissTopoStreetSurroundingHandler.add_width.__name__,
        )
        street_segment_path = fixtures_swisstopo_path.joinpath(
            "streets/mocked_street_fiona_entities.json"
        )
        with street_segment_path.open() as f:
            street_segment = json.load(f)[0]

        street_segment["properties"]["RICHTUNGSG"] = "Falsch"
        lv95_location = Point(2692204.0517202704, 1276649.3754272335)

        handler = SwissTopoStreetSurroundingHandler(
            location=lv95_location, simulation_version=random_simulation_version()
        )
        street_geometry = handler._get_geometry(entity=street_segment)

        assert street_geometry is not None
        assert isinstance(street_geometry, MultiPolygon)
        assert street_geometry.area == pytest.approx(19362.528, abs=1e-3)
        width_extension_mock.assert_called_once_with(
            handler, line=shape(street_segment["geometry"]), width=7
        )
