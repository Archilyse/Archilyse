from pathlib import Path
from typing import List, Optional, Tuple, Type, Union

import ifcopenshell
from numpy import array
from shapely.geometry import Polygon

from handlers.ifc.exporter.generators import (
    IfcGeometricRepresentationItemGenerator,
    IfcProductGenerator,
    IfcRelationshipGenerator,
)
from handlers.ifc.types import (
    IfcBuilding,
    IfcBuildingElement,
    IfcBuildingStorey,
    IfcDoor,
    IfcElement,
    IfcFurniture,
    IfcLocalPlacement,
    IfcOpeningElement,
    IfcProductDefinitionShape,
    IfcProject,
    IfcRailing,
    IfcRelAggregates,
    IfcRelContainedInSpatialStructure,
    IfcRepresentationContext,
    IfcSanitaryTerminal,
    IfcSite,
    IfcSlabStandardCase,
    IfcSpace,
    IfcSpatialZone,
    IfcStair,
    IfcWallStandardCase,
    IfcWindow,
)

from .geometry import GeometryIfcMapper
from .properties import PropertyIfcMapper
from .quantities import QuantityIfcMapper


class EntityIfcMapper:
    """
    Ifc Structure Logic, agnostic to brooks etc. but uses shapely (in GeometryIfcMapper)
    """

    @staticmethod
    def add_site(
        ifc_file,
        ifc_project: IfcProject,
        longitude: Tuple[int, int, int, int],
        latitude: Tuple[int, int, int, int],
        client_site_id: str,
        site_name: str,
    ) -> IfcSite:
        ifc_site = IfcProductGenerator.add_ifc_spatial_element(
            ifc_file=ifc_file,
            ifc_spatial_element_type=IfcSite,
            RefLongitude=longitude,
            RefLatitude=latitude,
            Name=client_site_id,
            LongName=site_name,
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file, Location=(0, 0, 0)
                ),
            ),
        )
        IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=ifc_project,
            children=[ifc_site],
            relationship_type=IfcRelAggregates,
        )
        return ifc_site

    @staticmethod
    def add_building(
        ifc_file, ifc_site: IfcSite, street: str, housenumber: str
    ) -> IfcBuilding:
        return IfcProductGenerator.add_ifc_spatial_element(
            ifc_file=ifc_file,
            ifc_spatial_element_type=IfcBuilding,
            Name=f"{street} {housenumber}",
            LongName=f"{street} {housenumber}",
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file, Location=(0, 0, 0)
                ),
                PlacementRelTo=ifc_site.ObjectPlacement,
            ),
        )

    @staticmethod
    def add_floor(
        ifc_file, ifc_building: IfcBuilding, floor_number: int, elevation: float
    ) -> IfcBuildingStorey:
        return IfcProductGenerator.add_ifc_spatial_element(
            ifc_file=ifc_file,
            ifc_spatial_element_type=IfcBuildingStorey,
            Name=f"Floor {floor_number}",
            LongName=f"Floor {floor_number}",
            Elevation=elevation,
            CompositionType="ELEMENT",
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file, Location=(0, 0, elevation)
                ),
                PlacementRelTo=ifc_building.ObjectPlacement,
            ),
        )

    @staticmethod
    def add_unit(ifc_file: ifcopenshell.file, client_id: str) -> IfcSpatialZone:
        return IfcProductGenerator.add_ifc_spatial_element(
            ifc_file=ifc_file,
            ifc_spatial_element_type=IfcSpatialZone,
            Name=client_id,
            LongName=client_id,
        )

    @staticmethod
    def add_area(
        ifc_file,
        context: IfcRepresentationContext,
        ifc_floor: IfcBuildingStorey,
        polygon: Polygon,
        start_elevation_relative_to_floor: float,
        height: float,
        area_type: str,
        area_number_in_floor: int,
        floor_number: int,
        is_public: bool,
        building_code_type: Optional[str] = None,
    ) -> IfcSpace:
        body = GeometryIfcMapper.polygon_to_footprint(
            ifc_file=ifc_file,
            context=context,
            polygon=polygon,
            start_altitude=start_elevation_relative_to_floor,
            end_altitude=height,
        )

        space_name = f"{area_type}-{floor_number}.{area_number_in_floor}"
        ifc_space = IfcProductGenerator.add_ifc_spatial_element(
            ifc_file=ifc_file,
            ifc_spatial_element_type=IfcSpace,
            Name=space_name,
            LongName=None,
            Representation=ifc_file.create_entity(
                IfcProductDefinitionShape.__name__, Representations=[body]
            ),
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file,
                    Location=(0, 0, start_elevation_relative_to_floor),
                ),
                PlacementRelTo=ifc_floor.ObjectPlacement,
            ),
        )

        QuantityIfcMapper.add_area_quantities(
            ifc_file=ifc_file, ifc_space=ifc_space, polygon=polygon, height=height
        )

        PropertyIfcMapper.add_area_properties(
            ifc_file=ifc_file,
            ifc_space=ifc_space,
            building_code_type=building_code_type,
            is_public=is_public,
        )

        return ifc_space

    # PHYSICAL ELEMENTS

    @staticmethod
    def add_wall_railing_slab_furniture(
        ifc_file,
        ifc_floor: IfcBuildingStorey,
        context: IfcRepresentationContext,
        polygon: Polygon,
        start_elevation_relative_to_floor: float,
        height: float,
        element_type: Type[
            Union[IfcWallStandardCase, IfcRailing, IfcSlabStandardCase, IfcFurniture]
        ],
        *args,
        **kwargs,
    ) -> IfcBuildingElement:
        geometry_start_altitude, geometry_end_altitude = 0.0, height
        if height < 0:
            geometry_start_altitude, geometry_end_altitude = (
                start_elevation_relative_to_floor + height,
                start_elevation_relative_to_floor,
            )

        body = GeometryIfcMapper.polygon_to_extruded_solid(
            ifc_file=ifc_file,
            polygon=polygon,
            context=context,
            start_altitude=geometry_start_altitude,
            end_altitude=geometry_end_altitude,
        )
        ifc_element = IfcProductGenerator.add_ifc_element(  # type: ignore
            ifc_file=ifc_file,
            ifc_element_type=element_type,
            Representation=ifc_file.create_entity(
                IfcProductDefinitionShape.__name__, Representations=[body]
            ),
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file,
                    Location=(0, 0, start_elevation_relative_to_floor),
                ),
                PlacementRelTo=ifc_floor.ObjectPlacement,
            ),
            *args,
            **kwargs,
        )

        return ifc_element

    @staticmethod
    def add_sanitary_terminal(
        ifc_file,
        ifc_floor: IfcBuildingStorey,
        context: IfcRepresentationContext,
        surface_model_path: Path,
        axes: array,
        scales: array,
        translation: array,
        ifc_element_type: Type[Union[IfcStair, IfcSanitaryTerminal]],
        surface_model_matrix: Optional[array] = None,
        *args,
        **kwargs,
    ) -> IfcBuildingElement:
        body = GeometryIfcMapper.transformed_surface_model(
            ifc_file=ifc_file,
            context=context,
            axes=axes,
            scales=scales,
            translation=translation,
            surface_model_path=surface_model_path,
            surface_model_matrix=surface_model_matrix,
        )

        ifc_element = IfcProductGenerator.add_ifc_element(  # type: ignore
            ifc_file=ifc_file,
            ifc_element_type=ifc_element_type,
            Representation=ifc_file.create_entity(
                IfcProductDefinitionShape.__name__, Representations=[body]
            ),
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file, Location=(0, 0, 0)
                ),
                PlacementRelTo=ifc_floor.ObjectPlacement,
            ),
            *args,
            **kwargs,
        )

        return ifc_element

    @staticmethod
    def add_door_window(
        ifc_file,
        context: IfcRepresentationContext,
        polygon: Polygon,
        height: float,
        ifc_wall: IfcWallStandardCase,
        element_type: Type[Union[IfcWindow, IfcDoor]],
        start_elevation_relative_to_floor: float = 0.0,
        *args,
        **kwargs,
    ) -> Tuple[Union[IfcWindow, IfcDoor], IfcOpeningElement]:
        element_body = GeometryIfcMapper.polygon_to_extruded_solid(
            ifc_file=ifc_file,
            context=context,
            polygon=polygon,
            start_altitude=0,
            end_altitude=height,
        )

        ifc_element: Union[IfcDoor, IfcWindow] = IfcProductGenerator.add_ifc_element(  # type: ignore
            ifc_file=ifc_file,
            ifc_element_type=element_type,
            Representation=ifc_file.create_entity(
                IfcProductDefinitionShape.__name__, Representations=[element_body]
            ),
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file,
                    Location=(0, 0, start_elevation_relative_to_floor),
                ),
                PlacementRelTo=ifc_wall.ObjectPlacement,
            ),
            *args,
            **kwargs,
        )

        opening_body = GeometryIfcMapper.polygon_to_extruded_solid(
            ifc_file=ifc_file,
            context=context,
            polygon=polygon,
            start_altitude=0,
            end_altitude=height,
        )

        ifc_opening: IfcOpeningElement = IfcProductGenerator.add_ifc_element(
            ifc_file=ifc_file,
            ifc_element_type=IfcOpeningElement,
            Representation=ifc_file.create_entity(
                IfcProductDefinitionShape.__name__, Representations=[opening_body]
            ),
            ObjectPlacement=ifc_file.create_entity(
                IfcLocalPlacement.__name__,
                RelativePlacement=IfcGeometricRepresentationItemGenerator._add_ifc_axis2_placement3d(
                    ifc_file=ifc_file,
                    Location=(0, 0, start_elevation_relative_to_floor),
                ),
                PlacementRelTo=ifc_wall.ObjectPlacement,
            ),
        )

        IfcRelationshipGenerator.add_opening_to_element(
            ifc_file=ifc_file, element=ifc_wall, opening=ifc_opening
        )

        IfcRelationshipGenerator.add_filling_to_opening(
            ifc_file=ifc_file,
            opening=ifc_opening,
            element=ifc_element,
        )

        if element_type == IfcDoor:
            QuantityIfcMapper.add_door_quantities(
                ifc_file=ifc_file,
                ifc_door=ifc_element,
                polygon=polygon,
                height=height,
            )
        elif element_type == IfcWindow:
            QuantityIfcMapper.add_window_quantities(
                ifc_file=ifc_file,
                ifc_window=ifc_element,
                polygon=polygon,
                height=height,
            )

        return ifc_element, ifc_opening

    # Assignments

    @staticmethod
    def add_buildings_to_site(
        ifc_file: ifcopenshell.file, site: IfcSite, buildings: List[IfcBuilding]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=site,
            children=buildings,
            relationship_type=IfcRelAggregates,
        )

    @staticmethod
    def add_floors_to_building(
        ifc_file, building: IfcBuilding, floors: List[IfcBuildingStorey]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=building,
            children=floors,
            relationship_type=IfcRelAggregates,
        )

    @staticmethod
    def add_units_to_floor(
        ifc_file, floor: IfcBuildingStorey, units: List[IfcSpatialZone]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=floor,
            children=units,
            relationship_type=IfcRelContainedInSpatialStructure,
        )

    @staticmethod
    def add_areas_to_floor(
        ifc_file: ifcopenshell.file, floor: IfcBuildingStorey, spaces: List[IfcSpace]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=floor,
            children=spaces,
            relationship_type=IfcRelAggregates,
        )

    @staticmethod
    def add_elements_to_floor(
        ifc_file, floor: IfcBuildingStorey, elements: List[IfcElement]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=floor,
            children=elements,
            relationship_type=IfcRelContainedInSpatialStructure,
        )

    @staticmethod
    def add_areas_to_unit(
        ifc_file: ifcopenshell.file, unit: IfcSpatialZone, areas: List[IfcSpace]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=unit,
            children=areas,
            relationship_type=IfcRelAggregates,
        )

    @staticmethod
    def add_elements_to_area(
        ifc_file: ifcopenshell.file, area: IfcSpace, elements: List[IfcElement]
    ):
        return IfcRelationshipGenerator.add_children_to_object(
            ifc_file=ifc_file,
            ifc_object=area,
            children=elements,
            relationship_type=IfcRelContainedInSpatialStructure,
        )
