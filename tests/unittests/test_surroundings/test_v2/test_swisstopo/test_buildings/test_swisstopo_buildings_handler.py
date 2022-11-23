import pytest
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon

from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.swisstopo.buildings.building_handler import (
    SwissTopoBuildingsGeometryProvider,
    SwissTopoBuildingsHandler,
)
from surroundings.v2.swisstopo.constants import BUILDINGS_FILE_TEMPLATES
from tests.surroundings_utils import create_fiona_collection
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestSwissTopoBuildingsGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoBuildingsGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == BUILDINGS_FILE_TEMPLATES


@pytest.fixture
def mocked_swisstopo_buildings_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D MultiPolygon",
        "properties": {},
    }
    entities = [
        (
            translate(
                MultiPolygon(
                    [
                        Polygon([(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)]),
                        Polygon([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]),
                    ]
                ),
                xoff=2700000.0,
                yoff=1200000.0,
            ),
            {},
        )
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoBuildingsGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestSwissTopoBuildingsHandler(_TestBaseSurroundingHandler):
    instance_cls = SwissTopoBuildingsHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.BUILDINGS
        )

    def test_triangulate_shapefile(self, mocked_swisstopo_buildings_shapefile, mocker):
        bounding_box = get_surroundings_bounding_box(
            x=2700000.0, y=1200000.0, bounding_box_extension=100
        )

        triangles = list(
            self.get_instance(
                bounding_box=bounding_box,
                region=REGION.CH,
                elevation_handler=mocker.ANY,
            ).get_triangles()
        )

        check_surr_triangles(
            expected_area=1.0,
            first_elem_height=0.0,
            expected_num_triangles=2,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.BUILDINGS},
        )
