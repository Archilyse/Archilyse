from dataclasses import dataclass
from typing import Optional, Union

from handlers.ifc.exporter.generators import IfcRelationshipGenerator
from handlers.ifc.types import IfcSpace


@dataclass
class Property:
    name: str
    value: Union[str, float, bool]
    description: str


class PropertyIfcMapper:
    @staticmethod
    def add_area_properties(
        ifc_file,
        ifc_space: IfcSpace,
        is_public: bool,
        building_code_type: Optional[str] = None,
    ):
        properties = [
            Property(
                name="PubliclyAccessible",
                value=is_public,
                description="Indication whether this space (in case of e.g., a toilet) is designed to serve as a publicly accessible space, e.g., for a public toilet (TRUE) or not (FALSE).",
            ),
        ]

        if building_code_type:
            # NOTE: Sometimes we don't have a mapping to an SIA416 category
            properties.append(
                Property(
                    name="Reference",
                    value=building_code_type,
                    description="Category of space usage or utilization of the area. It is defined according to the presiding national building code.",
                )
            )

        IfcRelationshipGenerator.add_properties_to_object(
            ifc_file=ifc_file,
            ifc_object=ifc_space,
            property_set_name="Pset_SpaceCommon",
            property_names=[property.name for property in properties],
            property_values=[property.value for property in properties],
            property_descriptions=[property.description for property in properties],
        )
