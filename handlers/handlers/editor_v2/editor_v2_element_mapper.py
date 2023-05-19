from collections import defaultdict
from typing import (
    DefaultDict,
    Dict,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Union,
    ValuesView,
)

from shapely.affinity import rotate
from shapely.geometry import LineString, MultiPolygon, Point, Polygon

from brooks import SpaceMaker
from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import (
    AreaType,
    FeatureType,
    OpeningSubType,
    OpeningType,
    SeparatorType,
)
from brooks.utils import get_default_element_height_range
from common_utils.constants import LENGTH_SI_UNITS, WALL_BUFFER_BY_SI_UNIT
from common_utils.exceptions import CorruptedAnnotationException
from common_utils.logger import logger
from dufresne.polygon.utils import get_biggest_polygon
from handlers.editor_v2.schema import (
    ReactPlannerArea,
    ReactPlannerData,
    ReactPlannerDoorSweepingPoints,
    ReactPlannerHole,
    ReactPlannerItem,
    ReactPlannerLine,
    ReactPlannerType,
)
from handlers.editor_v2.utils import (
    pixels_to_meters_scale,
    update_planner_element_coordinates,
)
from handlers.editor_v2.wall_postprocessor import ReactPlannerPostprocessor

_DEFAULT_SEPARATOR_TYPES = (
    SeparatorType.WALL,
    SeparatorType.COLUMN,
    SeparatorType.RAILING,
)


class ReactPlannerToBrooksMapper:

    REACT_PLANNER_TYPE_TO_FEATURES_MAP: Dict[ReactPlannerType, FeatureType] = {
        ReactPlannerType.KITCHEN: FeatureType.KITCHEN,
        ReactPlannerType.SEAT: FeatureType.SEAT,
        ReactPlannerType.SHOWER: FeatureType.SHOWER,
        ReactPlannerType.STAIRS: FeatureType.STAIRS,
        ReactPlannerType.TOILET: FeatureType.TOILET,
        ReactPlannerType.CAR_PARKING: FeatureType.CAR_PARKING,
        ReactPlannerType.ELEVATOR: FeatureType.ELEVATOR,
        ReactPlannerType.BATHTUB: FeatureType.BATHTUB,
        ReactPlannerType.RAMP: FeatureType.RAMP,
        ReactPlannerType.SINK: FeatureType.SINK,
        ReactPlannerType.BUILT_IN_FURNITURE: FeatureType.BUILT_IN_FURNITURE,
        ReactPlannerType.BIKE_PARKING: FeatureType.BIKE_PARKING,
        ReactPlannerType.SHAFT: FeatureType.SHAFT,
        ReactPlannerType.WASHING_MACHINE: FeatureType.WASHING_MACHINE,
        ReactPlannerType.OFFICE_DESK: FeatureType.OFFICE_DESK,
    }
    REACT_PLANNER_TYPE_TO_OPENING_MAP: Dict[ReactPlannerType, OpeningType] = {
        ReactPlannerType.WINDOW: OpeningType.WINDOW,
        ReactPlannerType.DOOR: OpeningType.DOOR,
        ReactPlannerType.SLIDING_DOOR: OpeningType.DOOR,
        ReactPlannerType.ENTRANCE_DOOR: OpeningType.ENTRANCE_DOOR,
    }
    REACT_PLANNER_TYPE_TO_SEPARATOR_MAP: Dict[ReactPlannerType, SeparatorType] = {
        ReactPlannerType.WALL: SeparatorType.WALL,
        ReactPlannerType.AREA_SPLITTER: SeparatorType.AREA_SPLITTER,
        ReactPlannerType.COLUMN: SeparatorType.COLUMN,
        ReactPlannerType.RAILING: SeparatorType.RAILING,
    }

    @staticmethod
    def get_element_polygon(
        element: Union[ReactPlannerLine, ReactPlannerHole],
    ) -> Polygon:
        try:
            if len(element.coordinates) > 1:
                return Polygon(
                    shell=element.coordinates[0], holes=element.coordinates[1:]
                )
            return Polygon(shell=element.coordinates[0])
        except (IndexError, ValueError):
            # if there are missing coordinates or the polygon is incorrect
            raise CorruptedAnnotationException(
                f"Line has no coordinates or doesn't have valid coordinates: {element.coordinates}"
            )

    @classmethod
    def get_layout(
        cls,
        planner_elements: ReactPlannerData,
        scaled: bool = True,
        post_processed: bool = False,
        set_area_types_by_features: bool = True,
        default_element_heights: Optional[Dict] = None,
        set_area_types_from_react_areas: bool = False,
    ) -> SimLayout:
        """WARNING: this process modifies the planner elements data structure,
        scaling the coordinates"""
        update_planner_element_coordinates(data=planner_elements, scaled=scaled)

        (separators, separators_by_id,) = cls.get_separators(
            planner_elements=planner_elements,
            post_processed=post_processed,
            default_element_heights=default_element_heights,
        )

        _: Set[SimOpening] = cls._create_n_assign_opening_to_separators(
            planner_elements=planner_elements,
            separators_by_id=separators_by_id,
            post_processed=post_processed,
            default_element_heights=default_element_heights,
        )
        features: Set[SimFeature] = cls._get_features_from_items(
            planner_elements=planner_elements,
            default_element_heights=default_element_heights,
        )
        area_splitters: Set[SimSeparator] = cls._get_separators_from_lines(
            planner_elements=planner_elements,
            separator_whitelist=(SeparatorType.AREA_SPLITTER,),
            default_element_heights=default_element_heights,
        )

        spaces: Set[SimSpace] = cls._get_spaces_from_areas(
            separators=separators,
            area_splitters=area_splitters,
            wall_buffer=cls.get_wall_buffer_size(
                scale=planner_elements.scale, scaled=scaled
            ),
            default_element_heights=default_element_heights,
        )
        scale_factor = pixels_to_meters_scale(scale=planner_elements.scale)
        layout = SimLayout(
            spaces=spaces,
            separators=separators,
            scale_factor=scale_factor if scaled else 1.0,
            default_element_heights=default_element_heights,
        )
        layout.all_processed_features = features
        layout.assign_features_to_areas()
        if set_area_types_by_features:
            layout.set_area_types_based_on_feature_types()

        if set_area_types_from_react_areas:
            cls._set_area_types_from_react_areas(
                layout.areas, planner_elements.layers["layer-1"].areas.values()
            )

        layout.post_process_shafts_to_cover_area_footprint()

        return layout

    @classmethod
    def get_wall_buffer_size(cls, scale: float, scaled: bool):
        return (
            WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE]
            if scaled
            else WALL_BUFFER_BY_SI_UNIT[LENGTH_SI_UNITS.METRE]
            / pixels_to_meters_scale(scale=scale)
        )

    @classmethod
    def get_separators(
        cls,
        planner_elements: ReactPlannerData,
        post_processed: bool,
        default_element_heights: Optional[Dict] = None,
    ) -> Tuple[Set[SimSeparator], Dict[str, SimSeparator]]:

        if post_processed:
            return cls._get_post_processed_separators(
                planner_elements=planner_elements,
                default_element_heights=default_element_heights,
            )
        else:
            separators = cls._get_separators_from_lines(
                planner_elements=planner_elements,
                default_element_heights=default_element_heights,
            )
            separators_by_id = {s.id: s for s in separators}
            return (
                separators,
                separators_by_id,
            )

    @classmethod
    def _get_post_processed_separators(
        cls,
        planner_elements: ReactPlannerData,
        default_element_heights: Optional[Dict] = None,
    ) -> Tuple[Set[SimSeparator], Dict[str, SimSeparator]]:
        """Currently only used to generate beautified DXF files"""
        separators: Set[SimSeparator] = set()
        polygon_and_line_ids_by_separator_type = ReactPlannerPostprocessor(
            data=planner_elements
        ).process()
        separators_by_id = {}
        for separator_type, (
            polygons,
            line_ids,
        ) in polygon_and_line_ids_by_separator_type.items():
            for polygon, pol_line_ids in zip(polygons, line_ids):
                separator = SimSeparator(
                    footprint=polygon,
                    separator_type=separator_type,
                    height=get_default_element_height_range(
                        element_type=separator_type, default=default_element_heights
                    ),
                )
                separators.add(separator)
                separators_by_id.update(
                    {line_id: separator for line_id in pol_line_ids}
                )
        return separators, separators_by_id

    @classmethod
    def get_original_separator_geometries(
        cls,
        planner_elements: ReactPlannerData,
        separator_whitelist: Iterable[SeparatorType] = _DEFAULT_SEPARATOR_TYPES,
    ) -> DefaultDict[SeparatorType, List[Polygon]]:
        geometries_by_separator_type = defaultdict(list)
        for separator_type in separator_whitelist:
            geometries_by_separator_type[separator_type] = [
                polygon
                for polygon in planner_elements.separator_polygons_by_id(
                    separator_type=separator_type
                ).values()
            ]

        return geometries_by_separator_type

    @classmethod
    def _get_separators_from_lines(
        cls,
        planner_elements: ReactPlannerData,
        separator_whitelist: Iterable[SeparatorType] = _DEFAULT_SEPARATOR_TYPES,
        default_element_heights: Optional[Dict] = None,
    ) -> Set[SimSeparator]:
        separators: Set[SimSeparator] = set()
        for layer in planner_elements.layers.values():
            for line in layer.lines.values():
                separator_type: SeparatorType = (
                    ReactPlannerToBrooksMapper.REACT_PLANNER_TYPE_TO_SEPARATOR_MAP[
                        ReactPlannerType(line.type)
                    ]
                )
                if separator_type not in separator_whitelist:
                    continue

                if polygon := cls.get_element_polygon(element=line):
                    separators.add(
                        SimSeparator(
                            separator_id=line.id,
                            separator_type=separator_type,
                            footprint=polygon,
                            height=get_default_element_height_range(
                                element_type=separator_type,
                                default=default_element_heights,
                            ),
                            reference_linestring=planner_elements.get_reference_linestring_of_separator(
                                line_id=line.id
                            ),
                            editor_properties=line.properties,
                        )
                    )

        return separators

    @classmethod
    def get_feature_from_item(
        cls,
        item: ReactPlannerItem,
        item_id: Optional[str] = None,
        default_element_heights: Optional[Dict] = None,
    ):
        half_width = item.properties.width.value / 2
        half_height = item.properties.length.value / 2
        feature_type = cls.REACT_PLANNER_TYPE_TO_FEATURES_MAP[
            ReactPlannerType(item.type)
        ]
        feature_type_properties = {}
        if feature_type == FeatureType.STAIRS:
            feature_type_properties["direction"] = item.properties.direction
        return SimFeature(
            feature_id=item_id,
            feature_type=feature_type,
            footprint=item.polygon,
            angle=item.rotation,
            dx=half_width,
            dy=half_height,
            feature_type_properties=feature_type_properties,
            height=get_default_element_height_range(
                element_type=feature_type, default=default_element_heights
            ),
        )

    @classmethod
    def _get_features_from_items(
        cls,
        planner_elements: ReactPlannerData,
        default_element_heights: Optional[Dict] = None,
    ) -> Set[SimFeature]:
        features: Set[SimFeature] = set()
        for layer in planner_elements.layers.values():
            for item_id, item in layer.items.items():
                features.add(
                    cls.get_feature_from_item(
                        item_id=item_id,
                        item=item,
                        default_element_heights=default_element_heights,
                    )
                )
        return features

    @staticmethod
    def _get_spaces_from_areas(
        separators: Set[SimSeparator],
        area_splitters: Set[SimSeparator],
        wall_buffer: Optional[float] = None,
        default_element_heights: Optional[Dict] = None,
    ) -> Set[SimSpace]:
        if separators:
            return SpaceMaker().create_spaces_and_areas(
                separators=separators,
                splitters=area_splitters,
                generic_space_height=get_default_element_height_range(
                    element_type="GENERIC_SPACE_HEIGHT", default=default_element_heights
                ),
                wall_buffer=wall_buffer,
            )
        return set()

    @classmethod
    def _create_n_assign_opening_to_separators(
        cls,
        planner_elements: ReactPlannerData,
        separators_by_id: Dict[str, SimSeparator],
        post_processed: bool,
        default_element_heights: Optional[Dict] = None,
    ) -> Set[SimOpening]:
        openings: Set[SimOpening] = set()
        for layer in planner_elements.layers.values():
            for hole in layer.holes.values():
                try:
                    opening = ReactPlannerOpeningMapper.get_opening(
                        hole=hole,
                        post_processed=post_processed,
                        separators_by_id=separators_by_id,
                        separator_reference_line=planner_elements.get_reference_linestring_of_separator(
                            line_id=hole.line
                        ),
                        default_element_heights=default_element_heights,
                    )
                    separators_by_id[hole.line].openings.add(opening)
                    openings.add(opening)
                except CorruptedAnnotationException:
                    logger.error(
                        "Opening discarded because the separator couldn't be created"
                    )
                    continue
        return openings

    @classmethod
    def _set_area_types_from_react_areas(
        cls, brooks_areas: Set[SimArea], react_areas: ValuesView[ReactPlannerArea]
    ):
        for react_area in react_areas:
            if not react_area.properties.areaType:
                continue
            representative_point = react_area.polygon.representative_point()
            for brooks_area in brooks_areas:
                if representative_point.within(brooks_area.footprint):
                    brooks_area._type = AreaType[react_area.properties.areaType]
                    break


class ReactPlannerOpeningMapper:

    _REACT_PLANNER_HOLE_TO_OPENING_MAP: Dict[ReactPlannerType, OpeningType] = {
        ReactPlannerType.WINDOW: OpeningType.WINDOW,
        ReactPlannerType.DOOR: OpeningType.DOOR,
        ReactPlannerType.ENTRANCE_DOOR: OpeningType.ENTRANCE_DOOR,
        ReactPlannerType.SLIDING_DOOR: OpeningType.DOOR,
    }

    _REACT_PLANNER_HOLE_TYPE_TO_PROPERTY_MAP: Dict[str, Dict[str, OpeningSubType]] = {
        ReactPlannerType.DOOR.value: {"opening_sub_type": OpeningSubType.DEFAULT},
        ReactPlannerType.ENTRANCE_DOOR.value: {
            "opening_sub_type": OpeningSubType.DEFAULT
        },
        ReactPlannerType.SLIDING_DOOR.value: {
            "opening_sub_type": OpeningSubType.SLIDING
        },
    }

    @staticmethod
    def post_process_opening(
        opening_polygon: Polygon, separator_post_processed: Polygon
    ) -> Polygon:
        """This is only needed so that the borders of the openings are matching exactly the wall when they are
         postprocessed due to problems with unary union in shapely.

        The width of the opening is extended 1 cm only in the direction of the wall thickness
        """
        opening_polygon_post_processed = separator_post_processed.intersection(
            opening_polygon
        )
        if opening_polygon_post_processed.area == 0.0:
            raise CorruptedAnnotationException(
                f"A postprocessed opening doesn't overlap with the separator at {opening_polygon.centroid}"
            )

        if isinstance(opening_polygon_post_processed, MultiPolygon):
            return get_biggest_polygon(opening_polygon_post_processed)
        return opening_polygon_post_processed

    @classmethod
    def get_opening(
        cls,
        hole: ReactPlannerHole,
        separators_by_id: Dict[str, SimSeparator],
        post_processed: bool,
        separator_reference_line: LineString,
        default_element_heights: Optional[Dict] = None,
    ) -> SimOpening:
        planner_type = ReactPlannerType(hole.type)
        if planner_type not in cls._REACT_PLANNER_HOLE_TO_OPENING_MAP:
            raise CorruptedAnnotationException(
                f"Requested mapping of type {hole.type} which is not recognized."
            )

        opening_type = cls._REACT_PLANNER_HOLE_TO_OPENING_MAP[
            ReactPlannerType(hole.type)
        ]
        default_opening_polygon = ReactPlannerToBrooksMapper.get_element_polygon(
            element=hole
        )
        opening_polygon_post_processed = default_opening_polygon
        if post_processed:
            opening_polygon_post_processed = cls.post_process_opening(
                opening_polygon=default_opening_polygon,
                separator_post_processed=separators_by_id[hole.line].footprint,
            )
        opening_properties: Dict = cls._REACT_PLANNER_HOLE_TYPE_TO_PROPERTY_MAP.get(
            hole.type, {}
        )
        opening = SimOpening(
            opening_id=hole.id,
            opening_type=opening_type,
            footprint=opening_polygon_post_processed,
            separator=separators_by_id[hole.line],
            separator_reference_line=separator_reference_line,
            height=cls._get_opening_heights(
                hole=hole,
                opening_type=opening_type,
                default_element_heights=default_element_heights,
            ),
            geometry_new_editor=default_opening_polygon,
            editor_properties=hole.properties,
            **opening_properties,
        )
        if hole.door_sweeping_points:
            opening.sweeping_points = [
                Point(hole.door_sweeping_points.angle_point),
                Point(hole.door_sweeping_points.closed_point),
                Point(hole.door_sweeping_points.opened_point),
            ]
        return opening

    @staticmethod
    def create_default_sweeping_points(
        opening_line: LineString,
    ) -> ReactPlannerDoorSweepingPoints:
        angle_point, closed_point = (opening_line.coords[0], opening_line.coords[1])

        perpendicular_opening_line = rotate(
            geom=opening_line,
            angle=90,
            origin=opening_line.coords[0],
        )
        dx = (
            perpendicular_opening_line.coords[1][0]
            - perpendicular_opening_line.coords[0][0]
        )
        dy = (
            perpendicular_opening_line.coords[1][1]
            - perpendicular_opening_line.coords[0][1]
        )
        opened_point = [angle_point[0] + dx, angle_point[1] + dy]
        return ReactPlannerDoorSweepingPoints(
            angle_point=angle_point,
            closed_point=closed_point,
            opened_point=opened_point,
        )

    @staticmethod
    def _get_opening_heights(
        hole: ReactPlannerHole,
        opening_type: OpeningType,
        default_element_heights: Optional[Dict],
    ) -> Tuple[float, float]:
        default_opening_heights = get_default_element_height_range(
            element_type=opening_type, default=default_element_heights
        )
        return (
            default_opening_heights[0]
            if hole.properties.heights.lower_edge is None
            else hole.properties.heights.lower_edge,
            default_opening_heights[1]
            if hole.properties.heights.upper_edge is None
            else hole.properties.heights.upper_edge,
        )
