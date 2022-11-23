from collections import Counter
from unittest.mock import PropertyMock

import pytest
from shapely.geometry import LineString, Polygon, box

from brooks.layout_validations import SimLayoutValidations
from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.models.violation import ViolationType
from brooks.types import SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


@pytest.mark.parametrize(
    "separator_a, separator_b, expected",
    [
        ((0, 0, 3, 2), (0, 0, 3, 2), ViolationType.OPENING_OVERLAPS_MULTIPLE_WALLS),
        ((-2, 0, 0.001, 2), (0, 0, 3, 2), None),
        ((-2, 0, 0, 2), (0, 0, 3, 2), None),
    ],
)
def test_validate_opening_overlaps(mocker, separator_a, separator_b, expected):
    separator_a = SimSeparator(
        footprint=box(*separator_a), separator_type=SeparatorType.WALL
    )
    separator_b = SimSeparator(
        footprint=box(*separator_b), separator_type=SeparatorType.WALL
    )
    mocker.patch.object(
        SimLayout,
        "openings",
        PropertyMock(
            return_value=[
                SimOpening(
                    footprint=box(0, 0, 2, 2),
                    separator=separator_a,
                    height=(1, 1),
                    separator_reference_line=get_center_line_from_rectangle(
                        polygon=separator_a.footprint
                    )[0],
                )
            ]
        ),
    )
    layout = SimLayout(separators={separator_b, separator_a})
    violations = list(
        SimLayoutValidations.validate_opening_overlaps_only_one_separator(layout=layout)
    )
    if expected:
        assert violations[0].violation_type == expected
    else:
        assert not violations


@pytest.mark.parametrize(
    "opening_a, opening_b, expected",
    [
        ((0, 0, 2, 2), (-2, 0, 0, 2), None),
        (
            (-2, 0, 0, 2),
            (-0.5, 0, 2, 2),
            ViolationType.OPENING_OVERLAPS_ANOTHER_OPENING,
        ),
    ],
)
def test_validate_openings_do_not_overlap(mocker, opening_a, opening_b, expected):
    separator = SimSeparator(footprint=Polygon(), separator_type=SeparatorType.WALL)
    mocker.patch.object(
        SimLayout,
        "openings",
        PropertyMock(
            return_value=[
                SimOpening(
                    footprint=box(*opening_a),
                    separator=separator,
                    height=(1, 1),
                    separator_reference_line=LineString(),
                ),
                SimOpening(
                    footprint=box(*opening_b),
                    separator=separator,
                    height=(1, 1),
                    separator_reference_line=LineString(),
                ),
            ]
        ),
    )
    violations = list(
        SimLayoutValidations.validate_openings_overlap_openings(layout=SimLayout())
    )
    if expected:
        assert violations
        assert violations[0].violation_type == expected
    else:
        assert not violations


@pytest.mark.parametrize(
    "feature_footprint, expected",
    [
        (box(10, 10, 11, 11), ViolationType.FEATURE_NOT_ASSIGNED),
        (box(0, 0, 2, 2), ViolationType.FEATURE_NOT_ASSIGNED),
        (box(0, 0, 0.5, 0.5), None),
    ],
)
def test_validate_check_features_belong_to_area(feature_footprint: Polygon, expected):
    layout = SimLayout(
        spaces={
            SimSpace(
                footprint=box(0, 0, 2, 2),
                areas={
                    SimArea(footprint=box(0, 0, 2, 1)),
                    SimArea(footprint=box(0, 1, 2, 2)),
                },
            )
        }
    )
    layout.all_processed_features = {SimFeature(footprint=feature_footprint)}
    errors = list(SimLayoutValidations.check_features_belong_to_area(layout=layout))
    if expected:
        assert len(errors) == 1
        assert errors[0].type == expected.name
    else:
        assert not errors


def test_validate_accessible_space(annotations_accessible_areas):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_accessible_areas),
        scaled=True,
    )
    errors = list(SimLayoutValidations.validate_accessible_spaces(layout=layout))
    assert Counter([error.violation_type.name for error in errors]) == {
        ViolationType.SPACE_NOT_ACCESSIBLE.name: 2,
    }
