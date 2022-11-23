import numpy as np
import pytest
from shapely.geometry import Point, box

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from surroundings.swisstopo import SwissTopoGroundSurroundingHandler
from tests.utils import check_surr_triangles


class TestSwissTopoGroundSurroundingHandler:
    @pytest.mark.parametrize(
        "sim_version, offset",
        [
            (SIMULATION_VERSION.PH_01_2021, 0.0),
            # triangles are shifted by 2m in fixtures
            (SIMULATION_VERSION.EXPERIMENTAL, 2.0),
        ],
    )
    @pytest.mark.parametrize(
        "tile,location,footprint_size,bounding_box_extension,expected_triangle_num,expected_area,first_elem_height,expected_avg_height",
        [
            (
                "swiss_1091_3",
                Point(2673000, 1243000),
                20,
                495,
                19690,
                980099.99,
                592.319,
                581.259,
            ),
            (
                "swiss_1047_4",
                Point(2613243.6, 1266471.1),
                50,
                50,
                485,
                12100.000,
                269.351,
                263.2716,
            ),
        ],
    )
    def test_get_triangles(
        self,
        tile,
        location,
        footprint_size,
        bounding_box_extension,
        expected_triangle_num,
        expected_area,
        first_elem_height,
        expected_avg_height,
        mocked_swisstopo_esri_ascii_grid,
        sim_version,
        offset,
    ):
        building_footprint = box(
            location.x - footprint_size / 2,
            location.y - footprint_size / 2,
            location.x + footprint_size / 2,
            location.y + footprint_size / 2,
        )
        ground_handler = SwissTopoGroundSurroundingHandler(
            location=location,
            building_footprints=[building_footprint],
            region=REGION.CH,
            bounding_box_extension=bounding_box_extension,
            simulation_version=sim_version,
        )

        with mocked_swisstopo_esri_ascii_grid(tile):
            triangles = list(ground_handler.get_triangles())

        # Content checks
        assert triangles is not None
        average_height = np.mean(
            [point[2] for surr_type, triangle in triangles for point in triangle]
        )
        assert average_height == pytest.approx(expected_avg_height + offset, abs=0.1)
        check_surr_triangles(
            expected_area=expected_area,
            first_elem_height=first_elem_height + offset,
            expected_num_triangles=expected_triangle_num,
            surr_triangles=triangles,
            expected_surr_type={SurroundingType.GROUNDS},
        )
