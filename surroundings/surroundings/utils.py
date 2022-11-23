import logging
from math import ceil, floor
from pathlib import Path
from typing import Dict, Iterator, List, NamedTuple, Tuple, Union

from contexttimer import timer
from numpy import hstack, vstack
from numpy.core._multiarray_umath import arange
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box
from shapely.ops import transform

from brooks.util.geometry_ops import get_polygons
from common_utils.constants import (
    GOOGLE_CLOUD_BUCKET,
    GOOGLE_CLOUD_SWISSTOPO,
    SWISSTOPO_DIR,
    SWISSTOPO_MISSING_TILES_BUILDINGS,
    SWISSTOPO_REQUIRED_FILES_ALTI,
    SWISSTOPO_REQUIRED_FILES_BUILDINGS,
    SWISSTOPO_REQUIRED_FILES_MOUNTAINS,
    SWISSTOPO_REQUIRED_FILES_TLM,
    SurroundingType,
)
from common_utils.exceptions import GCSLinkEmptyException, OutOfGridException
from common_utils.logger import logger

from .constants import (
    BOUNDING_BOX_EXTENSION,
    LK25_MIN_EAST,
    LK25_MIN_NORTH,
    LK25_SOUTH_WEST_INDEX,
    LK25_TILE_HEIGHT,
    LK25_TILE_WIDTH,
    LK25_TILES_PER_ROW,
)

SHAPEFILE_SUFFIX = (".cpg", ".dbf", ".prj", ".shp", ".shx")


# Types
PointTuple = Tuple[float, float, float]
Triangle = Tuple[
    PointTuple,
    PointTuple,
    PointTuple,
]
PixelPosition = Tuple[int, int]
SurrTrianglesType = Tuple[SurroundingType, List[PointTuple]]
TriangleOffsets = TriangleIndexes = Tuple[PixelPosition, PixelPosition, PixelPosition]
Bounds = Tuple[float, float, float, float]


TRIANGLE_OFFSETS: Tuple[TriangleOffsets, TriangleOffsets] = (
    ((0, 0), (0, 1), (1, 0)),
    ((0, 1), (1, 0), (1, 1)),
)


class FilteredPolygonEntity(NamedTuple):
    geometry: Union[Polygon, MultiPolygon, LineString, Point]
    entity: Dict

    @property
    def entity_class(self):
        return self.osm_properties.get("fclass")

    @property
    def osm_properties(self):
        return self.entity["properties"]


@timer(logger=logger, level=logging.DEBUG)
def download_swisstopo_if_not_exists(bounding_box, templates=None) -> List[Path]:
    from handlers import GCloudStorageHandler

    relative_file_paths_gcp = get_required_swisstopo_filepaths(
        bounding_box=bounding_box, templates=templates
    )
    destination_file_paths_local = [
        SWISSTOPO_DIR.joinpath(rel_path) for rel_path in relative_file_paths_gcp
    ]
    files_downloaded = []

    for relative_file_path_gcp, destination_file_path_local in zip(
        relative_file_paths_gcp, destination_file_paths_local
    ):
        try:
            GCloudStorageHandler().download_file(
                bucket_name=GOOGLE_CLOUD_BUCKET,
                remote_file_path=GOOGLE_CLOUD_SWISSTOPO.joinpath(
                    relative_file_path_gcp
                ),
                local_file_name=destination_file_path_local,
            )
            files_downloaded.append(destination_file_path_local)
        except GCSLinkEmptyException:
            continue

    return files_downloaded


@timer(logger=logger, level=logging.DEBUG)
def download_shapefile_if_not_exists(remote: Path, local: Path):
    from handlers import GCloudStorageHandler

    local.parent.mkdir(parents=True, exist_ok=True)

    for pattern in SHAPEFILE_SUFFIX:
        GCloudStorageHandler().download_file(
            bucket_name=GOOGLE_CLOUD_BUCKET,
            remote_file_path=remote.with_suffix(pattern),
            local_file_name=local.with_suffix(pattern),
        )


def lk25_to_lv95(index):
    # derived from this map:
    # https://www.swisstopo.admin.ch/content/swisstopo-internet/en/home/products/
    # maps/national/lk25/_jcr_content/contentPar/tabs_copy_copy_copy/items/
    # dokumente_publikatio/tabPar/downloadlist_copy_co/downloadItems/
    # 273_1466760668856.download/blueb25.pdf
    north = LK25_MIN_NORTH + LK25_TILE_HEIGHT * ceil(
        (LK25_SOUTH_WEST_INDEX - index) / LK25_TILES_PER_ROW
    )
    east = LK25_MIN_EAST + LK25_TILE_WIDTH * (
        (LK25_TILES_PER_ROW - (LK25_SOUTH_WEST_INDEX - index)) % LK25_TILES_PER_ROW
    )

    return north, east


def lv95_to_lk25(north, east):
    delta_north = (
        floor((north - LK25_MIN_NORTH) / LK25_TILE_HEIGHT) * LK25_TILES_PER_ROW
    )
    delta_west = floor((east - LK25_MIN_EAST) / LK25_TILE_WIDTH)

    return LK25_SOUTH_WEST_INDEX - delta_north + delta_west


def lv95_to_lk25_subindex(north, east, depth=2, eps=1e-6):
    # Reversed from shp files, no documentation existing afaik
    # Creates a matrix in the form of a quad tree hierarchy with
    # recursion depth `depth`, e.g. for depth 2:
    #  [[11 12 21 22]
    #  [13 14 23 24]
    #  [31 32 41 42]
    #  [33 34 43 44]]
    index_matrix = arange(1, 5).reshape((2, 2))
    for current_depth in range(1, depth):
        m1, m2, m3, m4 = [index_matrix + i * 10**current_depth for i in range(1, 5)]
        index_matrix = vstack([hstack([m1, m2]), hstack([m3, m4])])

    # compute lk25 parent tile
    lk25_index = lv95_to_lk25(north=north, east=east)
    lk25_north, lk25_east = lk25_to_lv95(lk25_index)

    # compute the position relative to the south-western border
    # of the parent tile
    delta_north = north - lk25_north + eps
    delta_east = east - lk25_east + eps

    # retrieve index name
    row = floor(2**depth * (1 - delta_north / LK25_TILE_HEIGHT))
    col = floor(2**depth * (delta_east / LK25_TILE_WIDTH))

    if not (0 <= row < index_matrix.shape[0] and 0 <= col < index_matrix.shape[1]):
        raise OutOfGridException(f"{east} {north} is outside of the lk25 grid.")
    return index_matrix[row][col]


def lk25_to_lv95_bounds(lk25_index, lk25_subindex):
    # Reversed from shp files, no documentation existing afaik
    # Creates a matrix in the form of a quad tree hierarchy with
    # recursion depth `depth`, e.g. for depth 2:
    #  [[11 12 21 22]
    #  [13 14 23 24]
    #  [31 32 41 42]
    #  [33 34 43 44]]
    depth = 2
    index_matrix = arange(1, 5).reshape((2, 2))
    for current_depth in range(1, depth):
        m1, m2, m3, m4 = [index_matrix + i * 10**current_depth for i in range(1, 5)]
        index_matrix = vstack([hstack([m1, m2]), hstack([m3, m4])])

    def get_row_col():
        for row, sub_indexes in enumerate(index_matrix):
            for col, sub_index in enumerate(sub_indexes):
                if lk25_subindex == sub_index:
                    return row, col

    row, col = get_row_col()

    delta_north = (1 - (row + 1) / (2**depth)) * LK25_TILE_HEIGHT
    delta_east = col * LK25_TILE_WIDTH / (2**depth)

    # compute lk25 parent tile
    lk25_north, lk25_east = lk25_to_lv95(lk25_index)

    x = delta_east + lk25_east
    y = delta_north + lk25_north
    return x, y, x + LK25_TILE_WIDTH / 4, y + LK25_TILE_HEIGHT / 4


def get_ignored_swisstopo_filepaths():
    ignored_files = set()

    for ignored_path_template in SWISSTOPO_REQUIRED_FILES_BUILDINGS:
        for lk25, lk25_subindexes_2 in SWISSTOPO_MISSING_TILES_BUILDINGS.items():
            for lk25_subindex_2 in lk25_subindexes_2:
                ignored_path = str(ignored_path_template).format(
                    lk25=lk25, lk25_subindex_2=lk25_subindex_2
                )
                ignored_files.add(ignored_path)

    return ignored_files


def get_grid_points(bounding_box: Polygon, interval: float = 500) -> Iterator[Point]:
    xmin, ymin, xmax, ymax = bounding_box.bounds
    for x in arange(xmin, xmax + interval, interval):
        for y in arange(ymin, ymax + interval, interval):
            yield Point(x, y)


def get_required_swisstopo_filepaths(bounding_box, templates=None):
    if templates is None:
        templates = (
            SWISSTOPO_REQUIRED_FILES_ALTI
            + SWISSTOPO_REQUIRED_FILES_TLM
            + SWISSTOPO_REQUIRED_FILES_BUILDINGS
            + SWISSTOPO_REQUIRED_FILES_MOUNTAINS
        )

    required_files = set()
    for point in get_grid_points(bounding_box=bounding_box):
        e = point.x
        n = point.y
        lk25 = lv95_to_lk25(n, e)
        try:
            lk25_subindex_1 = lv95_to_lk25_subindex(north=n, east=e, depth=1)
            lk25_subindex_2 = lv95_to_lk25_subindex(north=n, east=e, depth=2)
        except OutOfGridException:
            continue

        for required_path_template in templates:
            required_path = str(required_path_template).format(
                lk25=lk25,
                lk25_subindex_1=lk25_subindex_1,
                lk25_subindex_2=lk25_subindex_2,
            )
            required_files.add(required_path)

    return required_files - get_ignored_swisstopo_filepaths()


def get_absolute_building_filepaths(bounding_box: Polygon) -> List[Path]:
    relative_file_paths = get_required_swisstopo_filepaths(
        bounding_box, templates=SWISSTOPO_REQUIRED_FILES_BUILDINGS
    )
    return [
        SWISSTOPO_DIR.joinpath(rel)
        for rel in relative_file_paths
        if rel.endswith(".shp")
    ]


def get_surroundings_bounding_box(
    x, y, bounding_box_extension: float = BOUNDING_BOX_EXTENSION
):
    bounding_box: Polygon = box(
        x - bounding_box_extension,
        y - bounding_box_extension,
        x + bounding_box_extension,
        y + bounding_box_extension,
    )

    return bounding_box


def get_interpolated_height(x: float, y: float, from_triangle: Triangle) -> float:
    """Returns the z coordinate for the given x, y, z using the equation of a plane."""
    (x1, y1, z1), (x2, y2, z2), (x3, y3, z3) = from_triangle
    return (
        z1
        + (
            ((x2 - x1) * (z3 - z1) - (x3 - x1) * (z2 - z1))
            / ((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
        )
        * (y - y1)
        - (
            ((y2 - y1) * (z3 - z1) - (y3 - y1) * (z2 - z1))
            / ((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
        )
        * (x - x1)
    )


def triangle_intersection(
    footprint_2d: Union[Polygon, MultiPolygon], triangle_3d: Polygon
):
    """
    Args:
        footprint_2d: Can be a 2D or 3D polygon but in any case the z coordinate is not considered.
        triangle_3d: 3D polygon with 3 vertices.

    Returns:
        The intersecting part(s) of the 3D triangle as an iterator of 3D plane polygons.
    """
    if triangle_3d.within(footprint_2d):
        yield triangle_3d
    elif triangle_3d.intersects(footprint_2d):
        from_triangle = triangle_3d.exterior.coords[:3]

        def apply_elevation(x, y, _):
            return (
                x,
                y,
                get_interpolated_height(x=x, y=y, from_triangle=from_triangle),
            )

        yield from get_polygons(
            transform(apply_elevation, triangle_3d.intersection(footprint_2d))
        )
