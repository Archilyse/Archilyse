from collections import defaultdict
from typing import Dict, List, Set

from common_utils.constants import UNIT_USAGE
from common_utils.exceptions import DBException
from connectors.db_connector import get_db_session_scope
from handlers.db import SiteDBHandler, UnitDBHandler
from handlers.db.utils import retry_on_db_operational_error


class CVResultUploadHandler:
    @staticmethod
    def _validate_custom_valuator_results(
        expected_client_unit_ids: Set[str], custom_valuator_results: List[Dict]
    ):
        # 1. check if unknown client ids exist
        unknown_client_ids = [
            values["client_unit_id"]
            for values in custom_valuator_results
            if values["client_unit_id"] not in expected_client_unit_ids
        ]
        if unknown_client_ids:
            raise DBException(
                f"custom_valuator_results contains unknown client unit ids. "
                f"The following ids either do not exist OR are related to another site (first 10 results): "
                f"{unknown_client_ids[0:10]}"
            )

        # 2. check if all expected ids exist
        uploaded_client_ids = {v["client_unit_id"] for v in custom_valuator_results}
        missing_client_ids = [
            client_id
            for client_id in expected_client_unit_ids
            if client_id not in uploaded_client_ids
        ]
        if missing_client_ids:
            raise DBException(
                f"custom_valuator_results does not contain all expected client unit ids. "
                f"The following ids are missing in the input (first 10 results): {missing_client_ids[0:10]}"
            )

        # 3. validate duplicates
        if len(custom_valuator_results) != len(expected_client_unit_ids):
            raise DBException(
                f"custom_valuator_results contains "
                f"{len(custom_valuator_results) - len(expected_client_unit_ids)} "
                f"more elements than expected. Does the file contain duplicates?"
            )

    @classmethod
    def _get_expected_client_ids(cls, site_id: int) -> Dict[str, List[int]]:
        site_info = SiteDBHandler.get_by(
            id=site_id, output_columns=["sub_sampling_number_of_clusters"]
        )
        client_id_field = "client_id"
        if site_info["sub_sampling_number_of_clusters"]:
            client_id_field = "representative_unit_client_id"

        unit_ids = defaultdict(list)
        for unit_info in UnitDBHandler.find(
            site_id=site_id,
            output_columns=[
                "id",
                "client_id",
                "unit_usage",
                "representative_unit_client_id",
            ],
        ):
            if unit_info["unit_usage"] == UNIT_USAGE.RESIDENTIAL.name:
                unit_ids[unit_info[client_id_field]].append(unit_info["id"])

        return unit_ids

    @classmethod
    @retry_on_db_operational_error()
    def update_custom_valuator_results(
        cls, site_id: int, custom_valuator_results: List[Dict]
    ):
        if not custom_valuator_results:
            raise DBException("custom_valuator_results must not be empty.")

        fields_to_update = set(custom_valuator_results[0].keys()) - {"client_unit_id"}

        with get_db_session_scope():
            # 1. get unit ids from db
            unit_ids = cls._get_expected_client_ids(site_id=site_id)
            # 2. validate ph results contains the expected client ids
            cls._validate_custom_valuator_results(
                expected_client_unit_ids={*unit_ids.keys()},
                custom_valuator_results=custom_valuator_results,
            )
            # 3. update the database
            UnitDBHandler.bulk_update(
                **{
                    field: {
                        unit_id: values[field]
                        for values in custom_valuator_results
                        for unit_id in unit_ids[values["client_unit_id"]]
                    }
                    for field in fields_to_update
                }
            )
