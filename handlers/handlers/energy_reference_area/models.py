from dataclasses import dataclass
from typing import Optional


@dataclass
class EnergyAreasStatsPerFloor:
    total_era_area: float
    total_non_era_area: float
    era_wall_area: float
    era_areas: dict[str, list[float]]
    non_era_areas: dict[str, list[float]]
    floor_height: float
    floor_number: Optional[int] = None
    building_client_id: Optional[str] = None
    total_era_volume: Optional[float] = None


@dataclass
class DetailedAreaInformation:
    area_type: str
    area_size: float
    is_era: str
    floor_number: Optional[int] = None
    building_client_id: Optional[str] = None
