import pytest
from shapely.geometry import LineString

from common_utils.constants import REGION, SurroundingType
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo import SwissTopoRailwayHandler
from surroundings.v2.swisstopo.railways.railway_handler import (
    RailwayGeometryTransformer,
    SwissTopoRailwayGeometryProvider,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_streets_and_railway_geometry_transformer import (
    _TestStreetsAndRailwayTransformer,
)
from tests.utils import check_surr_triangles


@pytest.fixture
def mocked_swisstopo_railways_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D LineString",
        "properties": {
            "KUNSTBAUTE": "str",
            "AUSSER_BET": "str",
        },
    }
    entities = [
        (
            LineString(geom),
            {
                "KUNSTBAUTE": "FAKE-WILL-PROJECT-TO-GROUND",
                "AUSSER_BET": "False",
                **properties,
            },
        )
        for geom, properties in [
            (
                [(2700000.0, 1200000.0, 1), (2700000.0, 1200001.0, 1)],
                {},
            ),
            (
                [(2700000.0, 1200001.0, 1), (2700000.0, 1200002.0, 1)],
                {"KUNSTBAUTE": "Bruecke"},
            ),
            (
                # Tunnels are not triangulated
                [(2700000.0, 1200002.0, 1), (2700000.0, 1200003.0, 1)],
                {"KUNSTBAUTE": "Tunnel"},
            ),
            (
                # Inactive railways are not triangulated
                [(2700000.0, 1200002.0, 1), (2700000.0, 1200003.0, 1)],
                {"AUSSER_BET": "Wahr"},
            ),
            (
                # Out of bounding box
                [(2600000.0, 1200003.0, 1), (2600000.0, 1200004.0, 1)],
                {},
            ),
        ]
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoRailwayGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestRailwayTransformer(_TestStreetsAndRailwayTransformer):
    instance_cls = RailwayGeometryTransformer

    def test_get_width(self, mocker):
        # Always 1 meter width
        assert (
            self.get_instance().get_width(
                Geometry(geom=mocker.ANY, properties=mocker.ANY)
            )
            == 1.0
        )

    def test_get_extension_type(self, mocker):
        # Always symmetric
        assert (
            self.get_instance().get_extension_type(
                Geometry(geom=mocker.ANY, properties=mocker.ANY)
            )
            == LINESTRING_EXTENSION.SYMMETRIC
        )


class TestSwissTopoRailwayHandler(
    _TestBaseSurroundingHandler,
):
    instance_cls = SwissTopoRailwayHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.RAILROADS
        )

    def test_triangulate_shapefile(self, mocked_swisstopo_railways_shapefile):
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
            first_elem_height=-0.75,
            expected_num_triangles=6,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.RAILROADS},
        )
        assert any(z == 1.0 for _, triangle in triangles for _, _, z in triangle)
