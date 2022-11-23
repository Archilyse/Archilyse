from abc import abstractmethod

from shapely.geometry import Point

from common_utils.constants import NOISE_SOURCE_TYPE, NOISE_TIME_TYPE
from surroundings.utils import get_surroundings_bounding_box


class BaseNoiseLevelHandler:
    def __init__(
        self,
        location: Point,
        bounding_box_extension: int,
        noise_source_type: NOISE_SOURCE_TYPE,
        noise_time_type: NOISE_TIME_TYPE,
        **kwargs
    ):
        self.noise_source_type = noise_source_type
        self.noise_time_type = noise_time_type
        self.bounding_box = get_surroundings_bounding_box(
            x=location.x, y=location.y, bounding_box_extension=bounding_box_extension
        )

    @abstractmethod
    def get_at(self, location: Point) -> float:
        raise NotImplementedError
