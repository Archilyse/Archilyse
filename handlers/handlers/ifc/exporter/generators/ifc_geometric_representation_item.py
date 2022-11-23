from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import ifcopenshell
import numpy as np
from methodtools import lru_cache

from handlers.ifc.types import (
    IfcArbitraryClosedProfileDef,
    IfcArbitraryProfileDefWithVoids,
    IfcAxis2Placement2d,
    IfcAxis2Placement3d,
    IfcCartesianPoint,
    IfcCartesianTransformationOperator3dNonUniform,
    IfcConnectedFaceSet,
    IfcCurve,
    IfcDirection,
    IfcExtrudedAreaSolid,
    IfcFace,
    IfcFaceBasedSurfaceModel,
    IfcFaceOuterBound,
    IfcGeometricRepresentationItem,
    IfcMappedItem,
    IfcPolyline,
    IfcPolyLoop,
    IfcRepresentationContext,
    IfcRepresentationMap,
    IfcShapeRepresentation,
)


class IfcGeometricRepresentationItemGenerator:
    """
    From the documentation:
    ```
    An IfcGeometricRepresentationItem is the common supertype of all geometric items
    used within a representation. It is positioned within a geometric coordinate
    system, directly or indirectly through intervening items.
    ```

    All public methods return a RepresentationItem that can be wrapped
    inside a ShapeRepresentation / ProductDefinition in order to be displayed
    in the IFC.

    In order to add models for a product, the following methods are provided:
     * add_ifc_polyline
     * add_ifc_extruded_area_solid
     * add_ifc_face_based_surface_model
     * add_ifc_annotation_fill_area (TODO)
     * add_ifc_annotation_text (TODO)

    If a geometric item such as a surface model is instantiated ones and supposed
    to be mapped to different locations, the following method can be used
    to generate a representation item corresponding to the desired positioning:
     - add_mapping_to_item

    For styling of geometries or assigning them to layers, the following methods
    can be used:
     - add_style_to_item (TODO)
     - add_layer_to_item (TODO)
    """

    @classmethod
    def add_ifc_polyline(
        cls, ifc_file: ifcopenshell.file, Points: List[Tuple[float, float, float]]
    ) -> IfcPolyline:
        return ifc_file.create_entity(
            IfcPolyline.__name__,
            Points=cls._add_ifc_cartesian_points(ifc_file=ifc_file, points=Points),
        )

    # Extruded AreaSolid

    @classmethod
    def add_ifc_extruded_area_solid(
        cls,
        ifc_file,
        exterior: List[Tuple[float, float, float]],
        extrusion_height: float,
        holes: Optional[List[List[Tuple[float, float, float]]]],
        extrusion_direction: Optional[Tuple[float, float, float]] = (0.0, 0.0, 1.0),
        Position: Optional[IfcAxis2Placement3d] = None,
    ) -> IfcExtrudedAreaSolid:
        exterior_polyline = cls.add_ifc_polyline(ifc_file=ifc_file, Points=exterior)

        if not holes:
            swept_area = cls._add_ifc_arbitrary_closed_profile_def(
                ifc_file=ifc_file, OuterCurve=exterior_polyline, ProfileType="AREA"
            )
        else:
            interior_polylines = [
                cls.add_ifc_polyline(ifc_file=ifc_file, Points=polygon)
                for polygon in holes
            ]
            swept_area = cls._add_ifc_arbitrary_closed_profile_def_with_voids(
                ifc_file=ifc_file,
                OuterCurve=exterior_polyline,
                InnerCurves=interior_polylines,
                ProfileType="AREA",
            )

        if not Position:
            Position = ifc_file.create_entity(
                IfcAxis2Placement3d.__name__,
                Location=cls._add_ifc_cartesian_point(
                    ifc_file=ifc_file, point=(0, 0, 0)
                ),
            )

        return ifc_file.create_entity(
            IfcExtrudedAreaSolid.__name__,
            SweptArea=swept_area,
            Position=Position,
            Depth=extrusion_height,
            ExtrudedDirection=cls._add_ifc_direction(
                ifc_file=ifc_file, DirectionRatios=extrusion_direction
            ),
        )

    @classmethod
    def _add_ifc_arbitrary_closed_profile_def(
        cls,
        ifc_file,
        OuterCurve: IfcCurve,
        ProfileType: Literal["CURVE", "AREA"],
        ProfileName: Optional[str] = None,
    ):
        return ifc_file.create_entity(
            IfcArbitraryClosedProfileDef.__name__,
            ProfileType=ProfileType,
            ProfileName=ProfileName,
            OuterCurve=OuterCurve,
        )

    @classmethod
    def _add_ifc_arbitrary_closed_profile_def_with_voids(
        cls,
        ifc_file,
        OuterCurve: IfcCurve,
        InnerCurves: List[IfcCurve],
        ProfileType: Literal["CURVE", "AREA"],
        ProfileName: Optional[str] = None,
    ):
        return ifc_file.create_entity(
            IfcArbitraryProfileDefWithVoids.__name__,
            ProfileType=ProfileType,
            ProfileName=ProfileName,
            OuterCurve=OuterCurve,
            InnerCurves=InnerCurves,
        )

    # Surface Model

    @classmethod
    def add_ifc_face_based_surface_model(
        cls,
        ifc_file,
        file_path: Path,
        model_matrix: np.array,
        normalize: Optional[bool] = True,
    ) -> IfcFaceBasedSurfaceModel:
        """
        Args:
            model_matrix (np.array):
                The model matrix such that
                +x is a short side,
                +y is a long side,
                The + direction faces away from the wall if the feature is wall-aligned

            TODO: Remove this transformation logic and use the Placement
                  in add_mapping instead (there the base axes can be defined)
        """
        return ifc_file.create_entity(
            IfcFaceBasedSurfaceModel.__name__,
            FbsmFaces=cls._load_surface_model(
                ifc_file=ifc_file,
                file_path=file_path.as_posix(),
                model_matrix=tuple(map(tuple, model_matrix.tolist())),
                normalize=normalize,
            ),
        )

    @lru_cache(maxsize=None)
    @classmethod
    def _load_surface_model(
        cls,
        ifc_file,
        file_path: str,
        model_matrix: Tuple,
        normalize: Optional[bool] = True,
    ) -> List[IfcConnectedFaceSet]:
        from collada import Collada
        from collada.triangleset import TriangleSet

        mesh = Collada(file_path)

        # meta-data for normalization
        all_vertices = np.vstack(
            [
                triangle_set.vertex
                for geometry in mesh.geometries
                for triangle_set in geometry.primitives
            ]
        )
        length, width, height = all_vertices.max(axis=0) - all_vertices.min(axis=0)
        centroid = all_vertices.mean(axis=0)

        ifc_connected_face_sets = []
        for geometry in mesh.geometries:
            for triangle_set in geometry.primitives:
                if not isinstance(triangle_set, TriangleSet):
                    continue

                ifc_cartesian_points = [
                    tuple(
                        np.dot(
                            model_matrix,
                            ((vertex - centroid) / (length, width, height)),
                        )
                    )
                    if normalize
                    else tuple(np.dot(model_matrix, vertex))
                    for vertex in triangle_set.vertex
                ]

                ifc_faces = [
                    cls._add_ifc_face(
                        ifc_file=ifc_file,
                        Polygon=[
                            ifc_cartesian_points[i1],
                            ifc_cartesian_points[i2],
                            ifc_cartesian_points[i3],
                        ],
                    )
                    for i1, i2, i3 in triangle_set.vertex_index
                ]

                if ifc_faces:
                    ifc_connected_face_sets.append(
                        ifc_file.create_entity(
                            IfcConnectedFaceSet.__name__, CfsFaces=ifc_faces
                        )
                    )

        return ifc_connected_face_sets

    @classmethod
    def _add_ifc_face(
        cls, ifc_file: ifcopenshell.file, Polygon: List[Tuple[float, float, float]]
    ) -> IfcFace:
        polyloop = ifc_file.create_entity(
            IfcPolyLoop.__name__,
            Polygon=cls._add_ifc_cartesian_points(ifc_file=ifc_file, points=Polygon),
        )

        return ifc_file.create_entity(
            IfcFace.__name__,
            Bounds=[
                ifc_file.create_entity(
                    IfcFaceOuterBound.__name__, Bound=polyloop, Orientation=False
                )
            ],
        )

    # Mappings

    @classmethod
    def add_mapping(
        cls,
        ifc_file,
        MappedRepresentation: IfcShapeRepresentation,
        axes: List[Tuple[float, float, float]],
        scales: Tuple[float, float, float],
        translation: Tuple[float, float, float],
        MappingOrigin: Union[IfcAxis2Placement3d, IfcAxis2Placement2d] = None,
    ) -> IfcMappedItem:
        if not MappingOrigin:
            MappingOrigin = ifc_file.create_entity(
                IfcAxis2Placement3d.__name__,
                Location=cls._add_ifc_cartesian_point(
                    ifc_file=ifc_file, point=(0, 0, 0)
                ),
                # TODO: Use Axis / RefDirection here for transforming models,
                #       see `add_ifc_face_based_surface_model`
            )

        transformation = ifc_file.create_entity(
            IfcCartesianTransformationOperator3dNonUniform.__name__,
            Axis1=cls._add_ifc_direction(
                ifc_file=ifc_file, DirectionRatios=tuple(axes[0])
            ),
            Axis2=cls._add_ifc_direction(
                ifc_file=ifc_file, DirectionRatios=tuple(axes[1])
            ),
            LocalOrigin=cls._add_ifc_cartesian_point(
                ifc_file=ifc_file, point=tuple(translation)
            ),
            Scale=scales[0],
            Axis3=cls._add_ifc_direction(
                ifc_file=ifc_file, DirectionRatios=tuple(axes[2])
            ),
            Scale2=scales[1],
            Scale3=scales[2],
        )

        representation_map = ifc_file.create_entity(
            IfcRepresentationMap.__name__,
            MappingOrigin=MappingOrigin,
            MappedRepresentation=MappedRepresentation,
        )

        return ifc_file.create_entity(
            IfcMappedItem.__name__,
            MappingSource=representation_map,
            MappingTarget=transformation,
        )

    # Shape Representation

    @classmethod
    def add_shape_representation(
        cls,
        ifc_file,
        ContextOfItems: IfcRepresentationContext,
        RepresentationIdentifier: str,
        RepresentationType: str,
        Items: List[IfcGeometricRepresentationItem],
    ):
        return ifc_file.create_entity(
            IfcShapeRepresentation.__name__,
            ContextOfItems=ContextOfItems,
            RepresentationIdentifier=RepresentationIdentifier,
            RepresentationType=RepresentationType,
            Items=Items,
        )

    # Others

    @classmethod
    def _add_ifc_cartesian_points(
        cls, ifc_file: ifcopenshell.file, points: List[Tuple[float, float, float]]
    ) -> List[IfcCartesianPoint]:
        return [
            cls._add_ifc_cartesian_point(ifc_file=ifc_file, point=point)
            for point in points
        ]

    @lru_cache(maxsize=None)
    @classmethod
    def _add_ifc_cartesian_point(
        cls, ifc_file: ifcopenshell.file, point: Tuple[float, float, float]
    ) -> IfcCartesianPoint:
        return ifc_file.create_entity(
            IfcCartesianPoint.__name__, Coordinates=tuple(map(float, point))
        )

    @lru_cache(maxsize=None)
    @classmethod
    def _add_ifc_direction(
        cls,
        ifc_file,
        DirectionRatios: Union[Tuple[float, float, float], Tuple[float, float]],
    ) -> IfcDirection:
        return ifc_file.create_entity(
            IfcDirection.__name__, DirectionRatios=tuple(map(float, DirectionRatios))
        )

    @lru_cache()
    @classmethod
    def _add_ifc_axis2_placement3d(
        cls,
        ifc_file,
        Location: Tuple[float, float, float],
        Axis: Optional[IfcDirection] = None,
        RefDirection: Optional[IfcDirection] = None,
    ) -> IfcAxis2Placement3d:
        """
        Args:
            Axis (Optional[IfcDirection], optional): Z-Axis
            RefDirection (Optional[IfcDirection], optional): X-Axis (Y-axis is derived)
        """
        return ifc_file.create_entity(
            IfcAxis2Placement3d.__name__,
            Location=cls._add_ifc_cartesian_point(ifc_file=ifc_file, point=Location),
            Axis=Axis,
            RefDirection=RefDirection,
        )
