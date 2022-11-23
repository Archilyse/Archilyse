import contextlib
from collections import defaultdict
from typing import Any, Dict, Iterable, Iterator, List, Set, Tuple, Union

import pandas as pd

from brooks.classifications import UnifiedClassificationScheme
from brooks.util.io import BrooksJSONEncoder
from common_utils.constants import (
    ANF_DIFFERENCE_SQ_M_THRESHOLD,
    ANF_DIFFERENCE_THRESHOLD,
    DB_INDEX_ANF,
    DB_INDEX_FF,
    DB_INDEX_HNF,
    DB_INDEX_NET_AREA,
    DB_INDEX_NNF,
    DB_INDEX_ROOM_NUMBER,
    DB_INDEX_VF,
    MIN_NET_AREA_DIFFERENCE_SQ_M_THRESHOLD,
    NET_AREA_DIFFERENCE_THRESHOLD,
    QA_VALIDATION_CODES,
    ROOM_NUMBER_THRESHOLD,
    TASK_TYPE,
    UNIT_USAGE,
)
from common_utils.exceptions import (
    AreaMismatchException,
    DBNotFoundException,
    QAMissingException,
)
from handlers import AreaHandler
from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    QADBHandler,
    UnitDBHandler,
)
from handlers.db.qa_handler import (
    INDEX_ANF_AREA,
    INDEX_HNF_AREA,
    INDEX_NET_AREA,
    INDEX_ROOM_NUMBER,
)
from handlers.plan_handler import PlanHandlerSiteCacheMixin
from handlers.simulations.slam_simulation_handler import SlamSimulationHandler


class QAHandler(PlanHandlerSiteCacheMixin):
    def __init__(self, site_id: int):
        super().__init__(site_id=site_id)
        self.classification_scheme = UnifiedClassificationScheme()

    @classmethod
    def get_qa_data_check_exists(cls, site_id: int):
        qa_index_info = QADBHandler.get_by(site_id=site_id)["data"] or {}
        if not qa_index_info and PlanDBHandler.exists(
            site_id=site_id, without_units=False
        ):
            raise QAMissingException(
                f"QA data missing for site {site_id}", site_id=site_id
            )
        return qa_index_info

    def qa_validation(self) -> Dict[str, List[str]]:
        return self.qa_site_and_unit_errors(
            qa_index_info=self.get_qa_data_check_exists(site_id=self.site_id)
        )

    @classmethod
    def update(cls, qa_id: int, new_values: Dict) -> Dict:
        if new_values.get("data"):
            for _apartment_client_id, apartment_qa_data in new_values["data"].items():
                apartment_qa_data.pop("plan_id", None)
        return QADBHandler.update(item_pks=dict(id=qa_id), new_values=new_values)

    @classmethod
    def get_qa_data(
        cls, site_id: int = None, client_id_and_client_site_id: Tuple[int, str] = None
    ) -> Dict:
        if site_id is not None:
            qa_data = QADBHandler.get_by(site_id=site_id)
        elif client_id_and_client_site_id is not None:
            qa_data = QADBHandler.get_by(
                client_id=client_id_and_client_site_id[0],
                client_site_id=client_id_and_client_site_id[1],
            )
        else:
            raise Exception("Method requires at least one argument")

        if qa_data.get("data"):
            qa_data = cls._add_matching_plan_ids(qa_data=qa_data)

        return qa_data

    @classmethod
    def get_qa_data_by_building(cls, building: Dict) -> Dict[str, Dict[str, Any]]:
        site_id = building["site_id"]
        qa_data = QADBHandler.get_by(site_id=site_id)
        if not qa_data["data"]:
            raise QAMissingException(site_id=site_id)
        return {
            unit_client_id: qa_data
            for unit_client_id, qa_data in qa_data["data"].items()
            if qa_data["client_building_id"] == building["client_building_id"]
        }

    @staticmethod
    def _add_matching_plan_ids(qa_data: Dict[str, Dict]) -> Dict:
        if site_id := qa_data["site_id"]:
            building_id_by_client_building_id = {
                b["client_building_id"]: b["id"]
                for b in BuildingDBHandler.find(
                    output_columns=["id", "client_building_id"], site_id=site_id
                )
            }
            plan_id_by_building_and_floor_number: Dict[
                int, Dict[int, int]
            ] = defaultdict(dict)
            for floor in FloorDBHandler.find_in(
                building_id=building_id_by_client_building_id.values(),
                output_columns=["floor_number", "building_id", "plan_id"],
            ):
                plan_id_by_building_and_floor_number[floor["building_id"]][
                    floor["floor_number"]
                ] = floor["plan_id"]

            for apartment_qa_data in qa_data["data"].values():
                apartment_qa_data["plan_id"] = None
                if building_id := building_id_by_client_building_id.get(
                    apartment_qa_data["client_building_id"]
                ):
                    with contextlib.suppress(TypeError):
                        apartment_qa_data[
                            "plan_id"
                        ] = plan_id_by_building_and_floor_number[building_id].get(
                            apartment_qa_data["floor"]
                        )

        return qa_data

    @classmethod
    def _qa_unit_net_area_differences(
        cls,
        unit_qa_values: Dict[str, Any],
        unit_simulated_vector: Dict[str, Any],
    ):
        net_area_by_dimension = cls._get_net_area_by_dimension(
            expected_vector=unit_qa_values
        )
        if not net_area_by_dimension:
            return QA_VALIDATION_CODES.INDEX_NO_AREA.value

        unit_vector_dimension, expected_area, error_code = net_area_by_dimension

        db_area = unit_simulated_vector.get(unit_vector_dimension, None)
        if not db_area:
            return QA_VALIDATION_CODES.DB_NO_AREA.value

        absolute_net_area_difference = abs(expected_area - db_area)
        relative_net_area_difference = absolute_net_area_difference / expected_area
        if (
            relative_net_area_difference > NET_AREA_DIFFERENCE_THRESHOLD
            and absolute_net_area_difference > MIN_NET_AREA_DIFFERENCE_SQ_M_THRESHOLD
        ):
            scaling_factor_deviation = round(expected_area / db_area, 2)

            return (
                error_code.value
                + f" Should have {expected_area} m2 and it has {round(db_area, 1)} m2. "
                + f"Scale deviation factor: {scaling_factor_deviation}. "
            )

    @staticmethod
    def _get_net_area_by_dimension(
        expected_vector: Dict,
    ) -> Union[Tuple[str, float, QA_VALIDATION_CODES], None]:
        index_by_db_net_area_dimensions = (
            (DB_INDEX_HNF, INDEX_HNF_AREA, QA_VALIDATION_CODES.HNF_AREA_MISMATCH),
            (DB_INDEX_NET_AREA, INDEX_NET_AREA, QA_VALIDATION_CODES.NET_AREA_MISMATCH),
        )
        for (
            unit_vector_dimension,
            net_area_dimension,
            error_code,
        ) in index_by_db_net_area_dimensions:
            with contextlib.suppress(KeyError, ValueError, TypeError):
                if unit_net_area_dimension_value := float(
                    expected_vector[net_area_dimension]
                ):
                    return (
                        unit_vector_dimension,
                        unit_net_area_dimension_value,
                        error_code,
                    )
        return None

    @staticmethod
    def _qa_unit_anf_difference(
        unit_qa_values: Dict[str, Any],
        unit_simulated_vector: Dict[str, Any],
    ):
        expected_anf = unit_qa_values.get(INDEX_ANF_AREA, None)
        if expected_anf is not None:
            unit_anf = unit_simulated_vector.get(DB_INDEX_ANF)
            if unit_anf is None:
                return (
                    QA_VALIDATION_CODES.ANF_MISMATCH.value
                    + f" Should have {expected_anf} m2 but it has "
                    f"not been calculated for the unit. "
                )
            if absolute_anf_difference := abs(expected_anf - unit_anf):
                try:
                    relative_anf_difference = absolute_anf_difference / expected_anf
                except ZeroDivisionError:
                    return (
                        QA_VALIDATION_CODES.ANF_MISMATCH.value
                        + f" Should have {expected_anf} m2 and it has "
                        f"{round(unit_anf, 1)} m2. It's off by: {round(absolute_anf_difference, 1)} m2. "
                    )
                if (
                    relative_anf_difference > ANF_DIFFERENCE_THRESHOLD
                    and absolute_anf_difference > ANF_DIFFERENCE_SQ_M_THRESHOLD
                ):
                    return (
                        QA_VALIDATION_CODES.ANF_MISMATCH.value
                        + f" Should have {expected_anf} m2 and it has "
                        f"{round(unit_anf, 1)} m2. It's off by: {round(relative_anf_difference * 100, 2)} %. "
                    )

    @staticmethod
    def _qa_unit_number_rooms_difference(
        unit_qa_values: Dict[str, float], unit_simulated_vector: Dict[str, float]
    ):
        try:
            rooms_expected = float(unit_qa_values[INDEX_ROOM_NUMBER])
            if not rooms_expected:
                return QA_VALIDATION_CODES.INDEX_NO_ROOMS.value
        except (KeyError, ValueError, TypeError):
            return QA_VALIDATION_CODES.INDEX_NO_ROOMS.value

        db_rooms = unit_simulated_vector[DB_INDEX_ROOM_NUMBER]
        if not db_rooms:
            return QA_VALIDATION_CODES.DB_NO_ROOMS.value

        absolute_room_number_difference = abs(rooms_expected - db_rooms)
        if absolute_room_number_difference > ROOM_NUMBER_THRESHOLD:
            return (
                QA_VALIDATION_CODES.ROOMS_MISMATCH.value
                + f" Should have {rooms_expected} rooms and it has {db_rooms} rooms"
            )

    def _qa_validate_unit(
        self,
        unit_simulated_vector: Dict,
        unit_qa_values: Dict[str, float],
        unit_usage: UNIT_USAGE,
    ) -> List:
        unit_error = []
        if (
            unit_usage == UNIT_USAGE.RESIDENTIAL
            and not unit_simulated_vector["UnitBasics.number-of-kitchens"]
        ):
            unit_error.append(QA_VALIDATION_CODES.MISSING_KITCHEN.value)

        if (
            unit_usage == UNIT_USAGE.RESIDENTIAL
            and not unit_simulated_vector["UnitBasics.number-of-bathrooms"]
        ):
            unit_error.append(QA_VALIDATION_CODES.MISSING_BATHROOM.value)

        for qa_check in [
            self._qa_unit_number_rooms_difference,
            self._qa_unit_net_area_differences,
            self._qa_unit_anf_difference,
        ]:
            if qa_violation := qa_check(
                unit_qa_values=unit_qa_values,
                unit_simulated_vector=unit_simulated_vector,
            ):
                unit_error.append(qa_violation)

        return unit_error

    def _qa_validate_all_units(
        self,
        units_in_db: List[Dict],
        units_basic_features_results: Dict[int, List[Dict]],
        qa_index_info: Dict[str, Dict],
    ) -> Dict[str, List]:
        all_units_stats: Dict[str, List] = defaultdict(list)
        for unit_info in units_in_db:
            units_basic_features = units_basic_features_results.get(unit_info["id"])
            if not units_basic_features:
                all_units_stats[unit_info["client_id"]] = [
                    QA_VALIDATION_CODES.UNIT_NOT_SIMULATED.value
                ]
            else:
                try:
                    expected_values = qa_index_info[unit_info["client_id"]]
                except KeyError:
                    continue
                unit_stats = self._qa_validate_unit(
                    unit_simulated_vector=units_basic_features[0],
                    unit_qa_values=expected_values,
                    unit_usage=UNIT_USAGE[unit_info["unit_usage"]],
                )
                all_units_stats[unit_info["client_id"]].extend(unit_stats)
        return all_units_stats

    def buildings_wo_plans(self) -> Set[int]:
        return {
            building_id
            for building_id in self.building_ids
            if not self.plan_ids_per_building[building_id]
        }

    def plans_wo_floors(self) -> Set[int]:
        return {
            plan_id
            for plan_id in self.plan_ids
            if not any(FloorDBHandler.find_ids(plan_id=plan_id))
        }

    def site_wo_buildings(self) -> List[int]:
        if not any(self.building_ids):
            return [self.site_id]
        else:
            return []

    def general_site_problems(
        self, client_ids_in_db: Set[str], qa_index_unit_ids: Set[str]
    ) -> Dict[str, Iterable[Union[str, int]]]:
        from handlers.validators import GeoreferencingValidator

        geo_validator = GeoreferencingValidator(site_id=self.site_id)
        geo_validator._layout_handler_by_id = self._layout_handler_by_id
        return {
            "missing_units": qa_index_unit_ids - client_ids_in_db,
            "extra_units": client_ids_in_db - qa_index_unit_ids,
            "buildings_wo_plans": self.buildings_wo_plans(),
            "plans_wo_floors": self.plans_wo_floors(),
            "site_wo_buildings": self.site_wo_buildings(),
            "annotation_errors": self.annotation_errors(),
            "classification_errors": self.classification_errors(),
            "georeferencing_errors": geo_validator.georeferencing_errors(),
            "room_warnings": self.room_warnings(),
            "units_with_linking_errors": self.units_with_linking_errors(),
        }

    def qa_site_and_unit_errors(
        self,
        qa_index_info: Dict[str, Dict],
    ) -> Dict[str, List[str]]:
        units_in_db = UnitDBHandler.find(site_id=self.site_id)
        qa_validation: Dict[str, List] = defaultdict(list)

        qa_validation.update(
            self._qa_validate_all_units(
                units_in_db=units_in_db,
                units_basic_features_results={
                    unit_sim_results["unit_id"]: unit_sim_results["results"]
                    for unit_sim_results in SlamSimulationHandler.get_all_results(
                        site_id=self.site_id,
                        task_type=TASK_TYPE.BASIC_FEATURES,
                        check_status=False,
                    )
                },
                qa_index_info=qa_index_info,
            )
        )

        site_problems = self.general_site_problems(
            client_ids_in_db={x["client_id"] for x in units_in_db},
            qa_index_unit_ids=set(qa_index_info.keys()),
        )

        validation_text_mapping = {
            "missing_units": QA_VALIDATION_CODES.CLIENT_IDS_MISSING.value,
            "extra_units": QA_VALIDATION_CODES.CLIENT_IDS_UNEXPECTED.value,
        }

        for validation_type, default_text in validation_text_mapping.items():
            if client_ids := site_problems[validation_type]:
                qa_validation["site_warnings"].append(
                    default_text + f": {sorted(map(str, client_ids))}"
                )

        if site_problems["room_warnings"]:
            qa_validation["site_warnings"].extend(site_problems["room_warnings"])

        for warning in self.floors_without_units_warnings():

            qa_validation["site_warnings"].append(warning)

        blocking_errors = {
            "buildings_wo_plans": QA_VALIDATION_CODES.BUILDING_WO_PLANS.value,
            "plans_wo_floors": QA_VALIDATION_CODES.PLAN_WO_FLOORS.value,
            "site_wo_buildings": QA_VALIDATION_CODES.SITE_WO_BUILDINGS.value,
            "annotation_errors": QA_VALIDATION_CODES.ANNOTATIONS_ERROR.value,
            "georeferencing_errors": QA_VALIDATION_CODES.GEOREFERENCE_ERROR.value,
            "classification_errors": QA_VALIDATION_CODES.CLASSIFICATION_ERROR.value,
            "units_with_linking_errors": QA_VALIDATION_CODES.LINKING_ERROR.value,
        }

        for validation_type, default_text in blocking_errors.items():
            if error_msgs := site_problems[validation_type]:
                qa_validation["errors"].append(default_text + f": {error_msgs}")

        return qa_validation

    def annotation_errors(self) -> Dict[int, List[str]]:
        errors_by_plan = {}
        for plan_id in self.plan_ids:

            errors = (
                self.layout_handler_by_id(plan_id=plan_id)
                .get_layout(validate=True, classified=False, scaled=False)
                .errors
            )
            if errors:
                errors_by_plan[plan_id] = BrooksJSONEncoder.default(errors)

        return errors_by_plan

    def classification_errors(self) -> Dict[int, str]:
        errors_by_plan = {}
        for plan_id in self.plan_ids:
            try:
                area_id_to_area_type = {
                    area["id"]: area["area_type"]
                    for area in self.layout_handler_by_id(plan_id=plan_id).areas_db
                }
                violations = AreaHandler.validate_plan_classifications(
                    plan_id=plan_id,
                    area_id_to_area_type=area_id_to_area_type,
                    only_blocking=True,
                )
                if violations:
                    for violation in violations:
                        errors_by_plan[plan_id] = str(violation.text)
            except AreaMismatchException:
                errors_by_plan[plan_id] = (
                    "There is an area mismatch with the Database. "
                    "This should be solved by saving and validating annotations again"
                )
        return errors_by_plan

    def units_with_linking_errors(self) -> List[str]:
        from handlers.validators.linking.unit_linking_validator import (
            UnitLinkingValidator,
        )

        units = UnitDBHandler.find(
            site_id=self.site_id,
            output_columns=["id", "client_id", "unit_usage", "plan_id"],
        )
        units_by_plan_id = defaultdict(list)
        for unit in units:
            units_by_plan_id[unit["plan_id"]].append(unit)
        units_with_errors = []
        for plan_id, plan_units in units_by_plan_id.items():
            violation_by_units = UnitLinkingValidator.violations_by_unit_client_id(
                unit_list=plan_units, plan_id=plan_id
            )
            units_with_errors.extend(list(violation_by_units.keys()))
        return units_with_errors

    @staticmethod
    def map_apartments_to_index(
        apartments: Dict[int, float], qa_data: Dict[str, Dict]
    ) -> Iterator[Dict[str, Union[str, int]]]:
        candidates = dict(apartments)
        for client_unit_id, qa_values in qa_data.items():
            if unit_id := min(
                candidates.items(),
                key=lambda candidate: abs(candidate[1] - qa_values["HNF"]),
                default=(0, None),
            )[0]:
                del candidates[unit_id]
                yield {"unit_id": unit_id, "unit_client_id": client_unit_id}

    @staticmethod
    def map_maisonettes_to_index(maisonettes: Dict, qa_data: Dict) -> Iterator[Dict]:
        candidates = dict(maisonettes)
        for client_unit_id, qa_values in qa_data.items():
            if unit_id := min(
                filter(
                    lambda candidate: candidate[1]["number_of_rooms"]
                    == qa_values.get("number_of_rooms"),
                    candidates.items(),
                ),
                key=lambda candidate: abs(candidate[1]["net_area"] - qa_values["HNF"]),
                default=(None, None),
            )[0]:
                del candidates[unit_id]
                yield {"unit_id": unit_id, "unit_client_id": client_unit_id}

    def room_warnings(self) -> List[str]:
        warnings = []
        for plan_id in self.plan_ids:
            for violation in AreaHandler.validate_plan_classifications(
                plan_id=plan_id,
                only_blocking=False,
            ):
                warnings.append(f"plan {plan_id}: {violation.text}")

        return warnings

    def generate_qa_report(self) -> pd.DataFrame:
        """Generates a report comparing QA data with final vector data"""

        from handlers.ph_vector import PHResultVectorHandler

        qa_columns = [INDEX_ROOM_NUMBER, INDEX_NET_AREA, INDEX_HNF_AREA, INDEX_ANF_AREA]
        try:
            qa_data = QADBHandler.get_by(site_id=self.site_id)["data"]

        except DBNotFoundException:
            qa_data = {}

        if qa_data:
            df_qa_data = pd.DataFrame(data=qa_data).T
        else:
            df_qa_data = pd.DataFrame(columns=qa_columns)

        df_expected = df_qa_data[qa_columns]

        index_columns = [
            DB_INDEX_ROOM_NUMBER,
            DB_INDEX_NET_AREA,
            DB_INDEX_HNF,
            DB_INDEX_NNF,
            DB_INDEX_ANF,
            DB_INDEX_VF,
            DB_INDEX_FF,
        ]
        if unit_vectors := PHResultVectorHandler(site_id=self.site_id).basic_features:
            df_unit_vectors = pd.DataFrame(unit_vectors).T
            df_actual = df_unit_vectors[index_columns]
            df_actual = df_actual.rename(
                columns={
                    DB_INDEX_ROOM_NUMBER: INDEX_ROOM_NUMBER,
                    DB_INDEX_NET_AREA: INDEX_NET_AREA,
                    DB_INDEX_HNF: INDEX_HNF_AREA,
                    DB_INDEX_ANF: INDEX_ANF_AREA,
                    DB_INDEX_VF: "VF",
                    DB_INDEX_FF: "FF",
                    DB_INDEX_NNF: "NNF",
                },
            )

            return df_expected.merge(
                df_actual,
                left_index=True,
                right_index=True,
                suffixes=("_QA", None),
                how="outer",
            )
        return df_expected

    def floors_without_units_warnings(self) -> Iterator[str]:
        for building in BuildingDBHandler.find(
            site_id=self.site_id, output_columns=["id", "street", "housenumber"]
        ):
            for floor in FloorDBHandler.find(
                building_id=building["id"], output_columns=["id", "floor_number"]
            ):
                if (
                    len(UnitDBHandler.find(floor_id=floor["id"], output_columns=["id"]))
                    == 0
                ):
                    yield (
                        f"Floor number {floor['floor_number']} in building {building['street']} "
                        f"{building['housenumber']} doesn't contain any units"
                    )
