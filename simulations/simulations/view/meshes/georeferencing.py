from functools import cached_property
from typing import List, Optional, Union

import numpy as np
from shapely.affinity import affine_transform
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from brooks.util.geometry_ops import ensure_geometry_validity


class GeoreferencingTransformation:
    def __init__(self):
        # Rotation Defaults (no rotation)
        self._rotation_pivot_x = 0.0
        self._rotation_pivot_y = 0.0
        self._rotation_angle = 0.0

        # Scaling Defaults (no scaling)
        self._scaling_pivot_x = 0.0
        self._scaling_pivot_y = 0.0
        self._scaling_factor = 1.0

        # Translation defaults (no translation)
        self._translation_x = 0.0
        self._translation_y = 0.0
        self._translation_z = 0.0

        # Swap Dimensions
        self._swap_dimensions = None

    def set_scaling(self, pivot_x, pivot_y, factor):
        self._scaling_pivot_x = pivot_x
        self._scaling_pivot_y = pivot_y
        self._scaling_factor = factor

    def set_rotation(self, pivot_x, pivot_y, angle):
        self._rotation_pivot_x = pivot_x
        self._rotation_pivot_y = pivot_y
        self._rotation_angle = angle

    def set_translation(self, x, y, z):
        self._translation_x = x
        self._translation_y = y
        self._translation_z = z

    def set_swap_dimensions(self, axis1, axis2):
        self._swap_dimensions = (axis1, axis2)

    def apply(
        self, vertices: Union[List, np.ndarray], matrix: Optional[np.array] = None
    ):
        new_vertices = np.array(vertices)
        if new_vertices.size == 0:
            return np.array([])

        if matrix is None:
            matrix = self._affine_transformation_matrix

        new_vertices = np.tensordot(
            np.hstack([new_vertices, np.ones((new_vertices.shape[0], 1))]),
            matrix,
            axes=(1, 1),
        )[:, :-1]

        if self._swap_dimensions is not None:
            new_vertices[
                :, [self._swap_dimensions[0], self._swap_dimensions[1]]
            ] = new_vertices[:, [self._swap_dimensions[1], self._swap_dimensions[0]]]

        return new_vertices

    def apply_shapely(
        self,
        geom: Union[MultiPolygon, Polygon, Point, LineString],
        matrix: Optional[np.array] = None,
    ):
        if geom.is_empty:
            return geom

        if matrix is None:
            matrix = self._affine_transformation_matrix

        a, b, c, xoff, d, e, f, yoff, g, h, i, zoff, _, _, _, _ = matrix.flatten()

        return ensure_geometry_validity(
            affine_transform(
                geom=geom, matrix=(a, b, c, d, e, f, g, h, i, xoff, yoff, zoff)
            )
        )

    def invert(self, vertices: Union[List, np.ndarray]):
        new_vertices = np.array(vertices)

        if self._swap_dimensions:
            new_vertices[
                :, [self._swap_dimensions[0], self._swap_dimensions[1]]
            ] = new_vertices[:, [self._swap_dimensions[1], self._swap_dimensions[0]]]

        return self.apply(
            vertices=new_vertices, matrix=self._inverse_affine_transformation_matrix
        )

    def invert_shapely(
        self,
        geom: Union[MultiPolygon, Polygon, Point],
    ):
        return self.apply_shapely(
            geom=geom, matrix=self._inverse_affine_transformation_matrix
        )

    @cached_property
    def _affine_transformation_matrix(self):
        return np.dot(
            self._translation_matrix(),
            np.dot(self._rotation_matrix(), self._scaling_matrix()),
        )

    @cached_property
    def _inverse_affine_transformation_matrix(self):
        return np.dot(
            self._scaling_matrix(invert=True),
            np.dot(
                self._rotation_matrix(invert=True),
                self._translation_matrix(invert=True),
            ),
        )

    def _rotation_matrix(self, invert: bool = False) -> np.array:
        angle = np.deg2rad(
            self._rotation_angle if not invert else -self._rotation_angle
        )
        cosp, sinp = np.cos(angle), np.sin(angle)
        if abs(cosp) < 2.5e-16:
            cosp = 0.0
        if abs(sinp) < 2.5e-16:
            sinp = 0.0

        rx0, ry0 = self._rotation_pivot_x, self._rotation_pivot_y
        return np.array(
            (
                (cosp, -sinp, 0.0, rx0 - rx0 * cosp + ry0 * sinp),
                (sinp, cosp, 0.0, ry0 - rx0 * sinp - ry0 * cosp),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

    def _scaling_matrix(self, invert: bool = False) -> np.array:
        sx0, sy0 = self._scaling_pivot_x, self._scaling_pivot_y
        scaling_factor = (
            self._scaling_factor if not invert else 1 / self._scaling_factor
        )
        return np.array(
            (
                (scaling_factor, 0.0, 0.0, sx0 - sx0 * scaling_factor),
                (0.0, scaling_factor, 0.0, sy0 - sy0 * scaling_factor),
                (0.0, 0.0, 1.0, 0.0),
                (0.0, 0.0, 0.0, 1.0),
            )
        )

    def _translation_matrix(self, invert: bool = False) -> np.array:
        dx, dy, dz = (
            self._translation_x,
            self._translation_y,
            self._translation_z,
        )

        if invert:
            dx, dy, dz = -dx, -dy, -dz

        return np.array(
            (
                (1.0, 0.0, 0.0, dx),
                (0.0, 1.0, 0.0, dy),
                (0.0, 0.0, 1.0, dz),
                (0.0, 0.0, 0.0, 1.0),
            )
        )
