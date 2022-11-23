from copy import deepcopy
from dataclasses import asdict
from itertools import chain

import pytest
from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString, Point, box
from shapely.ops import unary_union

from brooks import SpaceMaker
from brooks.models import SimSeparator
from brooks.types import SeparatorType
from brooks.utils import get_default_element_lower_edge, get_default_element_upper_edge
from common_utils.constants import LENGTH_SI_UNITS, WALL_BUFFER_BY_SI_UNIT
from dufresne.linestring_add_width import (
    LINESTRING_EXTENSION,
    add_width_to_linestring_improved,
)
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData, ReactPlannerType


class TestSpaceMaker:
    @staticmethod
    @pytest.mark.parametrize(
        "splitter_coords, num_areas_expected, num_spaces_expected",
        [
            (
                [
                    [
                        [400, 430],
                        [405, 430],
                        [405, 660],
                        [400, 660],
                        [400, 430],
                    ]
                ],
                2,
                1,
            ),
            ([], 1, 1),
        ],
    )
    def test_space_maker_with_area_splitters(
        react_data_valid_square_space_with_entrance_door,
        splitter_coords,
        num_areas_expected,
        num_spaces_expected,
    ):
        if splitter_coords:
            splitter = ReactPlannerElementFactory.get_line_from_coordinates_and_width(
                coordinates=splitter_coords,
                width_in_cm=999,
                line_type=ReactPlannerType.AREA_SPLITTER,
            )
            react_data_valid_square_space_with_entrance_door = deepcopy(
                react_data_valid_square_space_with_entrance_door
            )
            react_data_valid_square_space_with_entrance_door["layers"]["layer-1"][
                "lines"
            ][splitter.id] = asdict(splitter)

        layout = ReactPlannerToBrooksMapper().get_layout(
            planner_elements=ReactPlannerData(
                **react_data_valid_square_space_with_entrance_door
            ),
            scaled=True,
        )

        assert len(layout.spaces) == num_spaces_expected
        assert (
            len([area for space in layout.spaces for area in space.areas])
            == num_areas_expected
        )
        assert (
            pytest.approx(sum(space.footprint.area for space in layout.spaces))
            == 5.18139
        )
        assert all(
            space_or_area.angle == 0
            for space_or_area in chain(layout.spaces, layout.areas)
        )

    @staticmethod
    @pytest.mark.parametrize(
        "annotations, num_areas_expected, num_spaces_expected",
        [
            (
                pytest.lazy_fixture("react_planner_background_image_full_plan"),
                12,
                12,
            ),
            (
                pytest.lazy_fixture("annotations_plan_2494"),
                49,
                46,
            ),
        ],
    )
    def test_space_maker_entire_plan(
        annotations, num_areas_expected, num_spaces_expected
    ):
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**annotations), scaled=True
        )

        assert len(layout.spaces) == num_spaces_expected
        assert (
            len([area for space in layout.spaces for area in space.areas])
            == num_areas_expected
        )
        # check the features assigned to spaces and areas are the same
        assert (
            len(layout.features)
            == sum(
                [len(area.features) for space in layout.spaces for area in space.areas]
            )
            == sum([len(space.features) for space in layout.spaces])
        )

        for space in layout.spaces:
            assert pytest.approx(space.footprint.area, rel=0.001) == sum(
                area.footprint.area for area in space.areas
            )

    @staticmethod
    def test_get_spaces_from_separators_square():
        point_a = Point(0, 0)
        point_b = Point(5, 0)
        point_c = Point(5, 5)
        point_d = Point(0, 5)
        width = 1.0
        line_a = add_width_to_linestring_improved(
            line=LineString((point_a, point_b)), width=width
        )
        line_b = add_width_to_linestring_improved(
            line=LineString((point_b, point_c)), width=width
        )
        line_c = add_width_to_linestring_improved(
            line=LineString((point_c, point_d)), width=width
        )
        line_d = add_width_to_linestring_improved(
            line=LineString((point_d, point_a)), width=width
        )
        separators = [line_a, line_b, line_c, line_d]
        polygon = SpaceMaker.get_spaces_from_separators(separators=separators)
        assert polygon.area == 16.0

    @staticmethod
    def test_get_spaces_from_separators_triangle():
        point_a = Point(0, 0)
        point_b = Point(5, 0)
        point_c = Point(2.5, 2.5)
        width = 1.0
        line_a = add_width_to_linestring_improved(
            line=LineString((point_a, point_b)),
            width=width,
            extension_type=LINESTRING_EXTENSION.RIGHT,
        )
        line_b = add_width_to_linestring_improved(
            line=LineString((point_b, point_c)),
            width=width,
            extension_type=LINESTRING_EXTENSION.RIGHT,
        )
        line_c = add_width_to_linestring_improved(
            line=LineString((point_c, point_a)),
            width=width,
            extension_type=LINESTRING_EXTENSION.RIGHT,
        )
        separators = [line_a, line_b, line_c]
        polygon = SpaceMaker.get_spaces_from_separators(separators=separators)
        assert polygon.area == 2.5 * 5.0 / 2.0

    @staticmethod
    @pytest.mark.parametrize(
        "precision_difference, expected_spaces",
        [(1e-6, 1), (0.001, 1), (0.01, 0)],
    )
    def test_space_created_despite_precision_gaps_between_walls(
        precision_difference, expected_spaces
    ):
        width = 0.2
        point_a = Point(0, 0)
        point_b1 = Point(0, 5)
        point_b2 = Point(0, 5 + precision_difference)
        point_c1 = Point(5, 5 + precision_difference)
        point_c2 = Point(5, 5)
        point_d = Point(5, 0)
        line_1 = add_width_to_linestring_improved(
            line=LineString((point_a, point_b1)),
            width=width,
            extension_type=LINESTRING_EXTENSION.SYMMETRIC,
        )
        line_2 = add_width_to_linestring_improved(
            line=LineString((point_b2, point_c1)),
            width=width,
            extension_type=LINESTRING_EXTENSION.LEFT,
        )
        line_3 = add_width_to_linestring_improved(
            line=LineString((point_c2, point_d)),
            width=width,
            extension_type=LINESTRING_EXTENSION.SYMMETRIC,
        )
        line_4 = add_width_to_linestring_improved(
            line=LineString((point_d, point_a)),
            width=width,
            extension_type=LINESTRING_EXTENSION.SYMMETRIC,
        )
        separators = {
            SimSeparator(footprint=line, separator_type=SeparatorType.WALL)
            for line in [line_1, line_4, line_3, line_2]
        }

        spaces = SpaceMaker.create_spaces_and_areas(
            separators=separators,
            splitters=set(),
            generic_space_height=[0, 2.6],
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        )
        assert len(spaces) == expected_spaces

    @staticmethod
    @pytest.mark.parametrize(
        "geometry, unwanted_connector",
        [
            ((box(0, 0, 1, 1), box(0, 2, 1, 3)), LineString([(1, 1), (1, 2)])),
        ],
    )
    def test_create_spaces_and_areas_editor_v2_unsafe_should_unroll_space_area_multipolygon(
        geometry, unwanted_connector
    ):
        expected_area = 2.0
        buffer_size = 1e-6
        faulty_space_geometry = unary_union(
            [*geometry, unwanted_connector.buffer(buffer_size)]
        )
        faulty_space_separators = (
            faulty_space_geometry.minimum_rotated_rectangle.buffer(
                0.25, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
            ).difference(faulty_space_geometry)
        )

        assert pytest.approx(2.000002, abs=10**-3) == faulty_space_geometry.area

        output_space = SpaceMaker().create_spaces_and_areas(
            separators={
                SimSeparator(
                    separator_type=SeparatorType.WALL, footprint=faulty_space_separators
                )
            },
            splitters=set(),
            generic_space_height=(
                get_default_element_lower_edge("GENERIC_SPACE_HEIGHT"),
                get_default_element_upper_edge("GENERIC_SPACE_HEIGHT"),
            ),
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        )

        assert len(output_space) == 2
        assert sum(s.footprint.area for s in output_space) == pytest.approx(
            expected=expected_area, abs=0.01
        )
        assert sum(g.area for g in geometry) == expected_area
        assert all(len(s.areas) == 1 for s in output_space)

    @staticmethod
    @pytest.mark.parametrize("geometry", [box(0, 0, 0.001, 0.001)])
    def test_create_spaces_and_areas_editor_v2_unsafe_should_discard_empty_space_polygons(
        geometry,
    ):
        space_separators = geometry.exterior.buffer(
            0.25, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
        ).difference(geometry)
        output_space = SpaceMaker().create_spaces_and_areas(
            separators={
                SimSeparator(
                    separator_type=SeparatorType.WALL, footprint=space_separators
                )
            },
            splitters=set(),
            generic_space_height=(
                get_default_element_lower_edge("GENERIC_SPACE_HEIGHT"),
                get_default_element_upper_edge("GENERIC_SPACE_HEIGHT"),
            ),
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        )
        assert not output_space

    @staticmethod
    @pytest.mark.parametrize(
        "space_geometry, area_splitter_geometry",
        [(box(0, 0, 1, 1), box(0.45, 0.45, 0.55, 0.55))],
    )
    def test_create_spaces_and_areas_editor_v2_unsafe_should_discard_empty_area_polygons(
        space_geometry, area_splitter_geometry
    ):
        space_separators = space_geometry.exterior.buffer(
            0.25, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
        ).difference(space_geometry)
        area_splitters = area_splitter_geometry.exterior.buffer(
            0.5, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
        ).difference(area_splitter_geometry)
        output_spaces = SpaceMaker().create_spaces_and_areas(
            separators={
                SimSeparator(
                    separator_type=SeparatorType.WALL, footprint=space_separators
                )
            },
            splitters={
                SimSeparator(
                    separator_type=SeparatorType.AREA_SPLITTER, footprint=area_splitters
                )
            },
            generic_space_height=(
                get_default_element_lower_edge("GENERIC_SPACE_HEIGHT"),
                get_default_element_upper_edge("GENERIC_SPACE_HEIGHT"),
            ),
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        )
        assert len(output_spaces) == 1
        space, *_ = output_spaces
        # the invalid area footprint from the area splitters is discarded by the SpaceMaker
        assert len(space.areas) == 1
