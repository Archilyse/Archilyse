from itertools import chain, product
from pathlib import Path
from tempfile import TemporaryDirectory

from shapely.geometry import CAP_STYLE, JOIN_STYLE, Point, box
from tqdm import tqdm

from common_utils.constants import REGION, SIMULATION_VERSION, SurroundingType
from dufresne.polygon.polygon_extrude_triangles import (
    get_triangles_from_extruded_polygon,
)
from handlers import GCloudStorageHandler
from surroundings.raster_window import RasterioRasterWindow
from surroundings.swisstopo import (
    SwissTopoBuildingSurroundingHandler,
    SwisstopoElevationHandler,
)
from surroundings.utils import (
    get_grid_points,
    get_surroundings_bounding_box,
    lv95_to_lk25,
    lv95_to_lk25_subindex,
)
from surroundings.visualization.sourroundings_3d_figure import (
    create_3d_surroundings_from_triangles_per_type,
)

bounding_box_extension = 50
dataset_resolution = 0.5
# NOTE: lower this if you are using a big bounding box as otherwise things get expensive ...
scale_factor = 1.0


def get_volumes_raster_window(bounding_box, sub):
    filenames = []
    with TemporaryDirectory() as tempdir:
        for xy in get_grid_points(bounding_box=bounding_box):
            prefix = "sub" if sub else "super"
            lk25_index = lv95_to_lk25(xy.y, xy.x)
            lk25_subindex_2 = lv95_to_lk25_subindex(xy.y, xy.x)
            relative_filename = f"{prefix}_{lk25_index}_{lk25_subindex_2}.tif"
            local_filename = Path(tempdir).joinpath(relative_filename)
            GCloudStorageHandler().download_file(
                bucket_name="swiss_building_volumes",
                remote_file_path=Path("bulk_volume_volumes_2021").joinpath(
                    relative_filename
                ),
                local_file_name=local_filename,
            )
            filenames.append(local_filename)
        return RasterioRasterWindow(
            *filenames,
            src_bounds=bounding_box.bounds,
            scale_factors=(scale_factor, scale_factor),
        )


def get_volume_triangles(bounding_box, sub):
    elevation_handler = SwisstopoElevationHandler(
        region=REGION.CH,
        bounds=bounding_box.bounds,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )
    window = get_volumes_raster_window(bounding_box, sub)
    for row, col in tqdm(product(range(window.height), range(window.width))):
        px_centroid = Point(*window.get_xy_from_pixel(row, col))
        px_footprint = px_centroid.buffer(
            dataset_resolution / scale_factor / 2,
            join_style=JOIN_STYLE.mitre,
            cap_style=CAP_STYLE.square,
        )
        px_ground_level = elevation_handler.get_elevation(px_centroid)
        volume = window.grid_values[row, col] / scale_factor**2
        if sub:
            ground_level = px_ground_level - volume / px_footprint.area - 0.2
            height = px_ground_level
        else:
            ground_level = px_ground_level
            height = px_ground_level + volume / px_footprint.area
        for triangle in get_triangles_from_extruded_polygon(
            polygon=px_footprint,
            ground_level=ground_level,
            height=height,
        ):
            yield SurroundingType.STREETS, triangle


def get_building_triangles(bounding_box):
    building_handler = SwissTopoBuildingSurroundingHandler(
        location=bounding_box.centroid,
        bounding_box_extension=bounding_box_extension,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )
    yield from building_handler.get_triangles(building_footprints=[])


def show_buildings_and_volumes(x, y, sub):
    bounding_box = get_surroundings_bounding_box(x, y, bounding_box_extension)
    create_3d_surroundings_from_triangles_per_type(
        filename="crosstesting_volumes",
        triangles_per_layout=[],
        triangles_per_surroundings_type=chain(
            get_building_triangles(bounding_box),
            get_volume_triangles(bounding_box, sub),
        ),
    )


def compute_volume(footprint):
    bounding_box = box(*footprint.bounds)
    window = get_volumes_raster_window(bounding_box, False)
    return sum(
        window.grid_values[row, col]
        for row, col in product(range(window.height), range(window.width))
        if Point(*window.get_xy_from_pixel(row, col)).intersects(footprint)
    )


if __name__ == "__main__":
    # Birkenstrasse 27 8134 Adliswil
    show_buildings_and_volumes(2683053.6, 1240797.5, True)
    show_buildings_and_volumes(2683053.6, 1240797.5, False)
