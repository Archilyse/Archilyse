from typing import Any, Dict, List, Literal, Optional, Type, Union

import ifcopenshell

from handlers.ifc.types import (
    IfcBoolean,
    IfcElement,
    IfcElementQuantity,
    IfcInteger,
    IfcMaterial,
    IfcMaterialLayer,
    IfcMaterialLayerSet,
    IfcMaterialLayerSetUsage,
    IfcObject,
    IfcOpeningElement,
    IfcPhysicalSimpleQuantity,
    IfcProperty,
    IfcPropertySet,
    IfcPropertySingleValue,
    IfcQuantityArea,
    IfcQuantityLength,
    IfcQuantityMass,
    IfcQuantityVolume,
    IfcRelAggregates,
    IfcRelAssociatesMaterial,
    IfcRelationship,
    IfcRelContainedInSpatialStructure,
    IfcRelDefinesByProperties,
    IfcRelFillsElement,
    IfcRelVoidsElement,
    IfcSIUnit,
    IfcText,
)

from .ifc_root import IfcRootGenerator


class IfcRelationshipGenerator(IfcRootGenerator):
    @classmethod
    def add_children_to_object(
        cls,
        ifc_file,
        ifc_object: IfcObject,
        children: List[IfcObject],
        relationship_type: Union[
            Type[IfcRelContainedInSpatialStructure], Type[IfcRelAggregates]
        ],
    ) -> IfcRelationship:
        if relationship_type == IfcRelContainedInSpatialStructure:
            return cls._generate_ifc_entity(
                ifc_file=ifc_file,
                ifc_entity_type=relationship_type,
                RelatedElements=children,
                RelatingStructure=ifc_object,
            )
        elif relationship_type == IfcRelAggregates:
            return cls._generate_ifc_entity(
                ifc_file=ifc_file,
                ifc_entity_type=relationship_type,
                RelatingObject=ifc_object,
                RelatedObjects=children,
            )

        raise NotImplementedError(f"Relation type {relationship_type} not implemented.")

    # Properties

    @classmethod
    def add_properties_to_object(
        cls,
        ifc_file,
        ifc_object: IfcObject,
        property_set_name: str,
        property_names: List[str],
        property_values: List[Any],
        property_descriptions: Optional[List[Optional[str]]] = None,
    ) -> IfcPropertySet:
        if property_descriptions is None:
            property_descriptions = [None] * len(property_names)

        ifc_property_set = cls._add_ifc_property_set(
            ifc_file=ifc_file,
            Name=property_set_name,
            HasProperties=[
                cls._add_ifc_property(
                    ifc_file=ifc_file, Name=name, Description=desc, NominalValue=value
                )
                for name, desc, value in zip(
                    property_names, property_descriptions, property_values
                )
            ],
        )

        cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcRelDefinesByProperties,
            RelatedObjects=[ifc_object],
            RelatingPropertyDefinition=ifc_property_set,
        )

        return ifc_property_set

    @classmethod
    def _add_ifc_property_set(
        cls, ifc_file: ifcopenshell.file, Name: str, HasProperties: List[IfcProperty]
    ) -> IfcPropertySet:
        ifc_property_set = cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcPropertySet,
            Name=Name,
            HasProperties=HasProperties,
        )

        return ifc_property_set

    @classmethod
    def _add_ifc_property(
        cls,
        ifc_file,
        Name: str,
        NominalValue: Union[int, str, bool],
        Description: Optional[str] = None,
    ) -> IfcProperty:
        IFC_SCALAR_TYPES = {
            int: IfcInteger,
            str: IfcText,
            bool: IfcBoolean,
        }

        if not isinstance(NominalValue, ifcopenshell.entity_instance):
            if type(NominalValue) not in IFC_SCALAR_TYPES:
                raise NotImplementedError(
                    f"Currently only nominal values of type {IFC_SCALAR_TYPES.keys()} are supported."
                )

            NominalValue = ifc_file.create_entity(
                IFC_SCALAR_TYPES[type(NominalValue)].__name__, NominalValue
            )
        return ifc_file.create_entity(
            IfcPropertySingleValue.__name__,
            Name=Name,
            Description=Description,
            NominalValue=NominalValue,
        )

    # Quantities

    @classmethod
    def add_quantities_to_object(
        cls,
        ifc_file,
        ifc_entity: IfcObject,
        quantity_types: List[
            Type[
                Union[
                    IfcQuantityArea,
                    IfcQuantityLength,
                    IfcQuantityVolume,
                    IfcQuantityMass,
                ]
            ]
        ],
        quantity_names: List[str],
        quantity_values: List[Any],
        quantity_descriptions: Optional[List[Optional[str]]] = None,
        quantity_set_name: Optional[str] = "BaseQuantities",
    ) -> IfcElementQuantity:
        if quantity_descriptions is None:
            quantity_descriptions = [None] * len(quantity_types)

        quantities = [
            ifc_file.create_entity(
                type.__name__,
                **{
                    "Name": name,
                    "Description": desc,
                    "Unit": cls._default_units(ifc_file=ifc_file).get(type),
                    f"{type.__name__.split('IfcQuantity')[1]}Value": value,
                },
            )
            for (type, name, value, desc) in zip(
                quantity_types,
                quantity_names,
                quantity_values,
                quantity_descriptions,
            )
        ]

        ifc_element_quantity = cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcElementQuantity,
            Name=quantity_set_name,
            MethodOfMeasurement="BaseQuantities",
            Quantities=quantities,
        )

        cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcRelDefinesByProperties,
            RelatedObjects=[ifc_entity],
            RelatingPropertyDefinition=ifc_element_quantity,
        )

        return ifc_element_quantity

    @classmethod
    def _default_units(
        cls, ifc_file
    ) -> Dict[Type[IfcPhysicalSimpleQuantity], Optional[IfcSIUnit]]:
        _si_units_in_template: Dict[str, Optional[IfcSIUnit]] = {
            unit.Name: unit for unit in ifc_file.by_type(IfcSIUnit.__name__)
        }

        return {
            IfcQuantityArea: _si_units_in_template.get("SQUARE_METRE"),
            IfcQuantityLength: _si_units_in_template.get("METRE"),
            IfcQuantityVolume: _si_units_in_template.get("CUBIC_METRE"),
        }

    # Materials

    @classmethod
    def add_materials_to_object(
        cls,
        ifc_file,
        ifc_object: IfcObject,
        axis: Literal["AXIS1", "AXIS2", "AXIS3"],
        material_names: List[str],
        layer_thicknesses: List[float],
        direction: Optional[Literal["POSITIVE", "NEGATIVE"]] = "POSITIVE",
    ) -> IfcMaterialLayerSetUsage:
        layer_set = cls._add_material_layer_set(
            ifc_file=ifc_file,
            MaterialLayers=[
                cls._add_ifc_material_layer(
                    ifc_file=ifc_file,
                    material=cls._add_ifc_material(ifc_file=ifc_file, Name=name),
                    LayerThickness=thickness,
                )
                for name, thickness in zip(material_names, layer_thicknesses)
            ],
        )

        layerset_usage = ifc_file.create_entity(
            IfcMaterialLayerSetUsage.__name__,
            ForLayerSet=layer_set,
            LayerSetDirection=axis,
            DirectionSense=direction,
            OffsetFromReferenceLine=0.0,
        )

        cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcRelAssociatesMaterial,
            RelatedObjects=[ifc_object],
            RelatingMaterial=layerset_usage,
        )

        return layerset_usage

    @classmethod
    def _add_material_layer_set(
        cls,
        ifc_file,
        MaterialLayers: List[IfcMaterialLayer],
        LayerSetName: Optional[str] = None,
        Description: Optional[str] = None,
    ) -> IfcMaterialLayerSet:
        return ifc_file.create_entity(
            IfcMaterialLayerSet.__name__,
            MaterialLayers=tuple(MaterialLayers),
            LayerSetName=LayerSetName,
            Description=Description,
        )

    @classmethod
    def _add_ifc_material_layer(
        cls,
        ifc_file,
        material: IfcMaterial,
        LayerThickness: float,
        IsVentilated: Optional[bool] = None,
        Name: Optional[str] = None,
        Description: Optional[str] = None,
        Category: Optional[str] = None,
        Priority: Optional[int] = None,
    ) -> IfcMaterialLayer:
        return ifc_file.create_entity(
            IfcMaterialLayer.__name__,
            Material=material,
            LayerThickness=LayerThickness,
            IsVentilated=IsVentilated,
            Name=Name,
            Description=Description,
            Category=Category,
            Priority=Priority,
        )

    @classmethod
    def _add_ifc_material(
        cls,
        ifc_file,
        Name: str,
        Description: Optional[str] = None,
        Category: Optional[str] = None,
    ) -> IfcMaterial:
        return ifc_file.create_entity(
            IfcMaterial.__name__,
            Name=Name,
            Description=Description,
            Category=Category,
        )

    # Voids

    @classmethod
    def add_opening_to_element(
        cls,
        ifc_file: ifcopenshell.file,
        element: IfcElement,
        opening: IfcOpeningElement,
    ) -> IfcRelVoidsElement:
        return cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcRelVoidsElement,
            RelatingBuildingElement=element,
            RelatedOpeningElement=opening,
        )

    @classmethod
    def add_filling_to_opening(
        cls,
        ifc_file: ifcopenshell.file,
        opening: IfcOpeningElement,
        element: IfcElement,
    ) -> IfcRelFillsElement:
        return cls._generate_ifc_entity(
            ifc_file=ifc_file,
            ifc_entity_type=IfcRelFillsElement,
            RelatingOpeningElement=opening,
            RelatedBuildingElement=element,
        )
