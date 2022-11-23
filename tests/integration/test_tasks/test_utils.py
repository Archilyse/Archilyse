import pydot
import pytest

import tasks
from handlers.db import ClientDBHandler
from tasks.utils.utils import WorkflowPlotter
from tasks.workflow_tasks import WorkflowGenerator


@pytest.fixture
def run_id_as_integer(mocker):
    run_id_counter = 0

    def fake_run_id(*args, **kwargs):
        nonlocal run_id_counter
        run_id_counter += 1
        return run_id_counter

    mocker.patch.object(
        tasks.workflow_tasks,
        "create_run_id",
        side_effect=fake_run_id,
    )


@pytest.mark.parametrize(
    "site_conf, expected",
    [
        ([True, True, True, True, True], "canvas/full_options.dot"),
        ([True, True, True, False, False], "canvas/no_analysis.dot"),
        ([False, False, False, True, True], "canvas/analysis_only.dot"),
    ],
)
def test_workflow_plotter(
    site_conf,
    expected,
    site_with_3_units,
    fixtures_path,
    run_id_as_integer,
    recreate_fixtures=False,
):
    ClientDBHandler.update(
        new_values={
            "option_dxf": site_conf[0],
            "option_pdf": site_conf[1],
            "option_ifc": site_conf[2],
            "option_analysis": site_conf[3],
            "option_competition": site_conf[4],
        },
        item_pks={"id": site_with_3_units["site"]["client_id"]},
    )
    wf = WorkflowGenerator(site_id=site_with_3_units["site"]["id"])
    canvas = wf.get_full_chain_based_on_client_options()

    if recreate_fixtures:
        WorkflowPlotter(canvas).to_dot(
            output=fixtures_path.joinpath(expected),
        )

    graph_data = WorkflowPlotter(canvas).as_graph()
    (expected_graph_data,) = pydot.graph_from_dot_file(fixtures_path.joinpath(expected))
    assert graph_data.to_string() == expected_graph_data.to_string()
