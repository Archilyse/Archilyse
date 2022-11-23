from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np
from shapely.affinity import scale
from shapely.geometry import GeometryCollection, LineString, Point, Polygon

from brooks.constants import FEATURE_SIDES_ON_WALL, FeatureSide
from brooks.types import FeatureType
from brooks.util.io import BrooksSerializable
from brooks.utils import get_default_element_height, get_default_element_lower_edge
from common_utils.exceptions import AngleInferenceException
from dufresne.polygon import (
    get_polygon_from_pos_dim_angle,
    get_sides_as_lines_by_length,
)

from .parameterical_geometry import ParametricalGeometry
from .spatial_entity import SpatialEntity

if TYPE_CHECKING:
    from simulations.view.meshes import GeoreferencingTransformation


class SimFeature(SpatialEntity, BrooksSerializable):
    """A Feature is a thing describing relevant things for an analyse."""

    __serializable_fields__ = (
        "type",
        "id",
        "height",
        "position",
        "dim",
        "tags",
        "angle",
        "parametrical_geometry",
        "footprint",
        "dx",
        "dy",
        "feature_type_properties",
    )

    def __init__(
        self,
        dim=None,
        height=None,
        footprint=None,
        feature_type: FeatureType = FeatureType.NOT_DEFINED,
        position=None,
        angle=None,
        feature_id=None,
        tags=None,
        parametrical_geometry: Optional[ParametricalGeometry] = None,
        name=None,
        dx=None,
        dy=None,
        feature_type_properties=None,
    ):
        """Initialisation of an object"""
        super().__init__(
            footprint=footprint,
            height=height,
            entity_id=feature_id,
            angle=angle,
            position=position,
        )

        self._type = feature_type
        self.dim = dim
        self.tags = tags
        self.parametrical_geometry = parametrical_geometry
        self.name = name
        self.dx = dx
        self.dy = dy

        if feature_type_properties is None:
            feature_type_properties = {}
        self.feature_type_properties = feature_type_properties

    def absolute_to_relative_coordinates(self, absolute_parent_position):
        if self.dim is not None:
            self.position = Point(
                self.position.x - absolute_parent_position.x,
                self.position.y - absolute_parent_position.y,
            )
        else:
            self.footprint_absolute_to_relative_coordinates(absolute_parent_position)

    def apply_georef(
        self, georeferencing_transformation: "GeoreferencingTransformation"
    ):
        super().apply_georef(
            georeferencing_transformation=georeferencing_transformation
        )
        if self.dim is not None:
            self.footprint = get_polygon_from_pos_dim_angle(
                pos=(self.position.x, self.position.y),
                dim=georeferencing_transformation.apply_shapely(geom=self.dim),
                angle=self.angle,
            )
        if self.angle is not None:
            self.angle -= georeferencing_transformation._rotation_angle
        if self.dx is not None:
            self.dx *= georeferencing_transformation._scaling_factor
        if self.dy is not None:
            self.dy *= georeferencing_transformation._scaling_factor

    # Orientation

    def _legacy_get_axes(self, walls: List[Polygon]):
        # NOTE: Can be removed when the old editor is being phased out / if
        #       we are sure we don't need to create IFCs from old annotations
        short_axis, long_axis = self._get_short_and_long_axis(walls=walls)

        axes = np.zeros((3, 3))
        axes[0] = [*short_axis, 0.0]
        axes[1] = [*long_axis, 0.0]
        axes[2] = [
            0.0,
            0.0,
            get_default_element_height(element_type=self.type),
        ]

        return axes

    def axes_scales_translation(
        self, walls: List[Polygon], altitude: float
    ) -> np.array:
        if self.angle is None:
            axes = self._legacy_get_axes(walls=walls)
            scales = np.linalg.norm(axes, ord=2, axis=1)
            axes = (np.array(axes.T) / scales).T.tolist()
        else:
            angle_rot = np.deg2rad(self.angle + 180.0)
            axes = np.array(
                [
                    [np.cos(-angle_rot), np.sin(-angle_rot), 0],
                    [np.sin(-angle_rot), np.cos(-angle_rot), 0],
                    [0, 0, 1],
                ]
            )
            scales = np.array(
                [
                    self.dx * 2,
                    self.dy * 2,
                    get_default_element_height(element_type=self.type),
                ]
            )

        translation = [
            self.footprint.centroid.x,
            self.footprint.centroid.y,
            altitude
            + get_default_element_lower_edge(element_type=self.type)
            + (get_default_element_height(element_type=self.type)) / 2,
        ]

        return axes, scales, translation

    def _get_short_and_long_axis(
        self, walls: List[Polygon]
    ) -> Tuple[np.array, np.array]:
        (
            intersecting_side,
            orthogonal_side,
        ) = self.get_intersecting_and_orthogonal_side_from_walls(walls=walls)

        if FEATURE_SIDES_ON_WALL.get(self.type) == FeatureSide.SHORT_SIDE:
            return (
                self.line_string_to_vector(intersecting_side),
                self.line_string_to_vector(orthogonal_side),
            )
        return (
            self.line_string_to_vector(orthogonal_side),
            self.line_string_to_vector(intersecting_side),
        )

    def get_intersecting_and_orthogonal_side_from_walls(
        self, walls: List[Polygon]
    ) -> Tuple[np.array, np.array]:
        feature_sides = get_sides_as_lines_by_length(
            self.footprint.minimum_rotated_rectangle
        )
        short_sides, long_sides = feature_sides[:2], feature_sides[2:]

        if FEATURE_SIDES_ON_WALL.get(self.type) is None:
            return (
                self.line_string_to_vector(long_sides[0]),
                self.line_string_to_vector(short_sides[1]),
            )

        # determine closest separator to the feature that is aligned on the long side
        # with the feature on the features expected side (FEATURE_SIDES_ON_WALL.get(self.type, ""))
        if FEATURE_SIDES_ON_WALL.get(self.type) == FeatureSide.SHORT_SIDE:
            must_intersect_line = scale(long_sides[0], xfact=5, yfact=5)
        else:
            must_intersect_line = scale(short_sides[0], xfact=5, yfact=5)

        separator_candidates = [
            wall
            for wall in walls
            if GeometryCollection(get_sides_as_lines_by_length(wall)[2:]).intersects(
                must_intersect_line
            )
        ]
        if not separator_candidates:
            raise AngleInferenceException(
                "Did not find any separators to infer the feature's axes from."
            )

        closest_intersecting_separator = sorted(
            separator_candidates,
            key=lambda z: z.distance(GeometryCollection(long_sides)),
        )[0]

        return self._get_intersecting_and_orthogonal_side(
            wall=closest_intersecting_separator
        )

    def _get_intersecting_and_orthogonal_side(
        self, wall: Polygon
    ) -> Tuple[LineString, LineString]:
        """Returns the orthogonal / side such that the + direction faces away from the separator"""
        sides = get_sides_as_lines_by_length(self.footprint.minimum_rotated_rectangle)

        interesecting_sides = (
            sides[:2]
            if FEATURE_SIDES_ON_WALL.get(self.type) == FeatureSide.SHORT_SIDE
            else sides[2:]
        )
        orthogonal_sides = (
            sides[2:]
            if FEATURE_SIDES_ON_WALL.get(self.type) == FeatureSide.SHORT_SIDE
            else sides[:2]
        )

        intersecting_side = sorted(interesecting_sides, key=lambda z: wall.distance(z))[
            0
        ]
        orthogonal_side = sorted(
            orthogonal_sides,
            key=lambda z: wall.distance(Point(z.coords[0])),
        )[1]

        return intersecting_side, orthogonal_side

    @staticmethod
    def line_string_to_vector(line: LineString) -> np.array:
        return np.array(line.coords[1]) - np.array(line.coords[0])
