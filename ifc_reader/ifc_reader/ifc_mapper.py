from abc import ABC
from typing import TYPE_CHECKING, List, Tuple

from brooks.util.geometry_ops import ensure_geometry_validity
from dufresne.polygon.utils import as_multipolygon
from ifc_reader.types import Ifc2DEntity

if TYPE_CHECKING:
    from ifc_reader.reader import IfcReader

from ifcopenshell.geom import create_shape as ifc_create_shape
from ifcopenshell.geom import settings
from shapely.geometry import CAP_STYLE, JOIN_STYLE, LineString, MultiPolygon, Polygon
from shapely.ops import unary_union

from common_utils.logger import logger
from ifc_reader.exceptions import (
    IfcMapperException,
    IfcUncoveredGeometricalRepresentation,
)


class IfcToSpatialEntityMapper(ABC):
    """
    Abstract class defining top-level operations for converting IFC elements into their Brooks counterparts, implemented
    to Gang of Four Strategy Pattern.
    """

    __ifc_settings = settings()
    __ifc_settings.set(settings.USE_WORLD_COORDS, True)

    def __init__(self, reader: "IfcReader"):
        self.wrapper = reader.wrapper
        self.length_si_unit = reader.length_si_unit
        self.reference_point = reader.reference_point

    def get_ifc_2d_entity(self, ifc_element) -> Ifc2DEntity:
        try:
            shape = ifc_create_shape(settings=self.__ifc_settings, inst=ifc_element)
            return self._get_geometry_from_ifc_shape(
                ifc_shape=shape, ifc_type=ifc_element.is_a()
            )
        except RuntimeError as e:
            if str(e) in ("Representation is NULL", "Failed to process shape"):
                raise IfcUncoveredGeometricalRepresentation(e)
            raise e
        except Exception as e:
            logger.debug(f"Could not generate geometry from an IFC shape. {e}")
            raise IfcMapperException(e) from e

    @staticmethod
    def _get_polygon_from_vertices(face_vertices: List) -> Polygon:
        """
        Constructs a polygon from element face vertices, with final coordinates for the geometry placement.
        Args:
            face_vertices: list of (x, y) vertices defining the face geometry.
        Returns:
            Polygon: face geometry, which can be subsequently merged with other element faces.
        """

        flattened_vertices = [(x, y) for x, y, _ in face_vertices]
        polygon = ensure_geometry_validity(geometry=Polygon(flattened_vertices))
        if polygon.area == 0.0:
            return ensure_geometry_validity(
                geometry=LineString(flattened_vertices).buffer(
                    distance=1e-9,
                    join_style=JOIN_STYLE.mitre,
                    cap_style=CAP_STYLE.square,
                )
            )
        return polygon

    def _get_geometry_from_ifc_shape(self, ifc_shape, ifc_type: str) -> Ifc2DEntity:
        # Get IFC shape geometry
        f = ifc_shape.geometry.faces
        v = ifc_shape.geometry.verts

        # Create vertices, faces
        verts = [v[i : i + 3] for i in range(0, len(v), 3)]
        faces = [f[i : i + 3] for i in range(0, len(f), 3)]
        if not verts or not faces:
            raise IfcMapperException(
                f"IFC element with id {ifc_shape.id} does not have a valid mesh to generate a geometry"
            )

        valid_polygons = self.get_polygons_from_vertices_and_faces(
            faces=faces, vertices=verts
        )
        combined_polygons = unary_union(valid_polygons)
        combined_polygons = as_multipolygon(
            ensure_geometry_validity(geometry=combined_polygons)
        )

        if combined_polygons.length == 0.0 or combined_polygons.area == 0.0:
            # It seems technically impossible to have this case, as we are always buffering if the polygon is a line
            raise IfcMapperException(
                f"IFC element with id {ifc_shape.id} is generating a polygon with no area"
            )

        if isinstance(
            combined_polygons,
            (
                Polygon,
                MultiPolygon,
            ),
        ):
            coord_z = [v[2] for v in verts]
            return Ifc2DEntity(
                min_height=min(coord_z),
                max_height=max(coord_z),
                geometry=combined_polygons,
                ifc_type=ifc_type,
            )

        raise IfcMapperException(
            f"IFC element with id {ifc_shape.id} is of type {type(combined_polygons)}"
            f" and not a Polygon/MultiPolygon."
        )

    def get_polygons_from_vertices_and_faces(
        self, faces: List[int], vertices: List[Tuple[float, float, float]]
    ):
        valid_polygons = []
        for a, b, c in faces:
            face_vertices = [vertices[a], vertices[b], vertices[c]]
            polygon = self._get_polygon_from_vertices(face_vertices=face_vertices)
            valid_polygons.append(polygon)
        return valid_polygons
