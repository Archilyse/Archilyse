from abc import ABC
from functools import cached_property
from itertools import chain
from typing import Dict, Iterator

from shapely.geometry import CAP_STYLE, JOIN_STYLE, MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from common_utils.constants import REGION, SurroundingType
from surroundings.constants import (
    BOUNDING_BOX_EXTENSION_MOUNTAINS,
    BOUNDING_BOX_EXTENSION_SAMPLE,
)
from surroundings.manual_surroundings import (
    ManualBuildingSurroundingHandler,
    ManualExclusionSurroundingHandler,
)
from surroundings.raster_window import RasterWindow
from surroundings.srtm.raster_window_provider import SRTMRasterWindowProvider
from surroundings.swisstopo.raster_window_provider import (
    SwissTopoGroundsRasterWindowProvider,
)
from surroundings.triangle_remover import TriangleRemover
from surroundings.utils import SurrTrianglesType, get_surroundings_bounding_box
from surroundings.v2.base import BaseElevationHandler
from surroundings.v2.constants import (
    BOUNDING_BOX_EXTENSION_BIG_ITEMS,
    BOUNDING_BOX_EXTENSION_SMALL_ITEMS,
    DEFAULT_SAFETY_BUFFER,
    MOUNTAINS_RESOLUTION,
    SAFETY_BUFFER_BY_SURROUNDING_TYPE,
)
from surroundings.v2.grounds import (
    ElevationHandler,
    GroundHandler,
    MultiRasterElevationHandler,
    UNMountainsHandler,
)
from surroundings.v2.osm.surroundings_mixin import OSMSurroundingsMixin
from surroundings.v2.swisstopo.surroundings_mixin import SwissTopoSurroundingsMixin


class SurroundingHandler:
    def __init__(
        self,
        region: REGION,
        location: Point,
        building_footprints: list[Polygon | MultiPolygon],
        sample: bool = False,
    ):
        self.location = location
        self.region = region
        self.building_footprints = building_footprints
        self.sample = sample

    @cached_property
    def _small_items_bbox(self):
        small_items_bbox_extension = (
            BOUNDING_BOX_EXTENSION_SAMPLE
            if self.sample
            else BOUNDING_BOX_EXTENSION_SMALL_ITEMS
        )
        return get_surroundings_bounding_box(
            x=self.location.x,
            y=self.location.y,
            bounding_box_extension=small_items_bbox_extension,
        )

    @cached_property
    def _big_items_bbox(self):
        if self.sample:
            return self._small_items_bbox
        return get_surroundings_bounding_box(
            x=self.location.x,
            y=self.location.y,
            bounding_box_extension=BOUNDING_BOX_EXTENSION_BIG_ITEMS,
        )

    @cached_property
    def _grounds_raster_window(self) -> RasterWindow:
        raster_window_provider_by_region = {
            REGION.CH: SwissTopoGroundsRasterWindowProvider
        }
        return raster_window_provider_by_region.get(
            self.region, SRTMRasterWindowProvider
        )(region=self.region, bounds=self._small_items_bbox.bounds).get_raster_window()

    @cached_property
    def _extended_grounds_raster_window(self) -> RasterWindow:
        mountains_bbox = get_surroundings_bounding_box(
            x=self.location.x,
            y=self.location.y,
            bounding_box_extension=BOUNDING_BOX_EXTENSION_MOUNTAINS,
        )
        return SRTMRasterWindowProvider(
            region=self.region,
            bounds=mountains_bbox.bounds,
            resolution=MOUNTAINS_RESOLUTION,
        ).get_raster_window()

    @cached_property
    def _small_items_elevation_handler(self) -> BaseElevationHandler:
        return ElevationHandler(raster_window=self._grounds_raster_window)

    @cached_property
    def _big_items_elevation_handler(self) -> BaseElevationHandler:
        if self.sample:
            return self._small_items_elevation_handler
        return MultiRasterElevationHandler(
            primary_window=self._grounds_raster_window,
            secondary_window=self._extended_grounds_raster_window,
        )

    @cached_property
    def _exclusion_area_by_surrounding_type(self):
        polygon = unary_union(self.building_footprints)
        return {
            surrounding_type: polygon.buffer(
                SAFETY_BUFFER_BY_SURROUNDING_TYPE.get(
                    surrounding_type, DEFAULT_SAFETY_BUFFER
                ),
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            )
            for surrounding_type in SurroundingType
        }

    @staticmethod
    def _crop_triangles(
        triangles: Iterator[SurrTrianglesType],
        exclusion_area_by_surrounding_type: Dict[
            SurroundingType, Polygon | MultiPolygon
        ],
    ) -> Iterator[SurrTrianglesType]:
        yield from (
            (surrounding_type, new_triangle)
            for surrounding_type, triangle in triangles
            for new_triangle in TriangleRemover.triangle_difference(
                triangle=triangle,
                footprint=exclusion_area_by_surrounding_type[surrounding_type],
            )
        )

    @staticmethod
    def generate_small_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError

    @staticmethod
    def generate_big_items(
        region: REGION, bounding_box: Polygon, elevation_handler: BaseElevationHandler
    ) -> Iterator[SurrTrianglesType]:
        raise NotImplementedError

    def _generate_items_triangles(self) -> Iterator[SurrTrianglesType]:
        yield from chain(
            self.generate_small_items(
                region=self.region,
                bounding_box=self._small_items_bbox,
                elevation_handler=self._small_items_elevation_handler,
            ),
            self.generate_big_items(
                region=self.region,
                bounding_box=self._big_items_bbox,
                elevation_handler=self._big_items_elevation_handler,
            ),
        )

    def _generate_ground_triangles(self) -> Iterator[SurrTrianglesType]:
        yield from GroundHandler(
            raster_window=self._grounds_raster_window
        ).get_triangles(building_footprints=self.building_footprints)
        if not self.sample:
            yield from UNMountainsHandler(
                raster_window=self._extended_grounds_raster_window,
                exclusion_bounds=self._small_items_bbox.bounds,
            ).get_triangles()

    def generate_view_surroundings(self) -> Iterator[SurrTrianglesType]:
        yield from self._crop_triangles(
            triangles=self._generate_items_triangles(),
            exclusion_area_by_surrounding_type=self._exclusion_area_by_surrounding_type,
        )
        yield from self._generate_ground_triangles()


class SlamSurroundingHandler(SurroundingHandler, ABC):
    def __init__(self, site_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.site_id = site_id

    @property
    def _exclusion_area_by_surrounding_type(self):
        manual_exclusion_footprint = ManualExclusionSurroundingHandler(
            site_id=self.site_id,
            region=self.region,
        ).get_footprint()
        return {
            surrounding_type: exclusion_area.union(manual_exclusion_footprint)
            for surrounding_type, exclusion_area in super(
                SlamSurroundingHandler, self
            )._exclusion_area_by_surrounding_type.items()
        }

    def _generate_manual_surroundings_triangles(self) -> Iterator[SurrTrianglesType]:
        yield from ManualBuildingSurroundingHandler(
            site_id=self.site_id,
            region=self.region,
            elevation_handler=self._small_items_elevation_handler,
        ).get_triangles()

    def generate_view_surroundings(self) -> Iterator[SurrTrianglesType]:
        yield from super(SlamSurroundingHandler, self).generate_view_surroundings()
        yield from self._generate_manual_surroundings_triangles()


class SwissTopoSlamSurroundingHandler(
    SwissTopoSurroundingsMixin, SlamSurroundingHandler
):
    pass


class SwissTopoSurroundingHandler(SwissTopoSurroundingsMixin, SurroundingHandler):
    pass


class OSMSurroundingHandler(OSMSurroundingsMixin, SurroundingHandler):
    pass


class OSMSlamSurroundingHandler(OSMSurroundingsMixin, SlamSurroundingHandler):
    pass
