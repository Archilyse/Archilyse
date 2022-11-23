import pytest
from shapely.geometry import LineString

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.constants import RIVER_FILE_TEMPLATES
from surroundings.v2.osm.rivers import OSMRiverGeometryProvider
from surroundings.v2.osm.rivers.river_handler import RIVER_TYPES, OSMRiverHandler
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


@pytest.fixture
def mocked_osm_river_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "LineString",
        "properties": {"fclass": "str"},
    }
    entities = [
        (
            project_geometry(
                LineString([(2700000.0, 1200000.0), (2700000.0, 1200001.0)]),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"fclass": river_type},
        )
        for river_type in RIVER_TYPES
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMRiverGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMRiverGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMRiverGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == RIVER_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "properties, expected_result",
        [
            *[({"fclass": river_type}, True) for river_type in RIVER_TYPES],
            ({"fclass": "Anything else"}, False),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_result
        )


class TestOSMRiverHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMRiverHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.RIVERS
        )

    def test_triangulate_shapefile(self, mocked_osm_river_shapefile):
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
            expected_area=4.0,
            first_elem_height=-0.85,
            expected_num_triangles=48,
            surr_triangles=triangles,
            expected_surr_type={
                SurroundingType.RIVERS,
            },
        )
