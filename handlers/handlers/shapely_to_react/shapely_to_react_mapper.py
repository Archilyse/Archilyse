from itertools import chain
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, Union

import numpy as np
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.constants import FEATURE_SIDES_ON_WALL, SuperTypes
from brooks.types import SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.exceptions import (
    AngleInferenceException,
    OpeningTooSmallException,
    ShapelyToReactMappingException,
)
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerHole,
    ReactPlannerItem,
    ReactPlannerLine,
    ReactPlannerName,
    ReactPlannerVertex,
)
from handlers.shapely_to_react.area_splitters_from_spaces import (
    CreateAreaSplitterFromSpaces,
)
from handlers.shapely_to_react.editor_ready_entity import EditorReadyEntity


class ShapelyToReactPlannerMapper:
    _M_TO_CM_MULTIPLIER = 100
    _ELEMENT_HEIGHTS: Dict[ReactPlannerName, Tuple[float, float]] = {
        ReactPlannerName.WINDOW: (0.9, 2.50),
        ReactPlannerName.DOOR: (0.0, 2.00),
        ReactPlannerName.SLIDING_DOOR: (0.0, 2.00),
    }

    @classmethod
    def create_vertices_and_lines_of_separators(
        cls,
        geometries: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]],
        scale_to_cm: float,
    ) -> Tuple[Dict[str, ReactPlannerVertex], Dict[str, ReactPlannerLine]]:
        planner_vertices = {}
        planner_lines = {}
        for line_type, editor_ready_entities in geometries.items():
            (sub_planner_vertices, sub_planner_lines,) = cls._create_lines_and_vertices(
                editor_ready_entities=editor_ready_entities,
                line_type=line_type,
                scale_to_cm=scale_to_cm,
            )
            planner_vertices.update(sub_planner_vertices)
            planner_lines.update(sub_planner_lines)
        return planner_vertices, planner_lines

    @classmethod
    def get_planner_items(
        cls,
        geometries: Mapping[
            SuperTypes, Mapping[ReactPlannerName, Iterable[EditorReadyEntity]]
        ],
        scale_to_cm: float,
    ) -> Dict[str, ReactPlannerItem]:
        walls_w_metadata = geometries[SuperTypes.SEPARATORS][ReactPlannerName.WALL]

        planner_items = {}
        for feature_type, features in geometries[SuperTypes.ITEMS].items():
            for feature in features:
                feature_geometry: Polygon = feature.geometry
                planner_item = ReactPlannerElementFactory.get_item(
                    polygon=feature_geometry,
                    name=feature_type,
                    scale_to_cm=scale_to_cm,
                )
                try:
                    cls._infer_angle_from_walls(
                        planner_item=planner_item,
                        walls=[wall.geometry for wall in walls_w_metadata],
                    )
                except AngleInferenceException:
                    logger.warning(
                        f"Could not infer angle from feature in position {feature_geometry.centroid}"
                    )

                planner_items[planner_item.id] = planner_item

        return planner_items

    @classmethod
    def add_area_splitters_to_react_planner_data(
        cls,
        planner_elements: ReactPlannerData,
        spaces: List[MultiPolygon],
        scale_to_cm: float,
    ) -> List[Polygon]:
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        separators, _ = ReactPlannerToBrooksMapper.get_separators(
            planner_elements=planner_elements,
            post_processed=False,
        )
        area_splitters = CreateAreaSplitterFromSpaces.create_area_splitters(
            separators=unary_union([s.footprint for s in separators]),
            spaces=cls._merge_spaces_geometries(spaces_geometries=spaces),
        )
        splitter_vertices, splitter_lines = cls._create_lines_and_vertices(
            editor_ready_entities=[
                EditorReadyEntity(
                    geometry=area_splitter.minimum_rotated_rectangle,
                )
                for area_splitter in area_splitters
            ],
            line_type=ReactPlannerName.AREA_SPLITTER,
            scale_to_cm=scale_to_cm,
        )

        planner_elements.layers["layer-1"].vertices.update(splitter_vertices)
        planner_elements.layers["layer-1"].lines.update(splitter_lines)
        return area_splitters

    @classmethod
    def create_holes_assigned_to_walls(
        cls,
        planner_data: ReactPlannerData,
        all_opening_elements: Mapping[ReactPlannerName, Iterable[EditorReadyEntity]],
        scale_to_cm: float,
    ) -> Dict[str, ReactPlannerHole]:
        react_planner_holes: Dict[str, ReactPlannerHole] = {}

        for opening_name, opening_elements in all_opening_elements.items():
            for editor_ready_entity in opening_elements:
                if hole := cls._create_react_hole(
                    planner_data=planner_data,
                    opening_name=opening_name,
                    editor_ready_entity=editor_ready_entity,
                    scale_to_cm=scale_to_cm,
                ):
                    react_planner_holes[hole.id] = hole

        return react_planner_holes

    @staticmethod
    def _merge_spaces_geometries(
        spaces_geometries: List[MultiPolygon],
    ) -> List[Polygon]:
        """
        Method merges separate polygons of the same space to 1 polygon if possible
        and returns geometries as a flat list of polygons.
        This is necessary as otherwise we create area splitters inside the same space but we should
        only create them between spaces
        """
        unified_geometries: List[MultiPolygon] = [
            as_multipolygon(unary_union(space_geometries))
            for space_geometries in spaces_geometries
        ]
        return [
            polygon
            for space_geometries in unified_geometries
            for polygon in space_geometries.geoms
        ]

    @classmethod
    def _create_lines_and_vertices(
        cls,
        editor_ready_entities: Iterable[EditorReadyEntity],
        line_type: ReactPlannerName,
        scale_to_cm: float,
    ) -> Tuple[Dict[str, ReactPlannerVertex], Dict[str, ReactPlannerLine]]:
        planner_lines: Dict[str, ReactPlannerLine] = {}
        planner_vertices: Dict[str, ReactPlannerVertex] = {}
        for editor_ready_entity in editor_ready_entities:
            normalized_polygon = editor_ready_entity.geometry
            width = ReactPlannerElementFactory.get_line_width(
                scaled_geometry=normalized_polygon,
                line_type=line_type,
                scale_to_cm=scale_to_cm,
            )
            vertices = cls._get_default_vertices_from_line(wall=normalized_polygon)
            auxiliary_vertices = cls._get_auxiliary_vertices_from_polygon(
                polygon=normalized_polygon
            )
            line: ReactPlannerLine = ReactPlannerElementFactory.get_line_from_vertices(
                vertices=vertices,
                auxiliary_vertices=auxiliary_vertices,
                width=width,
                name=line_type,
                line_polygon=normalized_polygon,
            )
            planner_lines[line.id] = line
            planner_vertices.update(
                {v.id: v for v in chain(vertices, auxiliary_vertices)}
            )
        return planner_vertices, planner_lines

    @staticmethod
    def _get_auxiliary_vertices_from_polygon(
        polygon: Polygon,
    ) -> List[ReactPlannerVertex]:
        auxiliary_vertices = [
            ReactPlannerVertex(x=x, y=y) for (x, y) in polygon.exterior.coords[:-1]
        ]
        if len(auxiliary_vertices) != 4:
            # This can not happen as long as we have a minimum rotated rectangle, so this is here as a safeguard
            raise ShapelyToReactMappingException(
                "A separator line doesn't have exactly 4 aux vertices"
            )
        return auxiliary_vertices

    @classmethod
    def _create_react_hole(
        cls,
        planner_data: ReactPlannerData,
        editor_ready_entity: EditorReadyEntity,
        opening_name: ReactPlannerName,
        scale_to_cm: float,
        opening_id: Optional[str] = None,
        required_underlying_wall_geometry: Optional[Polygon] = None,
    ) -> Union[ReactPlannerHole, None]:
        opening_polygon = editor_ready_entity.geometry
        required_underlying_wall_geometry = (
            required_underlying_wall_geometry or opening_polygon
        )
        try:
            line_id = cls._find_or_create_intersecting_wall(
                opening_polygon=required_underlying_wall_geometry,
                planner_data=planner_data,
                scale_to_cm=scale_to_cm,
            )
        except OpeningTooSmallException:
            return None

        hole = ReactPlannerElementFactory.get_hole(
            editor_ready_entity=editor_ready_entity,
            opening_id=opening_id,
            separator_id=line_id,
            separator_width=int(
                planner_data.lines_by_id[line_id].properties.width.value
            ),
            opening_polygon=opening_polygon,
            name=opening_name,
            height=(
                cls._ELEMENT_HEIGHTS[opening_name][0] * 100,
                cls._ELEMENT_HEIGHTS[opening_name][1] * 100,
            ),
            scale_to_cm=scale_to_cm,
        )
        planner_data.lines_by_id[line_id].holes.append(hole.id)
        return hole

    @classmethod
    def _find_or_create_intersecting_wall(
        cls,
        opening_polygon: Polygon,
        planner_data: ReactPlannerData,
        scale_to_cm: float,
    ) -> str:
        intersecting_walls_by_id = [
            (line_id, wall_polygon, wall_polygon.intersection(opening_polygon))
            for line_id, wall_polygon in planner_data.separator_polygons_by_id(
                separator_type=SeparatorType.WALL
            ).items()
            if wall_polygon.intersects(opening_polygon)
            and wall_polygon.intersection(opening_polygon).area / opening_polygon.area
            > 0.1  # ensures that slightly intersecting walls are not
            # considered (important for create wall from hole to work correctly)
        ]
        intersections_sorted = sorted(intersecting_walls_by_id, key=lambda x: x[2].area)
        if intersections_sorted:
            line_id, _, _ = intersections_sorted[-1]
        else:
            line_id, _ = cls._create_wall_from_hole(
                planner_data=planner_data,
                opening_polygon=opening_polygon,
                scale_to_cm=scale_to_cm,
            )

        return line_id

    @classmethod
    def _create_wall_from_hole(
        cls,
        planner_data: ReactPlannerData,
        opening_polygon: Polygon,
        scale_to_cm: float,
    ) -> Tuple[str, Polygon]:
        vertices, lines = cls._create_lines_and_vertices(
            editor_ready_entities=[EditorReadyEntity(geometry=opening_polygon)],
            line_type=ReactPlannerName.WALL,
            scale_to_cm=scale_to_cm,
        )
        planner_data.layers["layer-1"].lines.update(lines)
        planner_data.layers["layer-1"].vertices.update(vertices)
        planner_data.separator_polygons_by_id.cache_clear()  # This is necessary as we added a new wall
        line_id = [_id for _id in lines.keys()][0]
        if line_id not in planner_data.separator_polygons_by_id(
            separator_type=SeparatorType.WALL
        ):
            raise OpeningTooSmallException

        return line_id, opening_polygon

    @staticmethod
    def _get_default_vertices_from_line(wall: Polygon) -> List[ReactPlannerVertex]:
        centerline = get_center_line_from_rectangle(polygon=wall, only_longest=True)[0]
        point_a, point_b = centerline.coords[:]
        return [
            ReactPlannerVertex(x=point_a[0], y=point_a[1]),
            ReactPlannerVertex(x=point_b[0], y=point_b[1]),
        ]

    @staticmethod
    def _infer_angle_from_walls(planner_item: ReactPlannerItem, walls: List[Polygon]):
        """
        If we have an item who has to point away from a wall, we have two cases:

             ▲        ▲
             │        │
            ┌┼┐       │
            │|│     ┌─┼─┐
          ──┴─┴──  ─┴───┴─
           SHORT    LONG

        In cases like a toilet, the short side has to be aligned with the wall, in the case of a sink,
        the long side has to be on the wall. Our goal is to represent the item's geometry (width, length, rotation)
        such that:
         * the item is displayed like the original geometry in the editor
         * the arrow points in the correct direction (rotation angle is correct)

        The ReactPlanner convention for angles is atan2(y, x), width is dx and length is dy

          y ▲                     y ▲
            │        0              │     w
            │        ▲              │   ┌────┐
            │        │              │   │    │
            │ +90 ◄──┼──► -90       │   │    │ l
            │        │              │   │    │
            │        ▼              │   └────┘
            │       180             │
            └──────────────────►    └───────────►
                                x                x

        So if we have an arbitrary geometry, we:
         1) infer the axis pointing away from the wall
         2) compute the angle according to convention based on this axis
         3) make sure the width/length of the element are correct. This is done in ReactPlannerElementFactory.get_item.
        """
        feature = ReactPlannerToBrooksMapper.get_feature_from_item(item=planner_item)
        if FEATURE_SIDES_ON_WALL.get(feature.type) is not None:
            (
                intersecting_side,
                _,
            ) = feature.get_intersecting_and_orthogonal_side_from_walls(walls=walls)
            axis = feature.line_string_to_vector(intersecting_side)
            planner_item.rotation = np.arctan2(axis[1], axis[0]) * 360 / (2 * np.pi)
