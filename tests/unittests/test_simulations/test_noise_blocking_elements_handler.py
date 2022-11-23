import pytest
from shapely.geometry import Point, Polygon

from simulations.noise.noise_blocking_elements_handler import (
    NoiseBlockingElementsHandler,
)
from tests.utils import make_layout_square_4_windows


class TestNoiseBlockingElementsHandler:
    def test_get_blocking_elements_by_plan(self):
        # TODO refactor
        # given
        plan_id = 1
        layout = make_layout_square_4_windows(db_area_id=1)
        target_buildings = [
            [{"plan_layout": layout, "is_ground_floor": True, "id": plan_id}]
        ]

        # when
        blocking_elements_by_plan_id = (
            NoiseBlockingElementsHandler._get_blocking_elements(
                site_surroundings=[], target_buildings=target_buildings
            )
        )

        # then
        assert len(blocking_elements_by_plan_id) == 1
        assert isinstance(blocking_elements_by_plan_id[plan_id], Polygon)

    @pytest.mark.parametrize(
        "surrounding_footprints, expected_count",
        [
            # this is overlapping
            ([Point(0, 0).buffer(1000)], 0),
            # this is not overlapping
            ([Point(1000, 1000).buffer(1)], 1),
        ],
    )
    def test_exclude_intersecting_footprints(
        self, surrounding_footprints, expected_count
    ):
        ex_intersecting_footprint = list(
            NoiseBlockingElementsHandler._exclude_intersecting_footprints_from_surroundings(
                target_buildings=[
                    [{"plan_layout": make_layout_square_4_windows(db_area_id=1)}]
                ],
                site_surroundings=surrounding_footprints,
            )
        )
        assert len(ex_intersecting_footprint) == expected_count
