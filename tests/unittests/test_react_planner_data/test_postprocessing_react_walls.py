import json
from typing import List

import pytest
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box, shape
from shapely.geometry.base import GeometrySequence
from shapely.ops import unary_union

from brooks.layout_validations import SimLayoutValidations
from brooks.types import SeparatorType
from dufresne.linestring_add_width import add_width_to_linestring_improved
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from handlers.editor_v2.wall_postprocessor import (
    ReactPlannerPostprocessor,
    extend_geometry_to_fill_gap_to_another_geom,
)


@pytest.fixture
def mock_properties(mocker):
    def _mock_properties(
        wall_a,
        wall_b,
        vertex_a,
        vertex_b,
        vertex_c,
    ):
        mocker.patch.object(
            ReactPlannerPostprocessor,
            "polygons_by_type_and_id",
            mocker.PropertyMock(
                return_value={SeparatorType.WALL: {"line_1": wall_a, "line_2": wall_b}}
            ),
        )
        mocker.patch.object(
            ReactPlannerPostprocessor,
            "vertices_by_type_and_id",
            mocker.PropertyMock(
                return_value={
                    SeparatorType.WALL: {
                        "line_1": [vertex_a, vertex_b],
                        "line_2": [vertex_b, vertex_c],
                    }
                }
            ),
        )

    return _mock_properties


class TestPostprocessingReactData:
    @staticmethod
    @pytest.mark.parametrize(
        "annotations, annotation_type, expected_areas, expected_coords, expected_interiors",
        (
            [
                pytest.lazy_fixture("react_planner_floorplan_annotation_w_errors"),
                SeparatorType.WALL,
                [274734.97],
                [29],
                [2],
            ],
            [
                pytest.lazy_fixture("react_planner_floorplan_annotation_w_errors"),
                SeparatorType.RAILING,
                [24679.28],
                [13],
                [0],
            ],
            [
                pytest.lazy_fixture("react_planner_background_image_one_unit"),
                SeparatorType.WALL,
                [89311.50],
                [25],
                [5],
            ],
            [
                pytest.lazy_fixture("react_planner_background_image_one_unit"),
                SeparatorType.RAILING,
                [1948.527, 5072.670],
                [33, 10],
                [0, 0],
            ],
        ),
    )
    def test_postprocess_react_data_new_approach_floorplan(
        mocker,
        annotations,
        annotation_type,
        expected_areas,
        expected_coords,
        expected_interiors,
    ):
        get_line_ids_spy = mocker.spy(
            ReactPlannerPostprocessor, "get_line_ids_from_constructed_polygons"
        )
        (new_polygons, _,) = ReactPlannerPostprocessor(
            data=ReactPlannerData(**annotations)
        ).post_process_react_planner_separator_type(separator_type=annotation_type)
        geoms_passed_to_method = get_line_ids_spy.mock_calls[0].kwargs["polygons"]
        assert isinstance(geoms_passed_to_method, GeometrySequence)
        assert isinstance(new_polygons, MultiPolygon)
        new_polygons = sorted(new_polygons.geoms, key=lambda x: x.area)
        for polygon in new_polygons:
            assert polygon.is_valid
        assert len(new_polygons) == len(expected_areas)
        for (
            new_polygon,
            expected_area,
            expected_coord,
            expected_interior,
        ) in zip(new_polygons, expected_areas, expected_coords, expected_interiors):
            assert new_polygon.area == pytest.approx(expected_area, abs=0.1)
            assert len(new_polygon.exterior.coords[:]) == expected_coord
            # It should only have 3 interiors really, there is a dot in the middle which shouldn't be there
            assert len(new_polygon.interiors) == expected_interior

    @staticmethod
    def test_post_processed_layout(
        react_planner_background_image_one_unit,
    ):
        layout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=ReactPlannerData(
                **react_planner_background_image_one_unit
            ),
            scaled=False,
            post_processed=True,
        )
        assert len(layout.openings) == 10
        assert len(layout.separators) == 3
        assert len(layout.spaces) == 7
        assert len(layout.features) == 4
        assert len(layout.areas) == 7
        assert layout.get_polygon_of_spaces_and_doors(
            layout=layout, clipping_buffer=0.5
        )
        assert layout.footprint.area == pytest.approx(expected=577801.585, abs=0.01)
        assert layout.footprint.bounds == pytest.approx(
            (620.74, 419.19, 1720.76, 1240.86),
            abs=10**-2,
        )
        assert len(list(SimLayoutValidations.validate(layout=layout))) == 0

    @pytest.fixture
    def original_wall_line_points(self) -> List[Point]:
        point1 = shape(
            {"type": "Point", "coordinates": (12.343329498471089, 13.920956817640697)}
        )
        point2 = shape(
            {"type": "Point", "coordinates": (12.350751542716058, 12.461497445124802)}
        )
        return [point1, point2]

    def test_failing_intersection_of_original_wall_line_with_postprocessed_walls_polygon(
        self, mocker, original_wall_line_points, fixtures_path
    ):
        """
        The fixtures are coming from a real case where the origin wall line points where not intersecting with the
        postproccessed walls due to some precision errors. Thus we needed to reduce the max distance in the shapely custom intersection method
        """
        with fixtures_path.joinpath(
            "geometries/post_processed_walls_not_intersecting_with_one_of_the_original_wall.json"
        ).open("r") as f:
            postprocessed_walls = shape(json.load(f))

        wall_id = "random_id"
        mocker.patch.object(
            ReactPlannerPostprocessor,
            "vertices_by_type_and_id",
            mocker.PropertyMock(
                return_value={SeparatorType.WALL: {wall_id: original_wall_line_points}}
            ),
        )
        line_ids_by_polgon_index = ReactPlannerPostprocessor(
            data=None
        ).get_line_ids_from_constructed_polygons(
            polygons=postprocessed_walls, separator_type=SeparatorType.WALL
        )
        assert line_ids_by_polgon_index[0][0] == wall_id

    def test_match_line_with_nearest_polygon(self, mocker):
        """
        In some cases the original points of a wall are not within the postprocessed walls anymore. E.g. we remove
        the intersection with a column from the wall. In these cases we have to match the line id with the nearest polygon
        """
        wall_line_1 = LineString([(0, 0), (2, 0)])
        wall_line_2 = LineString([(2, 0), (2, 2)])
        column = box(1.8, -0.25, 2.3, 0.25)
        wall_polygon_1 = add_width_to_linestring_improved(line=wall_line_1, width=0.5)
        wall_polygon_2 = add_width_to_linestring_improved(line=wall_line_2, width=1.0)

        wall_1_ex_column = wall_polygon_1.difference(column)
        wall_2_ex_column = wall_polygon_2.difference(column)

        mocker.patch.object(
            ReactPlannerPostprocessor,
            "vertices_by_type_and_id",
            mocker.PropertyMock(
                return_value={
                    SeparatorType.WALL: {
                        "wall_1": [Point(coord) for coord in wall_line_1.coords],
                        "wall_2": [Point(coord) for coord in wall_line_2.coords],
                    }
                }
            ),
        )
        line_ids_by_polgon_index = ReactPlannerPostprocessor(
            data=None
        ).get_line_ids_from_constructed_polygons(
            polygons=[wall_1_ex_column, wall_2_ex_column],
            separator_type=SeparatorType.WALL,
        )
        assert line_ids_by_polgon_index == [["wall_1"], ["wall_2"]]


class TestPostprocessedRailings:
    @staticmethod
    def test_post_processing_railings_do_not_overlap_walls(
        react_planner_background_image_one_unit,
    ):
        polygons_by_type = ReactPlannerPostprocessor(
            data=ReactPlannerData(**react_planner_background_image_one_unit)
        ).process()
        mp_railings = MultiPolygon(polygons_by_type[SeparatorType.RAILING][0])
        mp_walls = MultiPolygon(polygons_by_type[SeparatorType.WALL][0])
        assert mp_railings.intersection(mp_walls).area == pytest.approx(
            0.0, abs=10**-11
        )

    @staticmethod
    @pytest.mark.parametrize(
        "railing_geometry",
        [
            MultiPolygon(
                [
                    box(0, 0, 0.1, 1),
                    box(0, 0.9, 1, 1),
                    box(0.9, 0, 1, 1),
                    box(0, 0, 1, 0.1),
                ]
            )
        ],
    )
    def test_post_processing_railings_without_any_walls_regression_DI_1160(
        railing_geometry,
    ):
        """
        Given a simple railing polygon that is passed to the postprocessor without any accompanying walls / columns

                +------------+
                │            │
                │            │
                +------------+
        When getting the railings not overlapped by any other wall / columns
        Then they should have the exact same shape as those railings, that have been passed to the postprocessor.
        """
        standalone_railings = ReactPlannerPostprocessor(
            data=None
        ).get_non_overlapped_railings(
            column_m_polygons=MultiPolygon(),
            wall_polygons=MultiPolygon(),
            railing_polygons=railing_geometry,
        )
        assert standalone_railings[:] == railing_geometry.geoms[:]

    @staticmethod
    def test_get_non_overlapped_railings_fully_overlapping():
        """Asserts the non overlapped railings generate the right simplified output of just polygons even when
        the railings are totally overlapped"""
        railings = MultiPolygon(
            [
                add_width_to_linestring_improved(
                    line=LineString((Point(0, 0), Point(0, 10))), width=1.0
                )
            ]
        )
        walls = MultiPolygon(
            [
                add_width_to_linestring_improved(
                    line=LineString((Point(0, 0), Point(0, 10))), width=1.0
                )
            ]
        )
        non_overlapped_railings = ReactPlannerPostprocessor(
            data=None
        ).get_non_overlapped_railings(
            column_m_polygons=MultiPolygon(),
            wall_polygons=walls,
            railing_polygons=railings,
        )
        assert not non_overlapped_railings

    @staticmethod
    def test_column_overlap_doesnt_create_multiple_subrailings():
        """
           ┌───┐ railing
           │   │
           │   │
           │   │
        ┌──┼───┼─┐ column
        │  │   │ │
        └──┼───┼─┘
           │   │
           │   │
           │   │
           │   │
           └───┘

        """
        railings = MultiPolygon(
            [
                add_width_to_linestring_improved(
                    line=LineString((Point(0, -5), Point(0, 5))), width=1.0
                )
            ]
        )

        columns = MultiPolygon([box(-1, -1, 1, 1)])

        non_overlapped_railings = ReactPlannerPostprocessor(
            data=None
        ).get_non_overlapped_railings(
            column_m_polygons=columns,
            wall_polygons=MultiPolygon(),
            railing_polygons=railings,
        )

        assert len(non_overlapped_railings) == 1
        assert isinstance(non_overlapped_railings[0], Polygon)

    @staticmethod
    def test_get_non_overlapped_railings_cross():
        """Asserts the non overlapped railings generate the right simplified output of just polygons
                ┌───┐ railings
                │   │
                │   │
                │   │
        ┌───────┼───┼───────┐ walls
        │       │   │       │
        └───────┼───┼───────┘
                │   │
                │   │
                │   │
                │   │
                └───┘

        """
        railings = MultiPolygon(
            [
                add_width_to_linestring_improved(
                    line=LineString((Point(0, 0), Point(0, 10))), width=1.0
                )
            ]
        )
        walls = MultiPolygon(
            [
                add_width_to_linestring_improved(
                    line=LineString((Point(-5, 5), Point(5, 5))), width=1.0
                )
            ]
        )
        non_overlapped_railings = ReactPlannerPostprocessor(
            data=None
        ).get_non_overlapped_railings(
            column_m_polygons=MultiPolygon(),
            wall_polygons=walls,
            railing_polygons=railings,
        )
        assert len(non_overlapped_railings) == 2
        for non_overlapped_railing in non_overlapped_railings:
            assert isinstance(non_overlapped_railing, Polygon)

        assert MultiPolygon(non_overlapped_railings).area == 9.0

    @staticmethod
    @pytest.mark.parametrize(
        "railings,walls",
        [
            (
                MultiPolygon([box(0, 0, 3, 1)]),
                MultiPolygon([box(0, 0, 0.5, 5), box(1.5, 0, 2, 5), box(2.5, 0, 3, 5)]),
            )
        ],
    )
    def test_post_processing_non_overlapped_railing_multipolygons_should_be_unpacked(
        mocker, railings, walls
    ):
        empty_columns = MultiPolygon([box(99, 99, 100, 100)])
        mocker.patch.object(
            ReactPlannerPostprocessor,
            "post_process_react_planner_separator_type",
            side_effect=[(empty_columns, None), (walls, None), (railings, None)],
        )
        line_ids_mock = mocker.patch.object(
            ReactPlannerPostprocessor, "get_line_ids_from_constructed_polygons"
        )

        ReactPlannerPostprocessor(data=None).process()

        railing_polygons_unpacked = [g for g in railings.difference(walls).geoms]

        assert line_ids_mock.call_count == 2

        assert len(line_ids_mock.call_args_list[0][1]["polygons"]) == len(
            railing_polygons_unpacked
        )

    @staticmethod
    def test_extend_railings_to_fill_gaps():
        railing = box(minx=0, miny=0, maxx=9.999, maxy=10)
        wall = box(minx=10, miny=0, maxx=20, maxy=10)
        assert not railing.intersects(wall)
        new_railing = extend_geometry_to_fill_gap_to_another_geom(
            geom_to_extend=railing, geom_reference=wall
        )
        assert railing.area < 10 * 10
        assert new_railing.area == 10 * 10
        union = unary_union([wall, new_railing])
        assert union.area == 20 * 10
        assert union.bounds == (0.0, 0.0, 20.0, 10.0)
        assert isinstance(union, Polygon)

    @staticmethod
    def test_extend_railings_to_fill_gaps_no_min_distance_check():
        """If minimum distance is not close enough to the reference wall the geometry is not extended"""
        railing = box(minx=0, miny=0, maxx=9.999, maxy=10)
        wall = box(minx=10, miny=0, maxx=20, maxy=10)
        assert not railing.intersects(wall)
        new_railing = extend_geometry_to_fill_gap_to_another_geom(
            geom_to_extend=railing, geom_reference=wall, distance_tolerance=0.00001
        )
        assert railing.area < 10 * 10
        assert new_railing.area == railing.area
        assert not new_railing.intersects(wall)
