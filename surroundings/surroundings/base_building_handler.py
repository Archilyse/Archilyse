import contextlib
from typing import Iterator

from shapely.errors import TopologicalError
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.exceptions import InvalidShapeException
from dufresne.dimension_from3dto2d import from3dto2d
from surroundings.constants import PERCENTAGE_AREA_OVERLAP_TO_REMOVE_BUILDING


class Building:
    def __init__(
        self,
        geometry: Polygon | MultiPolygon,
        footprint: Polygon | MultiPolygon,
    ):
        self.geometry = geometry
        self.footprint = footprint


class BaseBuildingSurroundingHandler:
    def get_buildings(self) -> Iterator[Building]:
        raise NotImplementedError

    @staticmethod
    def _create_building_footprint(
        geometry: MultiPolygon,
    ) -> Polygon | MultiPolygon | None:
        """
        The unary union of all the polygons of the geometry is mandatory because the geometry provided by
         swisstopo or other sources contains some invalid polygons according to shapely standards that translates
         into holes of the final footprint.

         To solve this issue, we will always use the exterior ring of points in case we have a polygon or
         if we have a multipolygon enclosing gaps, we will expand and reduce the geometry back to its normal size
         to remove this holes that will appear in the triangulated building.
        """
        geoms = []
        for polygon in geometry.geoms:
            with contextlib.suppress(InvalidShapeException):
                geoms.append(ensure_geometry_validity(polygon))

        union = unary_union(geoms=geoms)
        if isinstance(union, Polygon):
            union = Polygon(union.exterior)
        return None if union.is_empty else from3dto2d(union)

    @staticmethod
    def _is_target_building(
        building_footprint: Polygon | MultiPolygon,
        building_footprints: list[MultiPolygon],
    ) -> bool:
        # TODO to be removed once PH_2022_H1 is the standard
        for layout_footprint in building_footprints:
            try:
                if not building_footprint.intersects(layout_footprint):
                    continue
                intersection = building_footprint.intersection(layout_footprint)
                if (
                    intersection
                    and intersection.area / building_footprint.area
                    > PERCENTAGE_AREA_OVERLAP_TO_REMOVE_BUILDING
                ):
                    return True
                elif (
                    intersection
                    and intersection.area / layout_footprint.area
                    > PERCENTAGE_AREA_OVERLAP_TO_REMOVE_BUILDING
                ):
                    return True

            except TopologicalError as e:
                if (
                    "could not be performed. Likely cause is invalidity of the geometry"
                    in e.args[0]
                ):
                    if (
                        layout_footprint.centroid.distance(layout_footprint) < 1
                    ):  # This is to avoid using centroids which are lying outside the
                        # footprint e.g. L shaped buildings
                        if layout_footprint.centroid.within(building_footprint):
                            return True
                else:
                    raise e
        return False
