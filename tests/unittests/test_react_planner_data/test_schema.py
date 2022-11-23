import pytest

from common_utils.exceptions import CorruptedAnnotationException
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerData,
    ReactPlannerGeomProperty,
    ReactPlannerHole,
    ReactPlannerHoleHeights,
    ReactPlannerHoleProperties,
    ReactPlannerItem,
    ReactPlannerItemProperties,
    ReactPlannerLine,
    ReactPlannerLineProperties,
    ReactPlannerName,
    ReactPlannerType,
    ReactPlannerVertex,
)


def test_planner_scheme_is_empty():
    vertex = ReactPlannerVertex(x=0, y=0)
    item = ReactPlannerItem(
        x=0,
        y=0,
        name=ReactPlannerName.SINK.value,
        rotation=0,
        properties=ReactPlannerItemProperties(
            width=ReactPlannerGeomProperty(value=0),
            length=ReactPlannerGeomProperty(value=0),
        ),
        type=ReactPlannerType.SINK.value,
    )
    hole = ReactPlannerHole(
        line="asdas",
        properties=ReactPlannerHoleProperties(
            heights=ReactPlannerHoleHeights(),
            width=ReactPlannerGeomProperty(value=0),
            altitude=ReactPlannerGeomProperty(value=0),
            length=ReactPlannerGeomProperty(value=0),
        ),
        coordinates=[],
    )
    line = ReactPlannerLine(
        properties=ReactPlannerLineProperties(
            height=ReactPlannerGeomProperty(value=0),
            width=ReactPlannerGeomProperty(value=0),
        ),
        vertices=["bloh"],
        auxVertices=["blah"],
        coordinates=[],
    )
    area = ReactPlannerArea(coords=[])
    assert ReactPlannerData().is_empty is True

    annotation = ReactPlannerData()
    annotation.layers["layer-1"].vertices = {vertex.id: vertex}
    assert annotation.is_empty is False

    annotation = ReactPlannerData()
    annotation.layers["layer-1"].items = {item.id: item}
    assert annotation.is_empty is False

    annotation = ReactPlannerData()
    annotation.layers["layer-1"].holes = {hole.id: hole}
    assert annotation.is_empty is False

    annotation = ReactPlannerData()
    annotation.layers["layer-1"].lines = {line.id: line}
    assert annotation.is_empty is False

    annotation = ReactPlannerData()
    annotation.layers["layer-1"].areas = {area.id: area}
    assert annotation.is_empty is False


class TestReactPlannerSchemeValidations:
    @staticmethod
    def test_react_planner_scheme_validations_vertex_does_not_reference_back_the_line():
        planner_data = ReactPlannerData()
        # These vertices don't have any reference to the line
        vertex_a = ReactPlannerVertex(x=0, y=0)
        vertex_b = ReactPlannerVertex(x=10, y=10)
        planner_data.layers["layer-1"].vertices = {
            vertex_a.id: vertex_a,
            vertex_b.id: vertex_b,
        }
        line = ReactPlannerLine(
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=10),
                height=ReactPlannerGeomProperty(value=100),
            ),
            vertices=[vertex_a.id, vertex_b.id],
            auxVertices=[vertex_a.id, vertex_b.id],
            coordinates=[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]],
        )
        planner_data.layers["layer-1"].lines = {line.id: line}
        validation_errors = list(planner_data.validate())

        assert len(validation_errors) == 6
        assert (
            len(
                [
                    x
                    for x in validation_errors
                    if "doesn't reference back the line" in x.text
                ]
            )
            == 4
        )

        assert (
            len([x for x in validation_errors if "has repeated vertices" in x.text])
            == 1
        )

    @staticmethod
    def test_react_planner_scheme_validations_vertex_not_referenced_by_any_line_autofixed():
        planner_data = ReactPlannerData()
        # These vertices don't have any reference to the line
        vertex_a = ReactPlannerVertex(x=0, y=0)
        planner_data.layers["layer-1"].vertices = {
            vertex_a.id: vertex_a,
        }
        validation_errors = list(planner_data.validate())
        assert not validation_errors

    @staticmethod
    def test_react_planner_scheme_validations_vertex_references_non_existing_line_autofixed():
        planner_data = ReactPlannerData()
        line_a = ReactPlannerLine(
            coordinates=[[]],
            properties=ReactPlannerLineProperties(
                height=ReactPlannerGeomProperty(value=10),
                width=ReactPlannerGeomProperty(value=10),
            ),
        )
        vertex_a = ReactPlannerVertex(
            id="vertex_a", x=0, y=0, lines=["123", "123", "123", line_a.id]
        )
        vertex_b = ReactPlannerVertex(id="vertex_b", x=10, y=0, lines=[line_a.id])

        vertex_c = ReactPlannerVertex(id="vertex_c", x=0, y=2, lines=[line_a.id])
        vertex_d = ReactPlannerVertex(id="vertex_d", x=2, y=2, lines=[line_a.id])
        vertex_e = ReactPlannerVertex(id="vertex_e", x=2, y=-2, lines=[line_a.id])
        vertex_f = ReactPlannerVertex(id="vertex_f", x=0, y=-2, lines=[line_a.id])
        line_a.vertices = [vertex_a.id, vertex_b.id]
        line_a.auxVertices = [vertex_c.id, vertex_d.id, vertex_e.id, vertex_f.id]

        planner_data.layers["layer-1"].vertices = {
            vertex_a.id: vertex_a,
            vertex_b.id: vertex_b,
            vertex_c.id: vertex_c,
            vertex_d.id: vertex_d,
            vertex_e.id: vertex_e,
            vertex_f.id: vertex_f,
        }
        planner_data.layers["layer-1"].lines = {
            line_a.id: line_a,
        }
        validation_errors = list(planner_data.validate())

        assert not validation_errors
        assert vertex_a.lines == [line_a.id]
        assert vertex_b.lines == [line_a.id]
        assert vertex_c.lines == [line_a.id]
        assert vertex_d.lines == [line_a.id]
        assert vertex_e.lines == [line_a.id]
        assert vertex_f.lines == [line_a.id]

    @staticmethod
    def test_type_names_correct():
        for element_class, values in {
            ReactPlannerLine: {"coordinates": [], "properties": {}},
            ReactPlannerHole: {"coordinates": [], "line": "asdas", "properties": {}},
            ReactPlannerItem: {
                "x": 0,
                "y": 0,
                "rotation": 0,
                "name": ReactPlannerName.SINK.value,
                "type": ReactPlannerType.SINK.value,
                "properties": {},
            },
        }.items():
            with pytest.raises(CorruptedAnnotationException):
                element_class(**{**values, "type": "random"})

            with pytest.raises(CorruptedAnnotationException):
                element_class(**{**values, "name": "random"})

    @staticmethod
    def test_duplicated_vertex_in_line():
        planner_data = ReactPlannerData()
        # These vertices don't have any reference to the line
        vertex_a = ReactPlannerVertex(x=0, y=0)
        vertex_b = ReactPlannerVertex(x=0, y=2)
        vertex_c = ReactPlannerVertex(x=0, y=4)
        vertex_d = ReactPlannerVertex(x=10, y=4)
        vertex_e = ReactPlannerVertex(x=10, y=2)
        vertex_f = ReactPlannerVertex(x=10, y=2.00000001)  # duplicated vertex
        planner_data.layers["layer-1"].vertices = {
            vertex.id: vertex
            for vertex in [vertex_a, vertex_b, vertex_c, vertex_d, vertex_e, vertex_f]
        }
        line = ReactPlannerLine(
            properties=ReactPlannerLineProperties(
                width=ReactPlannerGeomProperty(value=10),
                height=ReactPlannerGeomProperty(value=100),
            ),
            vertices=[vertex_b.id, vertex_e.id],
            auxVertices=[vertex_a.id, vertex_c.id, vertex_d.id, vertex_f.id],
            coordinates=[[[0.0, 0.0], [10.0, 0.0], [10.0, 4.0], [0.0, 4.0]]],
        )
        planner_data.layers["layer-1"].lines = {line.id: line}
        validation_errors = list(planner_data.validate())
        assert (
            len([x for x in validation_errors if "has repeated vertices" in x.text])
            == 1
        )
