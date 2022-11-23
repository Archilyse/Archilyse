from pathlib import Path

import fiona
from tqdm import tqdm

OSM_FILES_FOLDER = Path("")  # ****** FILL AS NEEDED!!! ************
MERGED_FOLDER = OSM_FILES_FOLDER.joinpath("germany-latest-free")
MERGED_FOLDER.mkdir(parents=True, exist_ok=True)


file_list = [
    "gis_osm_water_a_free_1.shp",
    "gis_osm_railways_free_1.shp",
    "gis_osm_waterways_free_1.shp",
    "gis_osm_natural_free_1.shp",
    "gis_osm_buildings_a_free_1.shp",
    "gis_osm_natural_a_free_1.shp",
    "gis_osm_roads_free_1.shp",
    "gis_osm_landuse_a_free_1.shp",
]

folders = [f for f in OSM_FILES_FOLDER.glob(pattern="*.shp")]

for shp_file in tqdm(file_list):
    meta = fiona.open(folders[0].joinpath(shp_file).as_posix()).meta
    with fiona.open(MERGED_FOLDER.joinpath(shp_file).as_posix(), "w", **meta) as output:
        for folder in tqdm(folders):
            for features in fiona.open(folder.joinpath(shp_file).as_posix()):
                output.write(features)
