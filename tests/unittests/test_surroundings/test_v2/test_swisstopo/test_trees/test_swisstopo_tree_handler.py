import pytest
from shapely.geometry import Point

from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import TREES_FILE_TEMPLATES
from surroundings.v2.swisstopo.trees.tree_handler import (
    SwissTopoTreeGeometryProvider,
    SwissTopoTreeGeometryTransformer,
    SwissTopoTreeHandler,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestTreeGeometryTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestSwissTopoTreeGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoTreeGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == TREES_FILE_TEMPLATES


class TestSwissTopoTreeGeometryTransformer(_TestTreeGeometryTransformer):
    instance_cls = SwissTopoTreeGeometryTransformer

    @pytest.mark.parametrize(
        "ground_level, tree_geom_z, expected_tree_height",
        [
            (1.0, 10.0, 9.0),
            (2.5, 10.0, 7.5),
            (2.5, 15.0, 12.5),
        ],
    )
    def test_get_height(self, ground_level, tree_geom_z, expected_tree_height):
        elevation_handler = flat_elevation_handler(
            bounds=(0.0, 0.0, 1.0, 1.0), elevation=ground_level
        )
        tree_transformer = self.get_instance(elevation_handler=elevation_handler)
        assert (
            tree_transformer.get_height(
                geometry=Geometry(geom=Point(0.5, 0.5, tree_geom_z), properties={})
            )
            == expected_tree_height
        )


@pytest.fixture
def mocked_swisstopo_tree_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D Point",
        "properties": {},
    }
    entities = [
        (
            Point(2700000.0, 1200000.0, 10.0),
            {},
        )
    ]
    with create_fiona_collection(
        schema=schema,
        records=entities,
    ) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoTreeGeometryProvider, filenames=[shapefile.name]
        )
        yield


class TestSwissTopoTreeHandler(_TestBaseSurroundingHandler):
    instance_cls = SwissTopoTreeHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.TREES
        )

    def test_triangulate_shapefile(self, mocked_swisstopo_tree_shapefile):
        bounding_box = get_surroundings_bounding_box(
            x=2700000.0, y=1200000.0, bounding_box_extension=100
        )
        elevation_handler = flat_elevation_handler(
            bounds=bounding_box.bounds, elevation=0.0
        )

        triangles = list(
            self.get_instance(
                bounding_box=bounding_box,
                region=REGION.CH,
                elevation_handler=elevation_handler,
            ).get_triangles()
        )

        check_surr_triangles(
            expected_area=32.5,
            first_elem_height=0.0,
            expected_num_triangles=24,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.TREES},
        )
