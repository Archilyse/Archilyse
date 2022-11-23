from shapely.geometry import Point, box
from shapely.ops import unary_union
from shapely.wkt import loads
from tqdm import tqdm

from brooks.util.projections import project_geometry
from brooks.visualization.debug.visualisation import draw
from common_utils.constants import REGION, SIMULATION_VERSION
from common_utils.logger import logger
from handlers.db import PotentialSimulationDBHandler
from surroundings.swisstopo import SwissTopoBuildingSurroundingHandler
from tasks.potential_view_tasks import get_building_footprints_to_simulate

ZURICH = {
    "min_lon": 8.488388181714749,
    "min_lat": 47.350107191888505,
    "max_lon": 8.58034475941714,
    "max_lat": 47.39141758169881,
}
ZURICH_BOUNDING_BOX = project_geometry(
    geometry=box(
        ZURICH["min_lon"],
        ZURICH["min_lat"],
        ZURICH["max_lon"],
        ZURICH["max_lat"],
    ),
    crs_from=REGION.LAT_LON,
    crs_to=REGION.CH,
)


def get_st_buildings():
    zurich_bounds = ZURICH_BOUNDING_BOX.bounds
    bounding_box_extension = (
        max(zurich_bounds[2] - zurich_bounds[0], zurich_bounds[3] - zurich_bounds[1])
        / 2
    )
    projected_simulation_location = project_geometry(
        geometry=Point(
            ZURICH["min_lon"] + (ZURICH["max_lon"] - ZURICH["min_lon"]),
            ZURICH["min_lat"] + (ZURICH["max_lat"] - ZURICH["min_lat"]),
        ),
        crs_from=REGION.LAT_LON,
        crs_to=REGION.CH,
    )

    handler = SwissTopoBuildingSurroundingHandler(
        location=projected_simulation_location,
        simulation_version=SIMULATION_VERSION.PH_2022_H1,
        bounding_box_extension=bounding_box_extension + 200,
    )

    buildings = list(handler.get_buildings())

    buildings_of_interest = get_building_footprints_to_simulate(
        location=projected_simulation_location,
        bounding_box_extension=bounding_box_extension,
        buildings=buildings,
    )
    return buildings_of_interest


sims = PotentialSimulationDBHandler.get_simulations_list(bounding_box=ZURICH)

computed_buildings = unary_union(
    [
        project_geometry(
            loads(sim["building_footprint"]),
            crs_from=REGION.LAT_LON,
            crs_to=REGION.CH,
        )
        for sim in tqdm(sims)
    ]
)
real_buildings = unary_union(list(get_st_buildings()))

real_buildings = unary_union(
    [b for b in real_buildings.geoms if b.centroid.within(ZURICH_BOUNDING_BOX)]
)

to_plot = real_buildings - computed_buildings
logger.info(
    f"Total area difference: {to_plot.area}. Biggest area: {max([x.area for x in to_plot.geoms])}"
)
draw(to_plot)
