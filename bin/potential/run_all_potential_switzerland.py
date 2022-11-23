import os
import tempfile
from distutils.util import strtobool
from pathlib import Path

import click
import fiona
import numpy as np
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union
from tqdm import tqdm

from brooks.util.projections import project_geometry
from common_utils.constants import GOOGLE_CLOUD_BUCKET, REGION
from common_utils.logger import logger
from handlers import GCloudStorageHandler
from handlers.db.potential_progress_handler import PotentialCHProgressDBHandler
from tasks.potential_view_tasks import potential_simulate_area
from workers_config.celery_config import INCREASED_TASK_PRIORITY


def is_staging() -> bool:
    # Basic check but prevents running this script locally without updating the makefile
    if int(os.environ["PGBOUNCER_PORT"]) == 5432:
        return True
    return False


def is_eager() -> bool:
    return bool(strtobool(os.environ["CELERY_EAGER"]))


places_of_interest = {
    "geneve": box(2487895.0, 1107563.8, 2513634.9, 1143623.5),
    "bern": box(2585784.5, 1193421.2, 2607328.2, 1208314.9),
    "basel": box(2605226.3, 1260826.5, 2622974.3, 1274462.5),
}

places_already_computed = {
    "zurich": box(2671861.7, 1226594.9, 2710417.1, 1271640.2),
}


def get_ch_borders() -> Polygon:
    gcloud_handler = GCloudStorageHandler()
    filename = Path("swissBOUNDARIES3D_1_3_TLM_LANDESGEBIET")
    with tempfile.TemporaryDirectory() as tempdir:
        for suffix in (".shp", ".prj", ".shx", ".sbn", ".sbx"):
            remote_file_path = (
                Path("swisstopo/swissBOUNDARIES3D")
                .joinpath(filename)
                .with_suffix(suffix)
            )
            local_file_path = Path(tempdir).joinpath(filename).with_suffix(suffix)
            gcloud_handler.download_file(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                remote_file_path=remote_file_path,
                local_file_name=local_file_path,
            )
        with fiona.open(Path(tempdir).joinpath(filename).with_suffix(".shp")) as file:
            borders = unary_union([shape(entity["geometry"]) for entity in file])

    return borders


@click.command()
@click.option("--num_tiles", prompt=True, type=click.INT, required=True)
def trigger_tasks(num_tiles: int):
    if is_staging() or is_eager():
        raise Exception(
            "Payaso! Should not run in staging environment or in Celery Eager mode"
        )

    already_computed_tiles = {
        (t["x"], t["y"]) for t in PotentialCHProgressDBHandler().find()
    }

    resolution = 1000
    ch_borders = get_ch_borders()
    min_x, min_y, max_x, max_y = ch_borders.bounds
    for x_idx, x in tqdm(enumerate(np.arange(min_x, max_x, resolution)), total=349):
        if num_tiles == 0:
            break
        for y_idx, y in tqdm(
            enumerate(np.arange(min_y, max_y, resolution)), leave=False, total=221
        ):

            if (x_idx, y_idx) in already_computed_tiles:
                continue

            tile = box(x, y, x + resolution, y + resolution)
            if not ch_borders.intersects(tile):
                continue

            for place in places_of_interest.values():
                if place.intersects(tile):
                    break
            else:
                continue

            centroid_lat_lon = project_geometry(
                tile.centroid, crs_from=REGION.CH, crs_to=REGION.LAT_LON
            )
            potential_simulate_area.si(
                lat=centroid_lat_lon.y,
                lon=centroid_lat_lon.x,
                bounding_box_extension=resolution / 2,
            ).apply_async(
                priority=INCREASED_TASK_PRIORITY + 2,
            )

            PotentialCHProgressDBHandler.add(x=x_idx, y=y_idx)
            logger.info(f"Added tile {x_idx}, {y_idx}")

            num_tiles -= 1
            if num_tiles == 0:
                break


if __name__ == "__main__":
    trigger_tasks()
