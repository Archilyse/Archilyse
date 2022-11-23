import pytest
from shapely.geometry import LineString

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.constants import DEFAULT_STREET_WIDTH
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.streets import (
    OSMNoisyStreetsGeometryProvider,
    OSMStreetGeometryProvider,
    OSMStreetGeometryTransformer,
    OSMStreetHandler,
)
from surroundings.v2.osm.streets.constants import STREET_TYPE_MAPPING, STREET_TYPE_WIDTH
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
def mocked_osm_streets_shapefile(patch_geometry_provider_source_files):
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
            {"fclass": street_type},
        )
        for street_type in STREET_TYPE_MAPPING.keys()
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMStreetGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


class TestOSMStreetGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMStreetGeometryProvider

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


class TestOSMNoisyStreetGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMNoisyStreetsGeometryProvider

    @pytest.mark.parametrize(
        "properties, expected_result",
        [
            ({}, True),
            ({"tunnel": "T"}, False),
            ({"tunnel": 'Anything but "T"'}, True),
            ({"fclass": "whatever"}, True),
            ({"fclass": "primary"}, True),
            ({"fclass": "pedestrian"}, False),
            ({"fclass": "crossing"}, False),
        ],
    )
    def test_geometry_filter(self, mocker, properties, expected_result):
        assert (
            self.get_instance().geometry_filter(
                geometry=Geometry(geom=mocker.ANY, properties=properties)
            )
            == expected_result
        )

    def test_get_geometries_inputs_type(self, mocked_osm_streets_shapefile):
        STREET_TYPES = {
            # PEDESTRIAN excluded as it is filtered out
            SurroundingType.SECONDARY_STREET,
            SurroundingType.PRIMARY_STREET,
            SurroundingType.TERTIARY_STREET,
            SurroundingType.HIGHWAY,
        }

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
        assert geom_types == STREET_TYPES

    def test_get_geometries_clips_geometries(
        self,
        mocker,
    ):
        # To skip this test as the properties are manipulated
        pass

    def test_get_geometries(
        self,
        mocker,
        simple_shapefile_with_points=None,
        region=None,
        bounds=None,
        filter_return_value=None,
        expected_coords=None,
    ):
        # To skip this test as the properties are manipulated
        pass


class TestOSMStreetGeometryTransformer(_TestGroundCoveringLineStringTransformer):
    instance_cls = OSMStreetGeometryTransformer

    @pytest.mark.parametrize(
        "street_type, expected_width",
        [*STREET_TYPE_WIDTH.items(), ("some unknown", DEFAULT_STREET_WIDTH)],
    )
    def test_get_width(self, street_type, expected_width, mocker):
        assert (
            self.get_instance().get_width(
                geometry=Geometry(geom=mocker.ANY, properties={"fclass": street_type})
            )
            == expected_width
        )


class TestOSMStreetHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMStreetHandler

    @pytest.mark.parametrize(
        "street_fclass, expected_surrounding_type", STREET_TYPE_MAPPING.items()
    )
    def test_get_surrounding_type(
        self, street_fclass, expected_surrounding_type, mocker
    ):
        assert (
            self.get_instance().get_surrounding_type(
                geometry=Geometry(geom=mocker.ANY, properties={"fclass": street_fclass})
            )
            == expected_surrounding_type
        )

    def test_triangulate_shapefile(self, mocked_osm_streets_shapefile):
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
            expected_area=sum(STREET_TYPE_WIDTH.values()),
            first_elem_height=-0.80,
            expected_num_triangles=132,
            surr_triangles=triangles,
            expected_surr_type={
                SurroundingType.HIGHWAY,
                SurroundingType.PRIMARY_STREET,
                SurroundingType.SECONDARY_STREET,
                SurroundingType.TERTIARY_STREET,
                SurroundingType.PEDESTRIAN,
            },
        )
