from typing import TYPE_CHECKING, Dict, Iterator, Set

from methodtools import lru_cache

from brooks.models import SimLayout
from brooks.types import FeatureType
from handlers.db import BuildingDBHandler, FloorDBHandler, UnitDBHandler
from simulations.basic_features import CustomValuatorBasicFeatures2

if TYPE_CHECKING:
    from handlers import PlanHandler, PlanLayoutHandler


class AutoUnitLinkingHandler:
    def __init__(self, building_id: int):
        self.building_id = building_id
        self._building: Dict = {}
        self._already_linked_units: Set[str] = set()
        self._plan_ids_by_floor: Dict[int, int] = {}
        self._floor_number_by_id: Dict[int, int] = {}
        self._floor_id_by_number: Dict[int, int] = {}
        self._basic_features_service = CustomValuatorBasicFeatures2()

    @lru_cache()
    def _get_plan_layout_handler(self, floor_id: int) -> "PlanLayoutHandler":
        from handlers import PlanLayoutHandler

        return PlanLayoutHandler(plan_id=self._plan_ids_by_floor[floor_id])

    @lru_cache()
    def _get_plan_handler(self, floor_id: int) -> "PlanHandler":
        from handlers import PlanHandler

        return PlanHandler(plan_id=self._plan_ids_by_floor[floor_id])

    @lru_cache()
    def _get_georeferenced_layouts(self, floor_id: int) -> Dict[int, SimLayout]:
        """Returns an empty dict if plan is not georeferenced or floor doesn't exist."""
        plan_handler = self._get_plan_handler(floor_id=floor_id)
        if plan_handler.is_georeferenced:
            return {
                unit_info["id"]: layout
                for unit_info, layout in self._get_plan_layout_handler(
                    floor_id=floor_id
                ).get_unit_layouts(
                    floor_id=floor_id,
                    scaled=True,
                    georeferenced=True,
                )
            }
        return {}

    @staticmethod
    def _map_layouts_by_stairs(
        layout: SimLayout, candidates: Iterator[SimLayout]
    ) -> Iterator[SimLayout]:
        for candidate_layout in candidates:
            if any(
                stair.footprint.intersects(candidate_stair.footprint)
                for candidate_stair in candidate_layout.features_by_type[
                    FeatureType.STAIRS
                ]
                for stair in layout.features_by_type[FeatureType.STAIRS]
            ):
                yield candidate_layout

    def _get_connected_layouts(
        self, layout: SimLayout, floor_id: int, exclude_layouts=None
    ) -> Iterator[SimLayout]:
        """This method recursively finds all layouts across all floors connected with the layout provided"""
        # NOTE to avoid infinitive recursion exclude layouts which are already mapped
        if not exclude_layouts:
            exclude_layouts = set()
        exclude_layouts.add(layout)

        # try to find connected layouts on floors above and below
        floor_number = self._floor_number_by_id[floor_id]
        for floor_number_to_scan in [floor_number + 1, floor_number - 1]:
            floor_id_to_scan = self._floor_id_by_number.get(floor_number_to_scan)
            if floor_id_to_scan is None:
                continue
            # find layouts with stairs, excluding already mapped layouts
            candidates = filter(
                lambda c: c not in exclude_layouts
                and c.features_by_type.get(FeatureType.STAIRS),
                self._get_georeferenced_layouts(floor_id=floor_id_to_scan).values(),
            )
            for mapped_layout in self._map_layouts_by_stairs(layout, candidates):
                # if a connected layout is found yield it ...
                yield mapped_layout
                # ... and find the layouts connected with THAT layout
                yield from self._get_connected_layouts(
                    layout=mapped_layout,
                    floor_id=floor_id_to_scan,
                    exclude_layouts=exclude_layouts,
                )

    def _link_maisonettes(self, floor_id: int) -> Iterator[Dict]:
        from handlers import QAHandler

        maisonette_layouts = (
            (
                unit_id,
                [
                    layout,
                    *self._get_connected_layouts(layout=layout, floor_id=floor_id),
                ],
            )
            for unit_id, layout in self._get_georeferenced_layouts(
                floor_id=floor_id
            ).items()
            if layout.features_by_type.get(FeatureType.STAIRS)
        )

        yield from QAHandler.map_maisonettes_to_index(
            maisonettes={
                unit_id: {
                    "net_area": self._basic_features_service.net_area(
                        layouts=connected_layouts
                    )["net-area"],
                    "number_of_rooms": self._basic_features_service.number_of_rooms(
                        layouts=connected_layouts
                    )[0][1],
                }
                for unit_id, connected_layouts in maisonette_layouts
            },
            qa_data={
                client_unit_id: qa_values
                for client_unit_id, qa_values in QAHandler.get_qa_data_by_building(
                    building=self._building,
                ).items()
                if client_unit_id not in self._already_linked_units
            },
        )

    def _link_apartments(self, floor_id: int) -> Iterator[Dict]:
        from handlers import QAHandler

        apartment_layouts = [
            (k, v)
            for k, v in self._get_georeferenced_layouts(floor_id=floor_id).items()
        ]
        if not apartment_layouts:
            apartment_layouts = [
                (unit_info["id"], unit_layout)
                for unit_info, unit_layout in self._get_plan_layout_handler(
                    floor_id=floor_id
                ).get_unit_layouts(floor_id=floor_id, scaled=True)
            ]

        new_area_by_unit_id: Dict[int, float] = {
            unit_id: self._basic_features_service.net_area(layouts=[layout])["net-area"]
            for unit_id, layout in apartment_layouts
            if not layout.features_by_type.get(FeatureType.STAIRS)
        }
        qa_data_by_client_id = {
            client_unit_id: qa_values
            for client_unit_id, qa_values in self.get_qa_data_by_floor(
                floor_id=floor_id
            ).items()
            if client_unit_id not in self._already_linked_units
        }

        yield from QAHandler.map_apartments_to_index(
            apartments=new_area_by_unit_id,
            qa_data=qa_data_by_client_id,
        )

    def unit_linking(self, floor_id: int) -> Iterator[Dict]:
        self._building = BuildingDBHandler.get_by(id=self.building_id)
        self._already_linked_units = {
            u["client_id"]
            for u in UnitDBHandler.find(
                site_id=self._building["site_id"], output_columns=["client_id"]
            )
        }
        building_floors = FloorDBHandler.find(
            building_id=self.building_id,
            output_columns=["id", "floor_number", "plan_id"],
        )
        self._floor_number_by_id = {f["id"]: f["floor_number"] for f in building_floors}
        self._floor_id_by_number = {f["floor_number"]: f["id"] for f in building_floors}
        self._plan_ids_by_floor = {f["id"]: f["plan_id"] for f in building_floors}

        # if georeferenced try to link maisonettes
        if self._get_plan_handler(floor_id=floor_id).is_georeferenced:
            yield from self._link_maisonettes(floor_id=floor_id)

        yield from self._link_apartments(floor_id=floor_id)

    def get_qa_data_by_floor(self, floor_id: int) -> Dict[str, Dict]:
        from handlers import QAHandler

        return {
            unit_client_id: qa_data
            for unit_client_id, qa_data in QAHandler.get_qa_data_by_building(
                building=self._building
            ).items()
            if (qa_data["floor"] == self._floor_number_by_id[floor_id])
        }
