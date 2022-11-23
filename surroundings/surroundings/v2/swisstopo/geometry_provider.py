from pathlib import Path
from typing import Collection

from brooks.util.projections import project_geometry
from common_utils.constants import REGION
from surroundings.utils import download_swisstopo_if_not_exists
from surroundings.v2.geometry_provider import ShapeFileGeometryProvider


class SwissTopoShapeFileGeometryProvider(ShapeFileGeometryProvider):
    @property
    def dataset_crs(self) -> REGION:
        return REGION.CH

    @property
    def file_templates(self) -> Collection[str]:
        raise NotImplementedError

    def get_source_filenames(self) -> Collection[Path]:
        bounding_box_ch = project_geometry(
            self.bounding_box, crs_from=self.region, crs_to=self.dataset_crs
        )
        return [
            filename
            for filename in download_swisstopo_if_not_exists(
                bounding_box=bounding_box_ch,
                templates=[
                    f"{file_path}.{extension}"
                    for file_path in self.file_templates
                    for extension in ("shp", "shx", "prj", "dbf")
                ],
            )
            if filename.suffix == ".shp"
        ]
