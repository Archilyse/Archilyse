from itertools import chain
from typing import Any, Dict, List, Optional

from methodtools import lru_cache
from shapely.geometry import Point

from brooks.layout_validations import SimLayoutValidations
from brooks.models import SimLayout
from brooks.models.violation import Violation
from brooks.util.io import BrooksJSONEncoder
from common_utils.constants import SI_UNIT_BY_NAME
from common_utils.exceptions import (
    DBNotFoundException,
    ReactAnnotationMigrationException,
)
from common_utils.logger import logger
from handlers.db import PlanDBHandler, ReactPlannerProjectsDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    CURRENT_REACT_ANNOTATION_BASELINE,
    CURRENT_REACT_ANNOTATION_VERSION,
    ReactPlannerData,
    ReactPlannerSchema,
)
from handlers.editor_v2.utils import m_to_pixels_scale, pixels_to_meters_scale


class ReactPlannerHandler:
    def __init__(
        self,
        plan_data: Optional[Dict] = None,
    ):
        self.plan_data = plan_data

    def store_plan_data(self, plan_id: int, plan_data: Dict, validated: bool) -> Dict:
        from handlers import PlanHandler
        from handlers.plan_utils import create_areas_for_plan

        try:
            plan_data = self.migrate_data_if_old_version(plan_data=plan_data)
        finally:
            # Validates input data after attempting migration. If migration fails because of the schema,
            # it could appear as a migration error when in fact is a schema validation error.
            # In any case, in current design, since we are not controlling the browser planner version correctly,
            # BE is responsible for applying migrations and later here we check also the schema as it
            # should be in the latest version.
            schema_loaded = ReactPlannerSchema().load(plan_data)

        saved_data: Dict = self._saves_data_georef_invalidated(
            plan_id=plan_id, schema_loaded=schema_loaded
        )
        if validated:
            errors = self._validate_plan_data(
                plan_id=plan_id, schema_loaded=schema_loaded
            )
            annotation_finished = False

            if not [b for b in errors if b.is_blocking] and not schema_loaded.is_empty:
                annotation_finished = True
                create_areas_for_plan(plan_id=plan_id)

                plan_handler = PlanHandler(plan_id=plan_id)
                if not plan_handler.is_georeferenced:
                    plan_handler.update_rotation_point()

            PlanDBHandler.update(
                item_pks={"id": plan_id},
                new_values={
                    "annotation_finished": annotation_finished,
                    "georef_scale": saved_data["data"]["scale"]
                    * SI_UNIT_BY_NAME["cm"].value ** 2,
                },
            )
            saved_data["errors"] = BrooksJSONEncoder.default(errors)
            saved_data["annotation_finished"] = annotation_finished
        return saved_data

    @lru_cache()
    def project(self, plan_id: int) -> Dict:
        return self.get_by_migrated(plan_id=plan_id)

    @lru_cache()
    def get_data(self, plan_id: int) -> ReactPlannerData:
        return ReactPlannerData(**self.project(plan_id=plan_id)["data"])

    def image_height(self, plan_id: int) -> int:
        return self.project(plan_id=plan_id)["data"]["height"]

    def plan_scale(self, plan_id: int) -> float:
        return self.project(plan_id=plan_id)["data"]["scale"]

    def pixels_to_meters_scale(
        self, plan_id: int, plan_scale: Optional[float] = None
    ) -> float:
        plan_scale = plan_scale or self.plan_scale(plan_id=plan_id)
        return pixels_to_meters_scale(scale=plan_scale)

    def get_plan_data_w_validation_errors(
        self, plan_info: Dict, validated: bool
    ) -> Dict[str, Any]:
        react_planner_project = self.get_by_migrated(plan_id=plan_info["id"])

        if validated:
            errors = self._validate_plan_data(
                plan_id=plan_info["id"],
                schema_loaded=self.get_data(plan_id=plan_info["id"]),
            )
            react_planner_project["errors"] = BrooksJSONEncoder.default(errors)

        # To correct plans where we have previously allowed the plan to be finished with errors
        if (
            react_planner_project.get("errors")
            or self.get_data(plan_id=plan_info["id"]).is_empty
        ):
            react_planner_project["annotation_finished"] = False
        else:
            react_planner_project["annotation_finished"] = plan_info[
                "annotation_finished"
            ]
        return react_planner_project

    def _validate_plan_data(
        self, plan_id: int, schema_loaded: ReactPlannerData
    ) -> List[Violation]:
        plan_layout: SimLayout = ReactPlannerToBrooksMapper.get_layout(
            planner_elements=schema_loaded,
            scaled=True,
            post_processed=False,
        )

        # layout validations
        violations = list(SimLayoutValidations.validate(layout=plan_layout))
        layout_errors = list(chain(plan_layout.errors, violations))
        schema_errors = list(schema_loaded.validate())

        for error in layout_errors + schema_errors:
            self.violation_position_to_pixels(
                plan_id=plan_id,
                violation=error,
            )

        return layout_errors + schema_errors

    def violation_position_to_pixels(
        self, plan_id: int, violation: Violation
    ) -> Violation:
        if not violation.position:
            return violation
        scale_factor = m_to_pixels_scale(scale=self.plan_scale(plan_id=plan_id))
        violation.position = Point(
            violation.position.x * scale_factor, violation.position.y * scale_factor
        )
        return violation

    @staticmethod
    def _saves_data_georef_invalidated(
        plan_id: int, schema_loaded: ReactPlannerData
    ) -> Dict:
        """
        Important: this method creates or gets an existing React planner project, but additionally it sets the
        geo-referencing parameters (georef_x, georef_y) of the parent plan entity if and only if there is a change
        in the scale factor coming from the new editor. This is crucial for the consistency of the geo-referencing step,
        as in the event of the plan being rescaled, there will still be the old translation vector in the plan which
        will be in turned used to define an old rotation axis in the georef App in FE. For this reason, it has to be
        reset and if the plan is rescaled, it needs to be geo-referenced again as well.
        """
        try:
            saved_data = ReactPlannerProjectsDBHandler.get_by(
                plan_id=plan_id,
            )
            if schema_loaded.scale != saved_data["data"]["scale"]:
                PlanDBHandler.update(
                    item_pks={"id": plan_id},
                    new_values={"georef_x": None, "georef_y": None},
                )
            return ReactPlannerProjectsDBHandler.update(
                item_pks={"id": saved_data["id"]},
                new_values={"data": ReactPlannerSchema().dump(schema_loaded)},
            )
        except DBNotFoundException:
            return ReactPlannerProjectsDBHandler.add(
                plan_id=plan_id, data=ReactPlannerSchema().dump(schema_loaded)
            )

    @classmethod
    def migrate_data_if_old_version(cls, plan_data: Dict) -> Dict:
        from handlers.editor_v2.schema import migration_by_version

        while plan_data.get("version") != CURRENT_REACT_ANNOTATION_VERSION:
            try:
                current_version = plan_data["version"]
                version_integer = int(current_version[1:])
                if not version_integer >= CURRENT_REACT_ANNOTATION_BASELINE:
                    raise ReactAnnotationMigrationException(
                        "Project is not migrated up-to-date."
                    )
                logger.info(f"Updating react annotation version from {current_version}")
                plan_data = migration_by_version[current_version](data=plan_data)
                if current_version == plan_data["version"]:
                    raise ReactAnnotationMigrationException(
                        "Migration is not updating the version field"
                    )
            except Exception as e:
                raise ReactAnnotationMigrationException(
                    f"Could not migrate annotation from old version {plan_data.get('version')} to current version. "
                    f"Error: {e}"
                )
        return plan_data

    def get_by_migrated(self, plan_id: int) -> Dict:
        project = self.plan_data or ReactPlannerProjectsDBHandler.get_by(
            plan_id=plan_id
        )
        project["data"] = self.migrate_data_if_old_version(plan_data=project["data"])
        return project

    def get_image_transformation(self, plan_id: int) -> Dict:
        try:
            data = self.get_data(plan_id=plan_id)
        except DBNotFoundException:
            return {"shift_x": 0.0, "shift_y": 0.0, "scale": 1.0, "rotation": 0.0}
        original_image_width = PlanDBHandler.get_by(
            id=plan_id, output_columns=["image_width"]
        )["image_width"]
        if data.background.width is not None:
            scale = data.background.width / original_image_width
        else:
            scale = 1.0

        return {
            "shift_x": data.background.shift.x or 0.0,
            "shift_y": data.background.shift.y or 0.0,
            "scale": scale,
            "rotation": data.background.rotation or 0.0,
        }
