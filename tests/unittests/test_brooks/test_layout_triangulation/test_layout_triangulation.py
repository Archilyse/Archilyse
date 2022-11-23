import json
from copy import copy

import pytest
from numpy import array
from shapely import wkt
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from simulations.view.meshes import GeoreferencingTransformation, LayoutTriangulator
from simulations.view.meshes.triangulation3d import LayoutTriangulatorClabExtrusion
from tests.unittests.test_brooks.test_layout_triangulation.utils import (
    create_pseudo_slice_view,
)


class TestLayoutTriangulatorClabExtrusion:
    @pytest.fixture
    def layout_custom_heights(self, custom_element_heights) -> SimLayout:
        element_heights = copy(custom_element_heights)
        element_heights[SeparatorType.WALL] = (0, 42)
        area_1 = SimArea(
            footprint=box(0, 0, 10, 5),
            area_type=AreaType.ROOM,
            height=element_heights["GENERIC_SPACE_HEIGHT"],
        )
        separator1 = SimSeparator(
            footprint=box(0, -0.5, 10, 0),
            separator_type=SeparatorType.WALL,
            height=element_heights[SeparatorType.WALL],
        )
        separator2 = SimSeparator(
            footprint=box(10, -0.5, 10.5, 5.5),
            separator_type=SeparatorType.WALL,
            height=element_heights[SeparatorType.WALL],
        )
        separator3 = SimSeparator(
            footprint=box(0, 5, 10, 5.5),
            separator_type=SeparatorType.WALL,
            height=element_heights[SeparatorType.WALL],
        )
        separator4 = SimSeparator(
            footprint=box(-0.5, -0.5, 0, 5.5),
            separator_type=SeparatorType.WALL,
            height=element_heights[SeparatorType.WALL],
        )
        door1 = SimOpening(
            footprint=box(2, -0.5, 2.8, 0),
            separator=separator1,
            height=element_heights[OpeningType.DOOR],
            opening_type=OpeningType.DOOR,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )
        door2 = SimOpening(
            footprint=box(4, 5, 4.8, 5.5),
            separator=separator3,
            height=(7, 8),
            opening_type=OpeningType.DOOR,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator3.footprint
            )[0],
        )
        window1 = SimOpening(
            footprint=box(5.5, -0.5, 8.5, 0),
            separator=separator1,
            height=element_heights[OpeningType.WINDOW],
            opening_type=OpeningType.WINDOW,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )
        window2 = SimOpening(
            footprint=box(5.5, 5, 8.5, 5.5),
            separator=separator3,
            height=(33, 44),
            opening_type=OpeningType.WINDOW,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator3.footprint
            )[0],
        )

        separator1.add_opening(door1)
        separator1.add_opening(window1)
        separator3.add_opening(door2)
        separator3.add_opening(window2)
        space = SimSpace(footprint=box(0, 0, 10, 5))
        space.add_area(area_1)
        layout = SimLayout(
            separators={separator1, separator2, separator3, separator4},
            spaces={space},
            default_element_heights=element_heights,
        )
        return layout

    @pytest.fixture
    def layout_with_1_room_entrance_door_and_window(self) -> SimLayout:
        area_1 = SimArea(footprint=box(0, 0, 10, 5), area_type=AreaType.ROOM)
        separator1 = SimSeparator(
            footprint=box(0, -0.5, 10, 0),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator2 = SimSeparator(
            footprint=box(10, -0.5, 10.5, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator3 = SimSeparator(
            footprint=box(0, 5, 10, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator4 = SimSeparator(
            footprint=box(-0.5, -0.5, 0, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        door = SimOpening(
            footprint=box(2, -0.5, 2.8, 0),
            separator=separator1,
            height=(0, 2.0),
            opening_type=OpeningType.ENTRANCE_DOOR,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )

        window = SimOpening(
            footprint=box(5.5, -0.5, 8.5, 0),
            separator=separator1,
            height=(0.5, 2.4),
            opening_type=OpeningType.WINDOW,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )

        separator1.add_opening(door)
        separator1.add_opening(window)
        space = SimSpace(footprint=box(0, 0, 10, 5))
        space.add_area(area_1)
        layout = SimLayout(
            separators={separator1, separator2, separator3, separator4}, spaces={space}
        )
        return layout

    @pytest.fixture
    def layout_with_void_area(self) -> SimLayout:
        area_1 = SimArea(footprint=box(0, 0, 5, 5), area_type=AreaType.ROOM)
        area_2 = SimArea(footprint=box(5, 0, 10, 5), area_type=AreaType.VOID)
        separator1 = SimSeparator(
            footprint=box(0, -0.5, 10, 0),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator2 = SimSeparator(
            footprint=box(10, -0.5, 10.5, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator3 = SimSeparator(
            footprint=box(0, 5, 10, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        separator4 = SimSeparator(
            footprint=box(-0.5, -0.5, 0, 5.5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        area_splitter = SimSeparator(
            footprint=box(4.95, 0, 5.05, 5),
            separator_type=SeparatorType.AREA_SPLITTER,
            height=(0, 2.6),
        )
        window = SimOpening(
            footprint=box(5.5, -0.5, 8.5, 0),
            separator=separator1,
            height=(0.5, 2.4),
            opening_type=OpeningType.WINDOW,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )
        window2 = SimOpening(
            footprint=box(0.5, -0.5, 2.5, 0),
            separator=separator1,
            height=(0.5, 2.4),
            opening_type=OpeningType.WINDOW,
            separator_reference_line=get_center_line_from_rectangle(
                polygon=separator1.footprint
            )[0],
        )
        separator1.add_opening(window)
        separator1.add_opening(window2)
        space = SimSpace(footprint=box(0, 0, 10, 5))
        space.areas = {area_1, area_2}
        layout = SimLayout(
            separators={separator1, separator2, separator3, separator4, area_splitter},
            spaces={space},
        )
        return layout

    def test_triangulate_layout_custom_heights(self, mocker, layout_custom_heights):
        georef_transformation = GeoreferencingTransformation()
        georef_transformation.set_translation(x=0, y=0, z=0)
        georef_transformation.set_swap_dimensions(0, 1)

        add_window_spy = mocker.spy(LayoutTriangulatorClabExtrusion, "_add_window")
        add_door_spy = mocker.spy(LayoutTriangulatorClabExtrusion, "_add_door")
        add_separator_spy = mocker.spy(
            LayoutTriangulatorClabExtrusion, "_add_separator"
        )
        add_floors_and_ceiling_spy = mocker.spy(
            LayoutTriangulatorClabExtrusion, "_add_floors_and_ceilings"
        )

        level_baseline = 1337
        exp_ceiling_baseline = 1337 + 42

        LayoutTriangulatorClabExtrusion(
            layout=layout_custom_heights,
            georeferencing_parameters=georef_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        ).create_layout_triangles(layouts_upper_floor=[], level_baseline=level_baseline)

        assert {
            (
                call.kwargs["floor"],
                call.kwargs["window_lower_edge"],
                call.kwargs["window_upper_edge"],
                call.kwargs["ceiling"],
            )
            for call in add_window_spy.call_args_list
        } == {
            (
                level_baseline,
                level_baseline + window.height[0],
                level_baseline + window.height[1],
                exp_ceiling_baseline,
            )
            for window in layout_custom_heights.openings_by_type[OpeningType.WINDOW]
        }

        assert {
            (
                call.kwargs["floor"],
                call.kwargs["door_upper_edge"],
                call.kwargs["ceiling"],
            )
            for call in add_door_spy.call_args_list
        } == {
            (level_baseline, level_baseline + door.height[1], exp_ceiling_baseline)
            for door in layout_custom_heights.doors
        }

        assert {
            (
                call.kwargs["floor"],
                call.kwargs["ceiling"],
            )
            for call in add_separator_spy.call_args_list
        } == {(level_baseline, exp_ceiling_baseline)}

        assert {
            (
                call.kwargs["floor"],
                call.kwargs["ceiling"],
            )
            for call in add_floors_and_ceiling_spy.call_args_list
        } == {(level_baseline, exp_ceiling_baseline)}

    def test_triangulation_layout_with_void_area(
        self, layout_with_void_area, fixtures_path
    ):

        georef_transformation = GeoreferencingTransformation()
        georef_transformation.set_translation(x=0, y=0, z=0)
        georef_transformation.set_swap_dimensions(0, 1)

        triangles = LayoutTriangulatorClabExtrusion(
            layout=layout_with_void_area,
            georeferencing_parameters=georef_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        ).create_layout_triangles(layouts_upper_floor=[], level_baseline=0)

        actual_bottom_slice = create_pseudo_slice_view(
            triangles=triangles,
            slice_range=(
                -0.5,
                0.5,
            ),
        )

        actual_middle_slice = create_pseudo_slice_view(
            triangles=triangles, slice_range=(1, 2)
        )

        actual_top_slice = create_pseudo_slice_view(
            triangles=triangles, slice_range=(2, 5)
        )

        with fixtures_path.joinpath(
            "layout_triangles_slice_views/void_area_bottom_view.wkt"
        ).open("r") as f:

            expected_bottom_slice = wkt.load(f)
        with fixtures_path.joinpath(
            "layout_triangles_slice_views/void_area_middle_view.wkt"
        ).open("r") as f:
            expected_middle_slice = wkt.load(f)
        with fixtures_path.joinpath(
            "layout_triangles_slice_views/void_area_top_view.wkt"
        ).open("r") as f:
            expected_top_slice = wkt.load(f)

        assert (
            expected_bottom_slice.symmetric_difference(actual_bottom_slice).area
            < 0.0001
        )

        assert (
            expected_middle_slice.symmetric_difference(actual_middle_slice).area
            < 0.0001
        )

        assert expected_top_slice.symmetric_difference(actual_top_slice).area < 0.0001

    def test_triangulation_layout_if_upper_floor_has_void_area(
        self,
        layout_with_1_room_entrance_door_and_window,
        layout_with_void_area,
        fixtures_path,
    ):

        georef_transformation = GeoreferencingTransformation()
        georef_transformation.set_translation(x=0, y=0, z=0)
        georef_transformation.set_swap_dimensions(0, 1)

        triangles = LayoutTriangulatorClabExtrusion(
            layout=layout_with_1_room_entrance_door_and_window,
            georeferencing_parameters=georef_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        ).create_layout_triangles(
            layouts_upper_floor=[layout_with_void_area], level_baseline=0
        )

        actual_bottom_slice = create_pseudo_slice_view(
            triangles=triangles,
            slice_range=(
                -0.5,
                0.5,
            ),
        )

        actual_middle_slice = create_pseudo_slice_view(
            triangles=triangles, slice_range=(1, 2)
        )

        actual_top_slice = create_pseudo_slice_view(
            triangles=triangles, slice_range=(2, 5)
        )

        with fixtures_path.joinpath(
            "layout_triangles_slice_views/upper_floor_has_void_bottom_view.wkt"
        ).open("r") as f:

            expected_bottom_slice = wkt.load(f)
        with fixtures_path.joinpath(
            "layout_triangles_slice_views/upper_floor_has_void_middle_view.wkt"
        ).open("r") as f:
            expected_middle_slice = wkt.load(f)
        with fixtures_path.joinpath(
            "layout_triangles_slice_views/upper_floor_has_void_top_view.wkt"
        ).open("r") as f:
            expected_top_slice = wkt.load(f)

        assert (
            expected_bottom_slice.symmetric_difference(actual_bottom_slice).area
            < 0.0001
        )

        assert (
            expected_middle_slice.symmetric_difference(actual_middle_slice).area
            < 0.0001
        )

        assert expected_top_slice.symmetric_difference(actual_top_slice).area < 0.0001


class TestLayoutTriangulator:
    @pytest.mark.parametrize(
        "area_type,expected_triangle_num,should_fully_triangulate",
        [(AreaType.ROOM, (212, 3, 3), True), (AreaType.LIGHTWELL, (0,), False)],
    )
    def test_add_floor_and_ceiling(
        self, fixtures_path, area_type, expected_triangle_num, should_fully_triangulate
    ):
        from brooks.models import SimArea
        from simulations.view.meshes import GeoreferencingTransformation

        with fixtures_path.joinpath("geometries/polygon_with_hole.json").open(
            mode="r"
        ) as f:
            base_pol = shape(json.load(f))

        georeferencing_transformation = GeoreferencingTransformation()

        layout_mesh = LayoutTriangulator(
            layout=None,
            georeferencing_parameters=georeferencing_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        )

        layout_mesh._add_floors_and_ceilings(
            areas={SimArea(footprint=base_pol, area_type=area_type)},
            floor=5.8,
            ceiling=8.4,
            layouts_upper_floor=[],
        )

        triangles = array(layout_mesh._triangles.tolist())
        assert triangles.shape == expected_triangle_num

        triangles_pol = unary_union([Polygon(t) for t in triangles])

        # Checks area of triangles is similar to the polygon.
        # Buffered as triangulations currently buffers polygons slightly
        # It should be 2 times, but unary_union works on 2D so we get a 2D polygon
        expected_triangulation_area = (
            base_pol.buffer(0.125, cap_style=3, join_style=2, mitre_limit=2).area
            if should_fully_triangulate
            else 0
        )
        assert triangles_pol.area == pytest.approx(expected_triangulation_area)

    @staticmethod
    @pytest.mark.parametrize(
        "area_type, expected",
        [(AreaType.LIGHTWELL, False), (AreaType.ROOM, True)],
    )
    def test_add_floor_and_ceiling_no_ceiling_case(mocker, area_type, expected):
        """Regression test to make sure we control the cases where the upper floor has no floor and we don't try
        to add an empty ceiling"""
        mocker.patch.object(LayoutTriangulator, "_add_floor")
        mocked_add_ceiling = mocker.patch.object(LayoutTriangulator, "_add_ceiling")
        polygon = box(0, 0, 10, 10)
        LayoutTriangulator(
            layout=SimLayout(),
            georeferencing_parameters=GeoreferencingTransformation(),
        )._add_floors_and_ceilings(
            areas={SimArea(footprint=polygon, area_type=AreaType.ROOM)},
            floor=0,
            ceiling=0,
            layouts_upper_floor=[
                SimLayout(
                    spaces={
                        SimSpace(
                            areas={SimArea(footprint=polygon, area_type=area_type)},
                            footprint=polygon,
                        )
                    }
                )
            ],
        )
        assert bool(mocked_add_ceiling.call_count) == expected

    @pytest.fixture
    def area_ids(self):
        return [
            "f6203451-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f6203423-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f620344b-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f6203445-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f620341a-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f6203460-fc8c-11e9-a875-9cb6d0d2e5c9",
            "f6203432-fc8c-11e9-a875-9cb6d0d2e5c9",
        ]

    @pytest.fixture
    def plan_info(self):
        return {
            "image_width": 2479,
            "georef_rot_x": 1227.8136702813,
            "georef_rot_angle": 236.5,
            "annotation_finished": True,
            "georef_scale": 0.955865678666637,
            "georef_x": 8.492805708055917,
            "default_window_lower_edge": 0.5,
            "id": 868,
            "image_height": 3508,
            "georef_rot_y": -1744.19637852321,
            "created": "2019-10-29T08:20:35.752457",
            "georef_y": 47.39460630775943,
            "building_id": 332,
            "site_id": 164,
            "image_mime_type": "image/jpeg",
            "default_wall_height": 2.6,
            "image_hash": "dd6908fd3b0ce3198ea076de8355f0d3bbabb32b0a08c78b9f74cc91a11870c6",
            "default_window_upper_edge": 2.4,
            "updated": "2019-11-01T09:49:56.928779",
            "default_ceiling_slab_height": 0.3,
        }

    def test_create_layout_mesh(self, annotations_plan_3881, area_ids, plan_info):
        from simulations.view.meshes import GeoreferencingTransformation

        georeferencing_transformation = GeoreferencingTransformation()

        unit_layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(**annotations_plan_3881)
        )

        layout_mesh = LayoutTriangulator(
            layout=unit_layout,
            georeferencing_parameters=georeferencing_transformation,
            classification_scheme=UnifiedClassificationScheme(),
        )

        triangles = sorted(
            layout_mesh.create_layout_triangles(
                layouts_upper_floor=[], level_baseline=0
            ).tolist(),
            key=lambda x: x[0][0],
        )
        assert isinstance(triangles[0][0][0], float)
