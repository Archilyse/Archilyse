from pathlib import Path
from typing import Collection

from common_utils.constants import GOOGLE_CLOUD_OSM, REGION
from surroundings.constants import OSM_DIR, OSM_REGIONS_FILENAMES
from surroundings.utils import download_shapefile_if_not_exists
from surroundings.v2.geometry_provider import ShapeFileGeometryProvider


class OSMGeometryProvider(ShapeFileGeometryProvider):
    @property
    def file_templates(self) -> Collection[str]:
        raise NotImplementedError

    @property
    def dataset_crs(self) -> REGION:
        return REGION.LAT_LON

    @property
    def osm_directory(self) -> Path:
        return OSM_REGIONS_FILENAMES[self.region]

    def get_source_filenames(self) -> Collection[Path]:
        local_filenames = []
        for file_template in self.file_templates:
            sub_path = self.osm_directory.joinpath(file_template)
            local_path = OSM_DIR.joinpath(sub_path)
            remote = GOOGLE_CLOUD_OSM.joinpath(sub_path)
            download_shapefile_if_not_exists(remote=remote, local=local_path)
            local_filenames.append(local_path.with_suffix(".shp"))
        return local_filenames
