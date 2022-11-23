import math
from enum import Enum
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

import numpy as np
from matplotlib.axes import Axes
from matplotlib.patches import Patch
from matplotlib.patches import Polygon as PolygonPatch
from numpy import array
from shapely.affinity import rotate, scale, translate
from shapely.geometry import (
    CAP_STYLE,
    JOIN_STYLE,
    LineString,
    MultiLineString,
    MultiPolygon,
    Point,
    Polygon,
    box,
)
from shapely.ops import nearest_points, orient, unary_union

from brooks import SpaceConnector
from brooks.classifications import UnifiedClassificationScheme
from brooks.constants import (
    ITEM_SEPARATOR_INTERSECTING_THRESHOLD_IN_M2,
    ITEM_TO_SEPARATOR_SNAPPING_THRESHOLD_IN_M,
    THINNEST_WALL_POSSIBLE_IN_M,
    BathroomSubtype,
)
from brooks.models import SimArea, SimFeature, SimLayout, SimOpening, SimSeparator
from brooks.types import (
    AreaType,
    FeatureType,
    OpeningSubType,
    OpeningType,
    SeparatorType,
    SIACategory,
)
from brooks.util.geometry_ops import (
    buffer_unbuffer_geometry,
    dot_product_normalised_linestrings,
    ensure_geometry_validity,
)
from brooks.visualization.floorplans.assetmanager_style import (
    AssetManagerFloorOverviewStyle,
)
from brooks.visualization.floorplans.patches.collection import (
    RailingPatch,
    SeparatorPatch,
)
from brooks.visualization.utils import RECTANGLE_SIDE, ScaleRectangle, get_visual_center
from common_utils.constants import (
    LENGTH_SI_UNITS,
    SMALL_ROOM_SIZE,
    WALL_BUFFER_BY_SI_UNIT,
)
from common_utils.utils import pairwise
from dufresne.polygon.parameters_minimum_rotated_rectangle import (
    get_parameters_of_minimum_rotated_rectangle,
)
from dufresne.polygon.utils import as_multipolygon
from simulations.basic_features import CustomValuatorBasicFeatures2

from .dimension import DimensionIndicatorPatchCollection
from .door import DoorPatches
from .feature import (
    AreasEdgesPatch,
    AreasPatch,
    FeaturePatchCollection,
    GenericFeaturePatch,
    GenericPolygonFeaturePatch,
    StairArrowHeadPatch,
    StairArrowTailPatch,
)
from .orientation import OrientationPatchCollection
from .window import WindowCenterLinePatch, WindowPatch

_dimension_indicator_distance = 2
_dimension_indicator_length = 1


def _get_layout_separator_interior_lines(
    separators: Set[SimSeparator],
) -> MultiLineString:
    return MultiLineString(
        [
            LineString([point_a, point_b])
            for separator in separators
            for interior in separator.footprint.interiors
            for point_a, point_b in pairwise(interior.coords[:])
        ]
    )


def _are_lines_parallel(line_a: LineString, line_b: LineString) -> bool:
    """
    at the moment we only provide translation snapping and no rotation thats why we restrict it to parallel lines
    """
    angle = abs(dot_product_normalised_linestrings(line_a=line_a, line_b=line_b))
    return math.isclose(angle, 1, abs_tol=1e-3)


def _get_snapping_lines_from_separators(
    footprint: Polygon, separator_lines: MultiLineString
) -> List[Tuple[LineString, LineString]]:
    """
    As we assume that the item is rectangular we should only snap 1 of the parallel sides. This means we
    return here at max 2 snapping lines (to be more precise 2 pairs of feature_line - snapping_line)
    """

    feature_lines = [
        LineString(pair) for pair in pairwise(footprint.exterior.coords[:])
    ]

    parallel_lines_1 = [feature_lines[0], feature_lines[2]]
    parallel_lines_2 = [feature_lines[1], feature_lines[3]]

    final_snapping_candidates = []
    for parallel_lines in [parallel_lines_1, parallel_lines_2]:
        snapping_candidates = []
        for line in parallel_lines:
            for separator_line in separator_lines.geoms:
                if (
                    _are_lines_parallel(line, separator_line)
                    and snapping_line_bigger_or_almost_equal(
                        feature_line=line, snapping_line=separator_line
                    )
                    and line.centroid.distance(separator_line)
                    < ITEM_TO_SEPARATOR_SNAPPING_THRESHOLD_IN_M
                ):
                    snapping_candidates.append((separator_line, line))
        snapping_candidates = sorted(
            snapping_candidates, key=lambda lines: lines[0].distance(lines[1])
        )

        if snapping_candidates:
            final_snapping_candidates.append(snapping_candidates[0])

    return final_snapping_candidates


def snapping_line_bigger_or_almost_equal(
    feature_line: LineString, snapping_line: LineString
) -> bool:
    """
    This helps to avoid snapping to small irrelevant separator lines
    """
    threshold_as_fraction = 0.1
    return feature_line.length < snapping_line.length * (1 + threshold_as_fraction)


def _snap_items_to_walls(feature: SimFeature, separators: Set[SimSeparator]) -> Polygon:
    separator_lines = _get_layout_separator_interior_lines(separators=separators)
    footprint = feature.footprint
    if feature.type == FeatureType.SHAFT:
        return footprint  # shafts geoms are created from the area so no need to snap
    snapping_candidates = _get_snapping_lines_from_separators(
        footprint=footprint, separator_lines=separator_lines
    )
    for wall_line, feature_line in snapping_candidates:
        feature_center = feature_line.centroid
        wall_point = nearest_points(feature_center, wall_line)[1]

        # get the translation vector
        x_off, y_off = np.array(wall_point.xy) - np.array(feature_center.xy)
        # update the feature footprint, so it is 'snapped' to nearest wall
        translated_footprint = translate(footprint, xoff=x_off, yoff=y_off)
        if any(
            separator.footprint.intersection(translated_footprint).area
            > ITEM_SEPARATOR_INTERSECTING_THRESHOLD_IN_M2
            for separator in separators
        ):
            continue
        footprint = translated_footprint

    return footprint


def generate_feature_patches(
    layout: SimLayout,
    include_feature_types: Optional[Set[FeatureType]] = None,
) -> Iterator[Patch]:
    if not include_feature_types:
        include_feature_types = {feature_type for feature_type in FeatureType}

    features = sorted(
        [
            feature
            for feature in layout.features
            if feature.type in include_feature_types
        ],
        key=lambda f: f.footprint.area,
    )

    for feature in features:
        feature.footprint = _snap_items_to_walls(
            feature=feature, separators=layout.separators
        )
        if is_stair_and_has_direction_information(feature=feature):
            yield from generate_stair_patches(feature=feature)
        (x, y, dx, dy, angle,) = get_parameters_of_minimum_rotated_rectangle(
            polygon=feature.footprint,
            rotation_axis_convention="lower_left",
            return_annotation_convention=False,
        )
        yield from FeaturePatchCollection(
            xy=(x, y),
            length=dx,
            width=dy,
            angle=angle,
            feature_type=feature.type,
            feature_footprint=feature.footprint,
        ).get_patches()

    if FeatureType.KITCHEN in include_feature_types:
        yield from generate_kitchen_outline_feature_patches(layout=layout)


def is_stair_and_has_direction_information(feature: SimFeature) -> bool:
    """
    If stair feature has a direction property and its UP (UP/DOWN available) we
    draw the direction arrow
    """
    return (
        feature.type is FeatureType.STAIRS
        and "direction" in feature.feature_type_properties
    )


def _get_lims(layout):
    x0s = [area.footprint.bounds[0] for area in layout.areas]
    y0s = [area.footprint.bounds[1] for area in layout.areas]
    x1s = [area.footprint.bounds[2] for area in layout.areas]
    y1s = [area.footprint.bounds[3] for area in layout.areas]
    x0 = min(x0s)
    y0 = min(y0s)
    x1 = max(x1s)
    y1 = max(y1s)
    return x0, y0, x1, y1


def generate_kitchen_outline_feature_patches(layout: SimLayout):
    kitchen_unary_union = unary_union(
        [
            feature.footprint
            for feature in layout.features
            if feature.type == FeatureType.KITCHEN
        ]
    )

    for polygon in as_multipolygon(kitchen_unary_union).geoms:
        yield GenericPolygonFeaturePatch(
            polygon.exterior.coords, feature_type=FeatureType.KITCHEN
        )


def generate_stair_patches(feature: SimFeature):
    yield StairArrowHeadPatch(stair=feature)
    yield StairArrowTailPatch(stair=feature)


def generate_window_patch(
    opening: SimOpening, wall: SimSeparator
) -> Iterator[PolygonPatch]:
    if opening.geometry_new_editor:
        center_line_geometry = opening.geometry_new_editor
        opening_cropped = ScaleRectangle.round(
            rectangle=opening.geometry_new_editor.minimum_rotated_rectangle,
            applied_to=RECTANGLE_SIDE.BOTH_SIDE,
        )
    else:
        opening_cropped = wall.footprint.intersection(opening.footprint)
        if isinstance(opening_cropped, MultiPolygon):
            opening_cropped = buffer_unbuffer_geometry(
                geometry=opening_cropped,
                buffer=THINNEST_WALL_POSSIBLE_IN_M,
                reverse=True,
            )
        center_line_geometry = opening_cropped
        if len(center_line_geometry.exterior.coords[:]) > 5:
            center_line_geometry = center_line_geometry.minimum_rotated_rectangle

    yield WindowPatch(
        array(opening_cropped.exterior.coords),
        facecolor="white",
        edgecolor="black",
    )

    yield WindowCenterLinePatch(
        center_line_geometry,
        facecolor="none",
        edgecolor="black",
    )


def generate_wall_and_column_patches(layout: SimLayout) -> Iterator[SeparatorPatch]:
    for footprint in _generate_separator_footprints(
        layout=layout, separator_types={SeparatorType.WALL, SeparatorType.COLUMN}
    ):
        yield SeparatorPatch(polygon=orient(footprint))


def generate_railings_patches(layout: SimLayout) -> Iterator[RailingPatch]:
    for footprint in _generate_separator_footprints(
        layout=layout, separator_types={SeparatorType.RAILING}
    ):
        yield RailingPatch(polygon=orient(footprint))


def _generate_separator_footprints(
    layout: SimLayout, separator_types: Set[SeparatorType]
) -> List[Polygon]:
    footprints = MultiPolygon(
        [
            separator.footprint
            for separator in layout.separators
            if separator.type in separator_types
        ]
    )
    return sorted(footprints.geoms, key=lambda x: x.area)


def generate_door_patches(
    layout: SimLayout, unit_db_area_ids: Set[int]
) -> Iterator[Patch]:
    doors = {opening for opening in layout.openings if opening.is_door}
    door_areas_connected = SpaceConnector.get_connected_spaces_or_areas_per_door(
        doors=doors,
        spaces_or_areas=layout.areas,
    )
    public_area_ids = {area.db_area_id for area in layout.areas} - unit_db_area_ids

    for door in doors:
        connecting_areas = [
            area for area in layout.areas if area.id in door_areas_connected[door.id]
        ]
        yield from DoorPatches(
            door=ScaleRectangle.round(
                rectangle=door.geometry_new_editor.minimum_rotated_rectangle,
                applied_to=RECTANGLE_SIDE.BOTH_SIDE,
            )
            if door.geometry_new_editor
            else door.footprint,
            connecting_areas=connecting_areas,
            is_entrance=door.is_entrance,
            unit_db_area_ids=unit_db_area_ids,
            public_area_ids=public_area_ids,
            sweeping_points=door.sweeping_points,
            is_sliding=door.opening_sub_type == OpeningSubType.SLIDING,
        ).create_door_patches()


def generate_window_patches(layout: SimLayout) -> Iterator[PolygonPatch]:
    for wall in sorted(layout.walls, key=lambda x: x.footprint.area):
        for opening in sorted(wall.openings, key=lambda x: x.footprint.area):
            if opening.type is OpeningType.WINDOW:
                yield from generate_window_patch(opening=opening, wall=wall)


def generate_orientation_patches(angle_north: float, axis) -> Iterator[Patch]:
    xy = 0, 0
    arrow_length = 1

    add_N_symbol_to_compass(
        xy=xy, angle_north=angle_north, arrow_length=arrow_length, axis=axis
    )

    return OrientationPatchCollection(
        xy=xy, arrow_length=arrow_length, angle_north=angle_north
    ).get_patches()


def add_N_symbol_to_compass(xy: tuple, angle_north: float, arrow_length: float, axis):
    shift_from_center = rotate(
        geom=Point(arrow_length * 1.3, 0), angle=angle_north, origin=Point(0, 0)
    )

    axis.text(
        x=xy[0] + shift_from_center.x,
        y=xy[1] + shift_from_center.y,
        s="N",
        fontdict=AssetManagerFloorOverviewStyle.N_INDICATOR_FONT_STYLE,
        horizontalalignment="center",
        verticalalignment="center",
        rotation=-90 + angle_north,
    )


def generate_area_patches(
    layout: SimLayout,
) -> Iterator[AreasPatch]:
    areas = layout.areas
    for area in areas:
        if area.footprint.is_valid:
            if not (
                area.type in UnifiedClassificationScheme().AREA_TYPES_ACCEPTING_SHAFTS
                and area.type not in (AreaType.NOT_DEFINED, AreaType.VOID)
            ):
                polygon = area.footprint
                polygon = buffer_area_to_snap_to_walls(polygon=polygon)
                yield AreasPatch(polygon.exterior.coords)


def generate_layout_footprint_patches(
    layout: SimLayout,
) -> Iterator[AreasPatch]:
    spaces = layout.get_spaces_union(
        spaces=layout.spaces, public_space=False, clip_to=layout.footprint
    )

    if isinstance(spaces, MultiPolygon):
        spaces = sorted(spaces, key=lambda x: x.area)[
            -1
        ]  # This is a hack to remove artefacts from the union of spaces

    yield AreasPatch(spaces.exterior.coords)


def generate_sia_patches(
    layout: SimLayout,
    sia_category: SIACategory,
) -> Iterator[AreasPatch]:
    areas = CustomValuatorBasicFeatures2().get_areas_by_area_type_groups(
        layouts=[layout],
        groups={
            sia_category.name: set(
                UnifiedClassificationScheme().get_children(parent_type=sia_category)
            )
        },
    )[sia_category.name]
    for area in areas:
        if area.footprint.is_valid:
            polygon = area.footprint
            polygon = buffer_area_to_snap_to_walls(polygon=polygon)
            yield AreasPatch(polygon.exterior.coords)
            yield AreasEdgesPatch(polygon.exterior.coords)


def generate_dimension_patches(layout: SimLayout) -> Iterator[Patch]:
    x0, y0, x1, y1 = _get_lims(layout)

    horizontal = (x1, y0 - _dimension_indicator_distance, x1 - x0, 180)
    vertical = (x0 - _dimension_indicator_distance, y0, y1 - y0, 90)

    for x0, y0, l, a in [horizontal, vertical]:
        yield from DimensionIndicatorPatchCollection(
            (x0, y0), l, a, [0, 1], _dimension_indicator_length
        ).get_patches()


def generate_room_texts(
    layout: SimLayout,
    area_type_to_name: Dict[Enum, Any],
    axis: Axes,
    use_superscript_for_squaremeters: bool,
) -> Iterator[Tuple[float, float, str, float]]:
    """
    Yields:
        - Coordinate X for the text
        - Coordinate Y for the text
        - Content of the text
        - Angle
    """

    spaces_id_next_to_toilet = layout.spaces_next_to_toilet_space()

    for space in layout.spaces:
        for area in space.areas:
            if not area.footprint.is_valid:
                continue
            if area_type_to_name and not area_type_to_name.get(
                area.type
            ):  # if a name mapping is provided but the area type is not part of it, we don't display it
                continue

            footprint = footprint_without_features(axis=axis, area=area)

            if isinstance(footprint, MultiPolygon):
                footprint = max(footprint.geoms, key=lambda z: z.area)

            footprint = ensure_geometry_validity(geometry=footprint)
            # To generate consistent results we try to simplify the space geometry as it impacts the center result
            footprint = footprint.simplify(0.05, preserve_topology=True)
            footprint = ensure_geometry_validity(geometry=footprint)
            if footprint and footprint.area:
                visual_center = get_visual_center(footprint=footprint)

                area_name = (
                    apply_area_name_logic(
                        area=area,
                        area_type_to_name_mapping=area_type_to_name,
                        next_to_toilet=space.id in spaces_id_next_to_toilet,
                    )
                    if area_type_to_name
                    else area.type.name
                )
                area_size = round(number=area.footprint.area, ndigits=1)

                text_to_display = (
                    f"{area_name}\n{area_size:.1f} m$^2$"
                    if use_superscript_for_squaremeters
                    else f"{area_name}\n{area_size:.1f} m2"
                )
                yield (
                    visual_center.x,
                    visual_center.y,
                    text_to_display,
                    0,
                )


def footprint_without_features(axis: Axes, area: SimArea):
    obstacle_geometries = []
    for obstacle in axis.patches:
        if isinstance(obstacle, (GenericFeaturePatch, GenericPolygonFeaturePatch)):
            if obstacle.feature_type == FeatureType.ELEVATOR:
                continue
            transform = obstacle.get_patch_transform()
            obstacle_geometries.append(
                Polygon(transform.transform(obstacle.get_path().vertices))
            )

    return area.footprint.difference(unary_union(obstacle_geometries))


def apply_area_name_logic(
    area: SimArea,
    area_type_to_name_mapping: Dict[Enum, Any],
    next_to_toilet: bool,
) -> str:
    if area.type in (AreaType.BATHROOM, AreaType.STOREROOM) and {
        feature._type for feature in area.features
    } == {FeatureType.SINK}:
        if area.footprint.area < SMALL_ROOM_SIZE and next_to_toilet:
            return area_type_to_name_mapping[BathroomSubtype.WC]
        else:
            return area_type_to_name_mapping[BathroomSubtype.LAUNDRY]

    return area_type_to_name_mapping[
        bathroom_subtype(area=area) if area.type == AreaType.BATHROOM else area.type
    ]


def bathroom_subtype(area: SimArea) -> Enum:
    feature_to_subtype = {
        FeatureType.BATHTUB: AreaType.BATHROOM,
        FeatureType.SHOWER: BathroomSubtype.SHOWER,
        FeatureType.TOILET: BathroomSubtype.WC,
    }

    features_in_area = {feature._type for feature in area.features}
    for decisive_feature, subtype in feature_to_subtype.items():
        if decisive_feature in features_in_area:
            return subtype

    return area.type


def generate_dimension_texts(
    layout: SimLayout,
) -> Iterator[Tuple[float, float, str, float]]:
    """
    Yields:
        - Coordinate X for the text
        - Coordinate Y for the text
        - Content of the text
        - Angle
    """
    x0, y0, x1, y1 = _get_lims(layout)

    # horizontal
    yield (x0 + x1) / 2, y0 - _dimension_indicator_distance - 0.2, f"{x1 - x0:.1f}", 0

    # vertical
    yield x0 - _dimension_indicator_distance - 0.2, (y0 + y1) / 2, f"{y1 - y0:.1f}", 90


def buffer_area_to_snap_to_walls(polygon: Polygon) -> Polygon:
    """
    Remove gap between areas and walls. The gap is created in the space maker
    as we have to buffer the walls to ensure they are enclosed
    """
    return polygon.buffer(
        distance=WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE],
        cap_style=CAP_STYLE.square,
        join_style=JOIN_STYLE.mitre,
    )


class ScaleBarGenerator:
    def __init__(
        self,
        bar_segment_width: float = 1.0,
        bar_segment_height: float = 0.5,
        bar_y_shift: float = 1.0,
        text_y_shift: float = 0.1,
        text_fontsize: int = 8,
    ):
        self.bar_segment_width = bar_segment_width
        self.bar_segment_height = bar_segment_height
        self.bar_y_shift = bar_y_shift
        self.text_shift = text_y_shift
        self.text_fontsize = text_fontsize

    def add_scale_bar_to_axis(
        self, scale_bar_axis: Axes, reference_axis: Axes, add_texts: bool
    ):
        scale_bar_axis.set_xlim(0, 5)
        scale_bar_axis.set_ylim(0, 5)

        scale_factor = self.get_scale_factor_between_axis_x_direction(
            target_axis=scale_bar_axis, reference_axis=reference_axis
        )
        for patch in self._generate_bar_segment_patches(scale_x_direction=scale_factor):
            scale_bar_axis.add_patch(patch)

        if add_texts:
            self._add_texts_to_axis(
                scale_bar_axis=scale_bar_axis, scale_factor=scale_factor
            )
        return scale_factor

    def _generate_bar_segment_patches(
        self, scale_x_direction: float
    ) -> List[PolygonPatch]:
        class PatchSegmentType(Enum):
            SMALL_LOWER_LEFT = 1
            SMALL_LOWER_RIGHT = 2
            BIG_LOWER = 3
            SMALL_UPPER_LEFT = 4
            SMALL_UPPER_RIGHT = 5
            BIG_UPPER = 6

        patches = []
        polygons = []

        dx = self.bar_segment_width * scale_x_direction
        dy = self.bar_segment_height
        y_shift = self.bar_y_shift
        segment_template = box(0, y_shift, dx, y_shift + dy)
        for segment_type in PatchSegmentType:
            if segment_type in (PatchSegmentType.BIG_LOWER, PatchSegmentType.BIG_UPPER):
                polygon = scale(segment_template, xfact=2, origin=Point(0, 0))
            else:
                polygon = segment_template

            if segment_type in (
                PatchSegmentType.SMALL_LOWER_LEFT,
                PatchSegmentType.SMALL_LOWER_RIGHT,
                PatchSegmentType.BIG_LOWER,
            ):

                polygon = translate(
                    geom=polygon, xoff=(segment_type.value - 1) * dx, yoff=0
                )
            else:
                polygon = translate(
                    geom=polygon, xoff=(segment_type.value - 4) * dx, yoff=dy
                )

            polygons.append(polygon)
            patch = PolygonPatch(
                array(polygon.exterior.coords),
                facecolor="black" if segment_type.value % 2 == 0 else "white",
            )

            patches.append(patch)
        scale_bar_outline = PolygonPatch(
            array(unary_union(polygons).exterior.coords), fill=False
        )
        patches.append(scale_bar_outline)
        return patches

    def _add_texts_to_axis(self, scale_bar_axis: Axes, scale_factor: float):
        for i in (0, 1, 2, 4):
            scale_bar_axis.text(
                x=i * scale_factor * self.bar_segment_width,
                y=self.text_shift,
                s=str(i),
                fontsize=self.text_fontsize,
            )

    @staticmethod
    def get_scale_factor_between_axis_x_direction(
        target_axis: Axes, reference_axis: Axes
    ) -> float:
        reference_axis_width = reference_axis.properties()["position"].bounds[2]
        reference_axis_dx = abs(
            reference_axis.get_xlim()[1] - reference_axis.get_xlim()[0]
        )

        target_axis_width = target_axis.properties()["position"].bounds[2]
        target_axis_dx = abs(target_axis.get_xlim()[1] - target_axis.get_xlim()[0])

        return (reference_axis_width * target_axis_dx) / (
            reference_axis_dx * target_axis_width
        )
