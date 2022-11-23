from pathlib import Path
from typing import Optional

from numpy import array, identity
from shapely.geometry import Polygon
from shapely.ops import transform

from common_utils.constants import ARTEFACT_AREA_SIZE
from handlers.ifc.exporter.generators import IfcGeometricRepresentationItemGenerator
from handlers.ifc.types import (
    IfcGeometricRepresentationItem,
    IfcRepresentationContext,
    IfcShapeRepresentation,
)


class GeometryIfcMapper:
    """
    Shapely Logic
    """

    @staticmethod
    def polygon_to_footprint(
        ifc_file,
        context: IfcRepresentationContext,
        polygon: Polygon,
        start_altitude: float,
        end_altitude: float,
    ) -> IfcShapeRepresentation:
        polygon_3d = transform(lambda x, y: (x, y, start_altitude), polygon)

        geometrical_representation_item = (
            IfcGeometricRepresentationItemGenerator.add_ifc_extruded_area_solid(
                ifc_file=ifc_file,
                exterior=polygon_3d.exterior.coords,
                holes=[interior.coords for interior in polygon_3d.interiors],
                extrusion_height=end_altitude - start_altitude,
            )
        )

        return IfcGeometricRepresentationItemGenerator.add_shape_representation(
            ifc_file=ifc_file,
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[geometrical_representation_item],
        )

    @staticmethod
    def polygon_to_extruded_solid(
        ifc_file,
        context: IfcRepresentationContext,
        polygon: Polygon,
        start_altitude: float,
        end_altitude: float,
    ) -> IfcShapeRepresentation:
        polygon_3d = transform(lambda x, y: (x, y, start_altitude), polygon)
        geometrical_representation_item = (
            IfcGeometricRepresentationItemGenerator.add_ifc_extruded_area_solid(
                ifc_file=ifc_file,
                exterior=polygon_3d.exterior.coords,
                holes=[
                    interior.coords
                    for interior in polygon_3d.interiors
                    if Polygon(interior).area >= ARTEFACT_AREA_SIZE
                ],
                extrusion_height=end_altitude - start_altitude,
            )
        )

        return IfcGeometricRepresentationItemGenerator.add_shape_representation(
            ifc_file=ifc_file,
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[geometrical_representation_item],
        )

    @classmethod
    def transformed_surface_model(
        cls,
        ifc_file,
        context: IfcRepresentationContext,
        surface_model_path: Path,
        axes: array,
        scales: array,
        translation: array,
        surface_model_matrix: Optional[array] = None,
    ) -> IfcShapeRepresentation:
        if surface_model_matrix is None:
            surface_model_matrix = identity(3)

        geometrical_representation_item = (
            IfcGeometricRepresentationItemGenerator.add_ifc_face_based_surface_model(
                ifc_file=ifc_file,
                file_path=surface_model_path,
                model_matrix=surface_model_matrix,
            )
        )

        return cls._remap_ifc_geometry_to_polygon_bounds(
            ifc_file=ifc_file,
            context=context,
            geometrical_representation_item=geometrical_representation_item,
            axes=axes,
            scales=scales,
            translation=translation,
        )

    @staticmethod
    def _remap_ifc_geometry_to_polygon_bounds(
        ifc_file,
        context: IfcRepresentationContext,
        geometrical_representation_item: IfcGeometricRepresentationItem,
        axes: array,
        scales: array,
        translation: array,
    ) -> IfcShapeRepresentation:
        representation = (
            IfcGeometricRepresentationItemGenerator.add_shape_representation(
                ifc_file=ifc_file,
                ContextOfItems=context,
                RepresentationIdentifier="Body",
                RepresentationType="SurfaceModel",
                Items=[geometrical_representation_item],
            )
        )

        mapped_item = IfcGeometricRepresentationItemGenerator.add_mapping(
            ifc_file=ifc_file,
            MappedRepresentation=representation,
            axes=axes,
            scales=scales,
            translation=translation,
        )

        return IfcGeometricRepresentationItemGenerator.add_shape_representation(
            ifc_file=ifc_file,
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="MappedRepresentation",
            Items=[mapped_item],
        )
