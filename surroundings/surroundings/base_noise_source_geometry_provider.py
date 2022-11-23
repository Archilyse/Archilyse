from abc import abstractmethod
from typing import Iterable

from shapely.geometry import LineString, Point

from common_utils.constants import NOISE_SOURCE_TYPE, REGION
from surroundings.utils import get_surroundings_bounding_box


class BaseNoiseSourceGeometryProvider:
    def __init__(self, location: Point, region: REGION, bounding_box_extension: int):
        self.region = region
        self.location = location
        self.bounding_box_extension = bounding_box_extension
        self.bounding_box = get_surroundings_bounding_box(
            x=location.x, y=location.y, bounding_box_extension=bounding_box_extension
        )

    @abstractmethod
    def get_source_geometries(
        self, noise_source_type: NOISE_SOURCE_TYPE
    ) -> Iterable[LineString]:
        raise NotImplementedError()
