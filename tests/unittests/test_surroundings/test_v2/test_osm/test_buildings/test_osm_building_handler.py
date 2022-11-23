import pytest
from shapely.geometry import Polygon, box

from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SurroundingType
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.geometry import Geometry
from surroundings.v2.osm.buildings.building_handler import (
    OSMBuildingFootprintTransformer,
    OSMBuildingGeometryProvider,
    OSMBuildingHandler,
)
from surroundings.v2.osm.constants import (
    BUILDING_FILE_TEMPLATES,
    BUILDING_LEVEL_HEIGHT,
    MIN_BUILDING_HEIGHT,
)
from tests.surroundings_utils import create_fiona_collection, flat_elevation_handler
from tests.unittests.test_surroundings.test_v2.test_base_surrounding_handler import (
    _TestBaseSurroundingHandler,
)
from tests.unittests.test_surroundings.test_v2.test_geometry_transformer import (
    _TestBuildingFootprintTransformer,
)
from tests.unittests.test_surroundings.test_v2.test_osm.test_osm_geometry_provider import (
    _TestOSMGeometryProvider,
)
from tests.utils import check_surr_triangles


class TestOSMBuildingsGeometryProvider(_TestOSMGeometryProvider):
    instance_cls = OSMBuildingGeometryProvider

    def test_file_templates(self):
        assert self.get_instance().file_templates == BUILDING_FILE_TEMPLATES

    @pytest.mark.parametrize(
        "geometry, expected_result",
        [
            (Geometry(geom=Polygon(), properties={}), False),
            (Geometry(geom=box(0, 0, 1, 1), properties={}), True),
        ],
    )
    def test_geometry_filter(self, geometry, expected_result, mocker):
        assert self.get_instance().geometry_filter(geometry=geometry) == expected_result


class TestOSMBuildingsFootprintTransformer(_TestBuildingFootprintTransformer):
    instance_cls = OSMBuildingFootprintTransformer

    def get_instance(self, elevation_handler=None, building_heights_by_osm_id=None):
        return self.instance_cls(
            elevation_handler=elevation_handler,
            building_heights_by_osm_id=building_heights_by_osm_id,
        )

    @pytest.mark.parametrize(
        "building_heights_by_osm_id, expected_height",
        [
            ({1: {"tags": {"height": "145"}}}, 145.0),
            ({1: {"tags": {"building:levels": "16"}}}, BUILDING_LEVEL_HEIGHT * 16),
            ({1: {"tags": {"height": "15m"}}}, 15.0),
            ({1: {"tags": {"building:levels": "sixteen"}}}, BUILDING_LEVEL_HEIGHT * 16),
            ({1: {"tags": {}}}, MIN_BUILDING_HEIGHT),
            ({-999: {"tags": {"all": "other"}}}, MIN_BUILDING_HEIGHT),
        ],
    )
    def test_get_height(self, building_heights_by_osm_id, expected_height, mocker):
        geometry = Geometry(geom=mocker.ANY, properties={"osm_id": 1})
        assert self.get_instance(
            building_heights_by_osm_id=building_heights_by_osm_id
        ).get_height(geometry=geometry)

    def test_get_height_returns_default_height_on_missing_osm_id(self, mocker):
        geometry = Geometry(geom=mocker.ANY, properties={})
        assert (
            self.get_instance(building_heights_by_osm_id={}).get_height(
                geometry=geometry
            )
            == MIN_BUILDING_HEIGHT
        )


@pytest.fixture
def mocked_osm_buildings_shapefile(patch_geometry_provider_source_files):
    schema = {
        "geometry": "Polygon",
        "properties": {"osm_id": "int"},
    }
    entities = [
        (
            project_geometry(
                box(2700000.0, 1200000.0, 2700010.0, 1200010.0),
                crs_from=REGION.CH,
                crs_to=REGION.LAT_LON,
            ),
            {"osm_id": 1},
        )
    ]

    with create_fiona_collection(schema=schema, records=entities) as shapefile:
        patch_geometry_provider_source_files(
            OSMBuildingGeometryProvider,
            filenames=[shapefile.name],
        )
        yield


@pytest.fixture
def mock_overpass_api(mocker):
    def _internal(building_metadata):
        from surroundings.v2.osm.buildings.building_handler import OverpassAPIHandler

        return mocker.patch.object(
            OverpassAPIHandler, "get_building_metadata", return_value=building_metadata
        )

    return _internal


class TestOSMBuildingSurroundingHandler(_TestBaseSurroundingHandler):
    instance_cls = OSMBuildingHandler

    def test_get_surrounding_type(self, mocker):
        assert (
            self.get_instance().get_surrounding_type(geometry=mocker.ANY)
            == SurroundingType.BUILDINGS
        )

    def test_geometry_transformer(self, mock_overpass_api, mocker):
        import surroundings.v2.osm.buildings.building_handler

        region = REGION.CH
        bounding_box = box(2700000.0, 1200000.0, 2700010.0, 1200010.0)
        building_metadata = {1: {"tags": {"height": "145"}}}
        elevation_handler = flat_elevation_handler(
            bounds=bounding_box.bounds, elevation=-1.0
        )

        projection_spy = mocker.spy(
            surroundings.v2.osm.buildings.building_handler,
            "project_geometry",
        )
        mocked_overpass_api = mock_overpass_api(building_metadata=building_metadata)

        building_transformer = self.get_instance(
            region=region,
            bounding_box=bounding_box,
            elevation_handler=elevation_handler,
        ).geometry_transformer

        projection_spy.assert_called_once_with(
            bounding_box, crs_from=region, crs_to=REGION.LAT_LON
        )
        mocked_overpass_api.assert_called_once_with(
            bounding_box=projection_spy.spy_return
        )
        assert building_transformer.elevation_handler == elevation_handler
        assert building_transformer.building_heights_by_osm_id == building_metadata

    def test_triangulate_shapefile(
        self, mocked_osm_buildings_shapefile, mock_overpass_api
    ):
        mock_overpass_api(building_metadata={1: {"tags": {"height": "145"}}})

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
            expected_area=200.0,
            first_elem_height=-3.0,
            expected_num_triangles=12,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.BUILDINGS},
        )
