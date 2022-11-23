from .buildings import OSMBuildingHandler
from .forests import OSMForestHandler
from .parks import OSMParksHandler
from .railways import OSMRailwayHandler
from .rivers import OSMRiverHandler
from .sea import OSMSeaHandler
from .streets import OSMStreetHandler
from .trees import OSMTreeHandler
from .water import OSMWaterHandler

__all__ = [
    OSMParksHandler.__name__,
    OSMRailwayHandler.__name__,
    OSMRiverHandler.__name__,
    OSMSeaHandler.__name__,
    OSMStreetHandler.__name__,
    OSMWaterHandler.__name__,
    OSMForestHandler.__name__,
    OSMTreeHandler.__name__,
    OSMBuildingHandler.__name__,
]
