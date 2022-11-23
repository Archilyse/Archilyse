import pytest
from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.constants import PARK_FILE_TEMPLATES
from surroundings.v2.osm.parks import OSMParksGeometryProvider, OSMParksHandler
from surroundings.v2.osm.parks.parks_handler import PARK_TYPES
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMParksGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMParksGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == PARK_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "park_type, expected_result",
        [*[(park_type, True) for park_type in PARK_TYPES], ("Anything else", False)],
    )
    def test_geometry_filter(self, mocker, park_type, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(geom=mocker.ANY, properties={"fclass": park_type})
            )
            == expected_result
        )


@pytest.fixture
def mocked_osm_parks_shapefile(patch_geometry_provider_source_files):
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
            {"fclass": park_type},
        )
        for park_type in PARK_TYPES
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMParksGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMParksHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMParksHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.PARKS
        )

    def test_triangulate_shapefile(self, mocked_osm_parks_shapefile):
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
            expected_num_triangles=48,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.PARKS},
        )
