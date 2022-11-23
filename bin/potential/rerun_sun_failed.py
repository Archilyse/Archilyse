from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_POTENTIAL_DATASET,
    REGION,
    SIMULATION_TYPE,
)
from handlers import GCloudStorageHandler
from handlers.db import PotentialSimulationDBHandler
from handlers.simulations.potential_tile_exporter import PotentialTileExporter
from tasks.potential_view_tasks import get_potential_quavis_simulation_chain

zurich_shape = project_geometry(
    box(2671861.7, 1226594.9, 2710417.1, 1271640.2),
    crs_from=REGION.CH,
    crs_to=REGION.LAT_LON,
)
right_keys = {
    "observation_points",
    "sun-2018-03-21 08:00:00+01:00",
    "sun-2018-03-21 10:00:00+01:00",
    "sun-2018-03-21 12:00:00+01:00",
    "sun-2018-03-21 14:00:00+01:00",
    "sun-2018-03-21 16:00:00+01:00",
    "sun-2018-03-21 18:00:00+01:00",
    "sun-2018-06-21 06:00:00+02:00",
    "sun-2018-06-21 08:00:00+02:00",
    "sun-2018-06-21 10:00:00+02:00",
    "sun-2018-06-21 12:00:00+02:00",
    "sun-2018-06-21 14:00:00+02:00",
    "sun-2018-06-21 16:00:00+02:00",
    "sun-2018-06-21 18:00:00+02:00",
    "sun-2018-06-21 20:00:00+02:00",
    "sun-2018-12-21 10:00:00+01:00",
    "sun-2018-12-21 12:00:00+01:00",
    "sun-2018-12-21 14:00:00+01:00",
    "sun-2018-12-21 16:00:00+01:00",
}

storage_handler = GCloudStorageHandler()

for tile_bounds in PotentialTileExporter.get_tile_bounds(polygon=zurich_shape):
    left, bottom = tile_bounds[:2]
    filename = PotentialTileExporter._get_dump_filename(
        simulation_type=SIMULATION_TYPE.SUN, bottom=bottom, left=left
    )
    if not storage_handler.check_prefix_exists(
        bucket_name=GOOGLE_CLOUD_BUCKET,
        prefix=GOOGLE_CLOUD_POTENTIAL_DATASET.joinpath(filename)
        .with_suffix(".zip")
        .as_posix(),
    ):
        sims = PotentialSimulationDBHandler.get_simulations_list(
            {
                "min_lon": tile_bounds[0],
                "min_lat": tile_bounds[1],
                "max_lon": tile_bounds[2],
                "max_lat": tile_bounds[3],
            },
            simulation_type=SIMULATION_TYPE.SUN,
            limit_query=False,
        )
        for sim in sims:
            keys = set(sim["result"].keys())
            if keys != right_keys:
                PotentialSimulationDBHandler.update(
                    item_pks={"id": sim["id"]}, new_values={"status": "PENDING"}
                )
                get_potential_quavis_simulation_chain(simulation_id=sim["id"]).delay()
