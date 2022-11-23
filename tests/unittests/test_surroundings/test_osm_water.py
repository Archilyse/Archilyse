import json

import pytest

from common_utils.constants import REGION
from surroundings.osm import OSMLakesHandler, OSMRiversHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMWaterHandler:
    @pytest.mark.parametrize(
        "surrounding_file, osm_handler, expected_values",
        [
            (
                "rivers/switzerland.json",
                OSMRiversHandler,
                dict(
                    expected_area=2825.826,
                    first_elem_height=245.8356,
                    expected_num_triangles=234,
                ),
            ),
            (
                "bodies_of_water/switzerland.json",
                OSMLakesHandler,
                dict(
                    expected_area=72407.051,
                    first_elem_height=248.423,
                    expected_num_triangles=146,
                ),
            ),
        ],
    )
    def test_get_water_triangles(
        self,
        mocker,
        fixtures_osm_path,
        osm_handler,
        surrounding_file,
        basel_location,
        mocked_swisstopo_esri_ascii_grid,
        expected_values,
    ):

        with fixtures_osm_path.joinpath(surrounding_file).open() as rivers:
            mocker.patch.object(
                osm_handler,
                "load_entities",
                side_effect=[json.load(rivers)],
            )

        water_surrounding_handler = osm_handler(
            location=basel_location,
            region=REGION.CH,
            bounding_box_extension=200,
            simulation_version=random_simulation_version(),
        )

        tiles_to_mock = [
            "swiss_1047_2",
            "swiss_1047_3",
            "swiss_1047_4",
            "swiss_1067_2",
            "swiss_1067_1",
        ]
        with mocked_swisstopo_esri_ascii_grid(*tiles_to_mock):
            triangles = list(
                water_surrounding_handler.get_triangles(building_footprints=[])
            )

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            **expected_values,
            expected_surr_type={osm_handler.surrounding_type},
            surr_triangles=triangles,
        )
