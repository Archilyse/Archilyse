import pytest
from shapely.geometry import LineString, Polygon

from brooks.models import SimArea, SimFeature
from brooks.types import AreaType, FeatureType, SeparatorType


@pytest.mark.parametrize(
    "area_type, have_stairs, area_expected",
    [
        (AreaType.ROOM, True, 96),
        (AreaType.CORRIDOR, True, 96),
        (AreaType.CORRIDOR, False, 100),
        (AreaType.STAIRCASE, True, 96),
    ],
)
def test_area_without_stairs(area_type, have_stairs, area_expected):
    area = SimArea(
        footprint=Polygon(((0, 0), (0, 10), (10, 10), (10, 0), (0, 0))),
        area_type=area_type,
    )
    if have_stairs:
        feature = SimFeature(
            footprint=Polygon(((5, 5), (5, 7), (7, 7), (7, 5), (5, 5))),
            feature_type=FeatureType.STAIRS,
        )
        area.features.add(feature)
    assert area.area_without_stairs == area_expected


def test_area_wall_surface_area():
    from brooks.models import SimLayout, SimOpening, SimSeparator

    # base surface area should be 4 * 10 * 2.6 = 104sqm
    area = SimArea(
        footprint=Polygon(((0, 0.1), (0, 10.1), (10, 10.1), (10, 0.1), (0, 0.1))),
        area_type=AreaType.NOT_DEFINED,
        height=(0, 2.6),
    )
    layout = SimLayout()
    assert area.wall_surface_area(layout=layout) == pytest.approx(4 * 10 * 2.6)

    # 3m over the the area -> should count as 10 * 0.2 = 2sqm
    wall = SimSeparator(
        footprint=Polygon(((-10, 0), (-10, 0.1), (15, 0.1), (15, 0.0), (-5, 0.0))),
        separator_type=SeparatorType.WALL,
        height=(0, 2.6),
    )
    adjacent_opening = SimOpening(
        footprint=Polygon(((-1, 0), (-1, 0.1), (12, 0.1), (12, 0.0), (-1, 0.0))),
        height=(0.1, 0.3),
        separator=wall,
        separator_reference_line=LineString(),
    )
    non_adjacent_opening = SimOpening(
        footprint=Polygon(((-5, 0), (-5, 0.1), (-3, 0.1), (-3, 0.0), (-5, 0.0))),
        height=(0.1, 0.3),
        separator=wall,
        separator_reference_line=LineString(),
    )
    wall.openings = wall.openings | {adjacent_opening, non_adjacent_opening}
    layout.separators.add(wall)
    assert area.wall_surface_area(layout=layout) == pytest.approx(
        4 * 10 * 2.6 - 10 * 0.2
    )

    # add a railing / area_splitter as well
    # should count as 2.6 * 10 = 26sqm
    railing = SimSeparator(
        footprint=Polygon(((-10, 0), (-10, 0.1), (15, 0.1), (15, 0.0), (-5, 0.0))),
        separator_type=SeparatorType.RAILING,
        height=(0, 1.0),
    )
    # should count as 2.6 * 10 = 26sqm
    area_splitter = SimSeparator(
        footprint=Polygon(((-10, 0), (-10, 0.1), (15, 0.1), (15, 0.0), (-5, 0.0))),
        separator_type=SeparatorType.AREA_SPLITTER,
        height=(0, 0.5),
    )
    layout.separators |= {railing, area_splitter}
    assert area.wall_surface_area(layout=layout) == pytest.approx(
        4 * 10 * 2.6 - 10 * 0.2 - 10 * 2.6 - 10 * 2.6
    )
