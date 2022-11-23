from pathlib import Path

import pytest
from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.osm.constants import SEA_FILE_TEMPLATES
from surroundings.v2.osm.sea import OSMSeaGeometryProvider, OSMSeaHandler
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMSeaGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMSeaGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == SEA_FILE_TEMPLATES

    def test_osm_directory(self, mocker):
        assert self.get_instance(region=mocker.ANY).osm_directory == Path()


@pytest.fixture
def mocked_osm_sea_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "Polygon",
        "properties": {},
    }
    entities = [
        (
            project_geometry(
                box(2700000.0, 1200000.0, 2700000.1, 1200001.0),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {},
        )
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMSeaGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMSeaHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMSeaHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.SEA
        )

    def test_triangulate_shapefile(self, mocked_osm_sea_shapefile):
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
            expected_num_triangles=24,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.SEA},
        )
