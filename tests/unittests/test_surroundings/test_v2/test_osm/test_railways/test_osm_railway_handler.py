import pytest
from shapely.geometry import LineString

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.constants import DEFAULT_RAILWAY_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm import OSMRailwayHandler
from surroundings.v2.osm.constants import RAILWAY_FILE_TEMPLATES
from surroundings.v2.osm.railways import (
    OSMNoisyRailwayGeometryProvider,
    OSMRailwayGeometryProvider,
    OSMRailwayTransformer,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestGroundCoveringLineStringTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


@pytest.fixture
def mocked_osm_railways_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "LineString",
        "properties": {},
    }
    entities = [
        (
            project_geometry(
                LineString([(2700000.0, 1200000.0), (2700000.0, 1200001.0)]),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {},
        )
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMRailwayGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMRailwayGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMRailwayGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == RAILWAY_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "properties, expected_result",
        [
            ({}, True),
            ({"tunnel": "T"}, False),
            ({"tunnel": 'Anything but "T"'}, True),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_result
        )


class TestOSMNoisyRailwayGeometryProvider(TestOSMRailwayGeometryProvider):
    instance_cls = OSMNoisyRailwayGeometryProvider

    def test_geometry_provider_adds_type_rail(self, mocked_osm_railways_shapefile):
        bounding_box = get_surroundings_bounding_box(
            x=2700000.0, y=1200000.0, bounding_box_extension=100
        )
        geom_types = {
            g.properties["type"]
            for g in (
                self.get_instance(
                    bounding_box=bounding_box, region=REGION.CH
                ).get_geometries()
            )
        }
        assert geom_types == {"rail"}


class TestOSMStreetGeometryTransformer(_TestGroundCoveringLineStringTransformer):
    instance_cls = OSMRailwayTransformer

    def test_get_width(self, mocker):
        assert (
            self.get_instance().get_width(geometry=mocker.ANY) == DEFAULT_RAILWAY_WIDTH
        )


class TestOSMRailwayHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMRailwayHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.RAILROADS
        )

    def test_triangulate_shapefile(self, mocked_osm_railways_shapefile):
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
            expected_area=1.0,
            first_elem_height=-0.75,
            expected_num_triangles=4,
            surr_triangles=triangles,
            expected_surr_type={
                SurroundingType.RAILROADS,
            },
        )
