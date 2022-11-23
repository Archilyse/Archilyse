from dataclasses import dataclass
from typing import Type, Union

import ifcopenshell
from shapely.geometry import Polygon

from handlers.ifc.exporter.generators import IfcRelationshipGenerator
from handlers.ifc.types import (
    IfcDoor,
    IfcQuantityArea,
    IfcQuantityLength,
    IfcQuantityMass,
    IfcQuantityVolume,
    IfcSpace,
    IfcWindow,
)


@dataclass
class Quantity:
    type: Type[
        Union[IfcQuantityArea, IfcQuantityLength, IfcQuantityVolume, IfcQuantityMass]
    ]
    name: str
    value: float
    description: str


class QuantityIfcMapper:
    @staticmethod
    def add_area_quantities(
        ifc_file: ifcopenshell.file,
        ifc_space: IfcSpace,
        polygon: Polygon,
        height: float,
    ):
        # see https://standards.buildingsmart.org/IFC/DEV/IFC4_2/FINAL/HTML/schema/ifcproductextension/qset/qto_spacebasequantities.htm

        quantities = [
            Quantity(
                type=IfcQuantityLength,
                name="Height",
                description="Total height (from base slab without flooring to ceiling without suspended ceiling) for this space (measured from top of slab below to bottom of slab above). To be provided only if the space has a constant height.",
                value=height,
            ),
            Quantity(
                type=IfcQuantityLength,
                name="GrossPerimeter",
                description="Gross perimeter at the floor level of this space. It all sides of the space, including those parts of the perimeter that are created by virtual boundaries and openings (like doors).",
                value=polygon.length,
            ),
            Quantity(
                type=IfcQuantityArea,
                name="NetFloorArea",
                description="Sum of all usable floor areas covered by the space. It excludes the area covered by elements inside the space (columns, inner walls, built-in's etc.), slab openings, or other protruding elements. Varying heights are not taking into account (i.e. no reduction for areas under a minimum headroom).",
                value=polygon.area,
            ),
            Quantity(
                IfcQuantityArea,
                name="GrossWallArea",
                description="Sum of all wall (and other vertically bounding elements, like columns) areas bounded by the space. It includes the area covered by elements inside the wall area (doors, windows, other openings, etc.).",
                value=polygon.length * height,
            ),
            Quantity(
                IfcQuantityVolume,
                name="NetVolume",
                description="Gross volume enclosed by the space, including the volume of construction elements inside the space.",
                value=polygon.area * height,
            ),
        ]

        IfcRelationshipGenerator.add_quantities_to_object(
            ifc_file=ifc_file,
            ifc_entity=ifc_space,
            quantity_types=[quantity.type for quantity in quantities],
            quantity_names=[quantity.name for quantity in quantities],
            quantity_values=[quantity.value for quantity in quantities],
            quantity_descriptions=[quantity.description for quantity in quantities],
            quantity_set_name="Qto_SpaceBaseQuantities",
        )

    @staticmethod
    def add_window_quantities(
        ifc_file: ifcopenshell.file,
        ifc_window: IfcWindow,
        polygon: Polygon,
        height: float,
    ):
        # see https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD1/HTML/schema/ifcsharedbldgelements/qset/qto_windowbasequantities.htm
        from dufresne.polygon import get_sides_as_lines_by_length

        quantities = [
            Quantity(
                type=IfcQuantityLength,
                name="Width",
                description="Total outer width of the window lining. It should only be provided, if it is a rectangular window.",
                value=get_sides_as_lines_by_length(polygon.minimum_rotated_rectangle)[
                    -1
                ].length,
            ),
            Quantity(
                type=IfcQuantityLength,
                name="Height",
                description="Total outer heigth of the window lining. It should only be provided, if it is a rectangular window.",
                value=height,
            ),
            Quantity(
                type=IfcQuantityLength,
                name="Perimeter",
                description="Total perimeter of the outer lining of the window.",
                value=polygon.length,
            ),
            Quantity(
                IfcQuantityArea,
                name="Area",
                description="Total area of the outer lining of the window.",
                value=polygon.area,
            ),
        ]

        IfcRelationshipGenerator.add_quantities_to_object(
            ifc_file=ifc_file,
            ifc_entity=ifc_window,
            quantity_types=[quantity.type for quantity in quantities],
            quantity_names=[quantity.name for quantity in quantities],
            quantity_values=[quantity.value for quantity in quantities],
            quantity_descriptions=[quantity.description for quantity in quantities],
            quantity_set_name="Qto_WindowBaseQuantities",
        )

    @staticmethod
    def add_door_quantities(
        ifc_file: ifcopenshell.file,
        ifc_door: IfcDoor,
        polygon: Polygon,
        height: float,
    ):
        # see https://standards.buildingsmart.org/IFC/DEV/IFC4_2/FINAL/HTML/schema/ifcsharedbldgelements/qset/qto_doorbasequantities.htm
        from dufresne.polygon import get_sides_as_lines_by_length

        quantities = [
            Quantity(
                type=IfcQuantityLength,
                name="Width",
                description="Total outer width of the door lining. It should only be provided, if it is a rectangular door.",
                value=get_sides_as_lines_by_length(polygon.minimum_rotated_rectangle)[
                    -1
                ].length,
            ),
            Quantity(
                type=IfcQuantityLength,
                name="Height",
                description="Total outer heigth of the door lining. It should only be provided, if it is a rectangular door.",
                value=height,
            ),
            Quantity(
                type=IfcQuantityLength,
                name="Perimeter",
                description="Total perimeter of the outer lining of the door.",
                value=polygon.length,
            ),
            Quantity(
                IfcQuantityArea,
                name="Area",
                description="Total area of the outer lining of the door.",
                value=polygon.area,
            ),
        ]

        IfcRelationshipGenerator.add_quantities_to_object(
            ifc_file=ifc_file,
            ifc_entity=ifc_door,
            quantity_types=[quantity.type for quantity in quantities],
            quantity_names=[quantity.name for quantity in quantities],
            quantity_values=[quantity.value for quantity in quantities],
            quantity_descriptions=[quantity.description for quantity in quantities],
            quantity_set_name="Qto_DoorBaseQuantities",
        )
