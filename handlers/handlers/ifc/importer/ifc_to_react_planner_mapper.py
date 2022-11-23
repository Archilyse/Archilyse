from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple, Union

from shapely.affinity import scale, translate
from shapely.geometry import MultiPolygon, Point, Polygon
from shapely.ops import unary_union

from brooks.constants import SuperTypes
from brooks.types import AreaType
from brooks.util.geometry_ops import ensure_geometry_validity
from common_utils.logger import logger
from dufresne.polygon.utils import as_multipolygon
from handlers.editor_v2 import ReactPlannerElementFactory
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerLayer,
    ReactPlannerName,
)
from handlers.ifc.importer.ifc_react_mappings import (
    get_ifc_entity_supertype_and_planner_type,
)
from handlers.ifc.importer.ifc_reader_space_classifiers import (
    CUSTOM_CLASSIFICATION_BLACKLIST,
    IMPLENIA_PRE_CLASSIFICATION_MAP,
)
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from handlers.shapely_to_react.editor_ready_entity import (
    EditorReadyEntity,
    EntityProperties,
)
from ifc_reader.constants import IFC_SPACE
from ifc_reader.types import Ifc2DEntity, IfcSpaceProcessed


class IfcToReactPlannerMapper:
    _M_TO_CM_MULTIPLIER = 100
    _ELEMENT_HEIGHTS: Dict[ReactPlannerName, Tuple[float, float]] = {
        ReactPlannerName.WINDOW: (0.9, 2.50),
        ReactPlannerName.DOOR: (0.0, 2.00),
        ReactPlannerName.SLIDING_DOOR: (0.0, 2.00),
    }

    def __init__(self, ifc_storey_handler: IfcStoreyHandler):
        self.ifc_storey_handler: IfcStoreyHandler = ifc_storey_handler

    def get_react_planner_data_from_ifc_storey(
        self,
        storey_id: int,
    ) -> ReactPlannerData:
        ifc_unit_to_cm_multiplier: float = self._M_TO_CM_MULTIPLIER

        height, width, origin = self._get_react_planner_dimensions_origin(
            storey_id=storey_id
        )

        unrolled_ifc_geometries: DefaultDict[
            SuperTypes, DefaultDict[ReactPlannerName, List[EditorReadyEntity]]
        ] = self._geometries_n_metadata_for_react_planner(
            storey_id=storey_id, origin=origin
        )

        from handlers.shapely_to_react.shapely_to_react_mapper import (
            ShapelyToReactPlannerMapper,
        )

        (
            planner_vertices,
            planner_lines,
        ) = ShapelyToReactPlannerMapper.create_vertices_and_lines_of_separators(
            geometries=unrolled_ifc_geometries[SuperTypes.SEPARATORS], scale_to_cm=1
        )

        layer = ReactPlannerLayer(
            vertices=planner_vertices,
            lines=planner_lines,
        )
        planner_data = ReactPlannerData(
            width=int(width * ifc_unit_to_cm_multiplier),
            height=int(height * ifc_unit_to_cm_multiplier),
            layers={"layer-1": layer},
        )

        layer.holes = ShapelyToReactPlannerMapper.create_holes_assigned_to_walls(
            planner_data=planner_data,
            all_opening_elements=unrolled_ifc_geometries[SuperTypes.OPENINGS],
            scale_to_cm=1,
        )

        layer.items = ShapelyToReactPlannerMapper.get_planner_items(
            geometries=unrolled_ifc_geometries, scale_to_cm=1
        )

        spaces_classified: List[
            Tuple[MultiPolygon, AreaType]
        ] = self.adapt_spaces_geometries_to_new_editor(
            storey_id=storey_id,
            origin=origin,
            multiplier=ifc_unit_to_cm_multiplier,
        )

        # First we create the areas without the area splitters
        layer.areas = ReactPlannerElementFactory.create_areas_from_separators(
            planner_data=planner_data, area_splitter_polygons=[]
        )

        # Add space type if available
        if spaces_classified:
            area_splitter_polygons = (
                ShapelyToReactPlannerMapper.add_area_splitters_to_react_planner_data(
                    planner_elements=planner_data,
                    spaces=[geom for (geom, _) in spaces_classified],
                    scale_to_cm=1,
                )
            )

            # If there are area splitters available, the areas are recreated
            layer.areas = ReactPlannerElementFactory.create_areas_from_separators(
                planner_data=planner_data,
                area_splitter_polygons=area_splitter_polygons,
                spaces_classified=spaces_classified,
            )

        return planner_data

    @classmethod
    def _translate_rectangle_from_ifc_entity(
        cls,
        ifc_entity: Ifc2DEntity,
        origin: Point,
    ) -> Polygon:
        ifc_unit_to_cm_multiplier: float = cls._M_TO_CM_MULTIPLIER

        geometries = []
        for polygon in as_multipolygon(ifc_entity.geometry).geoms:
            geom = translate(geom=polygon, xoff=-origin.x, yoff=-origin.y)
            geom = scale(
                geom=geom,
                xfact=ifc_unit_to_cm_multiplier,
                yfact=ifc_unit_to_cm_multiplier,
                origin=Point(0, 0),
            )
            geometries.append(ensure_geometry_validity(geometry=geom))
        return ensure_geometry_validity(
            geometry=unary_union(geometries)
        ).minimum_rotated_rectangle

    def _geometries_n_metadata_for_react_planner(
        self, storey_id: int, origin: Point
    ) -> DefaultDict[
        SuperTypes, DefaultDict[ReactPlannerName, List[EditorReadyEntity]]
    ]:
        geometries_by_type: DefaultDict[
            SuperTypes, DefaultDict[ReactPlannerName, List[EditorReadyEntity]]
        ] = defaultdict(lambda: defaultdict(list))

        flattened_ifc_entities = [
            ifc_entity
            for ifc_type_sublist in self.ifc_storey_handler.get_storey_entities_by_ifc_type(
                storey_id=storey_id
            ).values()
            for ifc_entity in ifc_type_sublist
        ]
        for ifc_entity in flattened_ifc_entities:
            super_type, planner_type = get_ifc_entity_supertype_and_planner_type(
                ifc_entity=ifc_entity
            )
            if super_type is None or planner_type is None:
                logger.debug(
                    f"Discarding ifc element {ifc_entity.ifc_type} because there is no mapping to react Planner"
                )
                continue
            editor_ready_entity = self._get_editor_ready_entity(
                ifc_entity=ifc_entity, origin=origin
            )
            geometries_by_type[super_type][planner_type].append(editor_ready_entity)

        return geometries_by_type

    @classmethod
    def _get_editor_ready_entity(
        cls,
        ifc_entity: Union[Ifc2DEntity, IfcSpaceProcessed],
        origin: Point,
    ) -> EditorReadyEntity:
        polygon = cls._translate_rectangle_from_ifc_entity(
            ifc_entity=ifc_entity, origin=origin
        )
        operation_type = ifc_entity.related.get("OperationType", "") or ""
        return EditorReadyEntity(
            geometry=polygon,
            properties=EntityProperties(
                door_subtype=ReactPlannerName.SLIDING_DOOR
                if "SLIDING" in operation_type
                else None
            ),
        )

    def _get_react_planner_dimensions_origin(
        self, storey_id: int
    ) -> Tuple[int, int, Point]:
        xmin, ymin, xmax, ymax = self.ifc_storey_handler.storey_footprint(
            storey_id=storey_id
        ).bounds

        height = abs(ymax - ymin)
        width = abs(xmax - xmin)
        origin_point = Point(xmin, ymin)
        return height, width, origin_point

    def adapt_spaces_geometries_to_new_editor(
        self, storey_id: int, origin: Point, multiplier: float
    ) -> List[Tuple[MultiPolygon, AreaType]]:
        transformed_spaces: List[Tuple[MultiPolygon, AreaType]] = []
        for ifc_space in self.ifc_storey_handler.get_storey_entities_by_ifc_type(
            storey_id=storey_id
        )[IFC_SPACE]:
            geom = translate(
                geom=ifc_space.geometry,
                xoff=-origin.x,
                yoff=-origin.y,
            )
            geom = scale(
                geom=geom,
                xfact=multiplier,
                yfact=multiplier,
                origin=Point(0, 0),
            )
            area_type = self.get_area_type_from_space_classification(
                ifc_space=ifc_space
            )
            transformed_spaces.append((geom, area_type))
        return transformed_spaces

    @staticmethod
    def get_area_type_from_space_classification(
        ifc_space: IfcSpaceProcessed,
    ) -> AreaType:
        if classification_info := ifc_space.properties.get("RG-DWB_Raumtyp"):
            if classification_info not in CUSTOM_CLASSIFICATION_BLACKLIST:
                return IMPLENIA_PRE_CLASSIFICATION_MAP.get(
                    classification_info, AreaType.NOT_DEFINED
                )
        return AreaType.NOT_DEFINED
