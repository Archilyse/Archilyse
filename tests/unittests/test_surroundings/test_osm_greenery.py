import json

import pytest

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from surroundings.osm import OSMForestHandler, OSMParksHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestOSMGreeneryHandler:
    @pytest.mark.parametrize(
        "osm_handler, simulation_version, expected_values",
        [
            (
                OSMForestHandler,
                SIMULATION_VERSION.PH_01_2021,
                dict(
                    expected_area=7049.368,
                    first_elem_height=256.573,
                    expected_num_triangles=4208,
                    expected_surr_type={SurroundingType.FOREST},
                ),
            ),
            (
                OSMForestHandler,
                SIMULATION_VERSION.EXPERIMENTAL,
                dict(
                    expected_area=6126.86809474284,
                    first_elem_height=256.573,
                    expected_num_triangles=4208,
                    expected_surr_type={SurroundingType.FOREST},
                ),
            ),
            (
                OSMParksHandler,
                random_simulation_version(),
                dict(
                    expected_area=59001.1559,
                    first_elem_height=257.410,
                    expected_num_triangles=445,
                    expected_surr_type={SurroundingType.PARKS},
                ),
            ),
        ],
    )
    def test_osm_get_greenery_triangles(
        self,
        mocker,
        fixtures_osm_path,
        osm_handler,
        basel_location,
        simulation_version,
        expected_values,
        mocked_swisstopo_esri_ascii_grid,
    ):
        with fixtures_osm_path.joinpath(
            "greenery/switzerland-woods.json"
        ).open() as woods:
            mocker.patch.object(
                osm_handler,
                "load_entities",
                side_effect=[json.load(woods)],
            )

        surrounding_handler = osm_handler(
            location=basel_location,
            region=REGION.CH,
            bounding_box_extension=500,
            simulation_version=simulation_version,
        )

        tiles_to_mock = [
            "swiss_1047_2",
            "swiss_1047_3",
            "swiss_1047_4",
            "swiss_1067_2",
            "swiss_1067_1",
        ]
        with mocked_swisstopo_esri_ascii_grid(*tiles_to_mock):
            triangles = list(surrounding_handler.get_triangles(building_footprints=[]))

        # Content checks
        assert triangles is not None
        check_surr_triangles(
            **expected_values,
            surr_triangles=triangles,
        )
