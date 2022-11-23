from typing import Optional, Type

from handlers.ifc.types import (
    IfcElement,
    IfcObjectPlacement,
    IfcProduct,
    IfcProductDefinitionShape,
    IfcSpatialElement,
)

from .ifc_root import IfcRootGenerator


class IfcProductGenerator(IfcRootGenerator):
    @classmethod
    def add_ifc_element(
        cls,
        ifc_file,
        ifc_element_type: Type[IfcElement],
        ObjectPlacement: Optional[IfcObjectPlacement] = None,
        Representation: Optional[IfcProductDefinitionShape] = None,
        Name: Optional[str] = None,
        Description: Optional[str] = None,
        Label: Optional[str] = None,
        Tag: Optional[str] = None,
        *args,
        **kwargs,
    ) -> IfcElement:
        """
        Elements are physically existent objects, although they might be void elements, such as holes.
        """
        return cls._add_ifc_product(  # type: ignore
            ifc_file=ifc_file,
            ifc_product_type=ifc_element_type,
            Name=Name,
            Description=Description,
            Label=Label,
            ObjectPlacement=ObjectPlacement,
            Representation=Representation,
            Tag=Tag,
            *args,
            **kwargs,
        )

    @classmethod
    def add_ifc_spatial_element(
        cls,
        ifc_file,
        ifc_spatial_element_type: Type[IfcSpatialElement],
        ObjectPlacement: Optional[IfcObjectPlacement] = None,
        Representation: Optional[IfcProductDefinitionShape] = None,
        Name: Optional[str] = None,
        Description: Optional[str] = None,
        Label: Optional[str] = None,
        LongName: Optional[str] = None,
        *args,
        **kwargs,
    ) -> IfcSpatialElement:
        """
        A spatial element is the generalization of all spatial elements that might be used
        to define a spatial structure or to define spatial zones.
        """
        return cls._add_ifc_product(  # type: ignore
            ifc_file=ifc_file,
            ifc_product_type=ifc_spatial_element_type,
            Name=Name,
            Description=Description,
            Label=Label,
            ObjectPlacement=ObjectPlacement,
            Representation=Representation,
            LongName=LongName,
            *args,
            **kwargs,
        )

    @classmethod
    def _add_ifc_product(
        cls,
        ifc_file,
        ifc_product_type: Type[IfcProduct],
        ObjectPlacement: Optional[IfcObjectPlacement] = None,
        Representation: Optional[IfcProductDefinitionShape] = None,
        Name: Optional[str] = None,
        Description: Optional[str] = None,
        Label: Optional[str] = None,
        *args,
        **kwargs,
    ) -> IfcProduct:
        if not Name:
            Name = ifc_product_type.__name__

        if not Description:
            Description = ifc_product_type.__name__

        return cls._generate_ifc_entity(  # type: ignore
            ifc_file=ifc_file,
            ifc_entity_type=ifc_product_type,
            Name=Name,
            Description=Description,
            Label=Label,
            ObjectPlacement=ObjectPlacement,
            Representation=Representation,
            *args,
            **kwargs,
        )
