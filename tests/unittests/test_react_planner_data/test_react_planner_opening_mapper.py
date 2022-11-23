import pytest
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from brooks.layout_validations import SimLayoutValidations
from brooks.models import SimSeparator
from brooks.types import SeparatorType
from common_utils.exceptions import CorruptedAnnotationException
from dufresne.linestring_add_width import (
    LINESTRING_EXTENSION,
    add_width_to_linestring_improved,
)
from handlers.editor_v2.editor_v2_element_mapper import (
    ReactPlannerOpeningMapper,
    ReactPlannerToBrooksMapper,
)
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerDoorSweepingPoints,
    ReactPlannerGeomProperty,
    ReactPlannerHole,
    ReactPlannerHoleHeights,
    ReactPlannerHoleProperties,
    ReactPlannerName,
    ReactPlannerType,
)


class TestReactPlannerOpeningMapper:
    @pytest.fixture
    def hole(self, request):
        opening_name, opening_type, sweeping_points = request.param

        return ReactPlannerHole(
            line="a line",
            name=opening_name.value,
            type=opening_type.value,
            properties=ReactPlannerHoleProperties(
                heights=ReactPlannerHoleHeights(),
                length=ReactPlannerGeomProperty(value=80),
                width=ReactPlannerGeomProperty(value=15),
                altitude=ReactPlannerGeomProperty(value=200),
            ),
            coordinates=[[[0, 0], [0, 3], [1, 3], [1, 0], [0, 0]]],
            door_sweeping_points=ReactPlannerDoorSweepingPoints(**sweeping_points)
            if sweeping_points
            else None,
        )

    @staticmethod
    @pytest.mark.parametrize(
        "hole",
        [
            (
                ReactPlannerName.DOOR,
                ReactPlannerType.DOOR,
                {"angle_point": [0, 0], "closed_point": [0, 1], "opened_point": [1, 0]},
            ),
            (
                ReactPlannerName.ENTRANCE_DOOR,
                ReactPlannerType.ENTRANCE_DOOR,
                {
                    "angle_point": [1, 0],
                    "closed_point": [0, 0],
                    "opened_point": [-1, 1],
                },
            ),
        ],
        indirect=["hole"],
    )
    def test_get_layout_winged_doors_should_have_sweeping_points(hole):
        separators_by_id = {
            hole.line: SimSeparator(
                separator_type=SeparatorType.WALL, footprint=box(0, 0, 5, 1)
            )
        }
        opening = ReactPlannerOpeningMapper.get_opening(
            hole=hole,
            separators_by_id=separators_by_id,
            post_processed=False,
            separator_reference_line=LineString(),
        )
        sweeping_points = [
            Point(hole.door_sweeping_points.angle_point),
            Point(hole.door_sweeping_points.closed_point),
            Point(hole.door_sweeping_points.opened_point),
        ]
        assert sweeping_points == opening.sweeping_points

    @staticmethod
    @pytest.mark.parametrize(
        "hole",
        [
            (ReactPlannerName.SLIDING_DOOR, ReactPlannerType.SLIDING_DOOR, {}),
            (ReactPlannerName.WINDOW, ReactPlannerType.WINDOW, {}),
        ],
        indirect=["hole"],
    )
    def test_get_opening_should_not_set_sweeping_points(hole):
        separators_by_id = {
            hole.line: SimSeparator(
                separator_type=SeparatorType.WALL, footprint=box(0, 0, 5, 1)
            )
        }
        opening = ReactPlannerOpeningMapper.get_opening(
            hole=hole,
            separators_by_id=separators_by_id,
            post_processed=False,
            separator_reference_line=LineString(),
        )
        assert opening.sweeping_points is None

    @staticmethod
    @pytest.mark.parametrize(
        "hole_name, hole_type",
        [
            (ReactPlannerName.ENTRANCE_DOOR, ReactPlannerType.ENTRANCE_DOOR),
            (ReactPlannerName.DOOR, ReactPlannerType.DOOR),
        ],
    )
    def test_get_opening_raise_exception_if_sweeping_points_for_winged_doors_are_missing(
        hole_type, hole_name
    ):
        with pytest.raises(
            CorruptedAnnotationException,
            match="has no sweeping points set.",
        ):
            ReactPlannerHole(
                line="a line",
                name=hole_name.value,
                type=hole_type.value,
                properties=ReactPlannerHoleProperties(
                    heights=ReactPlannerHoleHeights(lower_edge=0, upper_edge=0),
                    length=ReactPlannerGeomProperty(value=80),
                    width=ReactPlannerGeomProperty(value=15),
                    altitude=ReactPlannerGeomProperty(value=200),
                ),
                coordinates=[[[0, 0], [0, 3], [1, 3], [1, 0], [0, 0]]],
            )

    @staticmethod
    def test_react_planner_postprocessed_unique_footprint_doors(
        react_planner_background_image_full_plan,
    ):
        """When postprocessing the walls, the doors could be not connecting anymore the spaces"""
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_background_image_full_plan
            ),
            scaled=True,
            post_processed=True,
        )
        separators = unary_union(
            [s.footprint for s in layout.separators if s.type == SeparatorType.WALL]
        )
        assert isinstance(separators, Polygon)
        openings = unary_union([o.footprint for o in layout.openings])
        separators_wo_openings = separators.difference(openings)

        assert separators_wo_openings.area == pytest.approx(17.28, abs=1e-3)
        errors = list(SimLayoutValidations.validate_door_connects_areas(layout=layout))
        assert not errors

    @staticmethod
    def test_post_process_opening_return_biggest_if_opening_creates_multipolygon():
        opening_line = LineString(((0, 0), (1, 5)))
        opening_polygon = add_width_to_linestring_improved(
            line=opening_line, width=2, extension_type=LINESTRING_EXTENSION.SYMMETRIC
        )
        expected = ReactPlannerOpeningMapper.post_process_opening(
            opening_polygon=opening_polygon,
            separator_post_processed=MultiPolygon(
                [
                    box(minx=0, maxx=1, miny=0, maxy=2.5),
                    box(minx=0, maxx=1, miny=3, maxy=5),
                ]
            ),
        )
        assert expected.area == 2.5

    @staticmethod
    def test_post_process_opening_raises_exception_if_no_overlap():
        with pytest.raises(CorruptedAnnotationException):
            ReactPlannerOpeningMapper.post_process_opening(
                opening_polygon=box(-1, -1, 0, 0),
                separator_post_processed=box(minx=0, maxx=1, miny=5, maxy=6),
            )

    @staticmethod
    @pytest.mark.parametrize(
        "lower_edge,upper_edge,expected_height",
        [
            (None, None, (0, 2.8)),
            (None, 1.6, (0, 1.6)),
            (0.5, None, (0.5, 2.8)),
            (0.5, 1.6, (0.5, 1.6)),
            (0.0, 1.8, (0.0, 1.8)),
        ],
    )
    def test_individual_opening_heights(
        mocker, lower_edge, upper_edge, expected_height
    ):
        hole = ReactPlannerHole(
            line="fake id",
            coordinates=[],
            type=ReactPlannerType.DOOR.value,
            name=ReactPlannerName.DOOR.value,
            properties=ReactPlannerHoleProperties(
                width=ReactPlannerGeomProperty(value=1),
                altitude=ReactPlannerGeomProperty(value=0),
                length=ReactPlannerGeomProperty(value=0),
                heights=ReactPlannerHoleHeights(
                    lower_edge=lower_edge, upper_edge=upper_edge
                ),
            ),
            door_sweeping_points=[],
        )

        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            "get_element_polygon",
            return_value=box(0, 0, 1, 1),
        )
        from handlers.editor_v2 import editor_v2_element_mapper

        mocker.patch.object(
            editor_v2_element_mapper,
            "get_default_element_height_range",
            return_value=(0, 2.8),
        )
        opening = ReactPlannerOpeningMapper.get_opening(
            hole=hole,
            separator_reference_line=None,
            separators_by_id={hole.line: None},
            post_processed=False,
            default_element_heights=None,
        )
        assert opening.height == pytest.approx(expected_height, abs=1e-7)
