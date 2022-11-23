from enum import Enum
from typing import TYPE_CHECKING, Optional

from shapely.geometry import Point

from brooks.util.io import BrooksSerializable

if TYPE_CHECKING:
    from .spatial_entity import SpatialEntity


class ViolationType(Enum):
    # ----- Mapping -----

    DOOR_HAS_NO_WALL = 1
    WINDOW_HAS_NO_WALL = 2
    FEATURE_NOT_ASSIGNED = 13
    OPENING_OVERLAPS_MULTIPLE_WALLS = 18
    OPENING_OVERLAPS_ANOTHER_OPENING = 19
    CORRUPTED_ANNOTATION = 20
    # Basic features does not evaluate
    # an area (most likely b/c of its type)
    AREA_NOT_EVALUATED = 5

    # Different errors for no entrance door.
    NO_ENTRANCE_DOOR = 3

    # Space connectivity violations
    SPACE_NOT_ACCESSIBLE = 16
    DOOR_NOT_CONNECTING_AREAS = 15
    AREA_OVERLAPS_MULTIPLE_SPACES = 14

    # Used for scaling validation
    INVALID_AREA = 17

    # ----- Splitting -----
    AREA_NOT_IN_PLAN = 101
    INSIDE_ENTRANCE_DOOR = 102
    AREA_NOT_DEFINED = 103
    APARTMENT_NOT_ACCESSIBLE = 105
    UNIT_SPACES_NOT_CONNECTED = 106
    CONNECTED_SPACES_MISSING = 107
    AREA_MISSING_SPACE = 108
    SPACE_MISSING_AREA_SELECTION = 109
    APARTMENT_MULTIPLE_KITCHENS = 110
    SHARED_SPACE_NOT_CONNECTED_WITH_ENTRANCE_DOOR = 111

    # ----- Classification -----
    SHAFT_WITHOUT_SHAFT_FEATURE = 201
    NON_SHAFT_WITH_SHAFT_FEATURE = 202
    STORAGE_ROOM_TOO_MANY_DOORS = 203
    CORRIDOR_NOT_ENOUGH_DOORS = 204
    FEATURE_DOES_NOT_MATCH_ROOM_TYPE = 205
    ROOM_NOT_ENOUGH_WINDOWS = 206
    SHAFT_HAS_OPENINGS = 207
    BALCONY_WITHOUT_RAILING = 208

    # ----- Georeferencing -----
    INTERSECTS_OTHER_BUILDING_PLAN = 301

    # ----- Linking -----

    AREA_TYPE_NOT_ALLOWED_FOR_UNIT_USAGE_TYPE = 401


class Violation(BrooksSerializable):
    __serializable_fields__ = [
        "type",
        "position",
        "object_id",
        "text",
        "human_id",
        "is_blocking",
    ]

    _texts = {
        # annotation Mapper
        ViolationType.DOOR_HAS_NO_WALL: "Door is not covered by a wall",
        ViolationType.WINDOW_HAS_NO_WALL: "Window is not covered by a wall",
        ViolationType.NO_ENTRANCE_DOOR: "No entrance door could be found",
        ViolationType.AREA_NOT_EVALUATED: "Area features were not included in the basic features simulation",
        ViolationType.FEATURE_NOT_ASSIGNED: "Feature {} could not be assigned exclusively to one area",
        ViolationType.AREA_OVERLAPS_MULTIPLE_SPACES: "Area {} overlaps with multiple spaces at the same time",
        ViolationType.SPACE_NOT_ACCESSIBLE: "Space not accessible. It should have a type of door, stairs or an elevator",
        ViolationType.DOOR_NOT_CONNECTING_AREAS: "Door is not connecting 2 areas",
        ViolationType.INVALID_AREA: "When scaling the area gets invalid or empty. This might be caused by thin gaps",
        ViolationType.OPENING_OVERLAPS_MULTIPLE_WALLS: "Opening overlaps with multiple separators: walls/railings/columns",
        ViolationType.OPENING_OVERLAPS_ANOTHER_OPENING: "Opening is overlapping another opening",
        # Splitting
        ViolationType.AREA_NOT_IN_PLAN: "Area IDs do not match the areas available for the plan",
        ViolationType.INSIDE_ENTRANCE_DOOR: "An entrance is connecting two spaces of a unit",
        ViolationType.AREA_NOT_DEFINED: "An area is NOT_DEFINED",
        ViolationType.APARTMENT_NOT_ACCESSIBLE: "The apartment is not accessible, must either have an entrance door, stairs or elevator to enter it",
        ViolationType.UNIT_SPACES_NOT_CONNECTED: "Spaces are not connected",
        ViolationType.CONNECTED_SPACES_MISSING: "There are spaces connected to the unit that are not assigned to it",
        ViolationType.AREA_MISSING_SPACE: "An area could not be mapped to any space",
        ViolationType.SPACE_MISSING_AREA_SELECTION: "There are spaces which are only partially assigned to the same apartment",
        ViolationType.APARTMENT_MULTIPLE_KITCHENS: "There are multiple kitchens in one apartment",
        ViolationType.SHARED_SPACE_NOT_CONNECTED_WITH_ENTRANCE_DOOR: "Shared space connected by a regular door instead of an entrance door",
        # Classification
        ViolationType.SHAFT_WITHOUT_SHAFT_FEATURE: "A shaft area has no shaft feature",
        ViolationType.NON_SHAFT_WITH_SHAFT_FEATURE: "An area has a shaft feature but is no shaft",
        ViolationType.STORAGE_ROOM_TOO_MANY_DOORS: "A storage room has too many doors",
        ViolationType.CORRIDOR_NOT_ENOUGH_DOORS: "A corridor has not enough doors",
        ViolationType.FEATURE_DOES_NOT_MATCH_ROOM_TYPE: "A room does match a feature it contains",
        ViolationType.ROOM_NOT_ENOUGH_WINDOWS: "A room has not enough windows",
        ViolationType.SHAFT_HAS_OPENINGS: "A shaft has openings (windows and/or doors)",
        ViolationType.BALCONY_WITHOUT_RAILING: "A balcony needs to be separated by a railing element.",
        ViolationType.INTERSECTS_OTHER_BUILDING_PLAN: "The plan intersects with another building's plan",
        # Linking
        ViolationType.AREA_TYPE_NOT_ALLOWED_FOR_UNIT_USAGE_TYPE: "Area type is not allowed for current unit usage type",
    }

    def __init__(
        self,
        violation_type: ViolationType,
        position: Point,
        object_id=None,
        object_type: Optional[str] = None,
        human_id: Optional[str] = None,
        is_blocking: Optional[bool] = True,
        text: Optional[str] = None,
    ):
        self.violation_type = violation_type
        self.position = position
        self.object_id = object_id
        self.object_type = object_type
        self.human_id = human_id
        self.is_blocking = is_blocking
        self._text = text

    @property
    def text(self) -> str:
        if not self._text:
            return self._texts[self.violation_type].format(self.object_type)

        return self._text

    @property
    def type(self):
        return self.violation_type.name

    def __repr__(self):
        return (
            f"Identifier: {self.human_id}. {self.type} at {self.position} in entity {self.object_id}."
            f" Type: {self.object_type}."
        )


class SpatialEntityViolation(Violation):
    def __init__(
        self,
        entity: "SpatialEntity",
        violation_type: ViolationType,
        human_id: Optional[str] = None,
        is_blocking: Optional[bool] = True,
        text: Optional[str] = None,
    ):
        self.entity = entity
        super().__init__(
            violation_type=violation_type,
            human_id=human_id,
            is_blocking=is_blocking,
            text=text,
            position=entity.footprint.representative_point(),
            object_type=entity.type.name,
            object_id=entity.id,
        )
