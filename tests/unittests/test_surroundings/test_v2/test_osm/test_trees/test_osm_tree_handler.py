import pytest
from shapely.geometry import Point

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.constants import DEFAULT_TREE_HEIGHT
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.constants import TREE_FILE_TEMPLATES
from surroundings.v2.osm.trees.tree_handler import (
    OSMTreeGeometryProvider,
    OSMTreeGeometryTransformer,
    OSMTreeHandler,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestTreeGeometryTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMTreeGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMTreeGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == TREE_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "fclass, expected_result",
        [
            ("tree", True),
            ("Anything else", False),
        ],
    )
    def test_geometry_filter(self, mocker, fclass, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(geom=mocker.ANY, properties={"fclass": fclass})
            )
            == expected_result
        )


class TestOSMTreeGeometryTransformer(_TestTreeGeometryTransformer):
    instance_cls = OSMTreeGeometryTransformer

    def test_get_height(self, mocker):
        assert (
            self.get_instance().get_height(geometry=mocker.ANY) == DEFAULT_TREE_HEIGHT
        )


@pytest.fixture
def mocked_osm_tree_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "Point",
        "properties": {"fclass": "str"},
    }
    entities = [
        (
            project_geometry(
                Point(2700000.0, 1200000.0),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"fclass": "tree"},
        )
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMTreeGeometryProvider, filenames=[shapefile.name]
        )
        yield


class TestOSMTreeHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMTreeHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.TREES
        )

    def test_triangulate_shapefile(self, mocked_osm_tree_shapefile):
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
            expected_area=20.0,
            first_elem_height=-1.0,
            expected_num_triangles=24,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.TREES},
        )
