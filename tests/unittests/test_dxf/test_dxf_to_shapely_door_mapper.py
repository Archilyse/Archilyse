import pytest
from shapely.geometry import LineString, MultiPolygon, Point, box

from dufresne.linestring_add_width import LINESTRING_EXTENSION
from handlers.dxf.dxf_constants import (
    DOOR_BLOCK_NAME_PREFIXES,
    DOOR_LAYERS,
    WINDOW_LAYERS,
)
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_door_mapper import (
    DXFToShapelyDoorMapper,
)
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_mapper import DXFtoShapelyMapper


class TestDXFToShapelyDoorMapper:
    @staticmethod
    @pytest.mark.parametrize("layers", [DOOR_LAYERS, WINDOW_LAYERS])
    def test_get_door_entities(mocker, layers):
        reference_walls = [box(0, 0, 2, 1), box(3, 0, 5, 1)]
        epsilon = 0.01
        arc = LineString([(2 + epsilon, 1), (3, 2)])
        line = LineString([(3, 1 + epsilon), (3, 2)])

        mocked_call = mocker.patch.object(
            DXFToShapelyDoorMapper,
            "_group_arcs_and_lines",
            return_value=[
                (arc, line),
            ],
        )
        mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value=layers)
        mocker.patch.object(DXFtoShapelyMapper, "get_block_names", return_value=set())
        doors = DXFToShapelyDoorMapper.get_door_entities(
            dxf_to_shapely_mapper=DXFtoShapelyMapper(dxf_modelspace=None),
            reference_walls=reference_walls,
            layers=layers,
        )
        assert [x.kwargs.get("layers") for x in mocked_call.call_args_list] == [layers]
        assert len(doors) == 1
        door_polygon = doors[0].geometry
        assert door_polygon.symmetric_difference(box(2, 0, 3, 1)).area < 1e-6

    @staticmethod
    @pytest.mark.parametrize("layers", [DOOR_LAYERS, WINDOW_LAYERS])
    def test_get_door_entities_for_double_swing_doors(mocker, layers):
        reference_walls = [box(-200, -100, 0, 0), box(200, -100, 500, 0)]
        arcs = [LineString([(100, 0), (0, 100)]), LineString([(100, 0), (200, 100)])]
        lines = [LineString([(0, 0), (0, 100)]), LineString([(200, 0), (200, 100)])]
        mocked_call = mocker.patch.object(
            DXFToShapelyDoorMapper,
            "_group_arcs_and_lines",
            return_value=[(arcs[0], lines[0]), (arcs[1], lines[1])],
        )
        mocker.patch.object(DXFtoShapelyMapper, "get_layer_names", return_value=layers)
        mocker.patch.object(DXFtoShapelyMapper, "get_block_names", return_value=set())
        doors = DXFToShapelyDoorMapper.get_door_entities(
            dxf_to_shapely_mapper=DXFtoShapelyMapper(dxf_modelspace=None),
            reference_walls=reference_walls,
            layers=layers,
        )

        assert [x.kwargs.get("layers") for x in mocked_call.call_args_list] == [layers]
        assert len(doors) == 2
        doors = sorted(doors, key=lambda door: door.geometry.centroid.x)
        assert doors[0].geometry.symmetric_difference(box(0, -100, 100, 0)).area < 1e-6
        assert (
            doors[1].geometry.symmetric_difference(box(100, -100, 200, 0)).area < 1e-6
        )

    @staticmethod
    @pytest.mark.parametrize(
        "angle_point,closing_point,opening_point,expected_extension_type",
        [
            (Point(0, 0), Point(1, 0), Point(0, 1), LINESTRING_EXTENSION.RIGHT),
            (Point(0, 0), Point(1, 0), Point(0, -1), LINESTRING_EXTENSION.LEFT),
            (Point(1, 0), Point(0, 0), Point(1, -1), LINESTRING_EXTENSION.RIGHT),
            (Point(1, 0), Point(0, 0), Point(1, 1), LINESTRING_EXTENSION.LEFT),
        ],
    )
    def test_get_extension_type_dxf_door(
        angle_point, closing_point, opening_point, expected_extension_type
    ):
        assert (
            DXFToShapelyDoorMapper._get_extension_type(
                axis_point=angle_point,
                closing_point=closing_point,
                opening_point=opening_point,
            )
            == expected_extension_type
        )

    @staticmethod
    @pytest.mark.parametrize(
        "axis_point,closed_point,extension_type,expected_sweeping_points",
        [
            (
                Point(0, 0.25),
                Point(1, 0.25),
                LINESTRING_EXTENSION.RIGHT,
                [[0, 0], [1, 0], [0, 1]],
            ),
            (
                Point(0, 0.25),
                Point(1, 0.25),
                LINESTRING_EXTENSION.LEFT,
                [[0, 0.5], [1, 0.5], [0, -0.5]],
            ),
            (
                Point(1, 0.25),
                Point(0, 0.25),
                LINESTRING_EXTENSION.RIGHT,
                [[1, 0.5], [0, 0.5], [1, -0.5]],
            ),
            (
                Point(1, 0.25),
                Point(0, 0.25),
                LINESTRING_EXTENSION.LEFT,
                [[1, 0.0], [0, 0], [1, 1]],
            ),
            (
                Point(0, 0),
                Point(0, 1),
                LINESTRING_EXTENSION.LEFT,
                [[-0.25, 0.0], [-0.25, 1], [0.75, 0]],
            ),
        ],
    )
    def test_create_sweeping_points(
        axis_point, closed_point, extension_type, expected_sweeping_points
    ):
        door_width = 0.5
        sweeping_points = DXFToShapelyDoorMapper._create_sweeping_points(
            axis_point=axis_point,
            closed_point=closed_point,
            extension_type=extension_type,
            door_width=door_width,
        )

        assert sweeping_points.angle_point == expected_sweeping_points[0]
        assert sweeping_points.closed_point == expected_sweeping_points[1]
        assert sweeping_points.opened_point == expected_sweeping_points[2]

    @staticmethod
    @pytest.mark.parametrize("block_refrence_name", [None, *DOOR_BLOCK_NAME_PREFIXES])
    def test_get_lines_for_doors(mocker, monkeypatch, block_refrence_name):
        line = LineString([(0, 0), (1, 0)])
        multiline = LineString([(2, 0), (3, 0), (4, 1)])
        polygon = box(10, 10, 11, 11)

        def _monkeypatched_get_dxf_geometries(
            self, allowed_layers, allowed_geometry_types, block_name_prefix=None
        ):
            if allowed_geometry_types == {"LINE"}:
                if (
                    block_refrence_name and block_name_prefix == block_refrence_name
                ) or (not block_name_prefix and not block_refrence_name):
                    return [line, multiline]
                else:
                    return []

            if allowed_geometry_types == {"LWPOLYLINE"}:
                if (
                    block_refrence_name and block_name_prefix == block_refrence_name
                ) or (not block_name_prefix and not block_refrence_name):
                    return [polygon]
                else:
                    return []

        monkeypatch.setattr(
            DXFtoShapelyMapper, "get_dxf_geometries", _monkeypatched_get_dxf_geometries
        )
        lines, polygon_to_avoid = DXFToShapelyDoorMapper._get_lines_for_doors(
            dxf_to_shapely_mapper=DXFtoShapelyMapper(
                dxf_modelspace=None,
            ),
            layers=set(),
            block_names=set([block_refrence_name]),
        )
        assert len(lines) == 3
        assert all(isinstance(line, LineString) for line in lines)
        assert lines[0] == line
        assert lines[1].coords[:] == [(2.0, 0.0), (3.0, 0.0)]
        assert lines[2].coords[:] == [(3.0, 0.0), (4.0, 1.0)]

        assert polygon_to_avoid == MultiPolygon([polygon])
