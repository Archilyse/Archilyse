from typing import Dict, List, Optional, Tuple, Union

from brooks.constants import SuperTypes
from handlers.editor_v2.schema import ReactPlannerName
from ifc_reader.constants import (
    IFC_COLUMN,
    IFC_CURTAIN_WALL,
    IFC_DISTRIBUTION_FLOW_ELEMENT,
    IFC_DOOR,
    IFC_FLOW_CONTROLLER,
    IFC_FURNISHING_ELEMENT,
    IFC_FURNITURE,
    IFC_RAILING,
    IFC_SANITARY_ELEMENT,
    IFC_STAIR,
    IFC_WALL,
    IFC_WALL_STANDARD_CASE,
    IFC_WINDOW,
)
from ifc_reader.types import Ifc2DEntity


def get_ifc_entity_supertype_and_planner_type(
    ifc_entity: Ifc2DEntity,
) -> Tuple[Optional[SuperTypes], Optional[ReactPlannerName]]:
    for super_type, sub_values in IFC_TO_REACT_PLANNER_MAPPING.items():
        if ifc_entity.ifc_type in sub_values:
            if (
                super_type != SuperTypes.ITEMS
                or ifc_entity.ifc_type in IFC_ITEMS_1_TO_1_MAPPING
            ):
                return super_type, sub_values[ifc_entity.ifc_type][0]
            else:
                if planner_name := get_ifc_item_planner_type_based_on_keywords(
                    ifc_entity=ifc_entity
                ):
                    return super_type, planner_name
    return None, None


def get_ifc_item_planner_type_based_on_keywords(
    ifc_entity: Ifc2DEntity,
) -> Union[ReactPlannerName, None]:
    for value in ifc_entity.properties.values():
        for (
            keyword,
            planner_name,
        ) in IFC_TO_REACT_PLANNER_FEATURE_KEYWORDS.items():
            value = str(value).lower()
            for word in value.split():
                if word and word in keyword.lower():
                    return planner_name
    return None


IFC_TO_REACT_PLANNER_MAPPING: Dict[SuperTypes, Dict[str, List[ReactPlannerName]]] = {
    SuperTypes.SEPARATORS: {
        IFC_WALL: [ReactPlannerName.WALL],
        IFC_WALL_STANDARD_CASE: [ReactPlannerName.WALL],
        IFC_CURTAIN_WALL: [ReactPlannerName.WALL],
        IFC_COLUMN: [ReactPlannerName.COLUMN],
        IFC_RAILING: [ReactPlannerName.RAILING],
    },
    SuperTypes.OPENINGS: {
        IFC_WINDOW: [ReactPlannerName.WINDOW],
        IFC_DOOR: [ReactPlannerName.DOOR],
    },
    SuperTypes.ITEMS: {
        IFC_STAIR: [ReactPlannerName.STAIRS],
        IFC_FURNISHING_ELEMENT: [ReactPlannerName.KITCHEN],
        IFC_FURNITURE: [ReactPlannerName.KITCHEN],
        IFC_SANITARY_ELEMENT: [
            ReactPlannerName.BATHTUB,
            ReactPlannerName.SHOWER,
            ReactPlannerName.SINK,
            ReactPlannerName.TOILET,
        ],
        IFC_DISTRIBUTION_FLOW_ELEMENT: [
            ReactPlannerName.BATHTUB,
            ReactPlannerName.SHOWER,
            ReactPlannerName.SINK,
            ReactPlannerName.TOILET,
        ],
        IFC_FLOW_CONTROLLER: [
            ReactPlannerName.BATHTUB,
            ReactPlannerName.SHOWER,
            ReactPlannerName.SINK,
            ReactPlannerName.TOILET,
        ],
    },
}
IFC_ITEMS_1_TO_1_MAPPING = {
    ifc_type
    for ifc_type, planner_mappings in IFC_TO_REACT_PLANNER_MAPPING[
        SuperTypes.ITEMS
    ].items()
    if len(planner_mappings) == 1
}
IFC_TO_REACT_PLANNER_FEATURE_KEYWORDS = {
    "bathtub": ReactPlannerName.BATHTUB,
    "bañera": ReactPlannerName.BATHTUB,
    "plato": ReactPlannerName.SHOWER,
    "ducha": ReactPlannerName.SHOWER,
    "shower": ReactPlannerName.SHOWER,
    "lavabo": ReactPlannerName.SINK,
    "sink": ReactPlannerName.SINK,
    "basin": ReactPlannerName.SINK,
    "toilet": ReactPlannerName.TOILET,
    "wc": ReactPlannerName.TOILET,
    "urinal": ReactPlannerName.TOILET,
    "cocina": ReactPlannerName.KITCHEN,
    "kitchen": ReactPlannerName.KITCHEN,
}
