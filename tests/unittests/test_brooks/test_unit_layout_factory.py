import pytest
from shapely.geometry import LineString, box

from brooks.models import SimLayout, SimOpening, SimSeparator
from brooks.types import SeparatorType
from brooks.unit_layout_factory import UnitLayoutFactory


@pytest.mark.parametrize(
    "separator_polygon, opening_polygon, overlap_threshold, expected_assignment",
    [
        (box(0, 0, 1, 1), box(0, 0, 1, 1), 1.0, True),
        (box(0, 0, 1, 1), box(-0.5, -0.5, 0.5, 0.5), 0.25, True),
        (box(0, 0, 1, 1), box(-0.5, -0.5, 0.5, 0.5), 0.6, False),
    ],
)
def test_copy_opening_to_separator(
    separator_polygon, opening_polygon, overlap_threshold, expected_assignment
):
    """The 2nd and 3rd example are 2 boxes where the overlap is only in one corner, so 1/4 of the separator"""
    separator = SimSeparator(
        footprint=separator_polygon, separator_type=SeparatorType.WALL
    )
    UnitLayoutFactory(plan_layout=SimLayout())._copy_opening_to_separator(
        new_separator=separator,
        opening=SimOpening(
            footprint=opening_polygon,
            height=(0, 3),
            separator=None,
            separator_reference_line=LineString(),
        ),
        overlap_threshold=overlap_threshold,
    )
    assert bool(separator.openings) == expected_assignment
