from shapely.geometry import box

from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from handlers.simulations.potential_tile_exporter import PotentialTileExporter
from tasks.potential_view_tasks import generate_potential_tile

zurich_shape = project_geometry(
    box(2671861.7, 1226594.9, 2710417.1, 1271640.2),
    crs_from=REGION.CH,
    crs_to=REGION.LAT_LON,
)

for tile_bounds in PotentialTileExporter.get_tile_bounds(polygon=zurich_shape):
    generate_potential_tile.delay(tile_bounds=tile_bounds, dump_shape=zurich_shape.wkt)
