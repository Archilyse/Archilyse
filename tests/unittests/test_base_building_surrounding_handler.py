import pytest
from shapely.geometry import box

from surroundings.base_building_handler import BaseBuildingSurroundingHandler


@pytest.mark.parametrize(
    "surrounding_footprint, layout_footprint, is_target_building",
    [
        (
            box(minx=0, miny=0, maxx=1000, maxy=1000),
            box(minx=0, miny=0, maxx=10, maxy=10),
            True,
        ),
        (
            box(minx=0, miny=0, maxx=10, maxy=10),
            box(minx=0, miny=0, maxx=1000, maxy=1000),
            True,
        ),
        (
            box(minx=0, miny=0, maxx=1000, maxy=1000),
            box(minx=-900, miny=-900, maxx=100, maxy=100),
            False,
        ),
        (
            box(minx=-900, miny=-900, maxx=100, maxy=100),
            box(minx=0, miny=0, maxx=1000, maxy=1000),
            False,
        ),
    ],
)
def test_is_target_building(
    surrounding_footprint, layout_footprint, is_target_building
):
    assert (
        BaseBuildingSurroundingHandler._is_target_building(
            building_footprint=surrounding_footprint,
            building_footprints=[layout_footprint],
        )
        is is_target_building
    )
