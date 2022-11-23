import uuid
from itertools import chain
from math import ceil
from typing import Dict, List, Optional, Tuple

from shapely.geometry import MultiPolygon, Polygon, mapping

from brooks import SpaceMaker
from brooks.constants import FEATURE_SIDES_ON_WALL, FeatureSide
from brooks.models import SimSeparator
from brooks.types import AreaType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from brooks.utils import (
    get_default_element_height,
    get_default_element_lower_edge,
    get_default_element_upper_edge,
)
from common_utils.constants import LENGTH_SI_UNITS, WALL_BUFFER_BY_SI_UNIT
from dufresne.polygon import get_sides_as_lines_by_length
from dufresne.polygon.parameters_minimum_rotated_rectangle import (
    get_parameters_of_minimum_rotated_rectangle,
)
from handlers.editor_v2.editor_v2_element_mapper import (
    ReactPlannerOpeningMapper,
    ReactPlannerToBrooksMapper,
)
from handlers.editor_v2.schema import (
    HOLE_TYPES_WITH_SWEEPING_POINTS,
    ReactPlannerArea,
    ReactPlannerAreaProperties,
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
    ReactPlannerReferenceLine,
    ReactPlannerType,
    ReactPlannerVertex,
    react_planner_name_to_type,
)
from handlers.shapely_to_react.editor_ready_entity import EditorReadyEntity


class ReactPlannerElementFactory:
    AREA_SPLITTER_THICKNESS = 1  # in cm
    MINIMUM_SEPARATOR_THICKNESS = 5  # cm

    @classmethod
    def get_line_from_vertices(
        cls,
        vertices: List[ReactPlannerVertex],
        auxiliary_vertices: List[ReactPlannerVertex],
        width: float,
        name: ReactPlannerName,
        line_polygon: Polygon,
        reference_line: str = ReactPlannerReferenceLine.CENTER.value,
    ) -> ReactPlannerLine:
        properties = ReactPlannerLineProperties(
            height=ReactPlannerGeomProperty(
                value=get_default_element_height(element_type=SeparatorType.WALL) * 100
            ),
            width=ReactPlannerGeomProperty(value=width),
            referenceLine=reference_line,
        )
        line = ReactPlannerLine(
            properties=properties,
            type=react_planner_name_to_type[name].value,
            name=name.value,
            vertices=[vertices[0].id, vertices[1].id],
            auxVertices=[v.id for v in auxiliary_vertices],
            coordinates=mapping(line_polygon)["coordinates"],
        )
        for vertex in chain(vertices, auxiliary_vertices):
            vertex.lines.append(line.id)
        return line

    @classmethod
    def get_line_width(
        cls, scaled_geometry: Polygon, line_type: ReactPlannerName, scale_to_cm: float
    ) -> int:
        if line_type is ReactPlannerName.AREA_SPLITTER:
            return cls.AREA_SPLITTER_THICKNESS
        shortest_side = get_sides_as_lines_by_length(polygon=scaled_geometry)[0]
        shortest_side_in_cm = cls._round_width_to_nearest_integer_in_cm(
            shortest_side.length * scale_to_cm
        )
        return max(shortest_side_in_cm, cls.MINIMUM_SEPARATOR_THICKNESS)

    @classmethod
    def get_hole(
        cls,
        editor_ready_entity: EditorReadyEntity,
        separator_id: str,
        separator_width: int,
        opening_polygon: Polygon,
        height: Tuple,
        name: ReactPlannerName,
        scale_to_cm: float,
        opening_id: Optional[str] = None,
    ) -> ReactPlannerHole:
        if (
            name == ReactPlannerName.DOOR
            and editor_ready_entity.properties.door_subtype
        ):
            name = editor_ready_entity.properties.door_subtype
        door_lines = get_sides_as_lines_by_length(polygon=opening_polygon)
        door_sweeping_points = None
        if react_planner_name_to_type[name] in HOLE_TYPES_WITH_SWEEPING_POINTS:
            door_sweeping_points = (
                editor_ready_entity.properties.door_sweeping_points
                or ReactPlannerOpeningMapper.create_default_sweeping_points(
                    opening_line=get_center_line_from_rectangle(
                        polygon=opening_polygon, only_longest=True
                    )[0],
                )
            )

        return ReactPlannerHole(
            id=opening_id or str(uuid.uuid4()),
            line=separator_id,
            name=name.value,
            type=react_planner_name_to_type[name].value,
            properties=ReactPlannerHoleProperties(
                length=ReactPlannerGeomProperty(
                    value=cls._round_down_opening_length_to_nearest_int_in_cm(
                        door_lines[-1].length * scale_to_cm
                    )
                ),
                heights=ReactPlannerHoleHeights(
                    lower_edge=height[0], upper_edge=height[1]
                ),
                altitude=ReactPlannerGeomProperty(value=height[0] or 0.0),
                width=ReactPlannerGeomProperty(value=separator_width),
            ),
            coordinates=mapping(opening_polygon)["coordinates"],
            door_sweeping_points=door_sweeping_points,
        )

    @staticmethod
    def create_areas_from_separators(
        planner_data: ReactPlannerData,
        area_splitter_polygons: List[Polygon],
        spaces_classified: Optional[List[Tuple[MultiPolygon, AreaType]]] = None,
        length_si_unit: LENGTH_SI_UNITS = LENGTH_SI_UNITS.METRE,
    ) -> Dict[str, ReactPlannerArea]:
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        separators, _ = ReactPlannerToBrooksMapper.get_separators(
            planner_elements=planner_data,
            post_processed=False,
        )
        if not separators:
            return {}
        spaces = SpaceMaker().create_spaces_and_areas(
            separators=separators,
            splitters={
                SimSeparator(
                    footprint=polygon, separator_type=SeparatorType.AREA_SPLITTER
                )
                for polygon in area_splitter_polygons
            },
            generic_space_height=(
                get_default_element_lower_edge("GENERIC_SPACE_HEIGHT"),
                get_default_element_upper_edge("GENERIC_SPACE_HEIGHT"),
            ),
            wall_buffer=WALL_BUFFER_BY_SI_UNIT[length_si_unit],
        )
        areas_from_separators = [
            area.footprint for space in spaces for area in space.areas
        ]

        areas_by_id: Dict[str, ReactPlannerArea] = {}
        for area in areas_from_separators:
            planner_area = ReactPlannerArea(
                id=str(uuid.uuid4()),
                coords=[[list(coord) for coord in area.exterior.coords[:]]],
                properties=ReactPlannerAreaProperties(
                    areaType=AreaType.NOT_DEFINED.name
                ),
            )
            if spaces_classified:
                matching_area_type = [
                    area_type
                    for (geom, area_type) in spaces_classified
                    if area.representative_point().within(geom)
                ]
                if matching_area_type:
                    planner_area.properties.areaType = matching_area_type[0].name
            areas_by_id[planner_area.id] = planner_area
        return areas_by_id

    @classmethod
    def get_item(
        cls,
        polygon: Polygon,
        name: ReactPlannerName,
        scale_to_cm: float,
        properties=None,
    ) -> ReactPlannerItem:
        properties = properties or {}

        (x, y, width, length, rotation,) = get_parameters_of_minimum_rotated_rectangle(
            polygon=polygon,
            return_annotation_convention=False,
            rotation_axis_convention="lower_left",
            align_short_side_to_x_axis=FEATURE_SIDES_ON_WALL.get(
                ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_FEATURES_MAP[
                    react_planner_name_to_type[name]
                ]
            )
            == FeatureSide.SHORT_SIDE,
        )
        return ReactPlannerItem(
            name=name.value,
            type=react_planner_name_to_type[name].value,
            x=polygon.centroid.x,
            y=polygon.centroid.y,
            rotation=rotation,
            properties=ReactPlannerItemProperties(
                width=ReactPlannerGeomProperty(
                    value=cls._round_width_to_nearest_integer_in_cm(width * scale_to_cm)
                ),
                length=ReactPlannerGeomProperty(
                    value=cls._round_width_to_nearest_integer_in_cm(
                        length * scale_to_cm
                    )
                ),
                **properties
            ),
        )

    @staticmethod
    def get_line_from_coordinates_and_width(
        coordinates: List[List[List[float]]],
        width_in_cm: int,
        line_type: ReactPlannerType,
    ) -> ReactPlannerLine:
        height = get_default_element_height(element_type=SeparatorType.WALL) * 100
        return ReactPlannerLine(
            coordinates=coordinates,
            type=line_type.value,
            properties=ReactPlannerLineProperties(
                height=ReactPlannerGeomProperty(value=height),
                width=ReactPlannerGeomProperty(value=width_in_cm),
            ),
        )

    @staticmethod
    def _round_width_to_nearest_integer_in_cm(width: float) -> int:
        """
        React planner elements should have widht & lenghts in cm as integers.
        In order to avoid gaps between elements we always round up (ceil)
        """
        return ceil(width)

    @staticmethod
    def _round_down_opening_length_to_nearest_int_in_cm(length: float) -> int:
        """
        To avoid issues in the editor like an opening overlaping multiple walls we
        need to round down the opening length instead of rounding up
        """
        return int(length)
