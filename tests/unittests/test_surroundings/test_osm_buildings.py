import json

import pytest
from shapely.geometry import box

from common_utils.constants import REGION, SurroundingType
from surroundings.constants import BOUNDING_BOX_EXTENSION_TARGET_BUILDING
from surroundings.osm import OSMBuildingsHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMBuildingsHandler:
    @staticmethod
    def get_monaco_triangles(fixtures_osm_path, mocker, monaco_buildings_location):
        with fixtures_osm_path.joinpath("buildings/monaco.shp").open(mode="r") as f:
            mocker.patch.object(
                OSMBuildingsHandler, "load_entities", return_value=json.load(f)
            )

        surrounding_handler = OSMBuildingsHandler(
            location=monaco_buildings_location,
            region=REGION.MC,
            simulation_version=random_simulation_version(),
        )
        building_footprints = [
            box(
                minx=monaco_buildings_location.x - 300,
                miny=monaco_buildings_location.y - 300,
                maxx=monaco_buildings_location.x + 300,
                maxy=monaco_buildings_location.y + 300,
            )
        ]
        return list(
            surrounding_handler.get_triangles(building_footprints=building_footprints)
        )

    def test_get_osm_building_triangles(
        self, mocker, fixtures_osm_path, monaco_buildings_location, overpass_api_mocked
    ):
        overpass_api_mocked(return_value={})

        triangles = self.get_monaco_triangles(
            fixtures_osm_path, mocker, monaco_buildings_location
        )

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            expected_area=309503.005,
            first_elem_height=-2.0,
            expected_num_triangles=12358,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.BUILDINGS},
        )

    @pytest.mark.parametrize(
        "overpass_tags, heights",
        [
            (
                {
                    23715051: {"tags": {"height": "145"}},
                    25722685: {"tags": {"building:levels": "16"}},
                },
                {145.0, 56.0, 10.0, -2.0},
            ),
            (  # should_ignore_non_digit_height_osm_tags:
                {
                    23715051: {"tags": {"height": "15m"}},
                    25722685: {"tags": {"building:levels": "sixteen"}},
                },
                {10.0, -2.0},
            ),
        ],
    )
    def test_get_building_metadata(
        self,
        mocker,
        fixtures_osm_path,
        monaco_buildings_location,
        overpass_api_mocked,
        overpass_tags,
        heights,
    ):
        overpass_api_mocked(return_value=overpass_tags)

        triangles = self.get_monaco_triangles(
            fixtures_osm_path, mocker, monaco_buildings_location
        )
        triangle_heights = {x[0][2] for _, x in triangles}

        assert heights == triangle_heights

    def test_init_calls_overpass_api_with_lon_lat_bounding_box(
        self, monaco_buildings_location, overpass_api_mocked
    ):
        # given
        mocked = overpass_api_mocked()
        # when
        OSMBuildingsHandler(
            location=monaco_buildings_location,
            region=REGION.MC,
            simulation_version=random_simulation_version(),
        )
        # then
        assert mocked.call_count == 1
        assert mocked.call_args[1]["bounding_box"].bounds == (
            7.414570079758963,
            43.730178825193484,
            7.4272195913876145,
            43.73935086090988,
        )

    @pytest.mark.parametrize(
        "value, expected",
        [
            ({"height": 15}, 15),
            ({"height": 0}, OSMBuildingsHandler._MIN_BUILDING_HEIGHT),
            ({"osm_id": 142}, 15),
            ({"id": 142}, OSMBuildingsHandler._MIN_BUILDING_HEIGHT),
        ],
    )
    def test_get_building_height(
        self, monaco_buildings_location, overpass_api_mocked, value, expected
    ):
        overpass_api_mocked(return_value={142: {"tags": {"height": "15"}}})

        height = OSMBuildingsHandler(
            location=monaco_buildings_location,
            region=REGION.MC,
            bounding_box_extension=BOUNDING_BOX_EXTENSION_TARGET_BUILDING,
            simulation_version=random_simulation_version(),
        )._get_building_height(value)
        assert height == expected
