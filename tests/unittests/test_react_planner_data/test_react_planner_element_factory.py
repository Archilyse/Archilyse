from typing import Dict, List

import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPoint, Point, Polygon, box

from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerGeomProperty,
    ReactPlannerLayer,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerName,
    ReactPlannerVertex,
)


def get_coordinates_from_vertices(
    line_vertices: List[ReactPlannerVertex],
    planner_vertices: Dict[str, ReactPlannerVertex],
) -> List[List[List[float]]]:
    c = MultiPoint(
        points=[
            Point(planner_vertices[v].x, planner_vertices[v].y) for v in line_vertices
        ]
    )
    return [[[x, y] for (x, y) in c.minimum_rotated_rectangle.exterior.coords[:]]]


class TestReactPlannerElementFactory:
    def test_element_factory_get_areas(self):
        """
                   a
           1┌─────────────┐2
            │             │ b
        d   │             │
           4└─────────────┘3
                   c
        """
        planner_vertices = {
            "1": ReactPlannerVertex(id="1", x=0, y=10, lines=["a", "d"]),
            "1a": ReactPlannerVertex(id="1a", x=0, y=11, lines=["a"]),
            "1b": ReactPlannerVertex(id="1b", x=0, y=9, lines=["a"]),
            "1c": ReactPlannerVertex(id="1c", x=-1, y=10, lines=["d"]),
            "1d": ReactPlannerVertex(id="1d", x=1, y=10, lines=["d"]),
            "2": ReactPlannerVertex(id="2", x=20, y=10, lines=["a", "b"]),
            "2a": ReactPlannerVertex(id="2a", x=20, y=9, lines=["a"]),
            "2b": ReactPlannerVertex(id="2b", x=20, y=11, lines=["a"]),
            "2c": ReactPlannerVertex(id="2c", x=19, y=10, lines=["b"]),
            "2d": ReactPlannerVertex(id="2d", x=21, y=10, lines=["b"]),
            "3": ReactPlannerVertex(id="3", x=20, y=0, lines=["b", "c"]),
            "3a": ReactPlannerVertex(id="3a", x=19, y=0, lines=["b"]),
            "3b": ReactPlannerVertex(id="3b", x=21, y=0, lines=["b"]),
            "3c": ReactPlannerVertex(id="3c", x=20, y=1, lines=["c"]),
            "3d": ReactPlannerVertex(id="3d", x=20, y=-1, lines=["c"]),
            "4": ReactPlannerVertex(id="4", x=0, y=0, lines=["c", "d"]),
            "4a": ReactPlannerVertex(id="4a", x=-1, y=0, lines=["d"]),
            "4b": ReactPlannerVertex(id="4b", x=1, y=0, lines=["d"]),
            "4c": ReactPlannerVertex(id="4c", x=0, y=-1, lines=["c"]),
            "4d": ReactPlannerVertex(id="4d", x=0, y=1, lines=["c"]),
        }
        properties = ReactPlannerLineProperties(
            width=ReactPlannerGeomProperty(value=1),
            height=ReactPlannerGeomProperty(value=0),
        )
        planner_lines = {
            "a": ReactPlannerLine(
                id="a",
                vertices=["1", "2"],
                auxVertices=["1a", "1b", "2a", "2b"],
                properties=properties,
                coordinates=get_coordinates_from_vertices(
                    line_vertices=["1", "2"] + ["1a", "1b", "2a", "2b"],
                    planner_vertices=planner_vertices,
                ),
            ),
            "b": ReactPlannerLine(
                id="b",
                vertices=["2", "3"],
                auxVertices=["2c", "2d", "3a", "3b"],
                properties=properties,
                coordinates=get_coordinates_from_vertices(
                    line_vertices=["2", "3"] + ["2c", "2d", "3a", "3b"],
                    planner_vertices=planner_vertices,
                ),
            ),
            "c": ReactPlannerLine(
                id="c",
                vertices=["3", "4"],
                auxVertices=["3c", "3d", "4c", "4d"],
                properties=properties,
                coordinates=get_coordinates_from_vertices(
                    line_vertices=["3", "4"] + ["3c", "3d", "4c", "4d"],
                    planner_vertices=planner_vertices,
                ),
            ),
            "d": ReactPlannerLine(
                id="d",
                vertices=["4", "1"],
                auxVertices=["1c", "1d", "4a", "4b"],
                properties=properties,
                coordinates=get_coordinates_from_vertices(
                    line_vertices=["4", "1"] + ["1c", "1d", "4a", "4b"],
                    planner_vertices=planner_vertices,
                ),
            ),
        }

        created_areas = ReactPlannerElementFactory.create_areas_from_separators(
            planner_data=ReactPlannerData(
                width=100,
                height=100,
                layers={
                    "layer-1": ReactPlannerLayer(
                        vertices=planner_vertices,
                        lines=planner_lines,
                    )
                },
            ),
            area_splitter_polygons=[],
        )
        assert len(created_areas) == 1
        assert not DeepDiff(
            [
                [
                    [
                        [1.001, 8.999],
                        [18.999, 8.999],
                        [18.999, 1.001],
                        [1.001, 1.001],
                        [1.001, 8.999],
                    ]
                ]
            ],
            [area.coords for area in created_areas.values()],
            ignore_order=True,
            significant_digits=2,
        )

    def test_no_separators_returns_empty_area_dict(self, mocker):
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        mocker.patch.object(
            ReactPlannerToBrooksMapper, "get_separators", return_value=([], None)
        )
        created_areas = ReactPlannerElementFactory.create_areas_from_separators(
            planner_data=None,
            area_splitter_polygons=[],
        )
        assert isinstance(created_areas, dict)
        assert not created_areas

    @staticmethod
    @pytest.mark.parametrize(
        "polygon, expected", [(box(0, 0, 3, 3), 5), (box(0, 0, 10, 10), 10)]
    )
    def test_planner_element_factory_get_line_width(polygon, expected):
        assert (
            ReactPlannerElementFactory.get_line_width(
                scaled_geometry=polygon, line_type=ReactPlannerName.WALL, scale_to_cm=1
            )
            == expected
        )

    @staticmethod
    def test_get_line_from_vertices():
        vertex_a = ReactPlannerVertex(x=0, y=0)
        vertex_b = ReactPlannerVertex(x=0, y=0)
        vertex_aux = ReactPlannerVertex(x=0, y=0)
        random_width = 20.0
        line = ReactPlannerElementFactory.get_line_from_vertices(
            auxiliary_vertices=[vertex_aux],
            vertices=[vertex_a, vertex_b],
            width=random_width,
            name=ReactPlannerName.WALL,
            line_polygon=Polygon(),
        )
        assert line.properties.height.value == 260.0
        assert line.properties.width.value == random_width
        assert vertex_a.lines == [line.id]
        assert vertex_b.lines == [line.id]
        assert vertex_aux.lines == [line.id]
        assert line.vertices == [vertex_a.id, vertex_b.id]
        assert line.auxVertices == [vertex_aux.id]
