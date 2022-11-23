from typing import Dict, Iterator

import numpy
from pygeos import area as pygeos_areas
from pygeos import from_shapely, intersection, intersects

from brooks import SpaceConnector
from brooks.models import SimLayout, SimOpening
from brooks.models.violation import SpatialEntityViolation, Violation, ViolationType
from brooks.types import FeatureType, OpeningType


class SimLayoutValidations:
    @classmethod
    def validate(cls, layout: SimLayout) -> Iterator[Violation]:
        for method in (
            cls.validate_door_connects_areas,
            cls.validate_accessible_spaces,
            cls.check_areas_not_overlap_with_multiple_spaces,
            cls.check_features_belong_to_area,
            cls.validate_opening_overlaps_only_one_separator,
            cls.validate_openings_overlap_openings,
        ):
            violations = list(method(layout=layout))
            yield from sorted(violations, key=lambda x: x.entity.footprint.area)

    @staticmethod
    def validate_door_connects_areas(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        doors_by_id: Dict[str, SimOpening] = {
            opening.id: opening for opening in layout.openings_by_type[OpeningType.DOOR]
        }
        # We use areas instead of spaces. See PR 1653, as we have a big space with different areas
        # which also have a door that connects them
        _, doors_not_connected = SpaceConnector().get_connected_spaces_using_doors(
            doors=layout.openings_by_type[OpeningType.DOOR],
            spaces_or_areas=layout.areas,
        )

        for door_id_not_connecting_spaces in doors_not_connected:
            yield SpatialEntityViolation(
                violation_type=ViolationType.DOOR_NOT_CONNECTING_AREAS,
                entity=doors_by_id[door_id_not_connecting_spaces],
            )

    @staticmethod
    def validate_accessible_spaces(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        for space in layout.spaces:
            space_contains_staircases = any(
                feature
                for area in space.areas
                for feature in area.features
                if feature.type is FeatureType.STAIRS
            )

            space_contains_elevator = any(
                feature
                for area in space.areas
                for feature in area.features
                if feature.type is FeatureType.ELEVATOR
            )

            space_contains_shaft = any(
                feature
                for area in space.areas
                for feature in area.features
                if feature.type is FeatureType.SHAFT
            )

            space_doors = {
                opening
                for opening in layout.spaces_openings[space.id]
                if opening.is_door
            }

            if (
                not space_doors
                and not space_contains_staircases
                and not space_contains_elevator
                and not space_contains_shaft
            ):
                yield SpatialEntityViolation(
                    violation_type=ViolationType.SPACE_NOT_ACCESSIBLE, entity=space
                )

    @staticmethod
    def check_areas_not_overlap_with_multiple_spaces(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        all_areas = {area for space in layout.spaces for area in space.areas}
        pygeos_spaces = from_shapely([space.footprint for space in layout.spaces])
        for area in all_areas:
            intersecting_spaces = intersects(
                from_shapely(area.footprint),
                pygeos_spaces,
            )
            if intersecting_spaces.sum() > 1:
                yield SpatialEntityViolation(
                    violation_type=ViolationType.AREA_OVERLAPS_MULTIPLE_SPACES,
                    entity=area,
                )

    @staticmethod
    def check_features_belong_to_area(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        pygeos_geometry_areas = from_shapely(
            [area.footprint for space in layout.spaces for area in space.areas]
        )
        for feature in layout.all_processed_features:
            intersecting_areas = intersects(
                from_shapely(feature.footprint),
                pygeos_geometry_areas,
            )
            if intersecting_areas.sum() != 1:
                yield SpatialEntityViolation(
                    violation_type=ViolationType.FEATURE_NOT_ASSIGNED, entity=feature
                )

    @staticmethod
    def validate_opening_overlaps_only_one_separator(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        """Meant to be used for the migrated plans from the old editor where this was not controlled"""
        all_separators = from_shapely([sep.footprint for sep in layout.separators])
        for opening in sorted(layout.openings, key=lambda x: x.footprint.area):
            opening_footprint_pygeos = from_shapely(opening.footprint)
            separators_intersecting = intersects(
                opening_footprint_pygeos,
                all_separators,
            )
            separators_intersections = intersection(
                [
                    all_separators[index]
                    for index in separators_intersecting.nonzero()[0]
                ],
                opening_footprint_pygeos,
            )
            area_intersections = pygeos_areas(separators_intersections)
            if len(numpy.where(area_intersections > 0.01)[0]) > 1:
                yield SpatialEntityViolation(
                    violation_type=ViolationType.OPENING_OVERLAPS_MULTIPLE_WALLS,
                    entity=opening,
                )

    @staticmethod
    def validate_openings_overlap_openings(
        layout: SimLayout,
    ) -> Iterator[SpatialEntityViolation]:
        openings_list = list(layout.openings)
        all_openings_pygeos = from_shapely([x.footprint for x in openings_list])
        for current_index, opening in enumerate(openings_list):
            current_opening = all_openings_pygeos[current_index]
            openings_intersecting = intersects(
                current_opening,
                all_openings_pygeos,
            )
            area_intersections = pygeos_areas(
                intersection(
                    [
                        all_openings_pygeos[index]
                        for index in openings_intersecting.nonzero()[0]
                        if index != current_index
                    ],
                    current_opening,
                )
            )
            # We have to discard the self intersection, for optimization purposes all the openings are always compared
            indexes_intersecting = numpy.where(area_intersections > 0.01)[0]
            if len(indexes_intersecting):
                yield SpatialEntityViolation(
                    violation_type=ViolationType.OPENING_OVERLAPS_ANOTHER_OPENING,
                    entity=opening,
                )
