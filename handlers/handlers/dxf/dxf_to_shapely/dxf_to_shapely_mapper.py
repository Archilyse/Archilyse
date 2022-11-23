from dataclasses import dataclass
from functools import cached_property
from itertools import groupby
from typing import TYPE_CHECKING, Iterator, Literal

from ezdxf.addons import geo
from ezdxf.entities import Arc, DXFEntity, Hatch, Line, LWPolyline
from ezdxf.layouts import Modelspace
from pygeos import difference, from_shapely, intersects, to_shapely, union_all
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    GeometryCollection,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
    shape,
)
from shapely.ops import unary_union
from shapely.validation import explain_validity, make_valid

from brooks.types import AreaType
from common_utils.exceptions import DXFImportException
from common_utils.logger import logger
from dufresne.polygon import get_sides_as_lines_by_length
from dufresne.polygon.utils import as_multipolygon
from handlers.dxf.dxf_constants import (
    ARC_DEGREE_PER_POINT,
    AREA_NAME_ENTITY_TYPE,
    AREA_NAME_LAYER,
    BLOCK_KEYWORDS,
    BUFFER_LINES_OF_ELEVATOR_GEOMETRIES,
    DISTANCE_TO_GROUP_STAIRS,
    ELEVATOR_MINIMUM_DIMENSION,
    KITCHEN_MINIMUM_SIDE_LENGTH,
    LAYER_KEYWORDS,
    MINIMUM_WINDOW_SIZE_IN_CM2,
    RAILING_DEFAULT_WIDTH_IN_CM,
    WALL_DEFAULT_WIDTH_IN_CM,
    WALL_LAYERS_HATCHES,
)
from handlers.dxf.dxf_to_shapely.dxf_to_shapely_utils import (
    close_parallel_lines_into_polygons,
    exclude_polygons_split_by_walls,
    filter_overlapping_or_small_polygons,
    filter_too_big_separators,
    get_area_type_from_room_stamp,
    get_bounding_boxes_for_groups_of_geometries,
    group_line_and_arcs_into_rectangles,
    iteratively_merge_by_intersection,
    lines_to_polygons,
    polygon_is_duplicated,
    polygonize_full_lists,
    split_polygons_fully_intersected_by_a_wall,
)
from handlers.dxf.polylines_to_rectangles import rectangles_from_skeleton
from handlers.editor_v2.schema import ReactPlannerName

if TYPE_CHECKING:
    from handlers.shapely_to_react.editor_ready_entity import EditorReadyEntity


@dataclass
class DXFClassificationInfo:
    position: Point
    area_type: AreaType


# --------- DXF Geometries --------- #


class DXFtoShapelyMapper:
    def __init__(self, dxf_modelspace: Modelspace):
        self.dxf_modelspace = dxf_modelspace

    @cached_property
    def layer_names(self) -> set[str]:
        return set([entity.dxf.layer for entity in self.dxf_modelspace.query("*")])

    @cached_property
    def blocks(self):
        return {
            block_name: list(blocks)
            for block_name, blocks in groupby(
                sorted(self.dxf_modelspace.query("INSERT"), key=lambda z: z.dxf.name),
                key=lambda z: z.dxf.name,
            )
        }

    def get_layer_names(self, react_planner_names: set[ReactPlannerName]) -> set[str]:
        layer_names = set()
        for layer_name in self.layer_names:
            if any(
                [
                    keyword in layer_name
                    for planner_name in react_planner_names
                    for keyword in LAYER_KEYWORDS[planner_name]
                ]
            ):
                layer_names.add(layer_name)

        return layer_names

    def get_block_names(self, react_planner_names: set[ReactPlannerName]) -> set[str]:
        block_names = set()
        for block in self.dxf_modelspace.query("INSERT"):
            if any(
                [
                    keyword in block.dxf.name
                    for planner_name in react_planner_names
                    for keyword in BLOCK_KEYWORDS[planner_name]
                ]
            ):
                block_names.add(block.dxf.name)

        return block_names

    @staticmethod
    def get_arc_geometry(entity) -> LineString:
        return LineString(
            [
                (point[0], point[1])
                for point in entity.flattening(sagitta=ARC_DEGREE_PER_POINT)
            ]
        )

    @staticmethod
    def get_polyline_geometry(entity) -> LineString | Polygon:
        with entity.points("xyseb") as points:
            if entity.closed and len(points) > 2:
                return Polygon([p[:2] for p in points])
            else:
                # Sanitary elements are sometimes only 2 points
                return LineString([p[:2] for p in points])

    @staticmethod
    def get_line_geometry(entity) -> LineString | None:
        line = LineString([entity.dxf.start.xyz[:2], entity.dxf.end.xyz[:2]])
        if line.length > 0.0:
            return line
        return None

    @staticmethod
    def make_all_geometries_valid(geometries: list):
        valid_geometries = []
        for geometry in geometries:
            valid_geometry = make_valid(ob=geometry)
            if hasattr(valid_geometry, "geoms"):
                for polygon in valid_geometry.geoms:
                    valid_geometries.append(polygon)
            else:
                valid_geometries.append(valid_geometry)
        return valid_geometries

    def get_allowed_layer_dxf_entity_geometries(
        self, entities: list, allowed_layers: set[str] | None = None
    ):
        geometries: list[LineString | Polygon] = []
        for entity in entities:
            if allowed_layers is not None and entity.dxf.layer not in allowed_layers:
                continue

            if entity.DXFTYPE == Arc.DXFTYPE:
                geometries.append(self.get_arc_geometry(entity=entity))
            elif entity.DXFTYPE == LWPolyline.DXFTYPE:
                if polyline := self.get_polyline_geometry(entity=entity):
                    geometries.append(polyline)
            elif entity.DXFTYPE == Hatch.DXFTYPE:
                if geometry := self._get_hatch_polygons(entity=entity):
                    geometries.extend(geometry)
            elif entity.DXFTYPE == Line.DXFTYPE:
                if line := self.get_line_geometry(entity=entity):
                    geometries.append(line)
            elif hasattr(entity, "points"):
                if geometry := self.get_polyline_geometry(entity=entity):
                    geometries.append(geometry)
            elif hasattr(entity.dxf, "start") and hasattr(entity.dxf, "end"):
                geometries.append(
                    LineString([entity.dxf.start.xyz[:2], entity.dxf.end.xyz[:2]])
                )
            elif hasattr(entity, "start_point") and hasattr(entity, "end_point"):
                geometries.append(
                    LineString([entity.start_point.xyz[:2], entity.end_point.xyz[:2]])
                )

        return self.make_all_geometries_valid(geometries=geometries)

    def get_dxf_geometries(
        self,
        allowed_layers: set[str],
        allowed_geometry_types: set[Literal["LWPOLYLINE", "LINE", "ARC", "HATCH"]],
        block_name_prefix: str | None = None,
    ) -> list[LineString | Polygon]:
        if block_name_prefix:
            filtered_entities = []
            for block_name in self.blocks.keys():
                if block_name.startswith(block_name_prefix):
                    filtered_entities += [
                        entity
                        for block in self.blocks.get(block_name)
                        for entity in block.virtual_entities()
                        if entity.dxf.dxftype in allowed_geometry_types
                        and block.dxf.layer in allowed_layers
                    ]

                    return self.get_allowed_layer_dxf_entity_geometries(
                        entities=filtered_entities
                    )
            return filtered_entities

        filtered_entities = self.dxf_modelspace.query(" ".join(allowed_geometry_types))
        return self.get_allowed_layer_dxf_entity_geometries(
            entities=filtered_entities, allowed_layers=allowed_layers
        )

    @classmethod
    def _get_hatch_polygons(cls, entity: DXFEntity) -> list[Polygon]:
        try:
            hatch_proxy = geo.proxy(entity)
        except (
            IndexError,
            ValueError,
        ):  # The external code is failing for some data
            return []

        geometries = shape(hatch_proxy)

        if not geometries.is_valid:
            if "Too few points in geometry" in explain_validity(geometries):
                return []

            geometries = make_valid(ob=geometries)

        if isinstance(geometries, Polygon):
            return [geometries]
        elif isinstance(geometries, MultiPolygon):
            return [geom for geom in geometries.geoms]
        elif isinstance(geometries, GeometryCollection):
            return [geom for geom in geometries.geoms if isinstance(geom, Polygon)]
        else:
            logger.error(
                f"ezdxf hatch is converted into a geometry type which is not suitable: {type(geometries)}"
            )
            return []

    def get_polygons_from_hatches(
        self,
        allowed_layers: set[str],
        allowed_geometry_types: set[Literal["LWPOLYLINE", "LINE", "ARC", "HATCH"]],
    ):
        geometries = self.get_dxf_geometries(
            allowed_layers=allowed_layers,
            allowed_geometry_types=allowed_geometry_types,
        )

        rectangles = []
        for geometry in geometries:
            if isinstance(geometry, LineString):
                geometry = lines_to_polygons(line_strings=[geometry], width=1.0)[0]

            rectangles.extend(rectangles_from_skeleton(geometry=geometry))

        return rectangles

    def get_item_polygons_from_layer(
        self,
        layer: set[str],
        wall_polygons: list[Polygon],
        distance_to_consider_group: int = 20,
        polylines_as_polygons: bool = True,
        block_name_prefix: str | None = None,
        bounding_boxes: bool = True,
    ) -> tuple[list[Polygon], list]:
        existing_dxf_polygons: list[Polygon] = self.get_dxf_geometries(
            allowed_layers=layer,
            allowed_geometry_types={"LWPOLYLINE"},
            block_name_prefix=block_name_prefix,
        )
        if polylines_as_polygons:
            existing_dxf_polygons = [
                Polygon(x)
                for x in existing_dxf_polygons
                if isinstance(x, Polygon) or (isinstance(x, LineString) and x.is_closed)
            ]

        lines_and_arcs = self.get_dxf_geometries(
            allowed_layers=layer,
            allowed_geometry_types={"LINE", "ARC"},
            block_name_prefix=block_name_prefix,
        )
        lines_from_polylines = [
            x for x in existing_dxf_polygons if isinstance(x, LineString)
        ]
        all_walls_union = unary_union(wall_polygons)
        polygons_from_lines: list[Polygon] = list(
            group_line_and_arcs_into_rectangles(
                distance_to_consider_group=distance_to_consider_group,
                all_elements=lines_and_arcs + lines_from_polylines,
                all_walls_union=all_walls_union,
            )
        )

        all_polygons = [*existing_dxf_polygons, *polygons_from_lines]
        raw_geometries = existing_dxf_polygons + lines_and_arcs
        if bounding_boxes:
            item_bounding_boxes = get_bounding_boxes_for_groups_of_geometries(
                geometries=all_polygons
            )
            return (
                split_polygons_fully_intersected_by_a_wall(
                    bounding_boxes=item_bounding_boxes, all_walls_union=all_walls_union
                ),
                raw_geometries,
            )
        else:
            return all_polygons, raw_geometries

    def get_elevators_as_polygons(self) -> list[Polygon]:
        """
        We assume that the elevator layer only has lines as geometries and
        is similar / equal to the elevator in the test example file

        Simplified illustration of the elevator:

        ---------- Opening Line
        ---------- Main Cabin
        |        |
        |        |
        ..........
        """
        dxf_geometries = self.get_dxf_geometries(
            allowed_layers=self.get_layer_names(
                react_planner_names={ReactPlannerName.ELEVATOR}
            ),
            allowed_geometry_types={"LINE"},
        )

        buffered_and_unionized_geometries = unary_union(
            [
                geom.buffer(
                    distance=BUFFER_LINES_OF_ELEVATOR_GEOMETRIES,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                )
                for geom in dxf_geometries
            ]
        )
        main_cabins_perimeters = []
        for geometry in buffered_and_unionized_geometries.geoms:
            if geometry.interiors and geometry.area > ELEVATOR_MINIMUM_DIMENSION:
                main_cabins_perimeters.append(geometry)

        main_cabins_bounding_boxes = [
            geom.minimum_rotated_rectangle for geom in main_cabins_perimeters
        ]

        return main_cabins_bounding_boxes

    # --------- Elements by Type --------- #

    def get_wall_polygons(self) -> list[Polygon]:
        polygons_from_hatches = self.get_polygons_from_hatches(
            allowed_layers=WALL_LAYERS_HATCHES,
            allowed_geometry_types={"HATCH"},
        )
        logger.debug("Polygons from hatches read")

        polygons_from_lines = self.get_separator_polygons_from_lines(
            layers=self.get_layer_names(react_planner_names={ReactPlannerName.WALL}),
            default_width=WALL_DEFAULT_WIDTH_IN_CM,
        )
        logger.debug("Polygons from lines done")

        polygons_from_hatches_as_union = unary_union(polygons_from_hatches)

        polygons_from_lines = [
            polygon
            for polygon in polygons_from_lines
            if not polygon_is_duplicated(
                existing_polygons=polygons_from_hatches_as_union, polygon=polygon
            )
        ]

        return polygons_from_hatches + polygons_from_lines

    def polygons_not_inside_rooms(self, multipolygon: MultiPolygon) -> list[Polygon]:
        all_area_union = unary_union(self.get_area_polygons())
        polygons_not_inside_room = []
        for polygon in multipolygon.geoms:
            polygons_not_inside_room.extend(
                [
                    geom.minimum_rotated_rectangle
                    for geom in as_multipolygon(
                        polygon.difference(all_area_union)
                    ).geoms
                    if geom.minimum_rotated_rectangle.area > MINIMUM_WINDOW_SIZE_IN_CM2
                ]
            )
        return polygons_not_inside_room

    def get_area_polygons(self) -> list[Polygon]:
        return self.get_dxf_geometries(
            allowed_layers=self.get_layer_names(
                react_planner_names={ReactPlannerName.AREA}
            ),
            allowed_geometry_types={"LWPOLYLINE"},
        )

    def get_separator_polygons_from_lines(
        self, layers: set, default_width: int
    ) -> list[Polygon]:
        geometries = self.get_dxf_geometries(
            allowed_layers=layers,
            allowed_geometry_types={"LWPOLYLINE", "LINE", "ARC"},
        )
        polygons = []
        line_strings = []
        for geometry in geometries:
            if isinstance(geometry, Polygon):
                polygons.append(geometry)
            elif isinstance(geometry, LineString):
                line_strings.append(geometry)

        (
            new_polygons,
            remaining_line_strings,
        ) = polygonize_full_lists(line_strings=line_strings)
        polygons.extend(new_polygons)

        (
            closed_polygons,
            unclosed_line_strings,
        ) = close_parallel_lines_into_polygons(line_strings=remaining_line_strings)
        polygons.extend(closed_polygons)

        polygons.extend(
            lines_to_polygons(line_strings=unclosed_line_strings, width=default_width)
        )
        rectangles = [
            rectangle
            for polygon in polygons
            for rectangle in rectangles_from_skeleton(geometry=polygon)
        ]
        return filter_too_big_separators(separator_polygons=rectangles)

    def get_door_polygons(
        self, wall_polygons: list[Polygon]
    ) -> list["EditorReadyEntity"]:
        from handlers.dxf.dxf_to_shapely.dxf_to_shapely_door_mapper import (
            DXFToShapelyDoorMapper,
        )

        return DXFToShapelyDoorMapper.get_door_entities(
            dxf_to_shapely_mapper=self,
            reference_walls=wall_polygons,
        ) + DXFToShapelyDoorMapper.get_door_entities(
            dxf_to_shapely_mapper=self,
            reference_walls=wall_polygons,
            layers=self.get_layer_names(react_planner_names={ReactPlannerName.WINDOW}),
        )

    def get_railing_polygons(self):
        return self.get_separator_polygons_from_lines(
            layers=self.get_layer_names(react_planner_names={ReactPlannerName.RAILING}),
            default_width=RAILING_DEFAULT_WIDTH_IN_CM,
        )

    def get_window_polygons(self) -> list[Polygon]:
        dxf_geometries = self.get_dxf_geometries(
            allowed_layers=self.get_layer_names(
                react_planner_names={ReactPlannerName.WINDOW}
            ),
            allowed_geometry_types={"LINE", "LWPOLYLINE"},
        )
        polygons = [
            geometry for geometry in dxf_geometries if isinstance(geometry, Polygon)
        ]
        line_strings = [
            geometry for geometry in dxf_geometries if isinstance(geometry, LineString)
        ]
        line_strings = [geom for geom in unary_union(line_strings).geoms]
        generated_polygons, line_strings_leftovers = polygonize_full_lists(
            line_strings=line_strings
        )
        polygons.extend(generated_polygons)
        new_polygons, remaining_line_strings = close_parallel_lines_into_polygons(
            line_strings=line_strings_leftovers, distance_threshold=50
        )
        polygons.extend(new_polygons)
        merged_polygons = iteratively_merge_by_intersection(
            polygons=polygons, intersection_size=10.0
        )
        # the minimum size of this method is key to avoid L shaped windows
        filtered_polygons = filter_overlapping_or_small_polygons(
            polygons=merged_polygons, minimum_size=30 * 30, condition="within"
        )
        # we could still have touching boxes that are not merged
        union_polygons = as_multipolygon(unary_union(filtered_polygons))
        return self.polygons_not_inside_rooms(multipolygon=union_polygons)

    def get_area_classifications(self) -> Iterator[DXFClassificationInfo]:
        classification_texts = [
            texts
            for layer_name in AREA_NAME_LAYER
            for texts in self.dxf_modelspace.query(
                f'{AREA_NAME_ENTITY_TYPE}[layer=="{layer_name}"]'
            )
        ]
        # The first 7 elements are the texts entries in the top right corner and does not contain classification texts
        classification_texts = classification_texts[7:]
        for classification_text in classification_texts:
            area_type = get_area_type_from_room_stamp(
                room_stamp=classification_text.dxf.text
            )
            if not area_type:
                logger.debug(
                    f"Unmapped classification type: {classification_text.dxf.text} in the DXF"
                )
                continue

            alignment_method = classification_text.get_pos()[0]
            if alignment_method in ("ALIGNED", "FIT"):
                raise DXFImportException(
                    "Text entity has alignment method which is not yet implemented"
                )

            yield DXFClassificationInfo(
                position=Point(
                    classification_text.get_pos()[1].x,
                    classification_text.get_pos()[1].y,
                ),
                area_type=area_type,
            )

    def get_kitchen_polygons(
        self,
        wall_polygons: list[Polygon],
        minimum_kitchen_side: int = KITCHEN_MINIMUM_SIDE_LENGTH,
    ) -> list[Polygon]:
        layer_names = self.get_layer_names(
            react_planner_names={ReactPlannerName.KITCHEN}
        )
        kitchens = self.get_item_polygons_from_layer(
            layer=layer_names,
            wall_polygons=wall_polygons,
            distance_to_consider_group=50,
            bounding_boxes=False,
        )[0]
        for block_name in self.get_block_names(
            react_planner_names={ReactPlannerName.KITCHEN}
        ):
            kitchens += self.get_item_polygons_from_layer(
                layer=layer_names,
                wall_polygons=wall_polygons,
                distance_to_consider_group=50,
                bounding_boxes=False,
                block_name_prefix=block_name,
            )[0]

        valid_kitchens_within_walls = exclude_polygons_split_by_walls(
            wall_polygons=wall_polygons, polygons=kitchens
        )
        return filter_overlapping_or_small_polygons(
            polygons=valid_kitchens_within_walls,
            minimum_size=minimum_kitchen_side * minimum_kitchen_side,
            condition="within",
        )

    @staticmethod
    def get_sanitary_element_type_by_geometry(
        polygon: Polygon, wall_polygons: list[Polygon]
    ) -> ReactPlannerName | None:
        wall_union = unary_union(wall_polygons).buffer(
            distance=2, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
        )
        short_side, short_side2, long_side, long_side2 = get_sides_as_lines_by_length(
            polygon.minimum_rotated_rectangle
        )

        if long_side.length > 142:
            return ReactPlannerName.BATHTUB
        elif long_side.length <= 142 and short_side.length > 74:
            return ReactPlannerName.SHOWER
        elif (
            long_side.length <= 142
            and short_side.length <= 74
            and wall_union.intersection(unary_union([long_side, long_side2])).length
            > 0.9 * long_side.length
        ):
            return ReactPlannerName.SINK
        elif (
            long_side.length <= 142
            and short_side.length <= 74
            and wall_union.intersection(unary_union([short_side, short_side2])).length
            > 0.9 * short_side.length
        ):
            return ReactPlannerName.TOILET

        return None

    def get_sanitary_element_polygons(
        self, wall_polygons: list[Polygon], react_planner_name: ReactPlannerName
    ) -> list[Polygon]:
        sanitary_elements = []
        layer_names = self.get_layer_names(react_planner_names={react_planner_name})
        block_names = self.get_block_names(react_planner_names={react_planner_name})

        for block_name in block_names:
            if block_name in self.blocks.keys():
                sanitary_elements += self.get_item_polygons_from_layer(
                    layer=layer_names,
                    wall_polygons=wall_polygons,
                    block_name_prefix=block_name,
                )[0]

        sanitary_elements += [
            geometry
            for geometry in self.get_item_polygons_from_layer(
                layer=layer_names,
                wall_polygons=wall_polygons,
            )[0]
            if self.get_sanitary_element_type_by_geometry(
                polygon=geometry, wall_polygons=wall_polygons
            )
            == react_planner_name
        ]

        return sanitary_elements

    def get_stairs_polygons(
        self, wall_polygons: list[Polygon], minimum_stair_size: float = 60 * 60
    ) -> list[Polygon]:
        stairs_polygons, raw_geometries = self.get_item_polygons_from_layer(
            layer=self.get_layer_names(react_planner_names={ReactPlannerName.STAIRS}),
            wall_polygons=wall_polygons,
            distance_to_consider_group=DISTANCE_TO_GROUP_STAIRS,
            polylines_as_polygons=False,
        )

        walls_union_geos = union_all(geometries=from_shapely(wall_polygons))
        stairs_raw_union = unary_union(raw_geometries)
        stairs_geos = from_shapely(stairs_polygons)
        stairs_intersected_by_wall = intersects(
            a=from_shapely(stairs_polygons), b=walls_union_geos
        )
        final_valid_polygons = []
        for i, stair_intersected in enumerate(stairs_intersected_by_wall):
            if stair_intersected:
                stair_polygon = difference(a=stairs_geos[i], b=walls_union_geos)
                for geom in as_multipolygon(to_shapely(stair_polygon)).geoms:
                    skeleton_stair_pieces = rectangles_from_skeleton(geometry=geom)
                    # Skeleton segments of a stair block with a wall inside will generate many
                    # blocks, that in many cases
                    # are overlapping each other or are too small
                    skeleton_post_processed_stairs = (
                        filter_overlapping_or_small_polygons(
                            polygons=[
                                final_stair_polygon
                                for final_stair_polygon in skeleton_stair_pieces
                            ],
                            minimum_size=minimum_stair_size,
                        )
                    )
                    for skeleton_piece in skeleton_post_processed_stairs:
                        if skeleton_piece.intersects(stairs_raw_union):
                            final_valid_polygons.append(skeleton_piece)
            else:
                final_valid_polygons.append(stairs_polygons[i])
        return final_valid_polygons
