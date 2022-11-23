import pytest
from pygeos import from_shapely
from shapely.geometry import LineString, box

from brooks import SpaceConnector
from brooks.models import SimArea, SimOpening, SimSeparator
from brooks.types import AreaType, OpeningType, SeparatorType
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


class TestShaftsNearestSpaceConnections:
    @staticmethod
    def test_shafts_nearest_space_connections_accessible_areas(
        annotations_accessible_areas,
    ):
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**annotations_accessible_areas)
        )
        connections = SpaceConnector().shafts_nearest_space_connections(layout=layout)

        assert AreaType.SHAFT in {
            area.type
            for connection in connections
            for space_id in connection
            for area in layout.spaces_by_id[space_id].areas
        }

    @staticmethod
    def test_shafts_nearest_space_connections_no_shaft(annotations_box_data):
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**annotations_box_data)
        )
        assert SpaceConnector().shafts_nearest_space_connections(layout=layout) == []


@pytest.mark.parametrize(
    "separator_reference_line, opening_footprint, expected_num_intersections",
    [
        (
            LineString([(0, 0), (2, 0)]),
            box(0, -0.5, 2, 0),
            2,
        ),
        (
            LineString(
                [(0.5, -0.5), (1.5, -0.5)]
            ),  # An example of line that goes over the lower edge of the space
            box(0, -0.5, 2, 0),
            2,
        ),
        (
            LineString([(0.5, -0.25), (1.5, -0.25)]),  # An example of centerline
            box(0, -0.5, 2, 0),
            2,
        ),
        (
            LineString(
                [(0.5, -0.25), (2, -0.25)]
            ),  # A very short but thick opening/separator still connects both spaces
            box(0.5, -0.5, 0.7, 0),
            2,
        ),
        (
            LineString(
                [(1, -0.49), (1, -0.0001)]
            ),  # a vertical wall, almost touching the areas should not connect both areas
            box(0, -0.5, 2, 0),
            0,
        ),
    ],
)
def test_get_intersecting_spaces_or_areas(
    separator_reference_line,
    opening_footprint,
    expected_num_intersections,
):
    """
    ┌────────┐ (2, 2)
    │        │
    │        │
    │0, 0    │
    └────────┘

    ┌────────┐ (2, -0.5)
    │        │
    │        │
    │        │
    └────────┘
    0, -2
    """
    area_1 = SimArea(footprint=box(0, 0, 2, 2))
    area_2 = SimArea(footprint=box(0, -2, 2, -0.5))
    big_footprint = box(0, -0.5, 2, 0)
    opening = SimOpening(
        footprint=opening_footprint,
        opening_type=OpeningType.DOOR,
        height=(0.0, 2.1),
        separator_reference_line=separator_reference_line,
        separator=SimSeparator(
            footprint=big_footprint, separator_type=SeparatorType.WALL
        ),
    )
    spaces_ordered_list = list({area_1, area_2})
    pygeos_spaces = from_shapely([entity.footprint for entity in spaces_ordered_list])
    intersecting = SpaceConnector().get_intersecting_spaces_or_areas(
        opening=opening,
        pygeos_spaces=pygeos_spaces,
        spaces_or_areas_list=spaces_ordered_list,
    )
    assert len(intersecting) == expected_num_intersections


def test_get_connected_spaces_using_doors(
    react_planner_background_image_full_plan,
):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**react_planner_background_image_full_plan),
        scaled=True,
    )
    (_, doors_not_connected,) = SpaceConnector.get_connected_spaces_using_doors(
        doors=layout.openings_by_type[OpeningType.DOOR],
        spaces_or_areas=layout.areas,
    )
    assert not doors_not_connected
    (_, window_not_connected,) = SpaceConnector.get_connected_spaces_using_doors(
        doors=layout.openings_by_type[OpeningType.WINDOW],
        spaces_or_areas=layout.areas,
    )
    # There is an additional window that is facing a balcony
    assert len(layout.openings_by_type[OpeningType.WINDOW]) == 4
    assert len(window_not_connected) == 3
