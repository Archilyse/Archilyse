import io
import json
from http import HTTPStatus

import pytest
import requests

from common_utils.logger import logger
from handlers.db import SlamSimulationValidationDBHandler
from tasks.post_simulations_validations import validators


@pytest.mark.parametrize(
    "response_code, response_json, expected_error",
    [
        (HTTPStatus.OK, {"ok": True}, False),
        (HTTPStatus.OK, {"ok": True}, False),
        (HTTPStatus.OK, {"ok": False}, True),
        (HTTPStatus.NOT_FOUND, {"ok": False}, True),
        (HTTPStatus.NOT_FOUND, {"ok": True}, True),
    ],
)
def test_validate_simulation_task(
    mocker,
    site,
    validation_unit_stats,
    validation_unit_stats_results,
    response_code,
    response_json,
    expected_error,
):
    from tasks import post_simulations_validations

    mocker.patch.object(
        post_simulations_validations,
        "get_aggregated_stats",
        return_value=validation_unit_stats,
    )

    response = requests.Response()
    response.status_code = response_code
    response.raw = io.BytesIO(json.dumps(response_json).encode())
    mocker.patch.object(
        requests,
        requests.post.__name__,
        return_value=response,
    )

    if expected_error:
        spy_logger = mocker.spy(logger, logger.error.__name__)
        post_simulations_validations.validate_simulations_task(site_id=site["id"])
        assert spy_logger.call_count == 1
        assert "Cant connect to slack: {'ok':" in spy_logger.call_args[0][0]
    else:
        post_simulations_validations.validate_simulations_task(site_id=site["id"])

    result = SlamSimulationValidationDBHandler.get_by(site_id=site["id"])["results"]
    assert result == validation_unit_stats_results


def test_validate_simulation_task_no_message(
    mocker,
    validation_unit_stats,
    site,
):
    from tasks import post_simulations_validations

    mocker.patch.object(
        post_simulations_validations,
        "get_aggregated_stats",
        return_value=validation_unit_stats,
    )
    for val in validators:
        mocker.patch.object(val, val.validate.__name__, return_value={})

    slack_message_spy = mocker.spy(
        post_simulations_validations,
        "post_message_to_slack",
    )

    SlamSimulationValidationDBHandler.add(
        site_id=site["id"], results={"There": "are errors"}
    )

    post_simulations_validations.validate_simulations_task(site_id=site["id"])

    slack_message_spy.assert_not_called()
