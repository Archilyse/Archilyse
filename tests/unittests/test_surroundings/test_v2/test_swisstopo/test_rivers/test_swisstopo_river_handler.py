import pytest
from shapely.geometry import LineString

from common_utils.constants import REGION, SurroundingType
from dufresne.linestring_add_width import LINESTRING_EXTENSION
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.geometry_transformer import RiverLinesGeometryTransformer
from surroundings.v2.swisstopo.rivers.rivers_handler import (
    SwissTopoRiverLinesGeometryProvider,
    SwissTopoRiverLinesHandler,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestGroundCoveringLineStringTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestRiverLinesGeometryTransformer(_TestGroundCoveringLineStringTransformer):
    instance_cls = RiverLinesGeometryTransformer

    def test_get_width(self, mocker):
        # Always 1 meter width
        assert (
            self.get_instance().get_width(
                Geometry(geom=mocker.ANY, properties=mocker.ANY)
            )
            == 2.0
        )

    def test_get_extension_type(self, mocker):
        # Always symmetric
        assert (
            self.get_instance().get_extension_type(
                Geometry(geom=mocker.ANY, properties=mocker.ANY)
            )
            == LINESTRING_EXTENSION.SYMMETRIC
        )


class TestRiverLinesGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoRiverLinesGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_return_value",
        [
            ({"VERLAUF": "FAKE-WILL-PROJECT-TO-GROUND"}, True),
            ({"VERLAUF": "Unterirdisch"}, False),
        ],
    )
    def test_geometry_filter(self, properties, expected_return_value, mocker):
        assert (
            self.get_instance().geometry_filter(
                Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_return_value
        )


@pytest.fixture
def mocked_rivers_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D LineString",
        "properties": {
            "VERLAUF": "str",
        },
    }
    entities = [
        (
            LineString([(2700000.0, 1200000.0, 1), (2700000.0, 1200001.0, 1)]),
            {"VERLAUF": "FAKE-WILL-PROJECT-TO-GROUND"},
        ),
        (
            # underground rivers are not triangulated
            LineString([(2700000.0, 1200002.0, 1), (2700000.0, 1200003.0, 1)]),
            {"VERLAUF": "Unterirdisch"},
        ),
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoRiverLinesGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestSwissTopoRiverLinesHandler(_TestBaseSurroundingHandler):
    instance_cls = SwissTopoRiverLinesHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.RIVERS
        )

    def test_triangulate_shapefile(self, mocked_rivers_shapefile):
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
            first_elem_height=-0.85,
            expected_num_triangles=3,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.RIVERS},
        )
