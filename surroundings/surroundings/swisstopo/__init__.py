from .building_surrounding_handler import SwissTopoBuildingSurroundingHandler
from .elevation_handler import SwisstopoElevationHandler
from .extra_lakes_surrounding_handler import SwissTopoExtraLakesSurroundingHandler
from .forest_surrounding_handler import SwissTopoForestSurroundingHandler
from .ground_surrounding_handler import (
    SwissTopoGroundSurroundingHandler,
    SwissTopoMountainSurroundingHandler,
)
from .lake_surrounding_handler import SwissTopoLakeSurroundingHandler
from .noise_surrounding_handler import SwissTopoNoiseLevelHandler
from .parks_surrounding_handler import SwissTopoParksSurroundingHandler
from .railroad_surrounding_handler import SwissTopoRailroadSurroundingHandler
from .river_surrounding_handler import SwissTopoRiverSurroundingHandler
from .street_surrounding_handler import SwissTopoStreetSurroundingHandler
from .tree_surrounding_handler import SwissTopoTreeSurroundingHandler

__all__ = (
    SwissTopoBuildingSurroundingHandler.__name__,
    SwissTopoGroundSurroundingHandler.__name__,
    SwissTopoMountainSurroundingHandler.__name__,
    SwissTopoLakeSurroundingHandler.__name__,
    SwissTopoExtraLakesSurroundingHandler.__name__,
    SwissTopoParksSurroundingHandler.__name__,
    SwissTopoRailroadSurroundingHandler.__name__,
    SwissTopoRiverSurroundingHandler.__name__,
    SwissTopoStreetSurroundingHandler.__name__,
    SwissTopoTreeSurroundingHandler.__name__,
    SwisstopoElevationHandler.__name__,
    SwissTopoForestSurroundingHandler.__name__,
    SwissTopoNoiseLevelHandler.__name__,
)
