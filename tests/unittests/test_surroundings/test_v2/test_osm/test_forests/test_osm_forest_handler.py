import pytest
from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.constants import FOREST_FILE_TEMPLATES
from surroundings.v2.osm.forests.forest_handler import (
    FOREST_GENERATORS_BY_TYPE,
    OSMForestGeometryProvider,
    OSMForestGeometryTransformer,
    OSMForestHandler,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestForestGeometryTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMForestGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMForestGeometryProvider

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
                geometry=Geometry(geom=mocker.ANY, properties={"fclass": forest_type})
            )
            == expected_result
        )


class TestOSMForestGeometryTransformer(_TestForestGeometryTransformer):
    instance_cls = OSMForestGeometryTransformer

    @pytest.mark.parametrize(
        "fclass, forest_generator_cls", FOREST_GENERATORS_BY_TYPE.items()
    )
    def test_get_forest_generator(self, fclass, forest_generator_cls, mocker):
        geometry = Geometry(geom=mocker.ANY, properties=dict(fclass=fclass))
        forest_generator = self.get_instance().get_forest_generator(geometry=geometry)
        if forest_generator_cls:
            assert isinstance(forest_generator, forest_generator_cls)
        else:
            assert forest_generator is None


@pytest.fixture
def mocked_osm_forest_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "Polygon",
        "properties": {"fclass": "str"},
    }
    entities = [
        (
            project_geometry(
                box(2700000.0, 1200000.0, 2700000.1, 1200001.0),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"fclass": forest_type},
        )
        for forest_type in FOREST_GENERATORS_BY_TYPE.keys()
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMForestGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMForestHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMForestHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.FOREST
        )

    def test_triangulate_shapefile(self, mocked_osm_forest_shapefile):
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
            first_elem_height=-0.95,
            expected_num_triangles=72,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.FOREST},
        )
