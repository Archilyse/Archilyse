from typing import Iterable

from shapely.geometry import MultiPolygon, Point, Polygon

from brooks.util.geometry_ops import get_line_strings
from common_utils.constants import (
    NOISE_SOURCE_TYPE,
    NOISE_TIME_TYPE,
    REGION,
    SurroundingType,
)
from simulations.noise.constants import (
    GENERIC_NOISE_LEVELS_BY_TYPE_AND_TIME,
    GENERIC_NOISE_PROVIDERS,
)
from simulations.noise.utils import fishnet_split
from surroundings.base_noise_source_geometry_provider import (
    BaseNoiseSourceGeometryProvider,
)
from surroundings.base_noise_surrounding_handler import BaseNoiseLevelHandler
from surroundings.eu_noise import EUNoiseLevelHandler, EUNoiseSourceGeometryProvider
from surroundings.manual_surroundings import ManualExclusionSurroundingHandler
from surroundings.swisstopo import SwissTopoNoiseLevelHandler
from surroundings.utils import get_surroundings_bounding_box
from surroundings.v2.swisstopo import SwissTopoNoiseSourceGeometryProvider


class BaseNoiseSourcesLevelsGenerator:
    @property
    def _source_geometry_provider(self) -> type[BaseNoiseSourceGeometryProvider]:
        raise NotImplementedError

    @property
    def _noise_level_handler(self) -> type[BaseNoiseLevelHandler]:
        raise NotImplementedError

    def __init__(
        self,
        location: Point,
        bounding_box_extension: int,
        region: REGION,
        noise_source_type: NOISE_SOURCE_TYPE,
    ):
        self.noise_source_type = noise_source_type
        common_kwargs = dict(
            location=location,
            bounding_box_extension=bounding_box_extension,
            region=region,
        )
        self.source_geometry_provider = self._source_geometry_provider(
            **common_kwargs,
        )
        self.noise_level_provider = {
            noise_time_type: self._noise_level_handler(
                **common_kwargs,
                noise_source_type=noise_source_type,
                noise_time_type=noise_time_type,
            )
            for noise_time_type in NOISE_TIME_TYPE
        }

    def generate(
        self, exclusion_area: Polygon | MultiPolygon
    ) -> Iterable[tuple[Point, dict[NOISE_TIME_TYPE, float]]]:
        noise_sources_ex_exclusion_area = (
            linestring_part
            for linestring in self.source_geometry_provider.get_source_geometries(
                noise_source_type=self.noise_source_type
            )
            for linestring_part in get_line_strings(
                linestring.difference(exclusion_area)
            )
        )
        noise_sample_locations = (
            linestring_part.centroid
            for linestring in noise_sources_ex_exclusion_area
            for linestring_part in fishnet_split(
                geometry=linestring, col_width=10, row_width=10
            )
        )
        for sample_location in noise_sample_locations:
            yield sample_location, {
                noise_time_type: self.noise_level_provider[noise_time_type].get_at(
                    location=sample_location
                )
                for noise_time_type in NOISE_TIME_TYPE
            }


class SwisstopoNoiseSourcesLevelsGenerator(BaseNoiseSourcesLevelsGenerator):
    @property
    def _source_geometry_provider(self) -> type[BaseNoiseSourceGeometryProvider]:
        return SwissTopoNoiseSourceGeometryProvider

    @property
    def _noise_level_handler(self) -> type[BaseNoiseLevelHandler]:
        return SwissTopoNoiseLevelHandler


class EuNoiseSourcesLevelsGenerator(BaseNoiseSourcesLevelsGenerator):
    @property
    def _source_geometry_provider(self) -> type[BaseNoiseSourceGeometryProvider]:
        return EUNoiseSourceGeometryProvider

    @property
    def _noise_level_handler(self) -> type[BaseNoiseLevelHandler]:
        return EUNoiseLevelHandler


class GenericNoiseSourcesLevelsGenerator:
    def __init__(
        self,
        location: Point,
        bounding_box_extension: int,
        region: REGION,
        noise_source_type: NOISE_SOURCE_TYPE,
    ):
        bounding_box = get_surroundings_bounding_box(
            x=location.x, y=location.y, bounding_box_extension=bounding_box_extension
        )
        self.noise_source_type = noise_source_type

        self.noise_provider = GENERIC_NOISE_PROVIDERS[noise_source_type](
            bounding_box=bounding_box,
            region=region,
        )

    def _get_noise_base_level_by_type(
        self, time_type: NOISE_TIME_TYPE, geom_type: str | SurroundingType
    ) -> float:
        return GENERIC_NOISE_LEVELS_BY_TYPE_AND_TIME[self.noise_source_type][geom_type][
            time_type
        ]

    def generate(
        self, exclusion_area: Polygon | MultiPolygon = None
    ) -> Iterable[tuple[Point, dict[NOISE_TIME_TYPE, float]]]:
        if not exclusion_area:
            exclusion_area = Polygon()
        for geometry in self.noise_provider.get_geometries():
            for linestring in get_line_strings(
                geometry.geom.difference(exclusion_area)
            ):
                for linestring_part in fishnet_split(
                    geometry=linestring, col_width=10, row_width=10
                ):
                    sample_location = linestring_part.centroid
                    yield sample_location, {
                        noise_time_type: self._get_noise_base_level_by_type(
                            noise_time_type, geometry.properties["type"]
                        )
                        for noise_time_type in NOISE_TIME_TYPE
                    }


NOISE_SOURCE_LEVELS_GENERATOR_PER_REGION = {
    REGION.CH: SwisstopoNoiseSourcesLevelsGenerator,
    REGION.DE_HAMBURG: EuNoiseSourcesLevelsGenerator,
}


def get_noise_sources(
    site_id: int,
    location: Point,
    region: REGION,
    bounding_box_extension: int,
    noise_source_type: NOISE_SOURCE_TYPE,
    **kwargs,
) -> Iterable[tuple[Point, dict[NOISE_TIME_TYPE, float]]]:
    exclusion_area = ManualExclusionSurroundingHandler(
        site_id=site_id, region=region
    ).get_footprint()
    noise_generator = NOISE_SOURCE_LEVELS_GENERATOR_PER_REGION.get(
        region, GenericNoiseSourcesLevelsGenerator
    )
    return noise_generator(
        location=location,
        bounding_box_extension=bounding_box_extension,
        region=region,
        noise_source_type=noise_source_type,
    ).generate(exclusion_area)
