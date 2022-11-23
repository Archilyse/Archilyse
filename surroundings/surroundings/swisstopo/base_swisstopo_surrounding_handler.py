from typing import Dict, Iterable, Iterator, Optional

import fiona
from shapely.geometry import MultiPolygon, Point

from common_utils.constants import REGION, SIMULATION_VERSION, SWISSTOPO_DIR
from common_utils.exceptions import NoEntitiesFileException
from dufresne.linestring_add_width import (
    add_width_to_linestring,
    add_width_to_linestring_improved,
)
from dufresne.polygon.utils import as_multipolygon
from surroundings.base_entity_surrounding_handler import BaseEntitySurroundingHandler
from surroundings.constants import BOUNDING_BOX_EXTENSION
from surroundings.utils import download_swisstopo_if_not_exists


class BaseEntitySwissTopoSurroundingHandler(BaseEntitySurroundingHandler):
    _BOUNDING_BOX_EXTENSION = BOUNDING_BOX_EXTENSION

    def __init__(
        self,
        location: Point,
        simulation_version: SIMULATION_VERSION,
        bounding_box_extension: Optional[float] = None,
    ):
        """
        NOTE: the location HAS to be provided already projected so that it is in meters AND in xy format!
        The bounding_box_extension has to be provided (in meters).
        """
        super().__init__(
            location=location,
            bounding_box_extension=bounding_box_extension,
            region=REGION.CH,
            simulation_version=simulation_version,
        )

    def load_entities(self, entities_file_path: Iterable[str]) -> Iterator[Dict]:
        if entities_file_path:
            if isinstance(entities_file_path, str):
                entities_file_path = [entities_file_path]
            download_swisstopo_if_not_exists(
                bounding_box=self.bounding_box,
                templates=[
                    file_path.format(extension)
                    for file_path in entities_file_path
                    for extension in ("shp", "shx", "prj", "dbf")
                ],
            )
            files = [
                fiona.open(SWISSTOPO_DIR.joinpath(file_path.format("shp")).as_posix())
                for file_path in entities_file_path
            ]
            return (
                entity
                for file in files
                for entity in file.filter(bbox=self.bounding_box.bounds)
            )
        raise NoEntitiesFileException

    def add_width(self, *args, **kwargs) -> MultiPolygon:
        if self.simulation_version in {
            SIMULATION_VERSION.EXPERIMENTAL,
            SIMULATION_VERSION.PH_2022_H1,
        }:
            return as_multipolygon(add_width_to_linestring_improved(*args, **kwargs))
        else:
            return add_width_to_linestring(*args, **kwargs)
