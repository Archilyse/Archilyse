from itertools import permutations
from unittest.mock import PropertyMock

import ezdxf
import pytest
from shapely.affinity import rotate
from shapely.geometry import GeometryCollection, LineString, Polygon, box
from shapely.ops import unary_union

from dufresne.linestring_add_width import add_width_to_linestring_improved
from handlers.dxf.dxf_constants import RAILING_DEFAULT_WIDTH_IN_CM, RAILING_LAYERS
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_mapper import DXFtoShapelyMapper
from handlers.dxf.polylines_to_rectangles import rectangles_from_skeleton
from handlers.editor_v2.schema import ReactPlannerName
from tests.constants import TEST_SKELETONIZE_TIMEOUT_IN_SECS


@pytest.fixture
def mocked_get_layer_names(mocker):
    return mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value={})


class TestDXFtoShapelyMapper:
    @staticmethod
    def test_get_elevator_main_geometries(mocker, mocked_get_layer_names):
        doc = ezdxf.new()
        msp = doc.modelspace()

        gap = 0.001
        opening_line = LineString([(0, -10), (100, -10)])
        main_cabine_as_linestrings = [
            LineString([(0, 0), (100, 0)]),
            LineString([(100, 0 + gap), (100, 200)]),
            LineString([(0, 200), (100, 200)]),
            LineString([(0, 0), (0, 200)]),
        ]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_dxf_geometries",
            return_value=[opening_line] + main_cabine_as_linestrings,
        )
        elevator_geometries = DXFtoShapelyMapper(
            dxf_modelspace=msp
        ).get_elevators_as_polygons()

        assert len(elevator_geometries) == 1
        assert (
            elevator_geometries[0].symmetric_difference(box(0, 0, 100, 200)).area
            < 61  # buffering increases the returned geometry a bit
        )

    @staticmethod
    def test_features_fully_intersected_by_walls_get_split(
        mocker, mocked_get_layer_names
    ):
        """In real scenarios we can have features in opposite sides of the walls almost touching
        each other which is generating a single geometry of feature that is intersected by a wall.
        Here we make sure it is split into 2 pieces"""
        bathtub_a = box(0, 0, 2.5, 2)
        bathtub_b = box(2.5, 0, 5, 2)
        wall = box(2, -1, 3, 5)
        lines_and_arcs = []
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_dxf_geometries",
            side_effect=[[bathtub_a, bathtub_b], lines_and_arcs],
        )
        final_features = DXFtoShapelyMapper(
            dxf_modelspace=None
        ).get_item_polygons_from_layer(layer={"lo_que_tal"}, wall_polygons=[wall])[0]
        assert len(final_features) == 2

    @staticmethod
    def test_get_stairs_polygons(mocker, mocked_get_layer_names):
        walls = [box(200, -200, 300, 300)]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_item_polygons_from_layer",
            return_value=([box(0, 0, 700, 200)], [box(0, 0, 700, 200)]),
        )
        stair_polygons = DXFtoShapelyMapper(dxf_modelspace=None).get_stairs_polygons(
            wall_polygons=walls
        )
        assert len(stair_polygons) == 2
        stair_polygons = sorted(stair_polygons, key=lambda stair: stair.centroid.x)
        assert stair_polygons[0].symmetric_difference(box(0, 0, 200, 200)).area < 1e-6
        assert stair_polygons[1].symmetric_difference(box(300, 0, 700, 200)).area < 1e-6

    @staticmethod
    def test_get_lw_polyline_not_closed_as_linestring():
        doc = ezdxf.new()
        msp = doc.modelspace()

        points = [(0, 0), (0, 500), (1000, 500), (1000, 0)]
        msp.add_lwpolyline(points)
        geometries = DXFtoShapelyMapper(dxf_modelspace=msp).get_dxf_geometries(
            allowed_layers={"0"}, allowed_geometry_types={"LWPOLYLINE"}
        )
        assert len(geometries) == 1
        assert geometries[0].symmetric_difference(LineString(points)).area < 1e-6

    @staticmethod
    def test_get_lw_polyline_closed_as_polygon():
        doc = ezdxf.new()
        msp = doc.modelspace()

        points = [(0, 0), (0, 500), (1000, 500), (1000, 0), (0, 0)]
        msp.add_lwpolyline(points, close=True)
        geometries = DXFtoShapelyMapper(dxf_modelspace=msp).get_dxf_geometries(
            allowed_layers={"0"}, allowed_geometry_types={"LWPOLYLINE"}
        )
        assert len(geometries) == 1
        assert geometries[0].symmetric_difference(Polygon(points)).area < 1e-6

    @staticmethod
    def test_get_hatch_polygons_filters_geometries_with_too_few_points(mocker):
        """
        This happens for rare cases when ezdxf is mapping an hatch entity to geojson
        """
        from ezdxf.addons import geo

        mocker.patch.object(
            geo,
            "proxy",
            return_value={
                "type": "Polygon",
                "coordinates": [[[30.0, 10.0], [40.0, 40.0], [40.0, 40.0]]],
            },
        )
        polygons = DXFtoShapelyMapper(dxf_modelspace=None)._get_hatch_polygons(
            entity=None
        )
        assert isinstance(polygons, list)
        assert len(polygons) == 0

    @staticmethod
    def test_get_hatch_polygons_handles_multipolygons(mocker):
        from ezdxf.addons import geo

        mocker.patch.object(
            geo,
            "proxy",
            return_value={
                "type": "MultiPolygon",
                "coordinates": [
                    [[[0, 0], [1, 0], [1, 1], [0, 1]]],
                    [[[5, 0], [6, 0], [6, 1], [5, 1]]],
                ],
            },
        )

        polygons = DXFtoShapelyMapper(dxf_modelspace=None)._get_hatch_polygons(
            entity=None
        )
        assert isinstance(polygons, list)
        assert len(polygons) == 2

    @staticmethod
    def test_get_hatch_polygons_makes_valid_only_polygons_returned(mocker):
        """
        Ensures that if makes valid returns a collection also containing linestrings
        these are filtered out
        """
        from ezdxf.addons import geo

        from handlers.dxf.dxf_to_shapely import dxf_to_shapely_mapper

        mocker.patch.object(Polygon, "is_valid", PropertyMock(return_value=False))
        mocker.patch.object(
            geo,
            "proxy",
            return_value=None,
        )
        mocker.patch.object(dxf_to_shapely_mapper, "shape", return_value=Polygon())
        mocker.patch.object(
            dxf_to_shapely_mapper,
            "make_valid",
            return_value=GeometryCollection(
                geoms=[box(0, 0, 1, 1), LineString([(0, 0), (1, 0)])]
            ),
        )

        polygons = DXFtoShapelyMapper(dxf_modelspace=None)._get_hatch_polygons(
            entity=None
        )
        assert isinstance(polygons, list)
        assert len(polygons) == 1
        assert isinstance(polygons[0], Polygon)

    @staticmethod
    def test_wrongly_marked_not_closed_line_is_closed_automatically():
        doc = ezdxf.new()
        msp = doc.modelspace()
        points = [(0, 0), (0, 20), (100, 20), (100, 0), (0, 0)]
        msp.add_lwpolyline(points, close=False, dxfattribs={"layer": "E03_BALKONE"})
        railing_polygons = DXFtoShapelyMapper(
            dxf_modelspace=msp
        ).get_separator_polygons_from_lines(
            layers=RAILING_LAYERS, default_width=RAILING_DEFAULT_WIDTH_IN_CM
        )
        assert len(railing_polygons) == 1
        assert railing_polygons[0].symmetric_difference(Polygon(points)).area < 1e-6

    @staticmethod
    def test_separators_include_arcs(mocker):
        mocker.patch(
            "handlers.dxf.polylines_to_rectangles.SKELETONIZE_TIMEOUT_IN_SECS",
            TEST_SKELETONIZE_TIMEOUT_IN_SECS,
        )
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_arc(
            center=[100, 100],
            radius=100,
            start_angle=0,
            end_angle=30,
            dxfattribs={"layer": "E03_BALKONE"},
        )
        railing_polygons = DXFtoShapelyMapper(
            dxf_modelspace=msp
        ).get_separator_polygons_from_lines(
            layers=RAILING_LAYERS, default_width=RAILING_DEFAULT_WIDTH_IN_CM
        )

        assert len(railing_polygons) == 6
        assert (
            pytest.approx(sum([x.area for x in railing_polygons]), abs=0.01) == 720.43
        )

    @staticmethod
    def test_separators_creates_polygons_from_parallel_lines():
        doc = ezdxf.new()
        msp = doc.modelspace()
        msp.add_line(
            start=[0, 0],
            end=[10, 0],
            dxfattribs={"layer": "E03_BALKONE"},
        )
        msp.add_line(
            start=[0, 2],
            end=[10, 2],
            dxfattribs={"layer": "E03_BALKONE"},
        )
        railing_polygons = DXFtoShapelyMapper(
            dxf_modelspace=msp
        ).get_separator_polygons_from_lines(
            layers=RAILING_LAYERS, default_width=RAILING_DEFAULT_WIDTH_IN_CM
        )
        assert len(railing_polygons) == 1
        assert pytest.approx(railing_polygons[0].area, abs=0.01) == 20.0

    @staticmethod
    def test_include_polylines_for_non_load_bearing_walls():
        doc = ezdxf.new()
        msp = doc.modelspace()
        points = [(0, 0), (0, 20), (100, 20), (100, 0), (0, 0)]
        msp.add_lwpolyline(
            points, close=False, dxfattribs={"layer": "E62_INNENWAENDE_NICHTTR"}
        )
        wall_polygons = DXFtoShapelyMapper(dxf_modelspace=msp).get_wall_polygons()
        assert len(wall_polygons) == 1
        assert isinstance(wall_polygons[0], Polygon)
        assert (
            wall_polygons[0]
            .symmetric_difference(
                Polygon([(0, 0), (0, 20), (100, 20), (100, 0), (0, 0)])
            )
            .area
            < 1e-6
        )

    @staticmethod
    def test_get_wall_polygons_remove_duplicates(mocker, mocked_get_layer_names):
        hatch_polygons = [box(0, 0, 100, 20)]
        polyline_polygons = [box(-0.1, -0.1, 20, 20)]
        mocked_polygons_from_hatches = mocker.patch.object(
            DXFtoShapelyMapper, "get_polygons_from_hatches", return_value=hatch_polygons
        )
        mocked_polygons_from_polylines = mocker.patch.object(
            DXFtoShapelyMapper,
            "get_separator_polygons_from_lines",
            return_value=polyline_polygons,
        )
        wall_polygons = DXFtoShapelyMapper(dxf_modelspace=None).get_wall_polygons()

        assert mocked_polygons_from_polylines.called
        assert mocked_polygons_from_hatches.called
        assert len(wall_polygons) == 1
        assert wall_polygons[0].symmetric_difference(hatch_polygons[0]).area < 1e-6

    @staticmethod
    def test_separator_as_simple_linestrings(mocker):
        railing = LineString([(0, 0), (0, 500), (1000, 500), (1000, 0)])
        mocker.patch.object(
            DXFtoShapelyMapper, "get_dxf_geometries", return_value=[railing]
        )
        railing_polygons = DXFtoShapelyMapper(
            dxf_modelspace=None
        ).get_separator_polygons_from_lines(
            layers=None, default_width=RAILING_DEFAULT_WIDTH_IN_CM
        )
        assert len(railing_polygons) == 3
        expected_railing_geometries = add_width_to_linestring_improved(
            line=railing, width=RAILING_DEFAULT_WIDTH_IN_CM
        )
        assert (
            unary_union(railing_polygons)
            .symmetric_difference(expected_railing_geometries)
            .area
            < 1e-6
        )

    @staticmethod
    def test_invalid_polygon_from_linestring_discarded(mocker):
        from handlers.dxf.dxf_to_shapely import (
            dxf_to_shapely_mapper,
            dxf_to_shapely_utils,
        )

        mocker.patch.object(Polygon, "is_valid", PropertyMock(return_value=False))
        mocker.patch.object(DXFtoShapelyMapper, "get_dxf_geometries", return_value=[])
        mocker.patch.object(
            dxf_to_shapely_mapper,
            "polygonize_full_lists",
            return_value=([], [LineString()]),
        )
        mocker.patch.object(
            dxf_to_shapely_utils,
            "add_width_to_linestring_improved",
            return_value=Polygon(),
        )
        railing_polygons = DXFtoShapelyMapper(
            dxf_modelspace=None
        ).get_separator_polygons_from_lines(
            layers=None, default_width=RAILING_DEFAULT_WIDTH_IN_CM
        )
        assert isinstance(railing_polygons, list)
        assert len(railing_polygons) == 0

    @staticmethod
    def test_get_window_polygons_from_separated_lines(mocker, mocked_get_layer_names):
        """The ends of the parallel lines are close enough to be closed and form 2 polygons"""
        input_lines = [
            LineString([(0, 0), (100, 0)]),
            LineString([(10, 40), (90, 40)]),
            LineString([(120, 0), (210, 0)]),
            LineString([(130, 30), (190, 30)]),
        ]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_dxf_geometries",
            return_value=input_lines,
        )
        windows = DXFtoShapelyMapper(dxf_modelspace=None).get_window_polygons()
        assert len(windows) == 2
        assert {x.bounds for x in windows} == {
            (120.0, 0.0, 210.0, 30.0),
            (0.0, 0.0, 100.0, 40.0),
        }

    @staticmethod
    def test_get_window_l_shapes_generate_individual_windows(mocker):
        """Small segments in the corners produced big windows covering partially the area,
        a regression test to avoid this case in the future
             ┌───────────────────────┐
             │                       │
           ┌─┴───────────────────────┘ 130, 120
           │
        ┌──┴┐ 20, 100
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        │   │
        └───┘
        0,0  20,0
        """
        connection_line = LineString([(15, 100), (19, 120), (30, 125)])
        connection_geom = add_width_to_linestring_improved(
            line=connection_line, width=3
        )
        input_geometries = [box(0, 0, 20, 100), box(30, 120, 130, 150), connection_geom]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_dxf_geometries",
            return_value=input_geometries,
        )
        mocker.patch.object(DXFtoShapelyMapper, "get_area_polygons", return_value=[])
        mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value=set())
        windows = DXFtoShapelyMapper(dxf_modelspace=None).get_window_polygons()
        assert len(windows) == 2
        assert {x.bounds for x in windows} == {
            (0.0, 0.0, 20.0, 100.0),
            (30.0, 120.0, 130.0, 150.0),
        }

    @staticmethod
    def test_get_window_polygons_from_separated_lines_edge_case(mocker):
        """
        Abstraction from a real case we have in dxf file 84024_B01_O01.1.dxf

        Ensures that clustering algorithm joins L1,L2,L3 to form a common geometry even though the wall
        is in between L2 and L3 .... we also ensure that the order in which we process the geometries doesn't matter

                       L1
        -----------------------------------
        |                                 |
        | L2                              |
        |                                 |
        ------ Wall


        -----------------------------------
                       L3


        """
        input_geometries = [
            LineString([(0, 0), (0, 10)]),
            LineString([(0, 10), (100, 10)]),
            LineString([(0, -20), (100, -20)]),
        ]
        mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value=set())
        for ordered_input_geometries in permutations(
            input_geometries
        ):  # ensuring order doesn't play a role for the grouping algorithm
            mocker.patch.object(
                DXFtoShapelyMapper,
                "get_dxf_geometries",
                return_value=ordered_input_geometries,
            )
            windows = DXFtoShapelyMapper(dxf_modelspace=None).get_window_polygons()
            assert len(windows) == 1
            assert windows[0].bounds == (0.0, -20.0, 100.0, 10.0)

    @staticmethod
    def test_get_window_polygons_from_separated_lines_that_are_closing_polygons(
        mocker, mocked_get_layer_names
    ):
        """
        This test makes sure we are also polygonizing the unary union of the lines
        ┌────────────────────────┐
        └──┼─────────────────┼───┘
           │                 │
           │                 │
           └─────────────────┘
        """
        input_lines = [
            LineString([(0, 50), (100, 50)]),
            LineString([(100, 50), (100, 40)]),
            LineString([(100, 40), (0, 40)]),
            LineString([(0, 40), (0, 50)]),
            LineString([(10, 40), (10, 0)]),
            LineString([(10, 0), (90, 0)]),
            LineString([(90, 0), (90, 40)]),
        ]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_dxf_geometries",
            return_value=input_lines,
        )
        windows = DXFtoShapelyMapper(dxf_modelspace=None).get_window_polygons()
        assert len(windows) == 1
        assert windows[0].bounds == (0.0, 0.0, 100.0, 50.0)

    def test_get_window_polygons_ony_uses_geometry_outside_of_room_area(self):
        doc = ezdxf.new()
        msp = doc.modelspace()
        window_points = [(0, 0), (0, 20), (100, 20), (100, 0), (0, 0)]
        room_points = [(0, 10), (0, 500), (500, 500), (500, 10), (0, 10)]
        msp.add_lwpolyline(
            window_points, close=True, dxfattribs={"layer": "E51_FENSTER"}
        )
        msp.add_lwpolyline(
            room_points, close=True, dxfattribs={"layer": "Z22_NGF-POLYGONE"}
        )
        windows = DXFtoShapelyMapper(dxf_modelspace=msp).get_window_polygons()
        assert len(windows) == 1
        assert windows[0].symmetric_difference(box(0, 0, 100, 10)).area < 1e-6

    @staticmethod
    def test_get_kitchen_polygons(mocker):
        rotated_box = rotate(
            geom=box(3, -1, 4, 3),
            angle=30,
        )
        polygons = [
            box(0, 0, 1, 2),
            box(1, 1, 2, -1),
            box(9, -1, 10, 5),
            rotated_box,
            LineString([(0, 0), (10, 10)]),
        ]
        mocker.patch.object(
            DXFtoShapelyMapper,
            "get_item_polygons_from_layer",
            return_value=(polygons, []),
        )
        mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value=set())
        mocker.patch.object(DXFtoShapelyMapper, "get_block_names", return_value=set())
        wall_polygons = [box(0, 0, 10, 1)]
        final_polygons = DXFtoShapelyMapper(dxf_modelspace=None).get_kitchen_polygons(
            wall_polygons=wall_polygons, minimum_kitchen_side=1
        )
        assert len(final_polygons) == 4
        assert (
            pytest.approx(sum([x.area for x in final_polygons]), abs=10**-3) == 8.2886
        )

    @staticmethod
    def test_get_door_polygons_is_built_also_with_windows_layers(mocker):
        from handlers.dxf.dxf_to_shapely.dxf_to_shapely_door_mapper import (
            DXFToShapelyDoorMapper,
        )

        mocked_call = mocker.patch.object(DXFToShapelyDoorMapper, "get_door_entities")
        mocked_get_layer_names = mocker.patch.object(
            DXFtoShapelyMapper, "get_layer_names", return_value={"WINDOW"}
        )
        DXFtoShapelyMapper(dxf_modelspace=None).get_door_polygons(
            wall_polygons=[box(0, 0, 10, 1)]
        )
        assert mocked_get_layer_names.call_args.kwargs["react_planner_names"] == {
            ReactPlannerName.WINDOW
        }
        assert [x.kwargs.get("layers") for x in mocked_call.call_args_list] == [
            None,
            {"WINDOW"},
        ]

    @staticmethod
    def test_make_all_geometries_valid():
        invalid_polygon = Polygon([(0, 1), (0, 2), (0, 1)])
        assert not invalid_polygon.is_valid
        valid_polygons = DXFtoShapelyMapper(
            dxf_modelspace=None
        ).make_all_geometries_valid(geometries=[invalid_polygon])
        assert len(valid_polygons) == 1
        assert valid_polygons[0].is_valid

    @staticmethod
    @pytest.mark.parametrize(
        "points, closed, expected",
        [
            [[(0, 0), (1, 0)], True, LineString],
            [[(0, 0), (1, 0), (1, 1)], True, Polygon],
            [[(0, 0), (1, 0), (1, 1)], False, LineString],
        ],
    )
    def test_get_polyline_geometry(mocker, points, closed, expected):
        entity = mocker.MagicMock()
        entity.closed = closed

        entity.points.return_value.__enter__.return_value = points
        valid_geometry = DXFtoShapelyMapper(dxf_modelspace=None).get_polyline_geometry(
            entity=entity
        )
        assert isinstance(valid_geometry, expected)
        if isinstance(valid_geometry, LineString):
            assert valid_geometry.length > 0
        elif isinstance(valid_geometry, Polygon):
            assert valid_geometry.area > 0


def test_rectangles_from_skeleton():
    square = box(0, 2, 0, 2)
    rectangles = rectangles_from_skeleton(geometry=square)
    assert len(rectangles) == 1
    assert rectangles[0].symmetric_difference(square).area < 1e-6
