from copy import deepcopy

import pytest

from handlers import QAHandler
from handlers.db import BuildingDBHandler


def test_add_matching_plan_ids(site, building, floor):
    client_building_id = "1"
    BuildingDBHandler.update(
        item_pks={"id": building["id"]},
        new_values={"client_building_id": client_building_id},
    )
    input_qa_data = {
        "site_id": site["id"],
        "data": {
            "2102090.01.01.0001": {
                "client_building_id": client_building_id,
                "floor": None,
            },
            "2102090.01.01.0002": {
                "client_building_id": client_building_id,
                "floor": 1,
            },
        },
    }
    new_qa_data = QAHandler._add_matching_plan_ids(qa_data=deepcopy(input_qa_data))
    expected_data = input_qa_data
    expected_data["data"]["2102090.01.01.0001"]["plan_id"] = None
    expected_data["data"]["2102090.01.01.0002"]["plan_id"] = floor["plan_id"]
    assert input_qa_data == new_qa_data


@pytest.mark.parametrize(
    "has_units, expected_warnings",
    [
        (
            False,
            ["Floor number 1 in building some street 20-22 doesn't contain any units"],
        ),
        (True, []),
    ],
)
def test_floors_without_units_warnings(
    site, floor, has_units, expected_warnings, make_units
):
    if has_units:
        make_units(*(floor,))
    warnings = list(QAHandler(site_id=site["id"]).floors_without_units_warnings())
    assert len(warnings) == len(expected_warnings)
    for i, warning in enumerate(warnings):
        assert warning == expected_warnings[i]
