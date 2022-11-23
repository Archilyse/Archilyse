import pytest

from common_utils.constants import (
    DEFAULT_RESULT_VECTORS,
    SIMULATION_VERSION,
    UNIT_USAGE,
)
from handlers.db import FloorDBHandler, SiteDBHandler, UnitDBHandler
from handlers.ph_vector import PHResultVectorHandler
from tasks.utils.deliverable_utils import get_index_by_result_type


@pytest.mark.parametrize("representative_units_only", [True, False])
def test_get_index_by_result_type_excludes_non_representative_units(
    mocker, representative_units_only
):
    # given
    representative_unit_client_id = "REPRESENT"
    non_representative_unit_client_id = "DOESNT REPRESENT"

    mocker.patch.object(PHResultVectorHandler, "__init__", return_value=None)
    mocker.patch.object(
        PHResultVectorHandler,
        PHResultVectorHandler.generate_vectors.__name__,
        return_value={
            vector_type: {
                client_id: [{}] if vector_type.name.startswith("ROOM") else {}
                for client_id in [
                    representative_unit_client_id,
                    non_representative_unit_client_id,
                ]
            }
            for vector_type in DEFAULT_RESULT_VECTORS
        },
    )

    mocker.patch.object(
        UnitDBHandler,
        UnitDBHandler.find.__name__,
        return_value=[
            {
                "client_id": client_id,
                "floor_id": i,
                "unit_usage": UNIT_USAGE.RESIDENTIAL.name,
                "apartment_no": i,
                "representative_unit_client_id": representative_unit_client_id,
            }
            for i, client_id in enumerate(
                [representative_unit_client_id, non_representative_unit_client_id],
                start=1,
            )
        ],
    )
    mocker.patch.object(
        FloorDBHandler,
        FloorDBHandler.find_by_site_id.__name__,
        return_value=[
            {"id": 1, "floor_number": 1},
            {"id": 2, "floor_number": 2},
        ],
    )
    mocker.patch.object(
        SiteDBHandler,
        SiteDBHandler.get_by.__name__,
        return_value={"simulation_version": SIMULATION_VERSION.PH_01_2021.value},
    )

    if representative_units_only:
        expected_client_ids = [representative_unit_client_id]
    else:
        expected_client_ids = [
            representative_unit_client_id,
            non_representative_unit_client_id,
        ]

    # when
    vectors = get_index_by_result_type(
        site_id=mocker.ANY, representative_units_only=representative_units_only
    )

    # then
    assert dict(vectors) == {
        vector.value: [
            {"apartment_no": i, "client_id": client_id, "floor_number": i}
            for i, client_id in enumerate(expected_client_ids, start=1)
        ]
        for vector in DEFAULT_RESULT_VECTORS
    }
