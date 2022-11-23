import pytest
from shapely.geometry import Polygon, box

from brooks.models import SimArea, SimFeature, SimLayout, SimSpace
from brooks.types import AreaType, FeatureType
from common_utils.exceptions import InvalidShapeException
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


@pytest.mark.parametrize(
    "xy_max, raises, expected_area",
    [
        (1, False, 1),
        (2, False, 4),
        (0, True, None),
    ],
)
def test_get_footprint_no_features_one_pol(xy_max, raises, expected_area):
    def get_footprint_no_features(sp):
        return SimLayout(spaces={sp}).get_footprint_no_features()

    space = SimSpace(footprint=box(0, 0, xy_max, xy_max))
    if raises:
        with pytest.raises(InvalidShapeException):
            get_footprint_no_features(space)
    else:
        pol = get_footprint_no_features(space)

        assert pol.area == pytest.approx(expected_area, abs=10**-2)


@pytest.mark.parametrize(
    "xy_max1, xy_max2, raises, expected_area",
    [
        (0.5, 0.9, True, None),  # Both too small
        (5, 0.1, False, 25),  # Big and small, pick big
        (3, 3, False, 18),  # Both big, return multipol
    ],
)
def test_get_footprint_no_features_multipol2(xy_max1, xy_max2, raises, expected_area):
    def get_footprint_no_features(sps):
        return SimLayout(spaces=sps).get_footprint_no_features()

    space1 = SimSpace(footprint=box(0, 0, xy_max1, xy_max1))
    space2 = SimSpace(footprint=box(10, 10, 10 + xy_max2, 10 + xy_max2))
    if raises:
        with pytest.raises(InvalidShapeException):
            get_footprint_no_features({space1, space2})
    else:
        pol = get_footprint_no_features({space1, space2})

        assert pol.area == pytest.approx(expected_area, abs=10**-1)


@pytest.mark.parametrize(
    "area_types, raises, expected_area",
    [
        ((AreaType.ROOM, AreaType.ROOM, AreaType.ROOM), False, 120),
        ((AreaType.VOID, AreaType.ROOM, AreaType.ROOM), False, 90),
        ((AreaType.VOID, AreaType.ROOM, AreaType.VOID), False, 40.088016),
        # Multipolygon:
        ((AreaType.ROOM, AreaType.VOID, AreaType.ROOM), False, 80.11658),
        ((AreaType.VOID, AreaType.VOID, AreaType.ROOM), False, 50.0905),
        ((AreaType.VOID, AreaType.VOID, AreaType.VOID), True, None),
    ],
)
def test_get_footprint_no_features_multipol3(area_types, raises, expected_area):
    """
    3 areas on a space, like being separated by an area splitter
    ┌─────────────────┬────────────────────┬──────────────────┐
    │                 │                    │                  │
    │                 │                    │                  │
    │        a1       │          a2        │         a3       │
    │                 │                    │                  │
    │                 │                    │                  │
    └─────────────────┴────────────────────┴──────────────────┘
    """

    def get_footprint_no_features(sps):
        return SimLayout(spaces=sps).get_footprint_no_features()

    space = SimSpace(footprint=box(0, 0, 12, 10))
    areas_footprints = [box(0, 0, 3, 10), box(3.01, 0, 7, 10), box(7.01, 0, 12, 10)]
    areas = {
        SimArea(footprint=f, area_type=a_type)
        for f, a_type in zip(areas_footprints, area_types)
    }
    space.areas = areas
    if raises:
        with pytest.raises(InvalidShapeException):
            get_footprint_no_features({space})
    else:
        pol = get_footprint_no_features({space})

        assert pol.area == pytest.approx(expected_area, abs=10**-1)


@pytest.mark.parametrize(
    "area_type,area_percentage",
    [
        (AreaType.SHAFT, 0.5),
        (AreaType.VOID, 0.5),
        (AreaType.ROOM, 1),
    ],
)
def test_get_footprint_no_features_with_shaft_valid(area_type, area_percentage):
    space1 = SimSpace(footprint=box(0, 0, 10, 10))
    space1.add_area(SimArea(footprint=box(0, 0, 5, 10), area_type=AreaType.ROOM))
    space1.add_area(SimArea(footprint=box(5, 0, 10, 10), area_type=area_type))
    footprint = SimLayout(spaces={space1}).get_footprint_no_features()
    assert footprint.area == pytest.approx(
        space1.footprint.area * area_percentage, abs=10**-1
    )


@pytest.mark.parametrize(
    "feature_type, feature_xy_max, expected_area",
    [
        (FeatureType.STAIRS, 9, 100),
        (FeatureType.SINK, 9, 19),
    ],
)
def test_get_footprint_no_features_features_removed(
    feature_type, feature_xy_max, expected_area
):
    space = SimSpace(footprint=box(0, 0, 10, 10))
    area = SimArea(footprint=box(0, 0, 10, 10), area_type=AreaType.ROOM)
    area.features = {
        SimFeature(
            footprint=box(0, 0, feature_xy_max, feature_xy_max),
            feature_type=feature_type,
        )
    }
    space.add_area(area)
    layout = SimLayout(spaces={space})

    pol = layout.get_footprint_no_features()

    assert pol.area == pytest.approx(expected_area, abs=10**-1)


@pytest.mark.parametrize(
    "post_processed",
    [(True,), (False,)],
)
def test_get_footprint_no_features_react_postprocessed_data(
    react_planner_background_image_full_plan,
    post_processed,
):
    footprint = (
        ReactPlannerToBrooksMapper()
        .get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_background_image_full_plan
            ),
            post_processed=post_processed,
            scaled=True,
        )
        .get_footprint_no_features()
    )
    assert isinstance(footprint, Polygon)
    assert footprint.area == pytest.approx(98.35851641893525, abs=10**-3)
    assert footprint.bounds == pytest.approx(
        (8.62783947891, 1.04267807472, 20.9144185359, 13.55253486085),
        abs=10**-3,
    )
