from .osm_building_handler import OSMBuildingsHandler
from .osm_greenery_handler import OSMForestHandler, OSMParksHandler
from .osm_grounds_handler import OSMGroundsHandler
from .osm_railway_handler import OSMRailwayHandler
from .osm_sea_handler import OSMSeaHandler
from .osm_street_handler import OSMStreetHandler
from .osm_trees_handler import OSMTreesHandler
from .osm_water_handler import (
    OSMLakesHandler,
    OSMRiversHandler,
    OSMRiversPolygonsHandler,
)

__all__ = (
    OSMBuildingsHandler.__name__,
    OSMGroundsHandler.__name__,
    OSMForestHandler.__name__,
    OSMParksHandler.__name__,
    OSMRailwayHandler.__name__,
    OSMRiversHandler.__name__,
    OSMRiversPolygonsHandler.__name__,
    OSMSeaHandler.__name__,
    OSMStreetHandler.__name__,
    OSMTreesHandler.__name__,
    OSMLakesHandler.__name__,
)
