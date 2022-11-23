from itertools import pairwise

import pytest
from deepdiff import DeepDiff
from shapely.affinity import rotate
from shapely.geometry import LineString, box

from brooks.constants import THICKEST_WALL_POSSIBLE_IN_M
from brooks.types import AreaType
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_utils import (
    exclude_polygons_split_by_walls,
    filter_overlapping_or_small_polygons,
    filter_too_big_separators,
    get_area_type_from_room_stamp,
    get_bounding_boxes_for_groups_of_geometries,
    iteratively_merge_by_intersection,
)


def test_get_bounding_boxes_for_groups_of_geometries():
    """
    Case of 2 Kitchen features with a sink. The geometries are all lines making up the boundaries of the sink
    and the boundaries of the whole kitchen element. The returned bounding box should be the outer lines of both kitchens.

     Kitchen Element 2                    Kitchen Element 1
     ..................                   ...................................
     |                |                   |                                 |
     |   ...          |                   |      ...........                |
     |  |   |         |                   |      |          |               |
     |  ....          |                   |      ...........                |
     ..................                   |.................................|

    """

    expected_kitchen_box_1 = box(0, 0, 5, 3)
    expected_kitchen_box_2 = box(-9, 0, -6, 3)

    kitchen_1_boundaries = [
        LineString(coords)
        for coords in pairwise(expected_kitchen_box_1.exterior.coords)
    ]

    sink_1_boundaries = [
        LineString(coords) for coords in pairwise(box(1, 1, 2, 2).exterior.coords)
    ]

    kitchen_2_boundaries = [
        LineString(coords)
        for coords in pairwise(expected_kitchen_box_2.exterior.coords)
    ]

    sink_2_boundaries = [
        LineString(coords) for coords in pairwise(box(-9, 1, -8, 2).exterior.coords)
    ]

    bounding_boxes = sorted(
        get_bounding_boxes_for_groups_of_geometries(
            geometries=kitchen_1_boundaries
            + kitchen_2_boundaries
            + sink_2_boundaries
            + sink_1_boundaries
        ),
        key=lambda box: box.area,
    )
    assert len(bounding_boxes) == 2

    assert bounding_boxes[0].symmetric_difference(expected_kitchen_box_2).area < 0.02
    assert bounding_boxes[1].symmetric_difference(expected_kitchen_box_1).area < 0.02


@pytest.mark.parametrize(
    "room_stamp,expected_area_type",
    [
        ("ZIMMER", AreaType.ROOM),
        ("ZIMMER 1", AreaType.ROOM),
        ("xdshf", None),
        ("wohnen/essen", AreaType.LIVING_DINING),
    ],
)
def test_get_area_type_from_room_stamp(room_stamp, expected_area_type):
    assert get_area_type_from_room_stamp(room_stamp=room_stamp) == expected_area_type


def test_exclude_polygons_split_by_walls():
    """
                    Pol C
                       ┌──┐
    Pol a              │  │
    ┌──┐               │  │
    │  │               │  │
    ├──┼──┬────────────┼──┤
    │  │  │       wall │  │
    └──┼──┼────────────┼──┤
       │  │            └──┘
       └──┘
       Pol b

    It should return the difference with the wall, Pol A will be returned above
    Pol B will be under the wall and Pol C will be returned as only 1 box above the wall
    (biggest part).
    The rotated box will be cut such that its remaining part is not crossing the wall anymore
    """
    wall_polygons = [box(0, 0, 10, 1)]
    rotated_box = rotate(
        geom=box(3, -1, 4, 3),
        angle=30,
    )
    polygons = [box(0, 0, 1, 2), box(1, 1, 2, -1), box(9, -1, 10, 5), rotated_box]
    final_polygons = exclude_polygons_split_by_walls(
        wall_polygons=wall_polygons, polygons=polygons
    )

    assert pytest.approx([x.bounds for x in final_polygons], abs=10**-3) == [
        (0.0, 1.0, 1.0, 2.0),
        (1.0, -1.0, 2.0, 0.0),
        (9.0, 1.0, 10.0, 5.0),
        (
            2.0669872981077804,
            0.5000000000000002,
            4.077350269189626,
            2.9820508075688776,
        ),
    ]


def test_filter_too_big_separators():
    max_wall_cm = THICKEST_WALL_POSSIBLE_IN_M * 100
    separator_polygons = [
        box(0, 0, max_wall_cm, max_wall_cm),
        box(0, 0, max_wall_cm + 1, max_wall_cm + 1),
        box(0, 0, max_wall_cm + 1, max_wall_cm - 1),
        box(0, 0, max_wall_cm - 1, max_wall_cm + 1),
    ]
    final_separators = filter_too_big_separators(separator_polygons=separator_polygons)
    assert len(final_separators) == 3
    for separator in final_separators:
        assert separator.area <= max_wall_cm**2


def test_filter_overlapping_or_small_polygons():
    polygons = [box(0, 0, 50, 10)]
    for angle in range(15, 60, 15):
        polygons.append(rotate(geom=box(0, 0, 10, 10), angle=angle))

    filtered_pols = filter_overlapping_or_small_polygons(
        polygons=polygons, minimum_size=5 * 5, condition="within"
    )
    assert len(filtered_pols) == 2
    # Only the one that is rotated 60 degrees remains as it passes the 10% area check
    assert not DeepDiff(
        {filtered.bounds for filtered in filtered_pols},
        {
            (0.0, 0.0, 50.0, 10.0),
            (
                -2.0710678118654746,
                -2.071067811865475,
                12.071067811865476,
                12.071067811865476,
            ),
        },
        ignore_order=True,
        significant_digits=3,
    )


def test_iteratively_merge_by_intersection():
    polygons = [
        box(0, 0, 2, 2),
        box(1.8, -1, 3.8, 1),
        box(3.6, 0, 5, 2),
    ]
    merged_polygons = iteratively_merge_by_intersection(
        polygons=polygons, intersection_size=0.1
    )
    assert len(merged_polygons) == 1
    assert pytest.approx(merged_polygons[0].bounds, abs=10**-3) == (
        -1.1275471698113206,
        -2.089056603773585,
        5.362264150943396,
        3.0075471698113203,
    )
