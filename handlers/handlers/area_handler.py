from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

from shapely import wkt
from shapely.affinity import scale
from shapely.geometry import Point

from brooks.models import SimArea, SimLayout, SimSpace
from brooks.models.violation import SpatialEntityViolation
from brooks.types import AreaType, get_valid_area_type_from_string
from common_utils.exceptions import AreaMismatchException, InvalidShapeException
from connectors.db_connector import get_db_session_scope
from db_models.db_entities import AreaDBModel, UnitsAreasDBModel
from handlers.db import UnitDBHandler
from handlers.db.area_handler import AreaDBHandler, UnitAreaDBHandler
from handlers.db.utils import retry_on_db_operational_error
from handlers.editor_v2 import ReactPlannerHandler


class AreaHandler:
    @classmethod
    def get_index_brooks_area_id_to_area_db_id(
        cls, db_areas: List[Dict], layout: SimLayout
    ) -> Dict[str, int]:
        return {
            brook_area.id: db_area["id"]
            for brook_area, db_area in cls.map_existing_areas(
                brooks_areas=layout.areas,
                db_areas=db_areas,
                raise_on_inconsistency=False,
            )
            if db_area
        }

    @classmethod
    def map_existing_areas(
        cls,
        brooks_areas: Set[SimArea],
        db_areas: List[Dict],
        raise_on_inconsistency=False,
    ) -> Iterator[Tuple[SimArea, Union[Dict, None]]]:
        """
        Maps brooks areas to existing areas (existing area's representative point
        must be within brooks areas footprint). If in case of for a given brooks area zero OR more than one existing
        area is found None is yielded instead.
        """
        points_by_area_id = {
            area["id"]: Point(area["coord_x"], area["coord_y"]) for area in db_areas
        }  # generating the points before the for loop to improve performance
        for brooks_area in brooks_areas:
            mapped_areas = [
                db_area
                for db_area in db_areas
                if points_by_area_id[db_area["id"]].within(brooks_area.footprint)
            ]
            if len(mapped_areas) == 1:
                yield brooks_area, mapped_areas[0]
            else:
                if raise_on_inconsistency:
                    closest_db_area = sorted(
                        [area for area in db_areas],
                        key=lambda x: Point(x["coord_x"], x["coord_y"]).distance(
                            brooks_area.footprint
                        ),
                    )[:2]
                    closest_db_area = [
                        {key: area[key] for key in ("coord_x", "coord_y", "area_type")}
                        for area in closest_db_area
                    ]
                    raise AreaMismatchException(
                        f"{len(mapped_areas)} db areas are inside of layout area with "
                        f"polygon boundaries: {wkt.dumps(brooks_area.footprint)}. "
                        f"The DB area types are: {','.join([m['area_type'] for m in mapped_areas])}. "
                        f"The closest DB areas to the layout area being mapped: {closest_db_area[:2]}."
                    )
                # If due to changes in the annotations, 2 or more representative points fall into the same polygon we
                # yield None. Same case as if we had no matches
                yield brooks_area, None
        if raise_on_inconsistency and len(db_areas) != len(brooks_areas):
            raise AreaMismatchException(
                "There are more areas in the db than in the layout"
            )

    @classmethod
    def _get_new_areas_with_recovered_info(
        cls, plan_layout: SimLayout, plan_id: int, existing_areas: List[Dict]
    ) -> Tuple[List, List]:
        recovered_areas = []
        new_areas = []
        for brooks_area, existing_area in cls.map_existing_areas(
            brooks_areas=plan_layout.areas, db_areas=existing_areas
        ):
            point = cls.get_representative_point(brooks_area.footprint)
            area = {
                "coord_x": point.x,
                "coord_y": point.y,
                "plan_id": plan_id,
                "scaled_polygon": wkt.dumps(brooks_area.footprint),
            }

            area_point = cls.scale_area_coordinates(
                area=area,
                scale_factor=1 / plan_layout.scale_factor,
            )
            area = {**area, "coord_x": area_point.x, "coord_y": area_point.y}

            if existing_area:
                area["id"] = existing_area["id"]
                area["area_type"] = get_valid_area_type_from_string(
                    existing_area["area_type"]
                )
                recovered_areas.append(AreaDBHandler.schema.dump(area))
            else:
                area["area_type"] = brooks_area.type
                new_areas.append(AreaDBHandler.schema.dump(area))
        return (
            sorted(new_areas, key=lambda z: (z["coord_x"], z["coord_y"])),
            recovered_areas,
        )

    @classmethod
    @retry_on_db_operational_error()
    def recover_and_upsert_areas(
        cls,
        plan_id: int,
        set_area_types_from_react_areas: bool = False,
        plan_layout: Optional[SimLayout] = None,
    ):
        from handlers import PlanLayoutHandler

        with get_db_session_scope():
            if plan_layout is None:
                plan_layout = PlanLayoutHandler(plan_id=plan_id).get_layout(
                    set_area_types_by_features=False,
                    scaled=True,
                    set_area_types_from_react_areas=set_area_types_from_react_areas,
                )

            existing_areas: List[Dict[str, Any]] = cls.get_existing_db_areas(
                plan_id=plan_id,
                plan_layout=plan_layout,
            )

            new_areas, recovered_areas = cls._get_new_areas_with_recovered_info(
                plan_id=plan_id,
                plan_layout=plan_layout,
                existing_areas=existing_areas,
            )
            valid_area_ids = {area["id"] for area in recovered_areas}
            stale_area_ids = {
                area["id"]
                for area in existing_areas
                if area["id"] not in valid_area_ids
            }
            AreaDBHandler.delete_in(id=stale_area_ids)
            AreaDBHandler.bulk_insert(items=new_areas)

            to_update: Dict[str, Dict[int, Any]] = defaultdict(dict)
            for area in recovered_areas:
                for field, value in area.items():
                    to_update[field].update({area["id"]: value})
            AreaDBHandler.bulk_update(**to_update)

    @classmethod
    def update_relationship_with_units(
        cls, plan_id: int, apartment_no: int, area_ids: List[int]
    ):
        """Deletes all the entries in the M2M relationship for the area_ids given and reinserts the new relationship
        between units and areas"""
        unit_ids = list(
            UnitDBHandler.find_ids(plan_id=plan_id, apartment_no=apartment_no)
        )

        UnitAreaDBHandler.delete_in(area_id=area_ids)
        UnitAreaDBHandler.delete_in(unit_id=unit_ids)

        unit_areas_to_insert = [
            {"unit_id": unit_id, "area_id": area_id}
            for unit_id in unit_ids
            for area_id in area_ids
        ]

        UnitAreaDBHandler.bulk_insert(items=unit_areas_to_insert)

    @classmethod
    def get_representative_point(cls, polygon):
        point = polygon.representative_point()
        if not point.within(polygon):
            if polygon.centroid.within(polygon):
                point = polygon.centroid
            else:
                raise InvalidShapeException(
                    f"The area cannot safely produce a representative point. Centroid: {polygon.centroid.xy}"
                )
        return point

    @classmethod
    def get_auto_classified_plan_areas_where_not_defined(cls, plan_id: int):
        from brooks.area_classifier import AreaClassifier
        from handlers import PlanLayoutHandler

        layout_handler = PlanLayoutHandler(plan_id=plan_id)
        layout_scaled = layout_handler.get_layout(
            scaled=True,
            classified=True,
            raise_on_inconsistency=True,
            set_area_types_by_features=False,
        )
        db_area_id_to_brooks_area = {
            area.db_area_id: area for area in layout_scaled.areas
        }

        area_classifier = AreaClassifier()
        area_classifier.load()

        db_areas = layout_handler.areas_db
        for db_area in db_areas:
            if (
                get_valid_area_type_from_string(db_area["area_type"])
                == AreaType.NOT_DEFINED
                and db_area["id"] in db_area_id_to_brooks_area
            ):
                db_area["area_type"] = area_classifier.classify(
                    plan_layout=layout_scaled,
                    area=db_area_id_to_brooks_area[db_area["id"]],
                ).name

        # HACK: classification UI uses the _unscaled_ area coordinates to match
        #       the areas from auto classification. Thus, we update them here.
        layout_unscaled = layout_handler.get_layout(
            scaled=False,
            classified=True,
            raise_on_inconsistency=True,
            set_area_types_by_features=False,
        )
        db_area_id_to_unscaled_brooks_area = {
            area.db_area_id: area for area in layout_unscaled.areas
        }
        for db_area in db_areas:
            area = db_area_id_to_unscaled_brooks_area[db_area["id"]]
            db_area["coord_x"] = float(area.footprint.representative_point().xy[0][0])
            db_area["coord_y"] = float(area.footprint.representative_point().xy[1][0])

        return db_areas

    @classmethod
    def validate_plan_classifications(
        cls,
        plan_id: int,
        area_id_to_area_type: Optional[Dict[int, str]] = None,
        only_blocking: Optional[bool] = True,
    ) -> List[SpatialEntityViolation]:
        """If area_id_to_area_type is provided, overrides the area
        types locally in the plan layout.
        """
        from handlers import PlanLayoutHandler
        from handlers.validators import (
            PlanClassificationBalconyHasRailingValidator,
            PlanClassificationDoorNumberValidator,
            PlanClassificationFeatureConsistencyValidator,
            PlanClassificationRoomWindowValidator,
            PlanClassificationShaftValidator,
        )

        layout_handler = PlanLayoutHandler(plan_id=plan_id)
        if area_id_to_area_type:
            plan_layout = layout_handler.get_layout_with_area_types(
                area_id_to_area_type=area_id_to_area_type
            )
        else:
            plan_layout = layout_handler.get_layout(
                scaled=True,
                classified=True,
                georeferenced=False,
            )

        validators: Iterable[Any] = (
            PlanClassificationBalconyHasRailingValidator,
            PlanClassificationShaftValidator,
            PlanClassificationDoorNumberValidator,
            PlanClassificationFeatureConsistencyValidator,
            PlanClassificationRoomWindowValidator,
        )

        violations: List[SpatialEntityViolation] = [
            violation
            for validator in validators
            for violation in validator(
                plan_id=plan_id, plan_layout=plan_layout
            ).validate()
            if (not only_blocking) or (only_blocking and violation.is_blocking)
        ]
        planner_handler = ReactPlannerHandler()
        violations = [
            planner_handler.violation_position_to_pixels(  # type: ignore
                violation=violation,
                plan_id=plan_id,
            )
            for violation in violations
        ]
        return violations

    @classmethod
    def put_new_classifications(
        cls, plan_id: int, areas_type_from_user: Dict[int, str]
    ) -> List[SpatialEntityViolation]:
        violations: List[SpatialEntityViolation] = cls.validate_plan_classifications(
            plan_id=plan_id,
            area_id_to_area_type=areas_type_from_user,
            only_blocking=False,
        )
        areas_not_valid: Set[int] = set()
        for violation in violations:
            if violation.is_blocking:
                if isinstance(violation.entity, SimSpace):
                    areas_not_valid.update(
                        {area.db_area_id for area in violation.entity.areas}
                    )
                elif isinstance(violation.entity, SimArea):
                    areas_not_valid.add(violation.entity.db_area_id)

        areas_to_update = {
            area_id: area_type
            for area_id, area_type in areas_type_from_user.items()
            if area_id not in areas_not_valid
        }

        AreaDBHandler.bulk_update(area_type=areas_to_update)
        return violations

    @classmethod
    def get_unit_areas(cls, unit_id: int):
        with get_db_session_scope(readonly=True) as session:
            areas = (
                session.query(AreaDBModel, UnitsAreasDBModel)
                .join(UnitsAreasDBModel)
                .filter(UnitsAreasDBModel.unit_id == unit_id)
                .all()
            )
            result = []
            for area, _unit_area in areas:
                result.append(AreaDBHandler.schema.dump(area))
                result[-1]["labels"] = _unit_area.labels
            return result

    @classmethod
    def scale_area_coordinates(cls, area: Dict, scale_factor: float) -> Point:
        rotation_point: Point = Point(0, 0)
        return scale(
            geom=Point(area["coord_x"], area["coord_y"]),
            xfact=scale_factor,
            yfact=scale_factor,
            origin=rotation_point,
        )

    @classmethod
    def get_existing_db_areas(
        cls,
        plan_id: int,
        plan_layout: SimLayout,
    ) -> List[Dict[str, Any]]:
        existing_areas = AreaDBHandler.find(plan_id=plan_id)
        for area in existing_areas:
            scaled_area = cls.scale_area_coordinates(
                area=area,
                scale_factor=plan_layout.scale_factor,
            )
            area["coord_x"] = scaled_area.x
            area["coord_y"] = scaled_area.y
        return existing_areas
