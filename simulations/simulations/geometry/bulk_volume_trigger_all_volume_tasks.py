import tempfile
from pathlib import Path
from typing import List, Tuple

import fiona
from shapely.geometry import Polygon, box, shape
from shapely.ops import unary_union
from tqdm import tqdm

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    GOOGLE_CLOUD_BUCKET,
    SWISSTOPO_MISSING_TILES_BUILDINGS,
)
from handlers import GCloudStorageHandler
from handlers.db import BulkVolumeProgressDBHandler
from surroundings.constants import (
    LK25_MIN_EAST,
    LK25_MIN_NORTH,
    LK25_TILE_HEIGHT,
    LK25_TILE_WIDTH,
    LK25_TILES_PER_ROW,
)
from surroundings.utils import lv95_to_lk25, lv95_to_lk25_subindex
from tasks.bulk_volume_volume_computation import bulk_volume_volume_task


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


def get_lk25_tiles(ch_borders: Polygon) -> List[Tuple[int, int]]:
    lk25_tiles = []
    for row in range(76):
        for col in range(LK25_TILES_PER_ROW * 4):
            tile = box(
                LK25_MIN_EAST + col * LK25_TILE_WIDTH / 4,
                LK25_MIN_NORTH + row * LK25_TILE_HEIGHT / 4,
                LK25_MIN_EAST + (col + 1) * LK25_TILE_WIDTH / 4,
                LK25_MIN_NORTH + (row + 1) * LK25_TILE_HEIGHT / 4,
            )
            if not tile.intersects(ch_borders):
                continue

            lk25_index = int(lv95_to_lk25(tile.centroid.y, tile.centroid.x))
            lk25_subindex_2 = int(
                lv95_to_lk25_subindex(tile.centroid.y, tile.centroid.x)
            )
            lk25_tiles.append((lk25_index, lk25_subindex_2))

    return lk25_tiles


def trigger_tasks(ch_borders: Polygon, resolution: float):
    for lk25_index, lk25_subindex in tqdm(get_lk25_tiles(ch_borders=ch_borders)):
        if lk25_subindex not in SWISSTOPO_MISSING_TILES_BUILDINGS.get(lk25_index, []):
            task_info = BulkVolumeProgressDBHandler.add(
                lk25_index=lk25_index,
                lk25_subindex_2=lk25_subindex,
                state=ADMIN_SIM_STATUS.PENDING.value,
            )
            bulk_volume_volume_task.delay(
                task_id=task_info["id"],
                lk25_index=lk25_index,
                lk25_subindex_2=lk25_subindex,
                resolution=resolution,
            )


if __name__ == "__main__":
    """
    # To visualize the tiles
    from matplotlib import pyplot

    ch_borders = get_ch_borders()
    for lk25_index, lk25_subindex in get_lk25_tiles(ch_borders=ch_borders):
        tile = box(*lk25_to_lv95_bounds(lk25_index, lk25_subindex))
        if lk25_subindex not in SWISSTOPO_MISSING_TILES_BUILDINGS.get(lk25_index, []):
            pyplot.plot(*tile.exterior.xy, color="green")
        else:
            pyplot.fill(*tile.exterior.xy, color="red")

    ch_borders = get_ch_borders()
    pyplot.plot(*ch_borders.exterior.xy)
    pyplot.show()
    """

    trigger_tasks(ch_borders=get_ch_borders(), resolution=0.5)
