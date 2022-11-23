import copy
from collections import defaultdict
from functools import cached_property
from typing import TYPE_CHECKING, Dict, Iterator, Optional, Union

from methodtools import lru_cache
from shapely.geometry import MultiPolygon, Polygon

from brooks.constants import GENERIC_HEIGHTS
from brooks.layout_validations import SimLayoutValidations
from brooks.models import SimLayout
from brooks.types import (
    FeatureType,
    OpeningType,
    SeparatorType,
    get_valid_area_type_from_string,
)
from brooks.unit_layout_factory import UnitLayoutFactory
from brooks.utils import get_default_element_lower_edge
from common_utils.exceptions import AreaMismatchException
from handlers.db import AreaDBHandler, PlanDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.utils import PartialUnitInfo
from simulations.view.meshes import GeoreferencingTransformation

if TYPE_CHECKING:
    from handlers import ReactPlannerHandler


class PlanLayoutHandler:
    def __init__(
        self,
        plan_data: Optional[dict] = None,
        react_planner_handler: Optional["ReactPlannerHandler"] = None,
        plan_id: Optional[int] = None,
        plan_info: Optional[dict] = None,
        site_info: Optional[dict] = None,
    ):
        from handlers import PlanHandler, ReactPlannerHandler

        self._plan_info = plan_info or {}
        try:
            self.plan_id: int = plan_id or int(self._plan_info["id"])
        except KeyError:
            raise Exception(
                f"no plan id provided to plan handler: Plan id: {plan_id}. Plan info: {plan_info}"
            )
        self.react_planner_handler = react_planner_handler or ReactPlannerHandler(
            plan_data=plan_data
        )
        self.plan_handler = PlanHandler(
            plan_id=self.plan_id,
            plan_info=self._plan_info,
            site_info=site_info or {},
        )

    @cached_property
    def plan_info(self):
        return self._plan_info or PlanDBHandler.get_by(id=self.plan_id)

    @cached_property
    def scale_factor(self) -> float:
        return self.react_planner_handler.pixels_to_meters_scale(plan_id=self.plan_id)

    @cached_property
    def areas_db(self) -> list[dict]:
        return AreaDBHandler.find(
            plan_id=self.plan_id,
            output_columns=["id", "plan_id", "coord_x", "coord_y", "area_type"],
        )

    @staticmethod
    def scale_areas(db_areas: list[dict], pixels_to_meters_scale: float):
        for db_area in db_areas:
            db_area["coord_x"] = pixels_to_meters_scale * db_area["coord_x"]
            db_area["coord_y"] = pixels_to_meters_scale * db_area["coord_y"]
        return db_areas

    @cached_property
    def scaled_areas_db(self) -> list[dict]:
        _scale = self.react_planner_handler.pixels_to_meters_scale(plan_id=self.plan_id)
        return self.scale_areas(db_areas=self.areas_db, pixels_to_meters_scale=_scale)

    @lru_cache()
    def get_layout(
        self,
        scaled: bool = False,
        validate: bool = False,
        classified: bool = False,
        georeferenced: bool = False,
        postprocessed: bool = False,
        anonymized: bool = False,
        raise_on_inconsistency: bool = True,
        set_area_types_by_features: bool = True,
        set_area_types_from_react_areas: bool = False,
        deep_copied: bool = True,
    ) -> SimLayout:
        scaled_plan_layout = self._get_raw_layout_from_react_data(
            postprocessed=postprocessed,
            set_area_types_by_features=set_area_types_by_features,
            set_area_types_from_react_areas=set_area_types_from_react_areas,
            deep_copied=deep_copied,
        )
        if not validate and not classified and not georeferenced and scaled:
            return scaled_plan_layout

        if deep_copied:
            copied_plan_layout = copy.deepcopy(scaled_plan_layout)
        else:
            copied_plan_layout = scaled_plan_layout
        if validate:
            for violation in SimLayoutValidations.validate(layout=copied_plan_layout):
                violation = self.react_planner_handler.violation_position_to_pixels(
                    violation=violation,
                    plan_id=self.plan_id,
                )
                copied_plan_layout.add_error(violation=violation)
        if classified:
            copied_plan_layout = self.map_and_classify_layout(
                layout=copied_plan_layout,
                areas_db=self.scaled_areas_db,
                raise_on_inconsistency=raise_on_inconsistency,
            )
        if georeferenced:
            copied_plan_layout.apply_georef_transformation(
                georeferencing_transformation=self.get_georeferencing_transformation(
                    to_georeference=True, anonymized=anonymized
                )
            )
        if not scaled:
            copied_plan_layout.apply_georef_transformation(
                georeferencing_transformation=self.get_georeferencing_transformation_to_unscale()
            )
            copied_plan_layout.scale_factor = 1.0
        return copied_plan_layout

    @lru_cache()
    def _get_raw_layout_from_react_data(
        self,
        postprocessed: bool = False,
        scaled: bool = True,
        set_area_types_by_features: bool = True,
        set_area_types_from_react_areas: bool = False,
        deep_copied: bool = True,
    ) -> SimLayout:
        from handlers.editor_v2.editor_v2_element_mapper import (
            ReactPlannerToBrooksMapper,
        )

        if deep_copied:
            planner_elements = copy.deepcopy(
                self.react_planner_handler.get_data(plan_id=self.plan_id)
            )
        else:
            planner_elements = self.react_planner_handler.get_data(plan_id=self.plan_id)
        # planner elements are modified in this method, since the planner data from the DB is cached in the
        # react planner handler, consecutive calls with different parameters will lead to incorrect raw layouts
        return ReactPlannerToBrooksMapper.get_layout(
            planner_elements=planner_elements,
            post_processed=postprocessed,
            scaled=scaled,
            set_area_types_by_features=set_area_types_by_features,
            default_element_heights=self.plan_element_heights,
            set_area_types_from_react_areas=set_area_types_from_react_areas,
        )

    def get_layout_with_area_types(
        self, area_id_to_area_type: dict[int, str]
    ) -> SimLayout:
        if differences := set(area_id_to_area_type.keys()).symmetric_difference(
            {x["id"] for x in self.scaled_areas_db}
        ):
            raise AreaMismatchException(
                f"Areas not belonging to the plan: {','.join(map(str, differences))}. "
                f"Please save annotations again to recreate the areas"
            )

        for db_area in self.scaled_areas_db:
            db_area["area_type"] = area_id_to_area_type[db_area["id"]]

        plan_layout = self.get_layout(
            scaled=True,
            classified=False,
            georeferenced=False,
            raise_on_inconsistency=True,
        )
        self.map_and_classify_layout(
            layout=plan_layout,
            areas_db=self.scaled_areas_db,
            raise_on_inconsistency=True,
        )

        return plan_layout

    def map_and_classify_layout(
        self,
        layout: SimLayout,
        areas_db: list[dict],
        raise_on_inconsistency: bool = True,
    ) -> SimLayout:
        from handlers import AreaHandler

        try:
            for brooks_area, existing_area in AreaHandler.map_existing_areas(
                brooks_areas=layout.areas,
                db_areas=areas_db,
                raise_on_inconsistency=raise_on_inconsistency,
            ):
                if existing_area:
                    brooks_area._type = get_valid_area_type_from_string(
                        existing_area["area_type"]
                    )
                    brooks_area.db_area_id = existing_area["id"]
        except AreaMismatchException as e:
            raise AreaMismatchException(
                f"Plan {self.plan_id} has invalid areas. {e}"
            ) from e
        return layout

    @lru_cache()
    def get_public_layout(self, scaled=False, georeferenced=False):
        plan_layout = self.get_layout(
            classified=True,
            scaled=scaled,
            georeferenced=georeferenced,
            raise_on_inconsistency=True,
        )

        private_areas = {
            unit_area["area_id"]
            for unit_area in UnitAreaDBHandler.find_in(
                unit_id=list(UnitDBHandler.find_ids(plan_id=self.plan_id)),
            )
        }
        public_areas = {
            area["id"] for area in self.areas_db if area["id"] not in private_areas
        }
        return UnitLayoutFactory(plan_layout=plan_layout).create_sub_layout(
            spaces_ids={
                space.id
                for space in plan_layout.spaces
                if any(area.db_area_id in public_areas for area in space.areas)
            },
            area_db_ids=public_areas,
            public_space=True,
        )

    def get_private_layout(self, scaled=False, georeferenced=False) -> SimLayout:
        plan_layout = self.get_layout(
            classified=True,
            scaled=scaled,
            georeferenced=georeferenced,
            raise_on_inconsistency=True,
        )

        private_areas = {
            unit_area["area_id"]
            for unit_area in UnitAreaDBHandler.find_in(
                unit_id=list(UnitDBHandler.find_ids(plan_id=self.plan_id)),
            )
        }
        return UnitLayoutFactory(plan_layout=plan_layout).create_sub_layout(
            spaces_ids={
                space.id
                for space in plan_layout.spaces
                if any(area.db_area_id in private_areas for area in space.areas)
            },
            area_db_ids=private_areas,
            public_space=False,
        )

    def get_unit_layouts(
        self, floor_id: int, scaled=False, georeferenced=False, anonymized: bool = False
    ) -> Iterator[tuple[PartialUnitInfo, SimLayout]]:
        """
        Returns: Tuple containing first the unit id & client id
                 and second the unit layout
        """
        # get plan layout
        plan_layout = self.get_layout(
            classified=True,
            scaled=scaled,
            georeferenced=georeferenced,
            raise_on_inconsistency=True,
            anonymized=anonymized,
        )

        # get unit areas using floor_number
        units_info: list[PartialUnitInfo] = UnitDBHandler.find(
            floor_id=floor_id,
            output_columns=["id", "client_id", "floor_id", "unit_usage"],
        )  # type: ignore
        units_areas = defaultdict(list)
        for unit_area in UnitAreaDBHandler.find_in(
            unit_id=[u["id"] for u in units_info],
        ):
            units_areas[unit_area["unit_id"]].append(unit_area["area_id"])

        # create unit layouts
        brooks_space_by_db_area = {
            area.db_area_id: space.id
            for space in plan_layout.spaces
            for area in space.areas
        }
        for unit_info in units_info:
            yield unit_info, UnitLayoutFactory(
                plan_layout=plan_layout
            ).create_sub_layout(
                spaces_ids={
                    brooks_space_by_db_area[db_area_id]
                    for db_area_id in units_areas[unit_info["id"]]
                },
                area_db_ids=set(units_areas[unit_info["id"]]),
            )

    def get_georeferencing_transformation(
        self,
        to_georeference: bool = False,
        z_off: float = 0.0,
        anonymized: bool = False,
    ) -> GeoreferencingTransformation:
        georef = GeoreferencingTransformation()
        if to_georeference:
            georef.set_rotation(
                pivot_x=self.plan_handler.rotation_point.x,
                pivot_y=self.plan_handler.rotation_point.y,
                angle=self.plan_info["georef_rot_angle"] or 0.0,
            )
            if anonymized:
                # NOTE: If we want an anonymized location, we do not reveal the
                #       position and only do scaling / rotation.
                georef.set_translation(
                    x=-self.plan_handler.rotation_point.x,
                    y=-self.plan_handler.rotation_point.y,
                    z=z_off,
                )
            else:
                georef.set_translation(
                    x=self.plan_handler.translation_point.x
                    - self.plan_handler.rotation_point.x,
                    y=self.plan_handler.translation_point.y
                    - self.plan_handler.rotation_point.y,
                    z=z_off,
                )

        return georef

    def get_georeferencing_transformation_to_unscale(
        self,
    ) -> GeoreferencingTransformation:
        georef = GeoreferencingTransformation()
        georef.set_scaling(
            pivot_x=0,
            pivot_y=0,
            factor=1 / self.scale_factor,
        )
        return georef

    def get_georeferenced_footprint(self) -> Union[Polygon, MultiPolygon]:
        """There are issues when scaling + georeferencing the footprint, so it needs to be done in 2 steps until
        the root cause is found.
        Brooks content is optional to increase the performance of methods
        that are building the footprint of many plans.
        """
        layout = self.get_layout(
            validate=False, classified=False, scaled=True, georeferenced=False
        )
        georef = self.get_georeferencing_transformation(to_georeference=True)
        return georef.apply_shapely(layout.footprint)

    @cached_property
    def plan_element_heights(
        self,
    ) -> dict[Union[SeparatorType, str, FeatureType, OpeningType], tuple[float, float]]:
        element_default_heights = copy.copy(GENERIC_HEIGHTS)

        separator_types_to_update: set[Union[str, SeparatorType, FeatureType]] = {
            SeparatorType.WALL,
            SeparatorType.COLUMN,
            SeparatorType.AREA_SPLITTER,
            "GENERIC_SPACE_HEIGHT",
            FeatureType.STAIRS,
            FeatureType.ELEVATOR,
        }
        for separator_type in separator_types_to_update:
            element_default_heights[separator_type] = (
                get_default_element_lower_edge(element_type=separator_type),
                get_default_element_lower_edge(element_type=separator_type)
                + self.plan_info["default_wall_height"],
            )

        element_default_heights[OpeningType.WINDOW] = (
            self.plan_info["default_window_lower_edge"],
            self.plan_info["default_window_upper_edge"],
        )

        element_default_heights["CEILING_SLAB"] = (
            get_default_element_lower_edge(element_type="CEILING_SLAB"),
            get_default_element_lower_edge(element_type="CEILING_SLAB")
            + self.plan_info["default_ceiling_slab_height"],
        )

        for opening_type in {OpeningType.DOOR, OpeningType.ENTRANCE_DOOR}:
            element_default_heights[opening_type] = (
                get_default_element_lower_edge(element_type=opening_type),
                get_default_element_lower_edge(element_type=opening_type)
                + self.plan_info["default_door_height"],
            )

        return element_default_heights


class PlanLayoutHandlerIDCacheMixin:
    def __init__(
        self, layout_handler_by_id: Optional[Dict[int, PlanLayoutHandler]] = None
    ):
        if layout_handler_by_id is None:
            # important to keep the reference
            layout_handler_by_id = {}
        self._layout_handler_by_id: Dict[int, PlanLayoutHandler] = layout_handler_by_id

    def layout_handler_by_id(self, plan_id: int) -> PlanLayoutHandler:
        if plan_handler := self._layout_handler_by_id.get(plan_id):
            return plan_handler
        self._layout_handler_by_id[plan_id] = PlanLayoutHandler(plan_id=plan_id)
        return self._layout_handler_by_id[plan_id]
