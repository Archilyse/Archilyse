import pytest
from shapely.geometry import Polygon

from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo import SwissTopoParksHandler
from surroundings.v2.swisstopo.parks import SwissTopoParksGeometryProvider
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestParksGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoParksGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            ({"OBJEKTART": "Campingplatzareal"}, False),
            ({"OBJEKTART": "Zooareal"}, False),
            ({"OBJEKTART": "Standplatzareal"}, False),
            ({"OBJEKTART": "Schwimmbadareal"}, False),
            ({"OBJEKTART": "Freizeitanlagenareal"}, False),
            ({"OBJEKTART": "Sportplatzareal"}, True),
            ({"OBJEKTART": "Golfplatzareal"}, True),
            ({"OBJEKTART": "Pferderennbahnareal"}, True),
            ({"OBJEKTART": "FAKE-WILL-PASS"}, True),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_return_value):
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )


@pytest.fixture
def parks_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D Polygon",
        "properties": {
            "OBJEKTART": "str",
        },
    }
    entities = [
        (
            Polygon(
                [
                    (2700000.0, 1200001.0, 0.0),
                    (2700000.0, 1200002.0, 0.0),
                    (2700001.0, 1200002.0, 0.0),
                    (2700001.0, 1200001.0, 0.0),
                    (2700000.0, 1200001.0, 0.0),
                ]
            ),
            {"OBJEKTART": "Sportplatzareal"},
        ),
        (
            Polygon(
                [
                    (2700000.0, 1200002.0, 0.0),
                    (2700000.0, 1200003.0, 0.0),
                    (2700001.0, 1200003.0, 0.0),
                    (2700001.0, 1200002.0, 0.0),
                    (2700000.0, 1200002.0, 0.0),
                ]
            ),
            {"OBJEKTART": "FAKE-WILL-PASS"},
        ),
    ]
    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoParksGeometryProvider, filenames=[shapefile.name]
        )
        yield


class TestSwissTopoParksHandler(
    _TestBaseSurroundingHandler,
):
    instance_cls = SwissTopoParksHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.PARKS
        )

    def test_triangulate_shapefile(self, parks_shapefile):
        bounding_box = get_surroundings_bounding_box(
            x=2700000.0, y=1200000.0, bounding_box_extension=100
        )
        elevation_handler = flat_elevation_handler(
            bounds=bounding_box.bounds, elevation=-1.0
        )

        triangles = list(
            self.get_instance(
                bounding_box=bounding_box,
                region=REGION.CH,
                elevation_handler=elevation_handler,
            ).get_triangles()
        )

        check_surr_triangles(
            expected_area=2.0,
            first_elem_height=-0.9,
            expected_num_triangles=3,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.PARKS},
        )
