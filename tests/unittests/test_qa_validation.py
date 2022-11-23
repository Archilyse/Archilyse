import pytest

from common_utils.constants import (
    DB_INDEX_ANF,
    DB_INDEX_HNF,
    DB_INDEX_NET_AREA,
    DB_INDEX_ROOM_NUMBER,
    QA_VALIDATION_CODES,
    UNIT_USAGE,
)
from common_utils.exceptions import QAMissingException
from handlers import QAHandler
from handlers.db import PlanDBHandler
from handlers.db.qa_handler import (
    INDEX_ANF_AREA,
    INDEX_HNF_AREA,
    INDEX_NET_AREA,
    INDEX_ROOM_NUMBER,
    QADBHandler,
)


@pytest.mark.parametrize(
    "expected_area,unit_area,expected",
    [
        (11.0, 11.0, None),
        (11.0, 10.0, None),
        (11.0, 12.0, None),
        (0.0, 0.0, QA_VALIDATION_CODES.INDEX_NO_AREA.value),
        (None, 0.0, QA_VALIDATION_CODES.INDEX_NO_AREA.value),
        (0.0, None, QA_VALIDATION_CODES.INDEX_NO_AREA.value),
        (None, None, QA_VALIDATION_CODES.INDEX_NO_AREA.value),
        (11.0, 0.0, QA_VALIDATION_CODES.DB_NO_AREA.value),
    ],
)
@pytest.mark.parametrize(
    "expected_dimension,actual_dimension",
    [(INDEX_HNF_AREA, DB_INDEX_HNF), (INDEX_NET_AREA, DB_INDEX_NET_AREA)],
)
def test_net_area_differences(
    expected_area, unit_area, expected, expected_dimension, actual_dimension
):
    qa_result = QAHandler._qa_unit_net_area_differences(
        unit_qa_values={expected_dimension: expected_area},
        unit_simulated_vector={actual_dimension: unit_area},
    )
    assert expected in qa_result if expected else expected == qa_result


@pytest.mark.parametrize(
    "expected_area,unit_area",
    [
        (11.0, 20.0),
        (11.0, 14.1),
    ],
)
@pytest.mark.parametrize(
    "expected_dimension,actual_dimension,expected",
    [
        (INDEX_HNF_AREA, DB_INDEX_HNF, QA_VALIDATION_CODES.HNF_AREA_MISMATCH.value),
        (
            INDEX_NET_AREA,
            DB_INDEX_NET_AREA,
            QA_VALIDATION_CODES.NET_AREA_MISMATCH.value,
        ),
    ],
)
def test_net_area_differences_mismatch(
    expected_area, unit_area, expected, expected_dimension, actual_dimension
):
    qa_result = QAHandler._qa_unit_net_area_differences(
        unit_qa_values={expected_dimension: expected_area},
        unit_simulated_vector={actual_dimension: unit_area},
    )
    assert expected in qa_result if expected else expected == qa_result


@pytest.mark.parametrize(
    "expected_rooms,unit_rooms,expected",
    [
        (1.0, 1.5, QA_VALIDATION_CODES.ROOMS_MISMATCH.value),
        (1.0, 1.0, None),
        (0.0, 0.0, QA_VALIDATION_CODES.INDEX_NO_ROOMS.value),
        (None, None, QA_VALIDATION_CODES.INDEX_NO_ROOMS.value),
        (None, 1.0, QA_VALIDATION_CODES.INDEX_NO_ROOMS.value),
        (1.0, None, QA_VALIDATION_CODES.DB_NO_ROOMS.value),
        (1.0, 2.0, QA_VALIDATION_CODES.ROOMS_MISMATCH.value),
        (3.0, 1.0, QA_VALIDATION_CODES.ROOMS_MISMATCH.value),
    ],
)
def test_number_rooms_difference(expected_rooms, unit_rooms, expected):
    qa_result = QAHandler._qa_unit_number_rooms_difference(
        unit_qa_values={INDEX_ROOM_NUMBER: expected_rooms},
        unit_simulated_vector={DB_INDEX_ROOM_NUMBER: unit_rooms},
    )

    assert expected in qa_result if expected else expected == qa_result


@pytest.mark.parametrize(
    "expected_anf,unit_anf,expected_qa_violation",
    [
        (None, None, None),
        (11.0, 10.5, None),
        (11.0, 12.1, QA_VALIDATION_CODES.ANF_MISMATCH.value),
        (0.0, 0.0, None),
        (None, 0.0, None),
        (0.0, None, QA_VALIDATION_CODES.ANF_MISMATCH.value),
        (11.0, 0.0, QA_VALIDATION_CODES.ANF_MISMATCH.value),
        (100.0, 97.0, None),
    ],
)
def test_qa_unit_anf_difference(expected_anf, unit_anf, expected_qa_violation):
    qa_result = QAHandler._qa_unit_anf_difference(
        unit_qa_values={INDEX_ANF_AREA: expected_anf},
        unit_simulated_vector={DB_INDEX_ANF: unit_anf},
    )
    assert (
        expected_qa_violation in qa_result
        if expected_qa_violation
        else expected_qa_violation == qa_result
    )


@pytest.mark.parametrize(
    "unit_simulated_vector,expected_values,results_expected",
    [
        (
            {
                "UnitBasics.number-of-kitchens": 0.0,
                "UnitBasics.number-of-bathrooms": 0.0,
                "UnitBasics.number-of-rooms": 0.0,
                "UnitBasics.net-area": 0.0,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_HNF_AREA: 10.0},
            [
                QA_VALIDATION_CODES.MISSING_BATHROOM,
                QA_VALIDATION_CODES.MISSING_KITCHEN,
                QA_VALIDATION_CODES.DB_NO_AREA,
                QA_VALIDATION_CODES.DB_NO_ROOMS,
            ],
        ),
        (
            {
                "UnitBasics.number-of-kitchens": 1.0,
                "UnitBasics.number-of-bathrooms": 1.0,
                "UnitBasics.number-of-rooms": 1.0,
                "UnitBasics.net-area": 15.0,
                "UnitBasics.area-sia416-HNF": 10.0,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_HNF_AREA: 10.0},
            [],
        ),
        (
            {
                "UnitBasics.number-of-kitchens": 1.0,
                "UnitBasics.number-of-bathrooms": 1.0,
                "UnitBasics.number-of-rooms": 1.0,
                "UnitBasics.net-area": 10.0,
                "UnitBasics.area-sia416-HNF": 15.0,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_NET_AREA: 10.0},
            [],
        ),
        (
            {
                "UnitBasics.number-of-kitchens": 1.0,
                "UnitBasics.number-of-bathrooms": 1.0,
                "UnitBasics.number-of-rooms": 1.0,
                "UnitBasics.net-area": 10.0,
                "UnitBasics.area-sia416-HNF": 14.1,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_HNF_AREA: 10.0},
            [QA_VALIDATION_CODES.HNF_AREA_MISMATCH],
        ),
        (
            {
                "UnitBasics.number-of-kitchens": 1.0,
                "UnitBasics.number-of-bathrooms": 1.0,
                "UnitBasics.number-of-rooms": 1.0,
                "UnitBasics.net-area": 14.1,
                "UnitBasics.area-sia416-HNF": 14.1,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_HNF_AREA: 10.0, INDEX_NET_AREA: 14.1},
            [QA_VALIDATION_CODES.HNF_AREA_MISMATCH],
        ),
        (
            {
                "UnitBasics.number-of-kitchens": 1.0,
                "UnitBasics.number-of-bathrooms": 1.0,
                "UnitBasics.number-of-rooms": 1.0,
                "UnitBasics.net-area": 14.1,
            },
            {INDEX_ROOM_NUMBER: 1.0, INDEX_NET_AREA: 17.1},
            [QA_VALIDATION_CODES.NET_AREA_MISMATCH],
        ),
    ],
)
def test_qa_validate_unit(
    mocker, unit_simulated_vector, expected_values, results_expected
):
    results = QAHandler(site_id=1)._qa_validate_unit(
        unit_qa_values=expected_values,
        unit_simulated_vector=unit_simulated_vector,
        unit_usage=UNIT_USAGE.RESIDENTIAL,
    )
    for result_expected in results_expected:
        assert any([result_expected.value in result for result in results])
    assert len(results) == len(results_expected)


@pytest.mark.parametrize(
    "plans_in_db,should_raise_exception",
    [
        (
            [
                {"without_units": True},
            ],
            False,
        ),
        ([{"without_units": False}], True),
        ([{"without_units": False}, {"without_units": True}], True),
    ],
)
def test_get_qa_data_missing(mocker, should_raise_exception, plans_in_db):
    qa_data_required = any(not p["without_units"] for p in plans_in_db)
    mocker.patch.object(PlanDBHandler, "exists", return_value=qa_data_required)
    mocker.patch.object(QADBHandler, "get_by", return_value={"data": {}})
    if should_raise_exception:
        with pytest.raises(QAMissingException, match="QA data missing for site 1"):

            QAHandler.get_qa_data_check_exists(site_id=1)

    else:
        qa_data = QAHandler.get_qa_data_check_exists(site_id=1)
        assert isinstance(qa_data, dict)
