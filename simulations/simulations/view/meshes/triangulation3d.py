from typing import Any, Iterable, List, Optional, Set, Union

from numpy import float32, ndarray, vstack
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    GeometryCollection,
    LineString,
    MultiPolygon,
    Polygon,
)

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout, SimSeparator
from brooks.types import OpeningType, SeparatorType
from brooks.utils import get_default_element_height
from common_utils.constants import OPENING_BUFFER_TO_CUT_WALLS, SIMULATION_VERSION
from common_utils.exceptions import LayoutTriangulationException
from dufresne.polygon.polygon_triangulate import triangulate_polygon

from .georeferencing import GeoreferencingTransformation


def to3d(p, z):
    return p[0], p[1], z


class LayoutTriangulator:
    _DEFAULT_CEILING_FLOOR_THICKNESS = 0.0001

    @property
    def floor_thickness(self):
        return self._DEFAULT_CEILING_FLOOR_THICKNESS

    @property
    def ceiling_thickness(self):
        return self._DEFAULT_CEILING_FLOOR_THICKNESS

    def __init__(
        self,
        layout: SimLayout,
        georeferencing_parameters: GeoreferencingTransformation,
        classification_scheme: Optional[Any] = None,
    ):
        self._layout = layout
        self._triangles = ndarray(shape=(0, 3, 3), dtype=float32)
        self._georeferencing_parameters = georeferencing_parameters
        self._classification_scheme = (
            classification_scheme or UnifiedClassificationScheme()
        )

    def create_layout_triangles(
        self, layouts_upper_floor: Iterable[SimLayout], level_baseline: float
    ) -> ndarray:

        floor_baseline = level_baseline
        ceiling_baseline = floor_baseline + get_default_element_height(
            SeparatorType.WALL, default=self._layout.default_element_heights
        )
        separators_wo_railings_area_splitters = (
            separator
            for separator in self._layout.separators
            if separator.type
            not in (SeparatorType.RAILING, SeparatorType.AREA_SPLITTER)
        )
        for separator in separators_wo_railings_area_splitters:
            opening_footprints_to_remove_from_separators = []

            non_entrance_door_openings = (
                opening
                for opening in separator.openings
                if opening.type is not OpeningType.ENTRANCE_DOOR
            )
            for opening in non_entrance_door_openings:
                intersection = opening.footprint.buffer(
                    OPENING_BUFFER_TO_CUT_WALLS,
                    cap_style=CAP_STYLE.square,
                    join_style=JOIN_STYLE.mitre,
                    mitre_limit=2,
                ).intersection(separator.footprint)

                if opening.type is OpeningType.DOOR:
                    self._add_door(
                        intersection=intersection,
                        door_upper_edge=floor_baseline + opening.height[1],
                        ceiling=ceiling_baseline,
                        floor=floor_baseline,
                    )

                elif opening.type is OpeningType.WINDOW:
                    self._add_window(
                        intersection=intersection,
                        floor=floor_baseline,
                        window_lower_edge=floor_baseline + opening.height[0],
                        window_upper_edge=floor_baseline + opening.height[1],
                        ceiling=ceiling_baseline,
                    )

                opening_footprints_to_remove_from_separators.append(
                    intersection.buffer(
                        OPENING_BUFFER_TO_CUT_WALLS / 5,
                        cap_style=CAP_STYLE.square,
                        join_style=JOIN_STYLE.mitre,
                        mitre_limit=2,
                    )
                )

            self._add_separator(
                separator=separator,
                opening_footprints_to_remove_from_separators=opening_footprints_to_remove_from_separators,
                floor=floor_baseline,
                ceiling=ceiling_baseline,
            )
        # Finally we add all the floors / ceilings
        self._add_floors_and_ceilings(
            areas=self._layout.areas,
            floor=floor_baseline,
            ceiling=ceiling_baseline,
            layouts_upper_floor=layouts_upper_floor,
        )

        return self._georeferencing_parameters.apply(
            self._triangles.reshape(-1, 3)
        ).reshape(-1, 3, 3)

    def _add_door(
        self,
        intersection: Polygon,
        door_upper_edge: float,
        ceiling: float,
        floor: float,
    ):
        self._add_polygons(
            polygon=intersection,
            zmin=door_upper_edge,
            zmax=ceiling + self.ceiling_thickness,
        )

        self._add_polygons(
            polygon=intersection, zmin=floor - self.floor_thickness, zmax=floor
        )

    def _add_window(
        self,
        intersection: Polygon,
        floor: float,
        window_lower_edge: float,
        window_upper_edge: float,
        ceiling: float,
    ):
        self._add_polygons(
            polygon=intersection,
            zmin=floor - self.floor_thickness,
            zmax=window_lower_edge,
        )
        self._add_polygons(
            polygon=intersection,
            zmin=window_upper_edge,
            zmax=ceiling + self.ceiling_thickness,
        )

    def _add_separator(
        self,
        separator: SimSeparator,
        opening_footprints_to_remove_from_separators: List[Polygon],
        floor: float,
        ceiling: float,
    ):
        # For each section of the wall that is left (after removing the windows & doors)
        # we add the full wall height
        remaining_separator_footprint: Union[
            Polygon, MultiPolygon
        ] = separator.footprint
        for opening_footprint in opening_footprints_to_remove_from_separators:
            remaining_separator_footprint = remaining_separator_footprint.difference(
                opening_footprint
            )

        if remaining_separator_footprint.is_empty:
            pass  # Case where separator and opening have the exact same geometry, so the difference is empty

        elif isinstance(remaining_separator_footprint, Polygon):
            self._add_polygons(
                polygon=remaining_separator_footprint,
                zmin=floor - self.floor_thickness,
                zmax=ceiling + self.ceiling_thickness,
            )
        elif isinstance(remaining_separator_footprint, MultiPolygon):
            for section in remaining_separator_footprint.geoms:
                self._add_polygons(
                    polygon=section,
                    zmin=floor - self.floor_thickness,
                    zmax=ceiling + self.ceiling_thickness,
                )

        else:
            raise LayoutTriangulationException(
                f"Remaining Separator geometry type {type(remaining_separator_footprint)} is not covered"
            )

    def _add_floors_and_ceilings(
        self,
        areas: Set[SimArea],
        floor: float,
        ceiling: float,
        layouts_upper_floor: Iterable[SimLayout],
    ):
        upper_areas_without_floor = MultiPolygon(
            [
                area.footprint
                for layout in layouts_upper_floor
                for area in layout.areas
                if area.type in self._classification_scheme.AREAS_WITHOUT_FLOORS
            ]
        )
        for area in areas:
            if area.type not in self._classification_scheme.AREAS_WITHOUT_FLOORS:
                self._add_floor(footprint=area.footprint, baseline=floor)
            if area.type not in self._classification_scheme.AREAS_WITHOUT_CEILINGS:
                ceiling_footprint = area.footprint.difference(upper_areas_without_floor)
                if ceiling_footprint.area > 0:
                    self._add_ceiling(
                        footprint=ceiling_footprint,
                        baseline=ceiling,
                    )

    def _add_floor(
        self,
        footprint: Union[Polygon, MultiPolygon],
        baseline: float,
    ):
        self._add_polygons(
            # small Buffer to make sure elements are overlapping
            # and avoid small gaps
            polygon=footprint.buffer(0.125, cap_style=3, join_style=2, mitre_limit=2),
            zmin=baseline - self.floor_thickness,
            zmax=baseline,
        )

    def _add_ceiling(
        self,
        footprint: Union[Polygon, MultiPolygon],
        baseline: float,
    ):
        self._add_polygons(
            # small Buffer to make sure elements are overlapping
            # and avoid small gaps
            polygon=footprint.buffer(0.125, cap_style=3, join_style=2, mitre_limit=2),
            zmin=baseline,
            zmax=baseline + self.ceiling_thickness,
        )

    def _add_triangle(self, a, b, c):
        self._triangles = vstack([self._triangles, [[a, b, c]]])

    def _add_vertical_triangles(self, polygon, zmin, zmax):
        coords = [x for x in polygon.exterior.coords]
        if coords[-1] != coords[0]:
            coords.append(coords[0])

        for idx, _ in enumerate(coords):
            t1 = [
                to3d(coords[idx], zmin),
                to3d(coords[idx], zmax),
                to3d(coords[(idx + 1) % len(coords)], zmax),
            ]

            t2 = [
                to3d(coords[idx], zmin),
                to3d(coords[(idx + 1) % len(coords)], zmax),
                to3d(coords[(idx + 1) % len(coords)], zmin),
            ]

            self._add_triangle(*t1)
            self._add_triangle(*t2)

    def _add_horizontal_triangles(self, polygon, z_value):
        # NOTE: mode `pi` allows segment constraints for non-convex polygons (-p) and
        # incremental Delauny (-i) seems to avoid segfaults.
        for triangle in triangulate_polygon(polygon, mode="pi"):
            self._add_triangle(*[to3d(p, z_value) for p in triangle[:3]])

    def _add_polygons(self, polygon, zmin, zmax):
        if isinstance(polygon, (GeometryCollection, MultiPolygon)):
            for poly in polygon:
                self._add_polygons(
                    polygon=poly,
                    zmin=zmin,
                    zmax=zmax,
                )
        elif isinstance(polygon, Polygon):
            self._extrude_polygon_and_triangulate(
                polygon=polygon,
                zmin=zmin,
                zmax=zmax,
            )
        elif isinstance(polygon, LineString):
            return
        else:
            raise RuntimeError("Trying to add non-polygon: {0}".format(type(polygon)))

    def _extrude_polygon_and_triangulate(
        self, polygon: Polygon, zmin: float, zmax: float
    ):
        """
        creates an extruded 3d body of the provided polygon extending from zmin to zmax
        and create triangles for this body
        """
        if not polygon.area:
            raise LayoutTriangulationException(
                "Trying to triangulate a polygon of size 0"
            )

        self._add_vertical_triangles(polygon, zmin, zmax)

        self._add_horizontal_triangles(polygon=polygon, z_value=zmin)

        self._add_horizontal_triangles(polygon=polygon, z_value=zmax)


class LayoutTriangulatorClabExtrusion(LayoutTriangulator):
    """
    New version of triangulating a layout:
    - Extrusion of floors and ceilings are extended to 0.15 meters

    This should only be used for simulation_version experimental as its changing the view values
    and custom_valuator didn't trained yet with this model
    """

    @property
    def floor_thickness(self):
        return (
            get_default_element_height(
                element_type="FLOOR_SLAB", default=self._layout.default_element_heights
            )
            / 2.0
        )

    @property
    def ceiling_thickness(self):
        return (
            get_default_element_height(
                element_type="CEILING_SLAB",
                default=self._layout.default_element_heights,
            )
            / 2.0
        )


TRIANGULATOR_BY_SIMULATION_VERSION = {
    simulation_version.name: (
        LayoutTriangulator
        if simulation_version
        not in {SIMULATION_VERSION.EXPERIMENTAL, SIMULATION_VERSION.PH_2022_H1}
        else LayoutTriangulatorClabExtrusion
    )
    for simulation_version in SIMULATION_VERSION
}
