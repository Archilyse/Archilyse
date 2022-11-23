import pytest
from shapely.geometry import LineString

from common_utils.constants import REGION, SurroundingType
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.constants import DEFAULT_STREET_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo import SwissTopoStreetsHandler
from surroundings.v2.swisstopo.constants import SWISSTOPO_TRUE
from surroundings.v2.swisstopo.streets.constants import STREET_CLASS, STREET_TYPE_WIDTH
from surroundings.v2.swisstopo.streets.street_handler import (
    StreetsGeometryTransformer,
    SwissTopoStreetsGeometryProvider,
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
def mocked_swisstopo_streets_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D LineString",
        "properties": {
            "KUNSTBAUTE": "str",
            "OBJEKTART": "str",
            "RICHTUNGSG": "str",
            "VERKEHRSBE": "str",
            "VERKEHRSBD": "str",
        },
    }
    entities = [
        (
            LineString(geom),
            {
                "KUNSTBAUTE": "FAKE-WILL-PROJECT-TO-GROUND",
                "OBJEKTART": "FAKE-WILL-GET-DEFAULT-WIDTH",
                "RICHTUNGSG": "FAKE-WILL-BE-SYMMETRIC",
                "VERKEHRSBE": "FAKE-WITH-CAR-TRAFFIC",
                "VERKEHRSBD": "ANY",
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
                # Faehre are not triangulated
                [(2700000.0, 1200002.0, 1), (2700000.0, 1200003.0, 1)],
                {"OBJEKTART": "Faehre"},
            ),
            (
                # Tunnels are not triangulated
                [(2700000.0, 1200003.0, 1), (2700000.0, 1200004.0, 1)],
                {"KUNSTBAUTE": "Tunnel"},
            ),
            (
                # Out of bounding box
                [(2600000.0, 1200002.0, 1), (2600000.0, 1200003.0, 1)],
                {},
            ),
            (
                # roads without car traffic
                [(2700000.0, 1200004.0, 1), (2700000.0, 1200005.0, 1)],
                {"VERKEHRSBE": "Allgemeines Fahrverbot"},
            ),
        ]
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoStreetsGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestStreetsGeometryTransformer(_TestStreetsAndRailwayTransformer):
    instance_cls = StreetsGeometryTransformer

    @pytest.mark.parametrize(
        "properties, expected_width",
        [
            (
                {"OBJEKTART": "FAKE-WILL-GET-DEFAULT-WIDTH"},
                DEFAULT_STREET_WIDTH,
            ),
            *[
                ({"OBJEKTART": street_type}, width)
                for street_type, width in STREET_TYPE_WIDTH.items()
            ],
        ],
    )
    def test_get_width(self, properties, expected_width, mocker):
        assert (
            self.get_instance().get_width(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_width
        )

    @pytest.mark.parametrize(
        "properties, expected_type",
        [
            *[
                ({"RICHTUNGSG": value}, LINESTRING_EXTENSION.RIGHT)
                for value in SWISSTOPO_TRUE
            ],
            *[({"RICHTUNGSG": "SOMETHING-NOT-TRUE"}, LINESTRING_EXTENSION.SYMMETRIC)],
        ],
    )
    def test_get_extension_type(self, properties, expected_type, mocker):
        assert (
            self.get_instance().get_extension_type(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_type
        )


class TestSwissTopoStreetHandler(_TestBaseSurroundingHandler):
    instance_cls = SwissTopoStreetsHandler

    @pytest.mark.parametrize(
        "street_class, expected_surrounding_type",
        [
            (STREET_CLASS.PEDESTRIAN, SurroundingType.PEDESTRIAN),
            (STREET_CLASS.HIGHWAY, SurroundingType.HIGHWAY),
            (STREET_CLASS.PRIMARY_STREET, SurroundingType.PRIMARY_STREET),
            (STREET_CLASS.SECONDARY_STREET, SurroundingType.SECONDARY_STREET),
            (STREET_CLASS.TERTIARY_STREET, SurroundingType.TERTIARY_STREET),
        ],
    )
    def test_get_surrounding_type(
        self, street_class, expected_surrounding_type, mocker
    ):
        from surroundings.v2.swisstopo.streets.street_classifier import (
            SwissTopoStreetsClassifier,
        )

        mocker.patch.object(
            SwissTopoStreetsClassifier, "classify", return_value=street_class
        )
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == expected_surrounding_type
        )

    def test_triangulate_shapefile(self, mocked_swisstopo_streets_shapefile):
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
            expected_area=18.0,
            first_elem_height=-0.80,
            expected_num_triangles=18,
            surr_triangles=triangles,
            expected_surr_type={
                SurroundingType.TERTIARY_STREET,
                SurroundingType.PEDESTRIAN,
            },
        )
        assert any(z == 1.0 for _, triangle in triangles for _, _, z in triangle)
