from pathlib import Path
from typing import Dict, Type, Union

import numpy as np

from brooks.types import FeatureType, OpeningType, SeparatorType
from ifc_reader.constants import (
    IFC_BEAM,
    IFC_SLAB,
    IFC_SLAB_STANDARD_CASE,
    IFC_SPACE,
    IFC_STAIR,
    IFC_STOREY,
    IFC_TRANSPORT_ELEMENT,
)

from .types import (
    IfcColumn,
    IfcDoor,
    IfcElement,
    IfcFurniture,
    IfcRailing,
    IfcSanitaryTerminal,
    IfcStair,
    IfcWallStandardCase,
    IfcWindow,
)

ELEMENT_IFC_TYPES: Dict[
    Union[FeatureType, OpeningType, SeparatorType], Type[IfcElement]
] = {
    SeparatorType.WALL: IfcWallStandardCase,
    SeparatorType.COLUMN: IfcColumn,
    SeparatorType.RAILING: IfcRailing,
    OpeningType.WINDOW: IfcWindow,
    OpeningType.DOOR: IfcDoor,
    OpeningType.ENTRANCE_DOOR: IfcDoor,
    FeatureType.KITCHEN: IfcFurniture,
    FeatureType.SINK: IfcSanitaryTerminal,
    FeatureType.TOILET: IfcSanitaryTerminal,
    FeatureType.SHOWER: IfcSanitaryTerminal,
    FeatureType.BATHTUB: IfcSanitaryTerminal,
    FeatureType.STAIRS: IfcStair,
}

# NOTE: Features not in here are being displayed as boxes
SURFACE_MODELS: dict[FeatureType, Path] = {}
SURFACE_MODEL_MATRICES: Dict[FeatureType, np.array] = {}
IFC_ELEMENTS_TO_IGNORE = {
    IFC_SLAB,
    IFC_SLAB_STANDARD_CASE,
    IFC_BEAM,
    IFC_STOREY,
    IFC_SPACE,  # Spaces are retrieved through a different method
}
PIXELS_PER_METER = 100
IFC_ELEMENTS_PLOT_TEXT_WHITELIST = {IFC_TRANSPORT_ELEMENT, IFC_STAIR, IFC_SPACE}
