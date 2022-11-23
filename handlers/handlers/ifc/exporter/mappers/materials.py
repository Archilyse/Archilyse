from typing import Literal

import ifcopenshell

from handlers.ifc.exporter.generators import IfcRelationshipGenerator
from handlers.ifc.types import IfcElement


class MaterialIfcMapper:
    @staticmethod
    def add_default_materials(
        ifc_file: ifcopenshell.file,
        element: IfcElement,
        axis: Literal["AXIS2", "AXIS3"] = "AXIS2",
    ):
        IfcRelationshipGenerator.add_materials_to_object(
            ifc_file=ifc_file,
            ifc_object=element,
            axis=axis,
            material_names=[f"Default {element.__dict__['type']} Material"],
            layer_thicknesses=[0],
        )
