import numpy
from shapely.affinity import scale as shapely_scale
from shapely.geometry import mapping, shape

from brooks.types import OpeningType, SeparatorType
from common_utils.constants import GEOMETRIES_PRECISION, SI_UNIT_BY_NAME
from handlers.editor_v2.schema import ReactPlannerData, ReactPlannerName

BROOKS_TYPE_TO_REACT_PLANNER_NAME = {
    SeparatorType.AREA_SPLITTER: ReactPlannerName.AREA_SPLITTER,
    SeparatorType.WALL: ReactPlannerName.WALL,
    SeparatorType.COLUMN: ReactPlannerName.COLUMN,
    SeparatorType.RAILING: ReactPlannerName.RAILING,
    OpeningType.DOOR: ReactPlannerName.DOOR,
    OpeningType.ENTRANCE_DOOR: ReactPlannerName.ENTRANCE_DOOR,
    OpeningType.WINDOW: ReactPlannerName.WINDOW,
}

ROUNDING_PRECISION = GEOMETRIES_PRECISION


def pixels_to_meters_scale(scale: float) -> float:
    return float(numpy.sqrt(scale) * SI_UNIT_BY_NAME["cm"].value)


def cm_to_pixels_scale(scale: float):
    return 1 / numpy.sqrt(scale)


def m_to_pixels_scale(scale: float):
    return (1 / SI_UNIT_BY_NAME["cm"].value) / numpy.sqrt(scale)


def update_planner_element_coordinates(data: ReactPlannerData, scaled: bool):
    scale_factor = pixels_to_meters_scale(scale=data.scale)
    _transform_vertices(
        planner_elements=data,
        scale_factor=scale_factor if scaled else 1.0,
    )
    _transform_coordinates(
        planner_elements=data,
        scale_factor=scale_factor if scaled else 1.0,
    )
    _transform_properties(
        planner_elements=data,
        scale_factor=SI_UNIT_BY_NAME["cm"].value
        if scaled
        else cm_to_pixels_scale(scale=data.scale),
        scaled=scaled,
    )


def _transform_vertices(
    planner_elements: ReactPlannerData,
    scale_factor: float,
):
    for layer in planner_elements.layers.values():
        for vertex in layer.vertices.values():
            vertex.x = round(vertex.x * scale_factor, ROUNDING_PRECISION)
            vertex.y = round(vertex.y * scale_factor, ROUNDING_PRECISION)

        for item in layer.items.values():
            item.x = round(item.x * scale_factor, ROUNDING_PRECISION)
            item.y = round(item.y * scale_factor, ROUNDING_PRECISION)


def _transform_coordinates(planner_elements: ReactPlannerData, scale_factor: float):
    for line in planner_elements.layers["layer-1"].lines.values():
        line.coordinates = [
            [[x * scale_factor, y * scale_factor] for [x, y] in line.coordinates[0]]
        ]
    for hole in planner_elements.layers["layer-1"].holes.values():
        hole.coordinates = [
            [[x * scale_factor, y * scale_factor] for [x, y] in hole.coordinates[0]]
        ]
        if sweeping_points := hole.door_sweeping_points:
            for point_type in sweeping_points.__annotations__:
                [x, y] = getattr(sweeping_points, point_type)
                setattr(
                    sweeping_points,
                    point_type,
                    [x * scale_factor, y * scale_factor],
                )
    for area in planner_elements.layers["layer-1"].areas.values():
        area.coords = mapping(
            shapely_scale(
                shape(
                    {"type": "Polygon", "coordinates": area.coords}
                ),  # We could also use the cached property area.polygon but we would then need
                # to delete the cache after we changed the coords
                xfact=scale_factor,
                yfact=scale_factor,
                origin=(0, 0),
            )
        )["coordinates"]


def _transform_properties(
    planner_elements: ReactPlannerData,
    scale_factor: float,
    scaled: bool,
):
    for layer in planner_elements.layers.values():
        for _, item in layer.items.items():
            item.properties.width.value *= scale_factor
            item.properties.length.value *= scale_factor

        for _, line in layer.lines.items():
            line.properties.width.value = round(
                line.properties.width.value * scale_factor,
                ROUNDING_PRECISION,
            )

        for _, hole in layer.holes.items():
            hole.properties.width.value = round(
                hole.properties.width.value * scale_factor, ROUNDING_PRECISION
            )
            hole.properties.length.value = round(
                hole.properties.length.value * scale_factor,
                ROUNDING_PRECISION,
            )
            if hole.properties.heights.upper_edge and scaled:
                hole.properties.heights.upper_edge *= SI_UNIT_BY_NAME["cm"].value

            if hole.properties.heights.lower_edge and scaled:
                hole.properties.heights.lower_edge *= SI_UNIT_BY_NAME["cm"].value
