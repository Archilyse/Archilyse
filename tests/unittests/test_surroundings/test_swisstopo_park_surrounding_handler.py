import json

import pytest
from shapely.geometry import Point

from common_utils.constants import SurroundingType
from surroundings.swisstopo import SwissTopoParksSurroundingHandler
from tests.utils import check_surr_triangles, random_simulation_version


class TestParksSurroundingHandler:
    @pytest.mark.parametrize(
        "fixture, location, num_triangles, area, first_elem_height",
        [
            ("parks/park.json", Point(2784998, 1152929), 339, 51940.68117, 1833.273),
            #
            # This one has a wrongly generated polygon as explained in https://github.com/Archilyse/slam/pull/1139
            #
            (
                "parks/park_invalid_polygon.json",
                Point(2674467, 1209100),
                104,
                26809.158486,
                435.551,
            ),
        ],
    )
    def test_get_triangles(
        self,
        mocker,
        fixtures_swisstopo_path,
        fixture,
        num_triangles,
        area,
        first_elem_height,
        location,
        mocked_gcp_download,
        mock_elevation,
    ):
        mock_elevation(first_elem_height)

        with fixtures_swisstopo_path.joinpath(fixture).open() as f:
            mocked_fiona_open = mocker.patch.object(
                SwissTopoParksSurroundingHandler,
                "load_entities",
                return_value=json.load(f),
            )

        park_triangles = list(
            SwissTopoParksSurroundingHandler(
                location=location, simulation_version=random_simulation_version()
            ).get_triangles()
        )

        assert mocked_fiona_open.call_count == 1
        check_surr_triangles(
            expected_area=area,
            first_elem_height=first_elem_height,
            expected_num_triangles=num_triangles,
            surr_triangles=park_triangles,
            expected_surr_type={SurroundingType.PARKS},
        )

    def test_get_triangles_none(self, mocker, fixtures_path, park_surr_location):
        mocker.patch.object(
            SwissTopoParksSurroundingHandler,
            "load_entities",
            return_value=[],
        )

        park_triangles = list(
            SwissTopoParksSurroundingHandler(
                location=park_surr_location,
                simulation_version=random_simulation_version(),
            ).get_triangles()
        )
        assert park_triangles == []
