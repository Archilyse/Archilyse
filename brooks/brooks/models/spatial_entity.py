import uuid
from functools import cached_property
from typing import TYPE_CHECKING, Optional, Tuple

from shapely import wkt
from shapely.affinity import translate
from shapely.geometry import Point, Polygon

from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.exceptions import InvalidShapeException
from dufresne.polygon import get_sides_as_lines_by_length

if TYPE_CHECKING:
    from simulations.view.meshes import GeoreferencingTransformation


class SpatialEntity:
    """A spatial entity is an object embedded in three dimensional space.

    A spatial entity has a 2d footprint and a 3d shape
    The footprint is a shapely Polygon the shape is something
    to be defined within the ifc import and not used in the archilogic
    framework -  right now it has only a height.
    A spatial entity optionally contains a direction - like a chair
    """

    def __init__(
        self,
        footprint: Polygon,
        height: Tuple[float, float],
        entity_id: Optional[str] = None,
        direction: float = None,
        angle: float = None,
        position: Point = None,
        geometry_new_editor: Optional[Polygon] = None,
    ):
        entity_id = entity_id or uuid.uuid4().hex
        angle = angle or 0.0
        position = position or Point(0, 0)

        self.id: str = entity_id
        self.footprint: Polygon = ensure_geometry_validity(geometry=footprint)
        self.height = height
        self.direction = direction

        # These attributes are for a relative coordinate system
        self.angle = angle
        self.position = position
        self.geometry_new_editor = geometry_new_editor

    @property
    def type(self):
        if hasattr(self, "_type"):
            return self._type

    def __repr__(self):
        return (
            f"{self.type}-{self.id} with wkt "
            f"{wkt.dumps(self.footprint) if self.footprint else self.footprint} at {self.position}"
        )

    def footprint_absolute_to_relative_coordinates(self, parent_position):
        self.position = Point(
            self.footprint.centroid.x - parent_position.x,
            self.footprint.centroid.y - parent_position.y,
        )
        translation = self.footprint.centroid
        self.footprint = translate(
            self.footprint, xoff=-translation.x, yoff=-translation.y
        )

    @cached_property
    def width(self) -> float:
        return get_sides_as_lines_by_length(self.footprint)[0].length

    @property
    def length(self) -> float:
        return get_sides_as_lines_by_length(self.footprint)[-1].length

    @property
    def surface_area(self) -> float:
        return (self.height[1] - self.height[0]) * self.length

    def apply_georef(
        self, georeferencing_transformation: "GeoreferencingTransformation"
    ):
        self.position = georeferencing_transformation.apply_shapely(self.position)
        self.footprint = georeferencing_transformation.apply_shapely(self.footprint)

        if not self.footprint.is_valid:
            fixed_footprint = ensure_geometry_validity(self.footprint)
            if isinstance(self.footprint, Polygon) and not isinstance(
                fixed_footprint, Polygon
            ):
                # If from a Polygon we go to a MultiPolygon this is not acceptable
                raise InvalidShapeException(
                    f"Polygon of type {self.type} with id {self.id} "
                    f"and WKT {wkt.dumps(self.footprint)} "
                    f"at position {self.position} can't be safely transformed"
                )
            self.footprint = fixed_footprint
