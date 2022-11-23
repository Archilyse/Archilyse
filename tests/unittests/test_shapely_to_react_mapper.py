import pytest
from deepdiff import DeepDiff
from shapely.affinity import rotate
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from brooks.constants import SuperTypes
from brooks.models import SimSeparator
from brooks.types import SeparatorType
from common_utils.exceptions import ShapelyToReactMappingException
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.editor_v2_element_mapper import (
    ReactPlannerOpeningMapper,
    ReactPlannerToBrooksMapper,
)
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerDoorSweepingPoints,
    ReactPlannerGeomProperty,
    ReactPlannerLayer,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerName,
    ReactPlannerReferenceLine,
    ReactPlannerType,
    ReactPlannerVertex,
)
from handlers.shapely_to_react.editor_ready_entity import (
    EditorReadyEntity,
    EntityProperties,
)
from handlers.shapely_to_react.shapely_to_react_mapper import (
    ShapelyToReactPlannerMapper,
)


@pytest.fixture
def walls_shape_e_letter():
    return [
        box(0, 0, 6, 2),
        box(0, 4, 6, 6),
        box(0, 8, 6, 10),
        box(0, 0, 2, 10),
    ]


class TestShapelyToReactPlannerMapper:
    @staticmethod
    @pytest.mark.parametrize(
        "item_type, wall, feature, expected_base_angle",
        [
            (ReactPlannerName.SINK, box(0, -0.3, 10, 0), box(5, 0, 6, 0.4), 0),
            (ReactPlannerName.SINK, box(-0.3, 0, 0, 10), box(0, 5, 0.4, 6), -90),
            (ReactPlannerName.TOILET, box(0, -0.3, 10, 0), box(5, 0, 5.4, 0.6), 0),
            (ReactPlannerName.TOILET, box(-0.3, 0, 0, 10), box(0, 5, 0.6, 5.4), -90),
        ],
    )
    @pytest.mark.parametrize("rotation_angle", range(-180, 180, 45))
    def test_import_feature_angles(
        mocker, item_type, wall, feature, expected_base_angle, rotation_angle
    ):
        fake_geometries = {
            SuperTypes.SEPARATORS: {
                ReactPlannerName.WALL: [
                    EditorReadyEntity(
                        geometry=rotate(
                            geom=wall, angle=rotation_angle, origin=Point(0, 0)
                        )
                    )
                ]
            },
            SuperTypes.ITEMS: {
                item_type: [
                    EditorReadyEntity(
                        geometry=rotate(
                            geom=feature, angle=rotation_angle, origin=Point(0, 0)
                        )
                    )
                ]
            },
        }

        mocker.patch.object(
            ReactPlannerElementFactory,
            "_round_width_to_nearest_integer_in_cm",
            lambda x: x,
        )

        items = ShapelyToReactPlannerMapper.get_planner_items(
            geometries=fake_geometries, scale_to_cm=1
        )
        feature_id = list(items.keys())[0]
        actual_angle = items[feature_id].rotation

        assert actual_angle % 360 == pytest.approx(
            (expected_base_angle + rotation_angle) % 360
        )

        infered_feature = ReactPlannerToBrooksMapper.get_feature_from_item(
            item_id="feature_id", item=items[feature_id]
        )
        assert infered_feature.footprint.symmetric_difference(
            fake_geometries[SuperTypes.ITEMS][item_type][0].geometry
        ).area == pytest.approx(0)

    @staticmethod
    def test_create_area_splitters_from_spaces(mocker):
        separators = [
            SimSeparator(footprint=box(0, 0, 1, 8), separator_type=SeparatorType.WALL),
            SimSeparator(footprint=box(1, 0, 8, 1), separator_type=SeparatorType.WALL),
            SimSeparator(footprint=box(7, 0, 8, 8), separator_type=SeparatorType.WALL),
            SimSeparator(footprint=box(0, 7, 8, 8), separator_type=SeparatorType.WALL),
        ]
        spaces = [
            MultiPolygon(
                [
                    box(1, 1, 7, 4),
                ]
            ),
            MultiPolygon([box(1, 4, 7, 7)]),
        ]

        planner_elements = ReactPlannerData(
            width=0,
            height=0,
            layers={"layer-1": ReactPlannerLayer()},
        )
        mocker.patch.object(
            ReactPlannerToBrooksMapper,
            "get_separators",
            return_value=(set(separators), None),
        )
        ShapelyToReactPlannerMapper.add_area_splitters_to_react_planner_data(
            planner_elements=planner_elements, spaces=spaces, scale_to_cm=1
        )
        assert len(planner_elements.layers["layer-1"].lines) == 1
        line = [line for line in planner_elements.layers["layer-1"].lines.values()][0]
        assert (
            line.properties.width.value
            == ReactPlannerElementFactory.AREA_SPLITTER_THICKNESS
        )
        assert line.vertices
        vertices = [
            (vertex.x, vertex.y)
            for vertex in planner_elements.layers["layer-1"].vertices.values()
        ]
        assert not DeepDiff(
            vertices,
            [
                (7.09, 4.0),
                (0.91, 4.0),
                (7.09, 3.9),
                (7.09, 4.1),
                (0.91, 4.1),
                (0.91, 3.9),
            ],
            significant_digits=12,
        )

        area_splitters = ReactPlannerToBrooksMapper._get_separators_from_lines(
            planner_elements=planner_elements,
            separator_whitelist=[SeparatorType.AREA_SPLITTER],
        )
        union_walls_and_area_splitters = unary_union(
            [separator.footprint for separator in separators]
            + [area_splitter.footprint for area_splitter in area_splitters]
        )
        assert (
            len(union_walls_and_area_splitters.interiors) == 2
        )  # two areas inside space

        interior_a = Polygon(union_walls_and_area_splitters.interiors[0])
        interior_b = Polygon(union_walls_and_area_splitters.interiors[1])
        assert interior_a.area == pytest.approx(expected=17.4, abs=0.001)
        assert interior_b.area == pytest.approx(expected=17.4, abs=0.001)

    @staticmethod
    def test_create_lines_from_vertices_associated_e_shape(walls_shape_e_letter):
        (vertices, lines,) = ShapelyToReactPlannerMapper._create_lines_and_vertices(
            editor_ready_entities=[
                EditorReadyEntity(geometry=wall) for wall in walls_shape_e_letter
            ],
            line_type=ReactPlannerName.WALL,
            scale_to_cm=1,
        )
        assert len(vertices) == 24
        assert len(lines) == 4
        for line in lines.values():
            assert len(line.vertices) == len(set(line.vertices))
            assert len(line.auxVertices) == len(set(line.auxVertices))

    @staticmethod
    @pytest.mark.parametrize(
        "opening_name", [ReactPlannerName.WINDOW, ReactPlannerName.DOOR]
    )
    def test_create_react_hole(mocker, opening_name):
        mocker.patch.object(
            ReactPlannerData,
            "separator_polygons_by_id",
            return_value={"l0": box(minx=0, miny=-10, maxx=1, maxy=10)},
        )

        planner_data = ReactPlannerData(
            layers={
                "layer-1": ReactPlannerLayer(
                    vertices={},
                    lines={
                        "l0": ReactPlannerLine(
                            id="l0",
                            vertices=[],
                            auxVertices=[],
                            properties=ReactPlannerLineProperties(
                                width=ReactPlannerGeomProperty(value=20),
                                height=ReactPlannerGeomProperty(value=300),
                                referenceLine=ReactPlannerReferenceLine.CENTER.value,
                            ),
                            coordinates=[],
                        )
                    },
                )
            },
        )
        opening_id, opening_polygon = ("o0", box(minx=0.25, miny=0, maxx=1.25, maxy=1))
        hole = ShapelyToReactPlannerMapper._create_react_hole(
            planner_data=planner_data,
            opening_id=opening_id,
            editor_ready_entity=EditorReadyEntity(geometry=opening_polygon),
            opening_name=opening_name,
            scale_to_cm=1,
        )
        assert hole.properties.length.value == 1.0
        assert (
            hole.properties.heights.lower_edge
            == ShapelyToReactPlannerMapper._ELEMENT_HEIGHTS[opening_name][0] * 100
        )
        assert (
            hole.properties.heights.upper_edge
            == ShapelyToReactPlannerMapper._ELEMENT_HEIGHTS[opening_name][1] * 100
        )
        assert hole.properties.width.value == 20
        assert (
            hole.properties.altitude.value
            == min(ShapelyToReactPlannerMapper._ELEMENT_HEIGHTS[opening_name]) * 100
        )
        assert hole.name == opening_name.value
        assert hole.type == opening_name.value.lower()
        assert hole.id == "o0"
        assert hole.prototype == "holes"

    @staticmethod
    @pytest.mark.parametrize(
        "vertices, line_width",
        [
            (
                [ReactPlannerVertex(x=0, y=0), ReactPlannerVertex(x=1, y=0)],
                0,
            ),
            (
                [ReactPlannerVertex(x=0, y=0), ReactPlannerVertex(x=0, y=1e-6)],
                1,
            ),
        ],
    )
    def test_create_react_hole_missing_line_width_ignores_wall(
        vertices, line_width, mocker
    ):
        wall_creation_spy = mocker.spy(
            ShapelyToReactPlannerMapper, "_create_wall_from_hole"
        )
        line = ReactPlannerLine(
            vertices=[vertex.id for vertex in vertices],
            auxVertices=[vertex.id for vertex in vertices],
            name=ReactPlannerName.WALL.value,
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=line_width),
                height=ReactPlannerGeomProperty(value=300),
                referenceLine=ReactPlannerReferenceLine.CENTER.value,
            ),
            coordinates=[[[1, 0], [1, 3], [2, 3], [2, 1], [1, 0]]],
        )
        for vertex in vertices:
            vertex.lines = [line.id]
        planner_data = ReactPlannerData(
            layers={
                "layer-1": ReactPlannerLayer(
                    vertices={v.id: v for v in vertices},
                    lines={line.id: line},
                )
            },
        )
        ShapelyToReactPlannerMapper._create_react_hole(
            planner_data=planner_data,
            editor_ready_entity=EditorReadyEntity(geometry=box(0, 0, 1, 1)),
            opening_name=ReactPlannerName.WINDOW,
            scale_to_cm=1,
        )

        assert (
            wall_creation_spy.call_count == 1
        )  # means the existing wall was discarded and a new one is created

    @staticmethod
    def test_react_hole_missing_wall_creates_wall(mocker):
        planner_data = ReactPlannerData(
            layers={
                "layer-1": ReactPlannerLayer(
                    vertices={},
                    lines={},
                )
            },
        )
        window_geometry = box(0, 0, 1, 0.5)
        door_geometry = box(1, 0, 1.8, 0.5)
        all_opening_elements = {
            ReactPlannerName.WINDOW: [EditorReadyEntity(geometry=window_geometry)],
            ReactPlannerName.DOOR: [EditorReadyEntity(geometry=door_geometry)],
        }

        mocker.patch.object(
            ReactPlannerElementFactory, "get_line_width", return_value=0.5
        )  # importer assumes geometries are in cm and rounds the width
        # which would create a 0 width for our testcase

        holes = ShapelyToReactPlannerMapper.create_holes_assigned_to_walls(
            planner_data=planner_data,
            all_opening_elements=all_opening_elements,
            scale_to_cm=1,
        )
        assert len(holes) == 2
        windows = [
            hole
            for hole in holes.values()
            if hole.name == ReactPlannerName.WINDOW.value
        ]
        doors = [
            hole for hole in holes.values() if hole.name == ReactPlannerName.DOOR.value
        ]

        assert len(windows) == 1
        assert len(doors) == 1

        walls = planner_data.separator_polygons_by_id(separator_type=SeparatorType.WALL)
        assert len(walls) == 2

        assert walls[doors[0].line].symmetric_difference(
            door_geometry
        ).area == pytest.approx(expected=0.0, abs=1e-6)
        assert walls[windows[0].line].symmetric_difference(
            window_geometry
        ).area == pytest.approx(expected=0.0, abs=1e-6)

    @staticmethod
    @pytest.mark.parametrize(
        "opening_box, expected_line_id",
        [
            (
                box(minx=0, miny=-1, maxx=10, maxy=1),
                "l1",
            ),
            (
                box(minx=9, miny=0, maxx=11, maxy=10),
                "l0",
            ),
        ],
    )
    def test_create_react_hole_assigned_to_most_overlapped_wall(
        mocker, opening_box, expected_line_id
    ):
        """
        In the case were the opening is in the horizontal line, l0 will be the opening assigned,
         l1 in the vertical case
                    ┌────┐
                    │    │
                    │l0  │
                    │    │
                    │    │
                    │    │
        ┌───────────┼────┤
        │ l1        │    │
        │           │    │
        └───────────┴────┘
        """
        mocker.patch.object(
            ReactPlannerData,
            "separator_polygons_by_id",
            return_value={
                "l1": box(minx=0, miny=-1, maxx=11, maxy=1),
                "l0": box(minx=9, miny=-1, maxx=11, maxy=10),
            },
        )
        vertex_a = ReactPlannerVertex(x=0, y=0, lines=["l0", "l1"])
        vertex_b = ReactPlannerVertex(x=10, y=10, lines=["l0", "l1"])
        line_a = ReactPlannerLine(
            id="l0",
            name=ReactPlannerName.WALL.value,
            type=ReactPlannerType.WALL.value,
            vertices=[vertex_a.id],
            auxVertices=[vertex_b.id],
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=1),
                height=ReactPlannerGeomProperty(value=300),
                referenceLine=ReactPlannerReferenceLine.CENTER.value,
            ),
            coordinates=[],
        )
        line_b = ReactPlannerLine(
            id="l1",
            name=ReactPlannerName.WALL.value,
            type=ReactPlannerType.WALL.value,
            vertices=[vertex_a.id],
            auxVertices=[vertex_b.id],
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=1),
                height=ReactPlannerGeomProperty(value=300),
                referenceLine=ReactPlannerReferenceLine.CENTER.value,
            ),
            coordinates=[],
        )

        # At the moment we can create lines without vertices as the schema doesn't check this
        layer = ReactPlannerLayer(
            vertices={
                vertex_a.id: vertex_a,
                vertex_b.id: vertex_b,
            },
            lines={line_a.id: line_a, line_b.id: line_b},
        )
        planner_data = ReactPlannerData(
            layers={"layer-1": layer},
        )
        hole = ShapelyToReactPlannerMapper._create_react_hole(
            planner_data=planner_data,
            editor_ready_entity=EditorReadyEntity(geometry=opening_box),
            opening_name=ReactPlannerName.DOOR,
            scale_to_cm=1,
        )
        layer.holes = {hole.id: hole}
        assert hole.line == expected_line_id

    @staticmethod
    def test_ensure_sweeping_points_are_taken_from_editor_ready_entity(
        mocker,
    ):
        mocked_create_sweeping_points = mocker.patch.object(
            ReactPlannerOpeningMapper, "create_default_sweeping_points"
        )

        planner_data = ReactPlannerData(
            layers={
                "layer-1": ReactPlannerLayer(
                    vertices={},
                    lines={},
                )
            },
        )
        opening_id, opening_polygon = ("o0", box(minx=0.25, miny=0, maxx=1.25, maxy=1))
        hole = ShapelyToReactPlannerMapper._create_react_hole(
            planner_data=planner_data,
            opening_id=opening_id,
            editor_ready_entity=EditorReadyEntity(
                geometry=opening_polygon,
                properties=EntityProperties(
                    door_sweeping_points=ReactPlannerDoorSweepingPoints(
                        angle_point=[5, 5], closed_point=[5, 5], opened_point=[5, 5]
                    )
                ),
            ),
            opening_name=ReactPlannerName.DOOR,
            scale_to_cm=1,
        )
        assert not mocked_create_sweeping_points.called
        assert hole.door_sweeping_points.angle_point == [5, 5]
        assert hole.door_sweeping_points.closed_point == [5, 5]
        assert hole.door_sweeping_points.opened_point == [5, 5]

    @staticmethod
    def test_get_auxiliary_vertices_raises_exception():
        """L-shape polygon should generate more than 4 auxiliary vertices"""
        polygon = Polygon([(0, 0), (5, 0), (5, 5), (4, 5), (4, 1), (0, 1), (0, 0)])
        with pytest.raises(ShapelyToReactMappingException):
            ShapelyToReactPlannerMapper._get_auxiliary_vertices_from_polygon(
                polygon=polygon
            )

    @staticmethod
    def test_get_auxiliary_vertices_returns_right_vertices():
        """L-shape polygon should generate more than 4 auxiliary vertices"""
        polygon = box(0, 0, 2, 2)
        vertices = ShapelyToReactPlannerMapper._get_auxiliary_vertices_from_polygon(
            polygon=polygon
        )
        assert len(vertices) == 4
        coords = [(v.x, v.y) for v in vertices]
        assert coords == [(2.0, 0.0), (2.0, 2.0), (0.0, 2.0), (0.0, 0.0)]
