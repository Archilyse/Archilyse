from dataclasses import dataclass, field
from typing import Optional

from shapely.geometry import Polygon

from handlers.editor_v2.schema import ReactPlannerDoorSweepingPoints, ReactPlannerName


@dataclass
class EntityProperties:
    door_subtype: Optional[ReactPlannerName] = field(default=None)
    door_sweeping_points: Optional[ReactPlannerDoorSweepingPoints] = field(default=None)


@dataclass
class EditorReadyEntity:
    geometry: Polygon
    properties: EntityProperties = field(default_factory=EntityProperties)
