from typing import Iterable, Iterator, List, Optional, Set, Tuple

from pygeos import Geometry, buffer, from_shapely, intersects, to_shapely, union_all
from shapely.affinity import scale
from shapely.geometry import MultiPolygon, Polygon

from brooks.models import SimArea, SimSeparator, SimSpace
from brooks.util.geometry_ops import buffer_unbuffer_geometry
from common_utils.constants import BUFFERING_1CM
from dufresne.polygon.utils import get_biggest_polygon


class SpaceMaker:
    """class for creating brook spaces from a list of brook separators and brook areas"""

    @staticmethod
    def get_buffer_unbuffer_polygons(m_polygon: MultiPolygon) -> Iterator[Polygon]:
        for polygon in m_polygon.geoms:
            polygon = buffer_unbuffer_geometry(
                geometry=polygon, reverse=True, buffer=BUFFERING_1CM
            )
            if polygon.area == 0:
                continue
            if isinstance(polygon, MultiPolygon):
                for geom in polygon.geoms:
                    yield geom
            else:
                yield polygon

    @classmethod
    def create_spaces_and_areas(
        cls,
        separators: Set[SimSeparator],
        splitters: Set[SimSeparator],
        generic_space_height: Tuple[float, float],
        wall_buffer: Optional[float] = None,
    ) -> Set[SimSpace]:
        spaces: Set[SimSpace] = set()
        areas: Set[SimArea] = set()
        spaces_polygons = cls.get_spaces_from_separators(
            separators=[s.footprint for s in separators],
            buffer_distance=wall_buffer,
        )
        area_splitter_polygons = cls.get_spaces_from_separators(
            separators=[s.footprint for s in separators.union(splitters)],
            buffer_distance=wall_buffer,
        )
        #  First we identify the spaces, based only on real walls
        for space_polygon in cls.get_buffer_unbuffer_polygons(
            m_polygon=spaces_polygons
        ):
            spaces.add(SimSpace(footprint=space_polygon, height=generic_space_height))

        spaces_list = list(spaces)
        spaces_geos_polygons = from_shapely([space.footprint for space in spaces_list])
        # Then we identify the areas, this time with all the walls, including the fake (aka splitters)
        for area_polygon in cls.get_buffer_unbuffer_polygons(
            m_polygon=area_splitter_polygons
        ):
            cls._create_and_add_area(
                spaces_geos_polygons=spaces_geos_polygons,
                spaces_list=spaces_list,
                footprint=area_polygon,
                accumulator=areas,
                area_height=generic_space_height,
            )

        return spaces

    @classmethod
    def _create_and_add_area(
        cls,
        spaces_geos_polygons: List[Geometry],
        spaces_list: List[SimSpace],
        footprint: Polygon,
        accumulator: Set[SimArea],
        area_height: Tuple[float, float],
    ) -> Set[SimArea]:
        area = SimArea(footprint=footprint, height=area_height)
        accumulator.add(area)

        area_geos = from_shapely(footprint)

        spaces_intersecting = intersects(area_geos, spaces_geos_polygons)
        if spaces_intersecting.sum():
            parent = spaces_list[spaces_intersecting.nonzero()[0][0]]
            parent.add_area(area)
        return accumulator

    @classmethod
    def get_spaces_from_separators(
        cls,
        separators: Iterable[Polygon],
        factor: float = 3.0,
        buffer_distance: Optional[float] = None,
    ) -> MultiPolygon:
        """Takes bounding box of the separator gauge then rescales it with a factor of
        3. From this box the difference with the original separator gauge is taken.
        the biggest polygon is removed, as its always the one lying outside the
        separator gauge. The remaining polygons are returned.

        Returns:
            MultiPolygon: created spaces.
        """
        separators = from_shapely(separators)
        if buffer_distance:
            separators = buffer(
                separators,
                radius=buffer_distance,
                cap_style="square",
                join_style="mitre",
            )

        separator_union = union_all(separators)
        separator_union = to_shapely(separator_union)

        scaled_bounding_box = scale(
            geom=separator_union.minimum_rotated_rectangle, xfact=factor, yfact=factor
        )
        indoor_area = scaled_bounding_box.difference(separator_union)
        biggest_space = get_biggest_polygon(indoor_area)

        indoor_area = indoor_area.difference(biggest_space)
        if isinstance(indoor_area, Polygon):
            return MultiPolygon([indoor_area])

        return indoor_area
