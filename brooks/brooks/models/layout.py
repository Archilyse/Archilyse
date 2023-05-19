from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from enum import Enum
from functools import cached_property
from itertools import chain
from typing import (
    DefaultDict,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)
from uuid import uuid1, uuid4

from pygeos import buffer, from_shapely, intersects, to_geojson
from shapely import wkt
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    GeometryCollection,
    LineString,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.ops import unary_union

from brooks.classifications import UnifiedClassificationScheme
from brooks.constants import GENERIC_HEIGHTS, THICKEST_WALL_POSSIBLE_IN_M
from brooks.models.area import SimArea
from brooks.models.feature import SimFeature
from brooks.models.opening import SimOpening
from brooks.models.separator import SimSeparator
from brooks.models.space import SimSpace
from brooks.models.spatial_entity import SpatialEntity
from brooks.models.violation import Violation
from brooks.types import AreaType, FeatureType, LayoutType, OpeningType, SeparatorType
from brooks.util.geometry_ops import (
    buffer_n_rounded,
    buffer_unbuffer_geometry,
    ensure_geometry_validity,
    get_center_line_from_rectangle,
    get_polygons,
    remove_small_holes_from_polygon,
    round_geometry,
)
from brooks.util.io import BrooksSerializable
from brooks.util.projections import pygeos_project
from brooks.utils import get_default_element_height_range
from common_utils.constants import REGION
from common_utils.exceptions import (
    CorruptedAnnotationException,
    FeaturesGenerationException,
    InvalidShapeException,
)
from common_utils.logger import logger
from common_utils.utils import pairwise
from dufresne.polygon.utils import as_multipolygon

PRECISION_UNARY_UNION = 11


class SimLayout(BrooksSerializable):
    MIN_POL_AREA = 1.0  # Minimum area when generating the custom polygon
    __serializable_fields__ = (
        "type",
        "id",
        "children",
        "errors",
    )
    simple_brooks_to_serialize: Dict[
        str, Set[Union[SeparatorType, OpeningType, FeatureType]]
    ] = {
        "separators": {SeparatorType.WALL, SeparatorType.RAILING, SeparatorType.COLUMN},
        "openings": {OpeningType.WINDOW, OpeningType.DOOR, OpeningType.ENTRANCE_DOOR},
        "features": {feature for feature in FeatureType},
    }

    """A layout is a the biggest private cluster in a public space"""

    def __init__(
        self,
        scale_factor: float = 1.0,
        layout_type: LayoutType = LayoutType.NOT_DEFINED,
        separators: Optional[Set[SimSeparator]] = None,
        spaces: Optional[Set[SimSpace]] = None,
        floor_number: int = 0,
        default_element_heights: Optional[
            Dict[
                Union[SeparatorType, str, FeatureType, OpeningType], Tuple[float, float]
            ]
        ] = None,
    ):
        self.id = uuid1()

        self.type = layout_type
        self.is_in_relative_coordinates = None
        # This set is needed to be able to perform validations over the layout independently of the mapper
        self.all_processed_features: Set[SimFeature] = set()

        self.scale_factor = scale_factor

        self.errors: List[Violation] = []
        self.classification_scheme = UnifiedClassificationScheme()

        self.separators: Set[SimSeparator] = separators or set()
        self.spaces: Set[SimSpace] = spaces or set()
        self.floor_number = floor_number
        self.default_element_heights = default_element_heights

    @property
    def default_element_heights(self):
        if self._default_element_heights is None:
            return GENERIC_HEIGHTS
        return self._default_element_heights

    @default_element_heights.setter
    def default_element_heights(self, value):
        self._default_element_heights = value

    @property
    def areas_by_type(
        self,
    ) -> Dict[AreaType, Set[SimArea]]:
        areas_by_type = defaultdict(set)
        for area in self.areas:
            areas_by_type[area.type].add(area)
        return areas_by_type

    @property
    def is_large_layout(self) -> bool:
        return self.footprint.minimum_rotated_rectangle.area > 5000

    @property
    def features_by_type(self) -> DefaultDict[FeatureType, Set[SimFeature]]:
        features_by_type = defaultdict(set)
        for feature in self.features:
            features_by_type[feature.type].add(feature)
        return features_by_type

    @property
    def openings_by_type(self) -> DefaultDict[OpeningType, Set[SimOpening]]:
        openings_by_type = defaultdict(set)
        for opening in self.openings:
            openings_by_type[opening.type].add(opening)
        return openings_by_type

    @property
    def children(self) -> List[Union[SimSeparator, SimSpace]]:
        return list(chain(self.spaces, self.separators))

    @property
    def spaces_by_id(self) -> Dict[str, SimSpace]:
        return {space.id: space for space in self.spaces}

    @property
    def areas(self) -> Set[SimArea]:
        return {area for space in self.spaces for area in space.areas}

    @property
    def features(self) -> Set[SimFeature]:
        return {feature for area in self.areas for feature in area.features}

    @property
    def openings(self) -> Set[SimOpening]:
        return {
            opening for separator in self.separators for opening in separator.openings
        }

    @property
    def separators_no_railings(self):
        return {
            separator
            for separator in self.separators
            if separator.type != SeparatorType.RAILING
        }

    @property
    def railings(self):
        return {
            separator
            for separator in self.separators
            if separator.type == SeparatorType.RAILING
        }

    @property
    def area_splitters(self):
        return {
            separator
            for separator in self.separators
            if separator.type == SeparatorType.AREA_SPLITTER
        }

    @property
    def walls(self):
        return {
            separator
            for separator in self.separators
            if separator.type == SeparatorType.WALL
        }

    @property
    def columns(self):
        return {
            separator
            for separator in self.separators
            if separator.type == SeparatorType.COLUMN
        }

    @property
    def doors(self) -> Set[SimOpening]:
        return {opening for opening in self.openings if opening.is_door}

    @cached_property
    def non_overlapping_separators(self) -> Set[SimSeparator]:
        sorted_separators = list(
            sorted(
                [deepcopy(s) for s in self.separators],
                key=lambda z: (z.width, z.footprint.area),
                reverse=True,
            )
        )
        for i, separator1 in enumerate(sorted_separators):
            for separator2 in sorted_separators[i + 1 :]:
                if separator1.footprint.intersects(separator2.footprint):
                    separator2.footprint = ensure_geometry_validity(
                        separator2.footprint.difference(separator1.footprint)
                    )

        polygonal_separators = set()
        for separator in sorted_separators:
            for geom in get_polygons(separator.footprint):
                new_separator = deepcopy(separator)
                new_separator.id = uuid4().hex
                new_separator.footprint = geom
                new_separator.openings = {
                    opening
                    for opening in separator.openings
                    if opening.footprint.intersects(geom)
                }
                for opening in new_separator.openings:
                    opening.footprint = opening.adjust_geometry_to_wall(
                        opening=opening.footprint, wall=geom, buffer_width=1.05
                    )
                polygonal_separators.add(new_separator)
        return polygonal_separators

    @cached_property
    def areas_openings(self) -> Dict[str, Set[SimOpening]]:
        """dict keys are area.id, dict values are all openings"""
        from brooks import SpaceConnector

        areas_openings: Dict[str, Set[SimOpening]] = {
            area.id: set() for area in self.areas
        }

        areas_ordered_list = list(self.areas)
        pygeos_spaces = from_shapely(
            [entity.footprint for entity in areas_ordered_list]
        )
        for opening in self.openings:
            connected_areas = SpaceConnector.get_intersecting_spaces_or_areas(
                opening=opening,
                spaces_or_areas_list=areas_ordered_list,
                pygeos_spaces=pygeos_spaces,
            )
            for area in connected_areas:
                areas_openings[area.id].add(opening)

        return areas_openings

    @cached_property
    def spaces_openings(self) -> Dict[str, Set[SimOpening]]:
        """dict keys are space.id, dict values are all openings belonging to areas of that space"""
        space_openings = {}
        for space in self.spaces:
            space_openings[space.id] = {
                opening
                for area in space.areas
                for opening in self.areas_openings[area.id]
            }

        return space_openings

    @cached_property
    def areas_separators(self) -> Dict[str, Set[SimSeparator]]:
        """dict keys are area.id, dict values are all separators intersecting with the area

        The separator footprint is scaled
        with the factor 1.02 to find intersection with areas.
        """
        areas_separators: Dict[str, Set[SimSeparator]] = {
            area.id: set() for area in self.areas
        }
        separators_list = list(self.separators)
        buffered_separators = buffer(
            from_shapely([sep.footprint for sep in separators_list]),
            radius=0.01,
            cap_style="square",
            join_style="mitre",
        )
        for area in self.areas:
            intersecting_separators = intersects(
                buffered_separators,
                from_shapely(area.footprint),
            )
            for separator_index in intersecting_separators.nonzero()[0]:
                areas_separators[area.id].add(separators_list[separator_index])
        return areas_separators

    @cached_property
    def spaces_separators(self) -> Dict[str, Set[SimSeparator]]:
        """dict keys are space.id, dict values are all separators of all areas belonging to the space"""

        space_separators = {}
        for space in self.spaces:
            space_separators[space.id] = {
                separator
                for area in space.areas
                for separator in self.areas_separators[area.id]
            }

        return space_separators

    @cached_property
    def outdoor_doors(self) -> Set[SimOpening]:
        # TODO make it multi scheme compatible
        outdoor_areas = [
            area
            for area_type in {AreaType.BALCONY, AreaType.LOGGIA}
            for area in self.areas_by_type[area_type]
        ]
        return {
            balcony_opening
            for area in outdoor_areas
            for balcony_opening in self.areas_openings[area.id]
            if balcony_opening.type == OpeningType.DOOR
        }

    @cached_property
    def outdoor_spaces(self) -> Set[SimSpace]:
        return {
            space
            for space in self.spaces
            for area in space.areas
            if area.type in self.classification_scheme.OUTDOOR_AREAS
        }

    @cached_property
    def outdoor_spaces_connected_by_entrance_door(self):
        return {
            space.id: space
            for space in self.outdoor_spaces
            for opening in self.spaces_openings[space.id]
            if opening.type == OpeningType.ENTRANCE_DOOR
        }

    @cached_property
    def footprint(self) -> Polygon:
        """WARNING: the footprint shouldn't be used in combination with georeferencing + scaling operations"""
        spaces = self._footprints_buffered_n_rounded_for_union(sim_elements=self.spaces)
        separators = [
            round_geometry(separator.footprint, precision=PRECISION_UNARY_UNION)
            for separator in self.separators
        ]
        footprint = unary_union(spaces + separators)
        valid_geometry = ensure_geometry_validity(geometry=footprint)
        # When performing unary unions, floating point difference can create holes
        # and this is only solving some problems
        if isinstance(valid_geometry, (MultiPolygon, GeometryCollection)):
            return ensure_geometry_validity(
                MultiPolygon([Polygon(polygon.exterior) for polygon in footprint.geoms])
            )
        else:
            return ensure_geometry_validity(Polygon(valid_geometry.exterior))

    @staticmethod
    def _footprints_buffered_n_rounded_for_union(
        sim_elements: Iterable[SpatialEntity], buffer: float = 0.001
    ):
        # Spaces are buffered because the rounding performed to avoid unary union problems can create gaps between
        # spaces geometries and the separators. The spaces should be always within walls, therefore the area of
        # the footprint shouldn't be artificially increased by this operation.
        return [
            buffer_n_rounded(
                geom=sim_element.footprint,
                buffer=buffer,
                precision=PRECISION_UNARY_UNION,
            )
            for sim_element in sim_elements
        ]

    def add_spaces(self, spaces: Set[SimSpace]):
        self.spaces.update(spaces)

    def add_separators(self, separators: Set[SimSeparator]):
        self.separators.update(separators)

    def _footprint_excluding_areas(
        self, areas_to_exclude: Set[SimArea], include_separators: bool = True
    ) -> Union[Polygon, MultiPolygon]:
        railings_to_exclude = {
            separator
            for area in areas_to_exclude
            for separator in self.areas_separators[area.id]
            if separator.type is SeparatorType.RAILING
        }

        separators: List[SpatialEntity] = [
            separator
            for separator in self.separators
            if separator not in railings_to_exclude
        ]
        areas: List[SpatialEntity] = [
            area for area in self.areas if area not in areas_to_exclude
        ]
        footprint = unary_union(
            self._footprints_buffered_n_rounded_for_union(
                sim_elements=areas + separators if include_separators else areas
            )
        )
        if isinstance(footprint, MultiPolygon):
            footprint = MultiPolygon(
                [
                    remove_small_holes_from_polygon(polygon=polygon)
                    for polygon in footprint.geoms
                ]
            )

        elif isinstance(footprint, Polygon):
            footprint = remove_small_holes_from_polygon(polygon=footprint)

        if isinstance(footprint, GeometryCollection) and footprint.is_empty:
            return Polygon()

        return ensure_geometry_validity(geometry=footprint)

    @cached_property
    def footprint_ex_balconies(self) -> Union[Polygon, MultiPolygon]:
        return self._footprint_excluding_areas(
            areas_to_exclude=self.areas_by_type[AreaType.BALCONY]
        )

    @cached_property
    def footprint_ex_areas_without_ceiling(self) -> Union[Polygon, MultiPolygon]:
        areas_to_exclude = set()
        for area_type in UnifiedClassificationScheme().AREAS_WITHOUT_CEILINGS:
            areas_to_exclude |= self.areas_by_type[area_type]

        return self._footprint_excluding_areas(areas_to_exclude=areas_to_exclude)

    @cached_property
    def footprint_ex_areas_without_floor(self) -> Union[Polygon, MultiPolygon]:
        areas_to_exclude = set()
        for area_type in UnifiedClassificationScheme().AREAS_WITHOUT_FLOORS:
            areas_to_exclude |= self.areas_by_type[area_type]

        return self._footprint_excluding_areas(areas_to_exclude=areas_to_exclude)

    @cached_property
    def outdoor_areas(self) -> Set[SimArea]:
        return {
            area
            for area in self.areas
            if area.type in self.classification_scheme.OUTDOOR_AREAS
        }

    @cached_property
    def footprint_facade(self) -> Union[Polygon, MultiPolygon]:
        return self._footprint_excluding_areas(self.outdoor_areas)

    @cached_property
    def footprint_outside(self) -> Union[Polygon, MultiPolygon]:
        return self._footprint_excluding_areas(
            self.areas - self.outdoor_areas, include_separators=False
        )

    @cached_property
    def footprint_areas_without_ceiling(self) -> Set[SimArea]:
        return unary_union(
            [
                area.footprint
                for area in self.areas
                if area.type in self.classification_scheme.AREAS_WITHOUT_CEILINGS
            ]
        )

    def asdict(self) -> dict:
        self.absolute_to_relative_coordinates()

        return super().asdict()

    def add_error(self, violation):
        self.errors.append(violation)

    def get_footprint_no_features(self) -> Polygon:
        """Footprint including spaces and doors and excluding voids and shafts, and the features.
        Stairs are not removed.

        The layout is expected to be scaled in meters as otherwise the buffering operation
        can't be guaranteed to success
        """
        # Add spaces and openings
        footprint = unary_union(
            self._footprints_buffered_n_rounded_for_union(
                sim_elements=self.spaces
                | set(
                    opening
                    for space in self.spaces
                    for opening in self.spaces_openings[space.id]
                    if opening.is_door
                )
            )
        )
        # Remove shafts and voids
        footprint -= unary_union(
            self._footprints_buffered_n_rounded_for_union(
                sim_elements=[
                    area
                    for area in self.areas
                    if area.type
                    in self.classification_scheme.AREA_TYPES_ACCEPTING_SHAFTS
                ]
            )
        )
        # Remove features, except the stairs
        footprint -= unary_union(
            self._footprints_buffered_n_rounded_for_union(
                sim_elements=[f for f in self.features if f.type != FeatureType.STAIRS]
            )
        )

        one_cm = 0.01
        footprint = buffer_unbuffer_geometry(buffer=one_cm, geometry=footprint)

        filtered_polygons = MultiPolygon(
            pol
            for pol in as_multipolygon(footprint).geoms
            if pol.area > self.MIN_POL_AREA
        )

        if not filtered_polygons.geoms:
            raise InvalidShapeException(
                "get_footprint_no_features cant generate a polygon."
            )
        if len(filtered_polygons.geoms) == 1:
            filtered_polygons = filtered_polygons.geoms[0]

        return ensure_geometry_validity(geometry=filtered_polygons)

    def get_windows_and_outdoor_doors(self, area: SimArea) -> Iterator[SimOpening]:
        for area_opening in self.areas_openings[area.id]:
            if area_opening.type is OpeningType.WINDOW:
                yield area_opening
            elif (
                area_opening.type is OpeningType.DOOR
                and area_opening in self.outdoor_doors
            ):
                yield area_opening

    def absolute_to_relative_coordinates(self):
        if self.is_in_relative_coordinates is not True:
            for separator in self.separators:
                separator.absolute_to_relative_coordinates(Point(0, 0))

            for space in self.spaces:
                space.absolute_to_relative_coordinates(Point(0, 0))
            self.is_in_relative_coordinates = True

    def get_spaces_union(
        self,
        spaces: Union[Set[SimSpace], Set[SimArea]],
        public_space: bool,
        clip_to: Optional[Union[Polygon, MultiPolygon]] = None,
    ) -> Union[Polygon, MultiPolygon]:
        """
        1. Apply generic buffer on the union
        2. if its not public spaces, a buffer is iteratively added until the spaces forming 1 polygon(max 20 iterations)

        Motivation:
        We buffer all spaces such that they build 1 polygon. This is necessary as we use this union
         later to cut separators to a unit.
        If there would be a gap between spaces only parts of the wall filling this gap would be
        copied over to the apartment.
        """
        union_spaces = unary_union(
            self._footprints_buffered_n_rounded_for_union(
                sim_elements=spaces, buffer=THICKEST_WALL_POSSIBLE_IN_M
            )
        )
        if public_space:
            union_spaces = ensure_geometry_validity(geometry=union_spaces)
            return union_spaces

        for _i in range(0, 20):
            if isinstance(union_spaces, Polygon):
                break
            union_spaces = union_spaces.buffer(
                distance=0.1,
                resolution=1,
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            )

        if clip_to:
            clip_to = buffer_unbuffer_geometry(geometry=clip_to)
            union_spaces = union_spaces.intersection(clip_to)

        # Sometimes could not be valid, so we see if it is due to internal artifacts
        union_spaces = ensure_geometry_validity(geometry=union_spaces)
        return union_spaces

    def to_lat_lon_json(
        self, from_region: REGION
    ) -> Dict[str, Dict[str, List[Dict[str, Dict[str, Dict]]]]]:
        layout_serialized: Dict[str, Dict[str, List[Dict[str, Dict[str, Dict]]]]] = {}
        for key, accepted_sub_types in self.simple_brooks_to_serialize.items():
            layout_serialized[key] = defaultdict(list)
            filtered_valid_items = [
                item for item in getattr(self, key) if item.type in accepted_sub_types
            ]

            pygeos_geometries = from_shapely(
                [item.footprint for item in filtered_valid_items]
            )
            projected_lines = pygeos_project(
                geometries=pygeos_geometries,
                crs_from=from_region,
                crs_to=REGION.LAT_LON,
                include_z=False,
            )
            geojson_projected_items = to_geojson(projected_lines)
            for item, geojson_projected_item in zip(
                filtered_valid_items, geojson_projected_items
            ):
                layout_serialized[key][item.type.name].append(
                    {"geometry": json.loads(geojson_projected_item)}
                )

        return layout_serialized

    # SCALING & GEOREFERENCING
    def apply_georef(self, georeferencing_transformation):
        if self.footprint:
            delattr(self, "footprint")

    def apply_georef_transformation(self, georeferencing_transformation) -> SimLayout:
        def _apply_georef_transformation(
            obj: Union[
                SimLayout,
                SimSpace,
                SimArea,
                SimSeparator,
                SimOpening,
                SimFeature,
            ],
            georeferencing_transformation,
        ):
            # Apply georeferencing transformation on children first
            if isinstance(obj, (SimLayout, SimSpace, SimArea, SimSeparator)):
                for child in obj.children:
                    _apply_georef_transformation(
                        obj=child,
                        georeferencing_transformation=georeferencing_transformation,
                    )
            obj.apply_georef(
                georeferencing_transformation=georeferencing_transformation
            )

        _apply_georef_transformation(
            obj=self, georeferencing_transformation=georeferencing_transformation
        )
        return self

    def stair_area_no_overlap(
        self, selected_areas: Optional[Set[SimArea]] = None
    ) -> float:
        whitelisted_areas = selected_areas if selected_areas is not None else self.areas
        stair_features_in_areas = {
            f.id
            for area in whitelisted_areas
            for f in area.features
            if f.type == FeatureType.STAIRS
        }
        stairs = unary_union(
            [
                f.footprint
                for f in self.features
                if f.type == FeatureType.STAIRS and f.id in stair_features_in_areas
            ]
        )

        walls = unary_union(
            [w.footprint for w in self.separators if w.type == SeparatorType.WALL]
        )
        return stairs.difference(walls).area

    def plot(self, plot_errors: bool = False):
        from brooks.visualization.debug.visualisation import draw

        geometries = [
            element.footprint
            for element in chain(
                self.areas, self.separators, self.openings, self.features
            )
        ]
        if plot_errors:
            geometries += [error.position for error in self.errors]
        draw(geometries=geometries)

    @property
    def gross_area(self) -> float:
        """Including walls"""
        return (
            sum([area.footprint.area for area in self.areas])
            + sum([separator.footprint.area for separator in self.separators])
            + sum([opening.footprint.area for opening in self.openings])
        )

    def spaces_next_to_toilet_space(
        self,
    ) -> Set[str]:
        """
        returns ids of all spaces having a neighbour space with a toilet feature
        """
        from brooks import SpaceConnector

        spaces_by_id = {space.id: space for space in self.spaces}

        space_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=self.doors,
            spaces_or_areas=self.spaces,
        )

        return {
            space.id
            for space in self.spaces
            if any(
                (
                    spaces_by_id[[value for value in connection.values()][0]].has_toilet
                    for connection in space_connections.get(space.id, [])
                )
            )
        }

    @classmethod
    def get_polygon_of_spaces_and_doors(
        cls, layout: SimLayout, clipping_buffer: float = 0.5, extra_buffer: float = 0.5
    ) -> Polygon:
        """Temporarily placed here to be used for the PNG generator, it returns a buffered polygon including all
        the areas of the layout given"""
        doors = [
            opening.footprint
            for opening in layout.openings
            if opening.type in {OpeningType.DOOR, OpeningType.ENTRANCE_DOOR}
        ]
        spaces = [space.footprint for space in layout.spaces]

        clipping_geometries = unary_union(spaces + doors)
        if clipping_buffer or extra_buffer:
            clipping_geometries = cls.buffer_and_erode_polygon(
                pol=clipping_geometries,
                clipping_buffer=clipping_buffer,
                extra_buffer=extra_buffer,
            )
        if not isinstance(clipping_geometries, Polygon):
            raise FeaturesGenerationException(
                f"Clipping using multiple connected areas for an apartment: {wkt.dumps(clipping_geometries)}"
            )

        return clipping_geometries

    @staticmethod
    def buffer_and_erode_polygon(pol, clipping_buffer, extra_buffer):
        pol = unary_union(  # Avoid internal artifacts
            pol.buffer(
                clipping_buffer + extra_buffer,
                cap_style=CAP_STYLE.square,
                join_style=JOIN_STYLE.mitre,
                mitre_limit=2,
            )
        )

        return pol.buffer(
            -extra_buffer,  # Erosion
            cap_style=CAP_STYLE.square,
            join_style=JOIN_STYLE.mitre,
            mitre_limit=2,
        )

    @staticmethod
    def find_area_intersecting_feature(pygeos_areas: List, feature: SimFeature) -> int:
        areas_intersecting = intersects(
            from_shapely(feature.footprint),
            pygeos_areas,
        )
        num_areas_intersecting = areas_intersecting.sum()
        if num_areas_intersecting == 1:
            return areas_intersecting.nonzero()[0][0]
        elif num_areas_intersecting > 1:
            msg = (
                f"Feature {feature.type} at {feature.footprint.centroid} could not be assigned exclusively to an area. "
                f"{num_areas_intersecting} intersecting areas."
            )
        else:
            msg = f"Feature {feature.type} at {feature.footprint.centroid} could not be assigned to any area. "
        raise CorruptedAnnotationException(msg)

    def assign_features_to_areas(self):
        areas_list = list(self.areas)
        pygeos_areas = from_shapely([x.footprint for x in areas_list])
        for feature in self.all_processed_features:
            try:
                intersecting_index = self.find_area_intersecting_feature(
                    feature=feature, pygeos_areas=pygeos_areas
                )
                areas_list[intersecting_index].features.update({feature})
            except CorruptedAnnotationException as e:
                logger.debug(e)

    def set_area_types_based_on_feature_types(self):
        """Set area types using the features lying in this area"""
        for area in self.areas:
            if area.type == AreaType.NOT_DEFINED:
                area_type = self._from_feature_types_to_area_types(
                    feature_types={feature.type for feature in area.features}
                )
                area._type = area_type

    def _from_feature_types_to_area_types(self, feature_types: Set[Enum]) -> AreaType:
        if FeatureType.ELEVATOR in feature_types:
            return self.classification_scheme.DEFAULT_ELEVATOR_AREA

        if (
            FeatureType.TOILET in feature_types
            or FeatureType.BATHTUB in feature_types
            or FeatureType.SHOWER in feature_types
            or FeatureType.SINK in feature_types
        ):
            return self.classification_scheme.DEFAULT_WATER_CONNECTION_AREA

        if FeatureType.SHAFT in feature_types:
            return self.classification_scheme.DEFAULT_SHAFT_AREA

        if FeatureType.STAIRS in feature_types:
            return self.classification_scheme.DEFAULT_STAIR_AREA

        return AreaType.NOT_DEFINED

    def post_process_shafts_to_cover_area_footprint(self):
        """To be deprecated once the shafts are only an area in the new editor and not a feature"""
        for area in self.areas:
            shaft_features = {
                feature
                for feature in area.features
                if feature.type == FeatureType.SHAFT
            }
            for shaft in shaft_features:
                shaft.footprint = Polygon(area.footprint)


class PotentialSimLayout(SimLayout):
    @staticmethod
    def _add_space_to_layout(footprint: Polygon, unit_layout: SimLayout):
        space = SimSpace(
            footprint=footprint,
            height=get_default_element_height_range(
                "GENERIC_SPACE_HEIGHT", default=unit_layout.default_element_heights
            ),
        )
        area = SimArea(
            footprint=footprint,
            area_type=AreaType.ROOM,
            height=get_default_element_height_range(
                "GENERIC_SPACE_HEIGHT", default=unit_layout.default_element_heights
            ),
        )
        space.add_area(area)
        unit_layout.add_spaces({space})


class PotentialLayoutWithWindows(PotentialSimLayout):
    def __init__(self, floor_number: int, footprint: Polygon):
        super(PotentialLayoutWithWindows, self).__init__(floor_number=floor_number)
        geom = self._get_outer_footprint_and_add_inner_walls(
            footprint=footprint, unit_layout=self
        )
        self._add_perimeter_windows_and_walls(footprint=geom, unit_layout=self)
        self._add_space_to_layout(footprint=geom, unit_layout=self)

    def _add_windows(self, walls: Set[SimSeparator]) -> Set[SimSeparator]:
        from brooks.types import OpeningType

        for wall in walls:
            # windows take 100% of the wall
            wall.add_opening(
                opening=SimOpening(
                    footprint=wall.footprint,
                    opening_type=OpeningType.WINDOW,
                    height=get_default_element_height_range(
                        element_type=OpeningType.WINDOW,
                        default=self.default_element_heights,
                    ),
                    separator=wall,
                    separator_reference_line=get_center_line_from_rectangle(
                        polygon=wall.footprint
                    )[0],
                )
            )
        return walls

    def _create_wall_from_linestring(self, linestring: LineString) -> SimSeparator:
        wall_footprint = linestring.buffer(
            0.1,
            cap_style=CAP_STYLE.flat,
            join_style=JOIN_STYLE.mitre,
            mitre_limit=2,
        )
        return SimSeparator(
            footprint=wall_footprint,
            separator_type=SeparatorType.WALL,
            height=get_default_element_height_range(
                element_type=SeparatorType.WALL, default=self.default_element_heights
            ),
        )

    def _get_outer_footprint_and_add_inner_walls(
        self, footprint: Polygon, unit_layout: SimLayout
    ):
        _wall_offset = -4.0  # meters
        space_footprint = Polygon(footprint.exterior.coords)
        inner_wall_footprint = space_footprint.buffer(
            _wall_offset, cap_style=CAP_STYLE.square, join_style=JOIN_STYLE.mitre
        )
        if inner_wall_footprint.area > 0.0:
            unit_layout.separators.add(
                SimSeparator(
                    footprint=inner_wall_footprint,
                    separator_type=SeparatorType.WALL,
                    height=get_default_element_height_range(
                        element_type=SeparatorType.WALL,
                        default=self.default_element_heights,
                    ),
                )
            )

        return ensure_geometry_validity(
            footprint.difference(inner_wall_footprint), force_single_polygon=True
        )

    def _add_perimeter_windows_and_walls(
        self, footprint: Polygon, unit_layout: SimLayout
    ):
        walls = self._add_windows(
            walls={
                self._create_wall_from_linestring(LineString([point_a, point_b]))
                for point_a, point_b in pairwise(footprint.exterior.coords[:])
            }
        )
        unit_layout.add_separators(separators=walls)
