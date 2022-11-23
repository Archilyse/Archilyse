from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Dict, List, Union

import pandas as pd
from shapely.geometry import CAP_STYLE, JOIN_STYLE, Polygon

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator
from brooks.types import AreaType, OpeningSubType, SIACategory
from common_utils.constants import UNIT_USAGE
from dufresne.polygon.utils import as_multipolygon
from handlers import BuildingHandler
from handlers.db import BuildingDBHandler, FloorDBHandler, PlanDBHandler


@dataclass
class ElementInformation:
    building_id: int
    floor_number: int
    type: str
    length: float
    width: float
    start_height: float
    end_height: float
    surface_area: float
    footprint_area: float
    is_on_outside_area: bool
    is_on_facade: bool

    _footprint: Polygon


@dataclass
class AreaInformation:
    building_id: int
    floor_number: int
    usage: str
    type: str
    start_height: float
    end_height: float
    footprint_area: float
    perimeter: float
    wall_surface_area: float
    sia416_type: str

    _footprint: Polygon


class MassExportHandler:
    _element_to_footprint: dict
    _area_to_footprint: dict

    SIA_MAPPING: dict[AreaType, SIACategory] = dict(
        [
            (area_type, sia_type.name)
            for sia_type, information in UnifiedClassificationScheme._AREA_TREE.items()
            for area_type in information["children"]
        ]
    )

    def __init__(self, site_id: int):
        self.site_id = site_id

    def export_elements(self, output_path: Path):
        self.element_data = list(
            chain(
                self._get_element_information(
                    building_id=building_id,
                    floor_number=floor_number,
                    layout=layout,
                    element=element,
                )
                for building_id, layouts_by_floor_number in self._layouts_by_building_id_and_floor_number.items()
                for floor_number, layout in layouts_by_floor_number.items()
                for element in layout.non_overlapping_separators
                | layout.openings
                | layout.features
            )
        )

        pd.DataFrame(self.element_data).drop("_footprint", axis="columns").to_csv(
            output_path.as_posix()
        )

    def export_areas(self, output_path: Path):
        self.area_data = list(
            chain(
                self._get_area_information(
                    building_id=building_id,
                    floor_number=floor_number,
                    layout=layout,
                    area=element,
                    area_id_to_usage_type=self._area_usages_by_building_id_and_floor_number[
                        building_id
                    ][
                        floor_number
                    ],
                )
                for building_id, layouts_by_floor_number in self._layouts_by_building_id_and_floor_number.items()
                for floor_number, layout in layouts_by_floor_number.items()
                for element in layout.areas
            )
        )
        pd.DataFrame(self.area_data).drop("_footprint", axis="columns").to_csv(
            output_path.as_posix()
        )

    def export_floor_data(self, output_path: Path):
        floor_data = []
        for building_info in BuildingDBHandler.find(site_id=self.site_id):
            for floor_info in FloorDBHandler.find(building_id=building_info["id"]):
                plan_info = PlanDBHandler.get_by(id=floor_info["plan_id"])
                floor_data.append(
                    {
                        "building": building_info["id"],
                        "floor_number": floor_info["floor_number"],
                        "wall_height": plan_info["default_wall_height"],
                        "slab_height": plan_info["default_ceiling_slab_height"],
                        "door_height": plan_info["default_door_height"],
                        "window_lower_edge": plan_info["default_window_lower_edge"],
                        "window_upper_edge": plan_info["default_window_upper_edge"],
                    }
                )
        pd.DataFrame(floor_data).to_csv(output_path.as_posix(), index=False)

    @classmethod
    def _get_element_information(
        cls,
        building_id: int,
        floor_number: int,
        layout: SimLayout,
        element: Union[SimSeparator, SimOpening],
        on_facade_threshold: float = 0.5,
        intersection_buffer: float = 5e-2,
    ) -> ElementInformation:
        return ElementInformation(
            building_id=building_id,
            floor_number=floor_number,
            type="SLIDING_DOOR"
            if (
                isinstance(element, SimOpening)
                and element.opening_sub_type == OpeningSubType.SLIDING
            )
            else element.type.name,
            width=element.width,
            length=element.length,
            start_height=element.height[0],
            end_height=element.height[1],
            footprint_area=element.footprint.area,
            surface_area=element.surface_area,
            is_on_outside_area=element.footprint.buffer(
                distance=intersection_buffer,
                join_style=JOIN_STYLE.mitre,
                cap_style=CAP_STYLE.square,
            ).intersects(layout.footprint_outside),
            is_on_facade=sum(
                [
                    element.footprint.buffer(
                        distance=intersection_buffer,
                        join_style=JOIN_STYLE.mitre,
                        cap_style=CAP_STYLE.square,
                    )
                    .intersection(facade_polygon.exterior)
                    .length
                    for facade_polygon in as_multipolygon(layout.footprint_facade)
                ]
            )
            > on_facade_threshold * element.length,
            _footprint=element.footprint,
        )

    @classmethod
    def _get_area_information(
        cls,
        building_id: int,
        floor_number: int,
        layout: SimLayout,
        area: SimArea,
        area_id_to_usage_type: Dict[int, UNIT_USAGE],
    ) -> AreaInformation:
        area_usage = area_id_to_usage_type.get(area.db_area_id, None)
        return AreaInformation(
            building_id=building_id,
            floor_number=floor_number,
            usage=area_usage.name if area_usage is not None else "PUBLIC",
            type=area.type.name,
            start_height=area.height[0],
            end_height=area.height[1],
            footprint_area=area.footprint.area,
            perimeter=area.footprint.exterior.length,
            wall_surface_area=area.wall_surface_area(layout=layout),
            sia416_type=cls.SIA_MAPPING.get(area.type, None),
            _footprint=area.footprint,
        )

    @cached_property
    def _layouts_by_building_id_and_floor_number(
        self,
    ) -> Dict[int, Dict[int, SimLayout]]:
        return {
            building_info["id"]: BuildingHandler(
                building_id=building_info["id"]
            )._plan_layouts_by_floor_number(
                classified=True,
                georeferenced=False,
            )
            for building_info in self._building_infos
        }

    @cached_property
    def _area_usages_by_building_id_and_floor_number(
        self,
    ) -> Dict[int, Dict[int, SimLayout]]:
        return {
            building_info["id"]: BuildingHandler(
                building_id=building_info["id"]
            )._area_usage_by_floor_number()
            for building_info in self._building_infos
        }

    @cached_property
    def _building_infos(self) -> List[Dict]:
        return list(BuildingDBHandler.find(site_id=self.site_id))


if __name__ == "__main__":
    export_handler = MassExportHandler(site_id=11492)
    export_handler.export_areas(output_path=Path("/tmp/areas.csv"))
    export_handler.export_elements(output_path=Path("/tmp/elements.csv"))
    export_handler.export_floor_data(output_path=Path("/tmp/floors.csv"))
