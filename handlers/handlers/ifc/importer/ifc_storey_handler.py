import math
from collections import defaultdict
from io import BytesIO
from typing import Dict, Optional, Union

from methodtools import lru_cache
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from brooks.types import OpeningType, SeparatorType
from brooks.util.geometry_ops import ensure_geometry_validity
from brooks.util.projections import project_geometry
from brooks.utils import (
    get_default_element_height,
    get_default_element_lower_edge,
    get_default_element_upper_edge,
)
from common_utils.constants import REGION
from common_utils.exceptions import IfcEmptyStoreyException
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from handlers.editor_v2.schema import ReactPlannerName
from handlers.ifc.constants import IFC_ELEMENTS_TO_IGNORE, PIXELS_PER_METER
from handlers.ifc.importer.ifc_floor_plan_plot import IfcFloorPlanPlot
from handlers.ifc.importer.ifc_react_mappings import (
    get_ifc_entity_supertype_and_planner_type,
)
from ifc_reader.constants import IFC_SPACE, SUPPORTED_IFC_TYPES
from ifc_reader.reader import IfcReader
from ifc_reader.types import Ifc2DEntity, IfcSpaceProcessed


class IfcStoreyHandler:
    def __init__(self, ifc_reader: IfcReader):
        self.ifc_reader = ifc_reader

    @lru_cache()
    def get_storey_entities_by_ifc_type(
        self, storey_id: int
    ) -> dict[str, list[Ifc2DEntity | IfcSpaceProcessed]]:
        """
        Generates a unique structured dictionary with all the different types supported by the editor or required
        to generate additional information, such as the spaces for the background image.

        If the ifc element contains sub-elements, those are already unrolled and returned as part of the ifc
        type category.

        Elevator are not part of the storeys so an additional lookup in the file is required.
        """
        geometries_by_type = defaultdict(list)
        for ifc_element in self.ifc_reader.storey_elements(storey_id=storey_id):
            if ifc_element.is_a() in IFC_ELEMENTS_TO_IGNORE:
                continue

            ifc_2d_entity = self.group_geometries_of_ifc_sub_elements(ifc_element)
            if ifc_2d_entity:
                geometries_by_type[ifc_element.is_a()].append(ifc_2d_entity)

        for ifc_elevator in self.ifc_reader.get_elevators():
            ifc_2d_entity = self.group_geometries_of_ifc_sub_elements(ifc_elevator)
            if ifc_2d_entity:
                geometries_by_type[ifc_elevator.is_a()].append(ifc_2d_entity)

        for ifc_space in self.ifc_reader.get_space_geometry_and_properties_by_storey_id[
            storey_id
        ]:
            geometries_by_type[IFC_SPACE].append(ifc_space)

        return {
            ifc_type: geometries_by_type.get(ifc_type, [])
            for ifc_type in SUPPORTED_IFC_TYPES
            if ifc_type in geometries_by_type or ifc_type == IFC_SPACE
        }

    def group_geometries_of_ifc_sub_elements(
        self, ifc_element
    ) -> Optional[Ifc2DEntity]:
        """This grouping of ifc sub elements generally result in better results for the editor.
        But it is highly correlated with the bad quality of the IFCs imported"""
        ifc_element_metadata: Dict = self.ifc_reader.get_all_properties(
            ifc_element=ifc_element
        )
        ifc_2d_entities = list(
            self.ifc_reader.ifc_2d_sub_entities_from_element(element=ifc_element)
        )
        if not ifc_2d_entities:
            return None
        geometries = [ifc_2d_entity.geometry for ifc_2d_entity in ifc_2d_entities]
        min_height = min(
            [ifc_2d_entity.min_height for ifc_2d_entity in ifc_2d_entities]
        )
        max_height = max(
            [ifc_2d_entity.max_height for ifc_2d_entity in ifc_2d_entities]
        )
        return Ifc2DEntity(
            geometry=as_multipolygon(unary_union(geometries)),
            ifc_type=ifc_element.is_a(),
            properties=ifc_element_metadata["properties"],
            quantities=ifc_element_metadata["quantities"],
            related=ifc_element_metadata["related"],
            min_height=min_height,
            max_height=max_height,
        )

    def storey_georeference_data(self, storey_id: int, region: REGION):
        """
        georef_scale: Inverse of applied scaling to pixel for the editor
        georef x & y: We need to inverse the editor translation
        """
        editor_translation = self.storey_translation(storey_id=storey_id)
        metric_reference_point = project_geometry(
            geometry=self.ifc_reader.reference_point,
            crs_from=REGION.LAT_LON,
            crs_to=region,
        )

        metric_translation = Point(
            metric_reference_point.x - editor_translation.x,
            metric_reference_point.y - editor_translation.y,
        )
        lat_lon_translation = project_geometry(
            geometry=metric_translation, crs_from=region, crs_to=REGION.LAT_LON
        )

        return {
            "georef_scale": 1 / PIXELS_PER_METER**2,
            "georef_rot_x": float(self.ifc_reader.georef_rotation[0].x),
            "georef_rot_y": float(self.ifc_reader.georef_rotation[0].y),
            "georef_rot_angle": self.ifc_reader.georef_rotation[1],
            "georef_x": lat_lon_translation.x,
            "georef_y": lat_lon_translation.y,
        }

    def storey_translation(self, storey_id: int) -> Point:
        """
        Translation to ensure that all geometries of the storey are inside the
        4 quadrant of the coordinate system. This is necessary in order for the
        editor to display correctly.



                         |
                 2       |       1
                         |
                         |      (xmin,ymax)---|
        -----------------(0,0)--|-------------|----
                         |      |    geom     |
                         |      |-------------|
                3        |        4
                         |
                         |
        """
        xmin, _, _, ymax = self.storey_footprint(storey_id=storey_id).bounds
        return Point(-xmin, -ymax)

    @lru_cache()
    def storey_footprint(self, storey_id: int) -> Union[Polygon, MultiPolygon]:
        storey_footprint = unary_union(
            [
                entity.geometry
                for items_by_ifc_type in self.get_storey_entities_by_ifc_type(
                    storey_id=storey_id
                ).values()
                for entity in items_by_ifc_type
            ]
        )
        storey_footprint = ensure_geometry_validity(geometry=storey_footprint)
        if storey_footprint.is_empty:
            raise IfcEmptyStoreyException(
                f"ifc storey with id {storey_id} doesn't contain any elements"
            )

        return storey_footprint

    def storey_figure(
        self,
        building_id: str,
        storey_id: int,
        image_height: Optional[float] = None,
        image_width: Optional[float] = None,
        scale_factor: Optional[float] = None,
    ) -> BytesIO:
        logger.debug(
            f"Generating IFC image for building: {building_id} and storey: {storey_id}"
        )
        storey_entities = self.get_storey_entities_by_ifc_type(storey_id=storey_id)
        if image_width is None or image_height is None or scale_factor is None:
            scale_factor = PIXELS_PER_METER
            images_sizes = self.storey_height_width_in_pixel(storey_id=storey_id)
            image_height = images_sizes["height"]
            image_width = images_sizes["width"]

        figure = IfcFloorPlanPlot(
            storey_entities=storey_entities,
            height=image_height,
            width=image_width,
        ).create_plot(scale_factor=scale_factor)
        output_stream = BytesIO()
        figure.savefig(output_stream, format="jpeg")
        output_stream.seek(0)
        logger.debug(
            f"Generated IFC image for building: {building_id} and storey: {storey_id}"
        )
        return output_stream

    def storey_height_width_in_pixel(self, storey_id: int) -> Dict[str, float]:
        xmin, ymin, xmax, ymax = self.storey_footprint(storey_id=storey_id).bounds

        image_height = abs(ymax - ymin) * PIXELS_PER_METER
        image_width = abs(xmax - xmin) * PIXELS_PER_METER
        return {
            "height": image_height,
            "width": image_width,
        }

    def get_relative_plan_heights(self, storey_id: int) -> Dict[str, float]:
        """Calculate the relative heights of each type of item, generally for the entire floor.
        The heights for doors and windows have to be always relative to the walls elevation.
        """
        max_height_by_planner_name: Dict[ReactPlannerName, float] = {}
        min_height_by_planner_name: Dict[ReactPlannerName, float] = {}
        for _, ifc_entities in self.get_storey_entities_by_ifc_type(
            storey_id=storey_id
        ).items():
            for ifc_entity in ifc_entities:
                _, planner_type = get_ifc_entity_supertype_and_planner_type(
                    ifc_entity=ifc_entity
                )
                if planner_type is None:
                    continue
                max_height_by_planner_name[planner_type] = max(
                    max_height_by_planner_name.get(planner_type, 0.0),
                    ifc_entity.max_height,
                )
                min_height_by_planner_name[planner_type] = min(
                    min_height_by_planner_name.get(planner_type, math.inf),
                    ifc_entity.min_height,
                )

        heights: Dict[str, float] = {
            "default_wall_height": get_default_element_height(SeparatorType.WALL),
            "default_door_height": get_default_element_height(OpeningType.DOOR),
            "default_window_lower_edge": get_default_element_lower_edge(
                OpeningType.WINDOW
            ),
            "default_window_upper_edge": get_default_element_upper_edge(
                OpeningType.WINDOW
            ),
            "default_ceiling_slab_height": get_default_element_height("CEILING_SLAB"),
        }

        db_column_to_annotation_type: Dict[str, ReactPlannerName] = {
            "default_door_height": ReactPlannerName.DOOR,
            "default_wall_height": ReactPlannerName.WALL,
        }
        for db_column, annotation_type in db_column_to_annotation_type.items():
            # For these items, the heights is the relative difference between the highest point and the lower
            max_height = max_height_by_planner_name.get(annotation_type)
            min_height = min_height_by_planner_name.get(annotation_type)
            if max_height is not None and min_height is not None:
                heights[db_column] = round(max_height - min_height, 2)

        window_min_height = min_height_by_planner_name.get(ReactPlannerName.WINDOW)
        window_max_height = max_height_by_planner_name.get(ReactPlannerName.WINDOW)
        if window_min_height is not None and window_max_height is not None:
            wall_min_height = min_height_by_planner_name[ReactPlannerName.WALL]
            # if the wall is below 0, we always need to use as a reference for the lower edge of the window,
            # the relative height with the wall
            heights["default_window_upper_edge"] = round(
                window_max_height - wall_min_height, 2
            )
            heights["default_window_lower_edge"] = round(
                window_min_height - wall_min_height, 2
            )

        return heights
