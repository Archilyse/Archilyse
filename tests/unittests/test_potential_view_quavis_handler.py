import pytest
from shapely.geometry import box

from common_utils.constants import POTENTIAL_LAYOUT_MODE
from handlers.quavis import PotentialViewQuavisHandler


@pytest.mark.parametrize(
    "layout_mode, expected_no_of_walls, expected_no_of_windows",
    [(POTENTIAL_LAYOUT_MODE.WITH_WINDOWS, 4, 4)],
)
def test_get_layout(
    layout_mode,
    expected_no_of_walls,
    expected_no_of_windows,
):
    layout = PotentialViewQuavisHandler._get_layout(
        floor_number=1,
        building_footprint=box(0, 0, 1, 1),
        layout_mode=layout_mode,
    )

    assert len(layout.walls) == expected_no_of_walls
    assert len(layout.openings) == expected_no_of_windows
