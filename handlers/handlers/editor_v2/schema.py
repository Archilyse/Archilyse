from dataclasses import field
from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Set
from uuid import uuid4

import marshmallow_dataclass
from methodtools import lru_cache
from shapely.affinity import rotate
from shapely.geometry import LineString, Polygon, box, shape

from brooks.models.violation import Violation, ViolationType
from common_utils.constants import N_DIGITS_ROUNDING_VERTICES
from common_utils.logger import logger
from handlers.editor_v2.migration_functions.delete_altitude_from_schema import (
    delete_altitude_from_schema,
)
from handlers.editor_v2.migration_functions.fix_openings_parents import (
    fix_opening_parents,
)
from handlers.editor_v2.migration_functions.remove_enable_postprocessing import (
    remove_enable_postprocessing,
)
from handlers.editor_v2.migration_functions.remove_orphan_vertex import (
    remove_orphan_vertices,
)

if TYPE_CHECKING:
    from dataclasses import dataclass
else:
    from marshmallow_dataclass import dataclass

from brooks.types import SeparatorType
from common_utils.exceptions import CorruptedAnnotationException

DEFAULT_SCENE_WIDTH = 3000
DEFAULT_SCENE_HEIGHT = 2000


class ReactPlannerVersions(Enum):
    V1 = "V1"
    V2 = "V2"
    V3 = "V3"
    V4 = "V4"
    V5 = "V5"
    V6 = "V6"
    V7 = "V7"
    V8 = "V8"
    V9 = "V9"
    V10 = "V10"
    V11 = "V11"
    V12 = "V12"
    V13 = "V13"
    V14 = "V14"
    V15 = "V15"
    V16 = "V16"
    V17 = "V17"
    V18 = "V18"
    V19 = "V19"


CURRENT_REACT_ANNOTATION_BASELINE = 5
CURRENT_REACT_ANNOTATION_VERSION = (
    ReactPlannerVersions.V19.name
)  # IMPORTANT: Also update FE version number if BE version changes here ->
# https://github.com/Archilyse/slam/blob/develop/ui/react-planner/src/models.js#L247

migration_by_version = {
    ReactPlannerVersions.V15.name: remove_enable_postprocessing,
    ReactPlannerVersions.V16.name: remove_orphan_vertices,
    ReactPlannerVersions.V17.name: fix_opening_parents,
    ReactPlannerVersions.V18.name: delete_altitude_from_schema,
}


class ReactPlannerReferenceLine(Enum):
    CENTER = "CENTER"
    OUTSIDE_FACE = "OUTSIDE_FACE"
    INSIDE_FACE = "INSIDE_FACE"


class ReactPlannerType(Enum):
    """To be deprecated or merge with ReactPlannerName,
    removing spaces for the names and using out of the box checks for the valid option of the enum"""

    # holes
    ENTRANCE_DOOR = "entrance_door"
    DOOR = "door"
    SLIDING_DOOR = "sliding_door"
    WINDOW = "window"

    # lines
    AREA_SPLITTER = "area_splitter"
    COLUMN = "column"
    RAILING = "railing"
    WALL = "wall"

    # items in order displayed in the UI
    KITCHEN = "kitchen"
    SEAT = "seat"
    SHOWER = "shower"
    STAIRS = "stairs"
    TOILET = "toilet"
    CAR_PARKING = "car_parking"
    ELEVATOR = "elevator"
    BATHTUB = "bathtub"
    RAMP = "ramp"
    SINK = "sink"
    BUILT_IN_FURNITURE = "built_in_furniture"
    BIKE_PARKING = "bike_parking"
    SHAFT = "shaft"
    WASHING_MACHINE = "washing_machine"
    OFFICE_DESK = "office_desk"


class ReactPlannerName(Enum):
    # holes
    ENTRANCE_DOOR = "Entrance Door"
    DOOR = "Door"
    SLIDING_DOOR = "Sliding Door"
    WINDOW = "Window"

    # lines
    AREA_SPLITTER = "Area Splitter"
    COLUMN = "Column"
    RAILING = "Railing"
    WALL = "Wall"

    # items in order displayed in the UI
    KITCHEN = "Kitchen"
    SEAT = "Seat"
    SHOWER = "Shower"
    STAIRS = "Stairs"
    TOILET = "Toilet"
    CAR_PARKING = "Car Parking"
    ELEVATOR = "Elevator"
    BATHTUB = "Bathtub"
    RAMP = "Ramp"
    SINK = "Sink"
    BUILT_IN_FURNITURE = "Built In Furniture"
    BIKE_PARKING = "Bike Parking"
    SHAFT = "Shaft"
    WASHING_MACHINE = "Washing Machine"
    OFFICE_DESK = "Office Desk"

    # misc
    VERTEX = "Vertex"
    AREA = "Area"


react_planner_name_to_type: Dict[ReactPlannerName, ReactPlannerType] = {
    ReactPlannerName.ENTRANCE_DOOR: ReactPlannerType.ENTRANCE_DOOR,
    ReactPlannerName.DOOR: ReactPlannerType.DOOR,
    ReactPlannerName.SLIDING_DOOR: ReactPlannerType.SLIDING_DOOR,
    ReactPlannerName.WINDOW: ReactPlannerType.WINDOW,
    ReactPlannerName.AREA_SPLITTER: ReactPlannerType.AREA_SPLITTER,
    ReactPlannerName.COLUMN: ReactPlannerType.COLUMN,
    ReactPlannerName.RAILING: ReactPlannerType.RAILING,
    ReactPlannerName.WALL: ReactPlannerType.WALL,
    ReactPlannerName.KITCHEN: ReactPlannerType.KITCHEN,
    ReactPlannerName.SEAT: ReactPlannerType.SEAT,
    ReactPlannerName.SHOWER: ReactPlannerType.SHOWER,
    ReactPlannerName.STAIRS: ReactPlannerType.STAIRS,
    ReactPlannerName.TOILET: ReactPlannerType.TOILET,
    ReactPlannerName.CAR_PARKING: ReactPlannerType.CAR_PARKING,
    ReactPlannerName.ELEVATOR: ReactPlannerType.ELEVATOR,
    ReactPlannerName.BATHTUB: ReactPlannerType.BATHTUB,
    ReactPlannerName.RAMP: ReactPlannerType.RAMP,
    ReactPlannerName.SINK: ReactPlannerType.SINK,
    ReactPlannerName.BUILT_IN_FURNITURE: ReactPlannerType.BUILT_IN_FURNITURE,
    ReactPlannerName.BIKE_PARKING: ReactPlannerType.BIKE_PARKING,
    ReactPlannerName.SHAFT: ReactPlannerType.SHAFT,
    ReactPlannerName.WASHING_MACHINE: ReactPlannerType.WASHING_MACHINE,
    ReactPlannerName.OFFICE_DESK: ReactPlannerType.OFFICE_DESK,
}

HOLE_TYPES_WITH_SWEEPING_POINTS: Set[ReactPlannerType] = {
    ReactPlannerType.DOOR,
    ReactPlannerType.ENTRANCE_DOOR,
}


class PostInitTypeNameCheckMixin:
    def __post_init__(self):
        try:
            ReactPlannerType(self.type)
        except ValueError:
            raise CorruptedAnnotationException(
                f"Type: {self.type} is not a valid value from {ReactPlannerType.__members__.values()}"
            )
        try:
            ReactPlannerName(self.name)
        except ValueError:
            raise CorruptedAnnotationException(
                f"Name: {self.name} is not a valid value from {ReactPlannerName.__members__.values()}"
            )


@dataclass
class ReactPlannerVertex:
    x: float
    y: float
    type: str = field(default="")
    name: str = field(default=ReactPlannerName.VERTEX.value)
    prototype: str = field(default="vertices")
    properties: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    lines: List[str] = field(default_factory=list)
    selected: bool = field(default=False)


@dataclass
class ReactPlannerGeomProperty:
    value: float
    unit: str = field(default="cm")


@dataclass
class ReactPlannerLineProperties:
    height: ReactPlannerGeomProperty
    width: ReactPlannerGeomProperty
    referenceLine: str = field(default=ReactPlannerReferenceLine.OUTSIDE_FACE.value)

    def __post_init__(self):
        if self.width is None:
            raise CorruptedAnnotationException("Width not set")
        if isinstance(self.width, dict):
            self.width = ReactPlannerGeomProperty(**self.width)
        if isinstance(self.height, dict):
            self.height = ReactPlannerGeomProperty(**self.height)


@dataclass
class ReactPlannerLine(PostInitTypeNameCheckMixin):
    properties: ReactPlannerLineProperties
    coordinates: List[List[List[float]]]
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = field(default=ReactPlannerName.WALL.value)
    type: str = field(default=ReactPlannerType.WALL.value)
    prototype: str = field(default="lines")
    vertices: List[str] = field(default_factory=list)
    auxVertices: List[str] = field(default_factory=list)
    holes: List[str] = field(default_factory=list)
    selected: bool = field(default=False)

    @property
    def separator_type(self):
        return SeparatorType[self.type.upper()]

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerLineProperties(**self.properties)


@dataclass
class ReactPlannerDoorSweepingPoints:
    angle_point: List[float]
    closed_point: List[float]
    opened_point: List[float]


@dataclass
class ReactPlannerHoleHeights:
    lower_edge: Optional[float] = field(default=None)
    upper_edge: Optional[float] = field(default=None)


@dataclass
class ReactPlannerHoleProperties:
    width: ReactPlannerGeomProperty
    length: ReactPlannerGeomProperty
    altitude: ReactPlannerGeomProperty
    heights: ReactPlannerHoleHeights
    flip_horizontal: bool = field(default=False)
    flip_vertical: bool = field(default=False)

    def __post_init__(self):
        if isinstance(self.width, dict):
            self.width = ReactPlannerGeomProperty(**self.width)
        if isinstance(self.length, dict):
            self.length = ReactPlannerGeomProperty(**self.length)
        if isinstance(self.altitude, dict):
            self.altitude = ReactPlannerGeomProperty(**self.altitude)
        if isinstance(self.heights, dict):
            self.heights = ReactPlannerHoleHeights(**self.heights)


@dataclass
class ReactPlannerHole(PostInitTypeNameCheckMixin):
    line: str
    properties: ReactPlannerHoleProperties
    coordinates: List[List[Any]]
    name: str = field(default=ReactPlannerName.WINDOW.value)
    type: str = field(default=ReactPlannerType.WINDOW.value)
    prototype: str = field(default="holes")
    id: str = field(default_factory=lambda: str(uuid4()))
    selected: bool = field(default=False)
    door_sweeping_points: Optional[ReactPlannerDoorSweepingPoints] = field(default=None)

    def __post_init__(self):
        super().__post_init__()
        if (
            ReactPlannerType(self.type) in HOLE_TYPES_WITH_SWEEPING_POINTS
            and self.door_sweeping_points is None
        ):
            raise CorruptedAnnotationException(
                f"Hole {self.id} that belongs to wall {self.line} of type {self.type} has no sweeping points set."
            )
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerHoleProperties(**self.properties)

        if isinstance(self.door_sweeping_points, dict):
            self.door_sweeping_points = ReactPlannerDoorSweepingPoints(
                **self.door_sweeping_points
            )


@dataclass
class ReactPlannerAreaProperties:
    areaType: str = field(default="")
    patternColor: str = field(default="#F5F4F4")
    texture: str = field(default="none")


@dataclass
class ReactPlannerArea:
    coords: List[List[List[float]]] = field()
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = field(default=ReactPlannerName.AREA.value)
    prototype: str = field(default="areas")
    type: str = field(default="area")
    properties: ReactPlannerAreaProperties = field(
        default_factory=ReactPlannerAreaProperties
    )
    holes: List[str] = field(default_factory=list)
    selected: bool = field(default=False)

    @cached_property
    def polygon(self) -> Polygon:
        return shape({"type": "Polygon", "coordinates": self.coords})

    def __post_init__(self):
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerAreaProperties(**self.properties)


@dataclass
class ReactPlannerItemProperties:
    width: ReactPlannerGeomProperty
    length: ReactPlannerGeomProperty
    height: ReactPlannerGeomProperty = field(
        default_factory=lambda: ReactPlannerGeomProperty(0)  # type: ignore
        # https://mypy.readthedocs.io/en/stable/additional_features.html#caveats-known-issues
    )
    altitude: ReactPlannerGeomProperty = field(
        default_factory=lambda: ReactPlannerGeomProperty(0)  # type: ignore
        # https://mypy.readthedocs.io/en/stable/additional_features.html#caveats-known-issues
    )
    direction: Optional[str] = field(default=None)

    def __post_init__(self):
        if isinstance(self.width, dict):
            self.width = ReactPlannerGeomProperty(**self.width)
        if isinstance(self.length, dict):
            self.length = ReactPlannerGeomProperty(**self.length)
        if isinstance(self.altitude, dict):
            self.altitude = ReactPlannerGeomProperty(**self.altitude)
        if isinstance(self.height, dict):
            self.height = ReactPlannerGeomProperty(**self.height)


@dataclass
class ReactPlannerItem(PostInitTypeNameCheckMixin):
    x: float
    y: float
    rotation: float
    name: str
    type: str
    properties: ReactPlannerItemProperties
    prototype: str = field(default="items")
    id: str = field(default_factory=lambda: str(uuid4()))
    selected: bool = field(default=False)

    def __post_init__(self):
        super().__post_init__()
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerItemProperties(**self.properties)

    @cached_property
    def polygon(self) -> Polygon:
        half_width = self.properties.width.value / 2
        half_height = self.properties.length.value / 2
        return rotate(
            geom=box(
                self.x - half_width,
                self.y - half_height,
                self.x + half_width,
                self.y + half_height,
            ),
            angle=self.rotation,
        )


@dataclass
class ReactPlannerGuide:
    horizontal: Dict[Any, Any] = field(default_factory=dict)
    vertical: Dict[Any, Any] = field(default_factory=dict)
    circular: Dict[Any, Any] = field(default_factory=dict)


@dataclass
class ReactPlannerGridProperties:
    step: int = field(default=20)
    colors: List[str] = field(
        default_factory=lambda: ["#808080", "#ddd", "#ddd", "#ddd", "#ddd"]
    )


@dataclass
class ReactPlannerHorizontalGrid:
    properties: ReactPlannerGridProperties = field(
        default_factory=ReactPlannerGridProperties
    )
    id: str = field(default="h1")
    type: str = field(default="horizontal-streak")

    def __post_init__(self):
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerGridProperties(**self.properties)


@dataclass
class ReactPlannerVerticalGrid:
    properties: ReactPlannerGridProperties = field(
        default_factory=ReactPlannerGridProperties
    )
    id: str = field(default="v1")
    type: str = field(default="vertical-streak")

    def __post_init__(self):
        if isinstance(self.properties, dict):
            self.properties = ReactPlannerGridProperties(**self.properties)


@dataclass
class ReactPlannerGrid:
    h1: ReactPlannerHorizontalGrid = field(default_factory=ReactPlannerHorizontalGrid)
    v1: ReactPlannerVerticalGrid = field(default_factory=ReactPlannerVerticalGrid)

    def __post_init__(self):
        if isinstance(self.h1, dict):
            self.h1 = ReactPlannerHorizontalGrid(**self.h1)
        if isinstance(self.v1, dict):
            self.v1 = ReactPlannerVerticalGrid(**self.v1)


@dataclass
class ReactPlannerLayer:
    selected: Dict[Any, Any] = field(default_factory=dict)
    vertices: Dict[str, ReactPlannerVertex] = field(default_factory=dict)
    lines: Dict[str, ReactPlannerLine] = field(default_factory=dict)
    holes: Dict[str, ReactPlannerHole] = field(default_factory=dict)
    areas: Dict[str, ReactPlannerArea] = field(default_factory=dict)
    items: Dict[str, ReactPlannerItem] = field(default_factory=dict)
    order: int = field(default=0)
    opacity: int = field(default=1)
    name: str = field(default="default")
    id: str = field(default="layer-1")

    def __post_init__(self):
        for vertex_id, vertex in self.vertices.items():
            if isinstance(vertex, dict):
                self.vertices[vertex_id] = ReactPlannerVertex(**vertex)
        for vertex_id, vertex in self.lines.items():
            if isinstance(vertex, dict):
                self.lines[vertex_id] = ReactPlannerLine(**vertex)
        for vertex_id, vertex in self.holes.items():
            if isinstance(vertex, dict):
                self.holes[vertex_id] = ReactPlannerHole(**vertex)
        for vertex_id, vertex in self.areas.items():
            if isinstance(vertex, dict):
                self.areas[vertex_id] = ReactPlannerArea(**vertex)
        for vertex_id, vertex in self.items.items():
            if isinstance(vertex, dict):
                self.items[vertex_id] = ReactPlannerItem(**vertex)


@dataclass
class ReactPlannerBackgroundShift:
    x: Optional[float] = field(default=0, metadata={"required": True})
    y: Optional[float] = field(default=0, metadata={"required": True})


@dataclass
class ReactPlannerBackground:
    width: Optional[int] = field(default=None, metadata={"required": True})
    height: Optional[int] = field(default=None, metadata={"required": True})
    rotation: float = field(default=0, metadata={"required": True})
    shift: Optional[ReactPlannerBackgroundShift] = field(
        default_factory=ReactPlannerBackgroundShift
    )

    def __post_init__(self):
        if isinstance(self.shift, dict):
            self.shift = ReactPlannerBackgroundShift(**self.shift)


@dataclass
class ReactPlannerData:
    grids: ReactPlannerGrid = field(default_factory=ReactPlannerGrid)
    guides: ReactPlannerGuide = field(default_factory=ReactPlannerGuide)
    width: int = field(default=DEFAULT_SCENE_WIDTH, metadata={"required": True})
    height: int = field(default=DEFAULT_SCENE_HEIGHT, metadata={"required": True})
    background: ReactPlannerBackground = field(default_factory=ReactPlannerBackground)
    layers: Dict[str, ReactPlannerLayer] = field(
        default_factory=lambda: {
            "layer-1": ReactPlannerLayer(),
        }
    )
    version: str = field(default=CURRENT_REACT_ANNOTATION_VERSION)
    groups: Dict[Any, Any] = field(default_factory=dict)
    meta: Dict[Any, Any] = field(default_factory=dict)
    unit: str = field(default="cm")
    selectedLayer: str = field(default="layer-1")
    scale: float = field(default=1.0, metadata={"required": True})
    scaleRatio: Optional[float] = field(default=None)
    paperFormat: str = field(default="")

    def __post_init__(self):
        if isinstance(self.grids, dict):
            self.grids = ReactPlannerGrid(**self.grids)
        if isinstance(self.guides, dict):
            self.guides = ReactPlannerGuide(**self.guides)
        if isinstance(self.background, dict):
            self.background = ReactPlannerBackground(**self.background)
        for layer_id, layer in self.layers.items():
            if isinstance(layer, dict):
                self.layers[layer_id] = ReactPlannerLayer(**layer)

    def lines_iterator(self) -> Iterator[ReactPlannerLine]:
        for layer in self.layers.values():
            for line in layer.lines.values():
                yield line

    @property
    def lines_by_id(self) -> Dict[str, ReactPlannerLine]:
        return self.layers["layer-1"].lines

    @property
    def vertices_by_id(self) -> Dict[str, ReactPlannerVertex]:
        return self.layers["layer-1"].vertices

    @property
    def holes_by_id(self) -> Dict[str, ReactPlannerHole]:
        return self.layers["layer-1"].holes

    @property
    def areas_by_id(self) -> Dict[str, ReactPlannerArea]:
        return self.layers["layer-1"].areas

    @property
    def items_by_id(self) -> Dict[str, ReactPlannerItem]:
        return self.layers["layer-1"].items

    def validate(self) -> Iterator[Violation]:
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        line_referenced_vertices = set()
        for line in self.lines_iterator():
            all_vertices = line.vertices + line.auxVertices
            for vertex_id in all_vertices:
                if vertex_id not in self.vertices_by_id:
                    yield Violation(
                        violation_type=ViolationType.CORRUPTED_ANNOTATION,
                        position=ReactPlannerToBrooksMapper.get_element_polygon(
                            element=line
                        ).centroid,
                        object_id=line.id,
                        human_id=line.id,
                        object_type=line.type,
                        text=f"A vertex {vertex_id} of the line {line.id} is not present in the vertices index."
                        f"Solution -> Redraw the line",
                    )
                elif line.id not in self.vertices_by_id[vertex_id].lines:
                    yield Violation(
                        violation_type=ViolationType.CORRUPTED_ANNOTATION,
                        position=ReactPlannerToBrooksMapper.get_element_polygon(
                            element=line
                        ).centroid,
                        object_id=line.id,
                        human_id=line.id,
                        object_type=line.type,
                        text=f"The vertex {vertex_id} doesn't reference back the line {line.id}."
                        f" Raise a support ticket",
                    )
                line_referenced_vertices.add(vertex_id)
            vertices_as_tuples = [
                (
                    round(self.vertices_by_id[vertex].x, N_DIGITS_ROUNDING_VERTICES),
                    round(self.vertices_by_id[vertex].y, N_DIGITS_ROUNDING_VERTICES),
                )
                for vertex in all_vertices
            ]

            if len(vertices_as_tuples) != len(set(vertices_as_tuples)):
                yield Violation(
                    violation_type=ViolationType.CORRUPTED_ANNOTATION,
                    position=ReactPlannerToBrooksMapper.get_element_polygon(
                        element=line
                    ).centroid,
                    object_id=line.id,
                    human_id=line.id,
                    object_type=line.type,
                    text=f"{line.type}: {line.id} has repeated vertices"
                    f" Raise a support ticket",
                )
            if len(all_vertices) != 6:
                vertex = self.vertices_by_id[all_vertices[0]]
                yield Violation(
                    violation_type=ViolationType.CORRUPTED_ANNOTATION,
                    position=ReactPlannerToBrooksMapper.get_element_polygon(
                        element=line
                    ).centroid,
                    object_id=line.id,
                    human_id=line.id,
                    object_type=line.type,
                    text=f"{line.type}: {line.id} has less than 6 vertices at {vertex.x, vertex.y}. "
                    f"Raise a support ticket",
                )

        for hole in self.holes_by_id.values():
            if hole.line not in self.lines_by_id:
                yield Violation(
                    violation_type=ViolationType.CORRUPTED_ANNOTATION,
                    position=ReactPlannerToBrooksMapper.get_element_polygon(
                        element=hole
                    ).centroid,
                    object_id=hole.id,
                    human_id=hole.id,
                    object_type=hole.type,
                    text=f"An opening {hole.id} is referencing a non existing line: {hole.line}. "
                    f"Adjust the opening",
                )

        yield from self.check_vertices_post_init(
            line_referenced_vertices=line_referenced_vertices
        )

    def check_vertices_post_init(self, line_referenced_vertices: Set[str]):
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        for vertex in self.vertices_by_id.values():
            lines_to_remove_from_vertices = set()
            for line_id in vertex.lines:
                if line := self.lines_by_id.get(line_id):
                    main_vertices = set(line.vertices)
                    aux_vertices = set(line.auxVertices)
                    if vertex.id not in main_vertices and vertex.id not in aux_vertices:
                        if vertex.id not in main_vertices:
                            yield Violation(
                                violation_type=ViolationType.CORRUPTED_ANNOTATION,
                                position=ReactPlannerToBrooksMapper.get_element_polygon(
                                    element=line
                                ).centroid,
                                object_id=line.id,
                                human_id=line.id,
                                object_type=line.type,
                                text=f"The line {line_id} doesn't reference back the main vertex {vertex.id}. "
                                f"Raise a support ticket",
                            )
                        yield Violation(
                            violation_type=ViolationType.CORRUPTED_ANNOTATION,
                            position=ReactPlannerToBrooksMapper.get_element_polygon(
                                element=line
                            ).centroid,
                            object_id=line.id,
                            human_id=line.id,
                            object_type=line.type,
                            text=f"The line {line_id} doesn't reference back the aux vertex {vertex.id}"
                            f"Solution -> Redraw the line, tech is working hard to fix this",
                        )
                else:
                    lines_to_remove_from_vertices.add(line_id)

            vertex.lines = [
                x for x in vertex.lines if x not in lines_to_remove_from_vertices
            ]

        if orphan_vertices := set(self.vertices_by_id).difference(
            line_referenced_vertices
        ):
            logger.error(
                f"Found {len(orphan_vertices)} orphan vertices and removing them while loading the payload"
            )
            for orphan in orphan_vertices:
                self.vertices_by_id.pop(orphan)

    @property
    def is_empty(self) -> bool:
        return (
            not self.holes_by_id
            and not self.vertices_by_id
            and not self.lines_by_id
            and not self.areas_by_id
            and not self.items_by_id
        )

    @lru_cache()
    def separator_polygons_by_id(
        self, separator_type: SeparatorType
    ) -> Dict[str, Polygon]:
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )
        from handlers.editor_v2.utils import BROOKS_TYPE_TO_REACT_PLANNER_NAME

        result = {}
        for line in self.lines_by_id.values():
            if line.name == BROOKS_TYPE_TO_REACT_PLANNER_NAME[separator_type].value:
                if polygon := ReactPlannerToBrooksMapper.get_element_polygon(
                    element=line
                ):
                    result[line.id] = polygon
        return result

    def get_reference_linestring_of_separator(self, line_id: str) -> LineString:
        vertices_id = self.lines_by_id[line_id].vertices
        vertices = [self.vertices_by_id[vertex_id] for vertex_id in vertices_id]
        return LineString([(vertex.x, vertex.y) for vertex in vertices])


ReactPlannerSchema = marshmallow_dataclass.class_schema(ReactPlannerData)
