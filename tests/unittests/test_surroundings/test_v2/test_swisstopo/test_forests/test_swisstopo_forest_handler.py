import pytest
from shapely.affinity import translate
from shapely.geometry import box

from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.swisstopo.constants import FOREST_FILE_TEMPLATES
from surroundings.v2.swisstopo.forests.forest_handler import (
    FOREST_GENERATORS_BY_TYPE,
    SwissTopoForestGeometryProvider,
    SwissTopoForestGeometryTransformer,
    SwissTopoForestHandler,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestForestGeometryTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_swisstopo.test_swisstopo_geometry_provider import (
    _TestSwissTopoShapeFileGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMForestGeometryProvider(_TestSwissTopoShapeFileGeometryProvider):
    instance_cls = SwissTopoForestGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == FOREST_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "forest_type, expected_result",
        [
            *[(forest_type, True) for forest_type in FOREST_GENERATORS_BY_TYPE.keys()],
            ("Anything else", False),
        ],
    )
    def test_geometry_filter(self, mocker, forest_type, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(
                    geom=mocker.ANY, properties={"OBJEKTART": forest_type}
                )
            )
            == expected_result
        )


class TestSwissTopoForestGeometryTransformer(_TestForestGeometryTransformer):
    instance_cls = SwissTopoForestGeometryTransformer

    @pytest.mark.parametrize(
        "forest_type, forest_generator_cls", FOREST_GENERATORS_BY_TYPE.items()
    )
    def test_get_forest_generator(self, forest_type, forest_generator_cls, mocker):
        geometry = Geometry(geom=mocker.ANY, properties=dict(OBJEKTART=forest_type))
        forest_generator = self.get_instance().get_forest_generator(geometry=geometry)
        assert isinstance(forest_generator, forest_generator_cls)


@pytest.fixture
def mocked_swisstopo_forest_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "3D Polygon",
        "properties": {"OBJEKTART": "str"},
    }
    entities = [
        (
            translate(box(2700000.0, 1200000.0, 2700000.1, 1200001.0), xoff=0.0),
            {"OBJEKTART": forest_type},
        )
        for forest_type in FOREST_GENERATORS_BY_TYPE.keys()
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            SwissTopoForestGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestSwissTopoForestHandler(_TestBaseSurroundingHandler):
    instance_cls = SwissTopoForestHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.FOREST
        )

    def test_triangulate_shapefile(self, mocked_swisstopo_forest_shapefile):
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
            expected_area=67.0,
            first_elem_height=-1.0,
            expected_num_triangles=60,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.FOREST},
        )
