from dataclasses import dataclass, field
from typing import Union

from shapely.geometry import MultiPolygon, Polygon

from ifc_reader.constants import IFC_SPACE


@dataclass
class Ifc2DEntity:
    geometry: Union[Polygon, MultiPolygon]
    ifc_type: str = field(default="")
    min_height: float = field(default=0.0)
    max_height: float = field(default=0.0)
    properties: dict = field(default_factory=dict)
    quantities: dict = field(default_factory=dict)
    related: dict = field(default_factory=dict)

    @property
    def text(self) -> str:
        return self.ifc_type


@dataclass
class IfcSpaceProcessed:
    area_type: str
    geometry: Polygon
    ifc_type: str = field(default=IFC_SPACE)
    properties: dict = field(default_factory=dict)
    quantities: dict = field(default_factory=dict)
    related: dict = field(default_factory=dict)

    @property
    def text(self) -> str:
        area_size: float = self.properties.get("PSet_BiG_Flaeche")
        return f"{self.area_type}\n{area_size}m²" if area_size else self.area_type


class EditorReadyIfcEntity(Ifc2DEntity):
    geometry: Polygon
