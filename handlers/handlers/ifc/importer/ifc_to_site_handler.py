import typing
from collections import defaultdict
from dataclasses import asdict
from typing import Any, Dict, List

from brooks.types import AnnotationType
from common_utils.constants import REGION
from common_utils.exceptions import IfcEmptyStoreyException
from common_utils.logger import logger
from connectors.db_connector import get_db_session_scope
from handlers import PlanHandler
from handlers.db import BuildingDBHandler, FloorDBHandler, ReactPlannerProjectsDBHandler
from handlers.db.utils import retry_on_db_operational_error
from handlers.ifc.constants import PIXELS_PER_METER
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from handlers.ifc.importer.ifc_to_react_planner_mapper import IfcToReactPlannerMapper
from ifc_reader.constants import IFC_BUILDING
from ifc_reader.reader import IfcReader


class IfcToSiteHandler:
    """
                                       Generates:
    ┌───────────────────┐                - Site
    │                   │  ────────────► - Building
    │                   │                - Plans ◄─────────────────────────────┐
    │  IfcToSiteHandler │                - Floors                              │
    │                   │                                                      │
    │                   │  ────────────► ReactPlanner Annotations              │
    └─────────┬─────────┘                           │                          │
              │                                     │                          │
              │                                     │                          │
              │                                     │                          │
     ┌────────┴────────┐                   ┌────────┴─────────┐                │
     │                 │                   │                  │       ┌────────┴─────────┐
     │    IfcReader    ├───────────────────┤                  │       │                  │
     │                 │                   │ IfcStoreyHandler ├───────┤ IfcFloorPlanPlot │
     └───────┬─────────┘                   │                  │       │                  │
             │                             │                  │       └──────────────────┘
             │                             └───────┬──────────┘
             │                                     │
             │                                     │  Ifc2DEntities containing all
    ┌────────┴──────────────┐                      │  the information related and
    │                       │                      │  the 2D geometries
    │  IfcSpaceClassifiers  ├─────────────────────►│
    │                       │                      │
    └───────────────────────┘                      │
                                                   │               Configures how each IFC type
                                                   ▼            is mapped to each react planner type,
                                 ┌────────────────────────────┐ either based on ifc types or ifc properties
                                 │                            │      ┌─────────────────────┐
                                 │                            │      │                     │
                                 │   IfcToReactPlannerMapper  ├──────┤   IfcReactMappings  │
                                 │                            │      │                     │
                                 │                            │      └─────────────────────┘
                                 └────────────────────────────┘
    """

    def __init__(self, ifc_reader: IfcReader):
        self.ifc_reader = ifc_reader
        self.elements_by_building_floor_type: Dict[
            str, Dict[int, Dict[AnnotationType, List[Any]]]
        ] = defaultdict(lambda: defaultdict(dict))
        self.storey_handler = IfcStoreyHandler(ifc_reader=self.ifc_reader)

    def create_and_save_site_entities(
        self, site_id: int, ifc_filename: str
    ) -> List[Dict]:
        entities = self._create_site_entities(
            site_id=site_id, ifc_filename=ifc_filename
        )
        self._save_site_entities(site_id=site_id, buildings=entities)
        return entities

    @retry_on_db_operational_error()
    def _save_site_entities(self, site_id: int, buildings: List[Dict]):
        with get_db_session_scope():
            for building in buildings:
                db_building = BuildingDBHandler.add(
                    site_id=site_id, **building["building"]
                )
                de_duplicated_floor_numbers_by_plan_id: typing.DefaultDict[
                    int, List[int]
                ] = defaultdict(list)

                for plan, floor, annotations_react_planner in zip(
                    building["plans"],
                    building["floors"],
                    building["annotations_react_planner"],
                ):
                    db_plan = PlanHandler.add(building_id=db_building["id"], **plan)
                    if de_duplicated_floor_numbers_by_plan_id[db_plan["id"]]:
                        FloorDBHandler.add(
                            building_id=db_building["id"],
                            plan_id=db_plan["id"],
                            **floor,
                        )
                        continue
                    FloorDBHandler.add(
                        building_id=db_building["id"], plan_id=db_plan["id"], **floor
                    )

                    ReactPlannerProjectsDBHandler.add(
                        plan_id=db_plan["id"],
                        data=annotations_react_planner,
                    )
                    de_duplicated_floor_numbers_by_plan_id[db_plan["id"]].append(
                        floor["floor_number"]
                    )

    def _create_site_entities(
        self, site_id: int, ifc_filename: str, region: REGION = REGION.CH
    ) -> List[Dict]:
        buildings = []

        floor_number_index = self.ifc_reader.storey_floor_numbers
        storeys_by_building_index = self.ifc_reader.storeys_by_building

        # NOTE parsing the file into db entity like objects takes forever ...
        for building in self.ifc_reader.wrapper.by_type(IFC_BUILDING):
            building_entity = {
                "building": self.ifc_reader.get_address_info(
                    ifc_building=building, ifc_filename=ifc_filename
                )
            }
            buildings.append(building_entity)

            building_entity["floors"] = []
            building_entity["plans"] = []
            building_entity["annotations_react_planner"] = []
            for storey_id in sorted(
                storeys_by_building_index[building.GlobalId],
                key=lambda s: floor_number_index[s],
            ):
                logger.debug(f"Creating floor number {floor_number_index[storey_id]}")
                try:
                    storey_sizes = self.storey_handler.storey_height_width_in_pixel(
                        storey_id=storey_id
                    )
                    storey_georeference_data = (
                        self.storey_handler.storey_georeference_data(
                            storey_id=storey_id,
                            region=region,
                        )
                    )
                except IfcEmptyStoreyException as e:
                    logger.warning(str(e))
                    continue

                storey_height_by_annotation_type = (
                    self.storey_handler.get_relative_plan_heights(storey_id=storey_id)
                )

                building_entity["plans"].append(
                    dict(
                        plan_content=self.storey_handler.storey_figure(
                            storey_id=storey_id,
                            scale_factor=PIXELS_PER_METER,
                            building_id=building.GlobalId,
                            image_width=storey_sizes["width"],
                            image_height=storey_sizes["height"],
                        ).read(),
                        plan_mime_type="image/jpg",
                        site_id=site_id,
                        **storey_height_by_annotation_type,
                        **storey_georeference_data,
                    )
                )
                building_entity["floors"].append(
                    dict(floor_number=floor_number_index[storey_id])
                )

                building_entity["annotations_react_planner"].append(
                    asdict(
                        IfcToReactPlannerMapper(
                            ifc_storey_handler=self.storey_handler
                        ).get_react_planner_data_from_ifc_storey(
                            storey_id=storey_id,
                        )
                    )
                )
        return buildings
