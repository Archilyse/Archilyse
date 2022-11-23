from typing import Iterable

from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString, MultiLineString
from shapely.ops import linemerge, unary_union

from brooks.models import SimLayout
from brooks.types import AreaType, FeatureType
from common_utils.utils import pairwise
from dufresne.linestring_add_width import add_width_to_linestring_improved
from handlers import PlanLayoutHandler
from handlers.editor_v2 import ReactPlannerElementFactory, ReactPlannerHandler
from handlers.editor_v2.schema import (
    ReactPlannerName,
    ReactPlannerSchema,
    ReactPlannerVertex,
)
from handlers.editor_v2.utils import pixels_to_meters_scale

KITCHEN_ELEMENT_BUFFER_IN_METERS = 0.05
AREA_BUFFER_IN_METERS = 0.02
AREA_SPLITTER_WIDTH_IN_METERS = 0.01


class CreateAreaSplittersFromKitchenElements:
    @classmethod
    def create_and_add_area_splitters_to_react_data(cls, plan_id: int) -> dict:
        data = ReactPlannerHandler().get_data(plan_id=plan_id)
        from_meters_to_pixel = 1 / pixels_to_meters_scale(scale=data.scale)
        layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
            scaled=True, classified=True
        )
        for splitters in cls.create_splitters(layout=layout):
            main_vertices, aux_vertices, lines = cls.get_vertices_lines_from_splitter(
                splitters=splitters, from_meters_to_pixel=from_meters_to_pixel
            )

            for vertex in main_vertices:
                data.layers["layer-1"].vertices[vertex.id] = vertex
            for vertex in aux_vertices:
                data.layers["layer-1"].vertices[vertex.id] = vertex
            for line in lines:
                data.layers["layer-1"].lines[line.id] = line
        return ReactPlannerSchema().dump(data)

    @classmethod
    def create_splitters(cls, layout: SimLayout) -> Iterable[LineString]:

        for area in layout.areas:
            if area.type == AreaType.KITCHEN:
                continue
            if kitchen_features := [
                feature
                for feature in area.features
                if feature.type == FeatureType.KITCHEN
            ]:
                if len(kitchen_features) == 1:
                    continue
                kitchen_features_bounding_box = unary_union(
                    [feature.footprint for feature in kitchen_features]
                ).minimum_rotated_rectangle.buffer(
                    KITCHEN_ELEMENT_BUFFER_IN_METERS,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                )
                kitchen_perimeter = LineString(
                    [coord for coord in kitchen_features_bounding_box.exterior.coords]
                )
                area_splitters = area.footprint.buffer(
                    AREA_BUFFER_IN_METERS,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                ).intersection(kitchen_perimeter)

                if isinstance(area_splitters, MultiLineString):
                    area_splitters = linemerge(area_splitters)

                if isinstance(area_splitters, LineString):
                    yield area_splitters

    @classmethod
    def get_vertices_lines_from_splitter(
        cls, splitters: LineString, from_meters_to_pixel: float
    ):

        main_vertices = [
            ReactPlannerVertex(
                x=coord[0] * from_meters_to_pixel, y=coord[1] * from_meters_to_pixel
            )
            for coord in splitters.coords
        ]
        all_aux_vertices = []
        all_lines = []
        for vertex_a, vertex_b in pairwise(main_vertices):
            polygon = add_width_to_linestring_improved(
                line=LineString([(vertex_a.x, vertex_a.y), (vertex_b.x, vertex_b.y)]),
                width=AREA_SPLITTER_WIDTH_IN_METERS * from_meters_to_pixel,
            )
            auxiliary_vertices = [
                ReactPlannerVertex(x=x, y=y) for (x, y) in polygon.exterior.coords[:-1]
            ]
            all_aux_vertices.extend(auxiliary_vertices)
            line = ReactPlannerElementFactory.get_line_from_vertices(
                vertices=[vertex_a, vertex_b],
                auxiliary_vertices=auxiliary_vertices,
                width=AREA_SPLITTER_WIDTH_IN_METERS,
                name=ReactPlannerName.AREA_SPLITTER,
                line_polygon=polygon,
            )
            all_lines.append(line)
        return main_vertices, all_aux_vertices, all_lines
