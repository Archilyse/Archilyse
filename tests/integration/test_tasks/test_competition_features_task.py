from operator import itemgetter

import pytest
from deepdiff import DeepDiff

from common_utils.constants import ADMIN_SIM_STATUS, SIMULATION_VERSION, TASK_TYPE
from handlers import StatsHandler
from handlers.db import (
    CompetitionFeaturesDBHandler,
    SiteDBHandler,
    SlamSimulationDBHandler,
)
from tasks.competition_features_tasks import get_area_stats


def test_competition_features_task(
    celery_eager,
    site,
    site_prepared_for_competition,
    expected_competition_features_site_1,
):
    from tasks.workflow_tasks import WorkflowGenerator

    # when
    WorkflowGenerator(site_id=site["id"]).get_competition_features_task_chain().delay()

    # then
    all_simulations = sorted(
        SlamSimulationDBHandler.find(site_id=site["id"]), key=itemgetter("created")
    )
    # view_sun, Noise, competition, biggest rectangle
    assert len(all_simulations) == 6

    assert all_simulations[-1]["type"] == TASK_TYPE.COMPETITION.name
    assert all_simulations[-1]["state"] == ADMIN_SIM_STATUS.SUCCESS.name
    assert not all_simulations[-1]["errors"]

    competition_features = CompetitionFeaturesDBHandler.get_by(
        run_id=all_simulations[-1]["run_id"]
    )
    assert not DeepDiff(
        expected_competition_features_site_1,
        competition_features["results"],
        ignore_order=True,
        significant_digits=2,
    )


@pytest.mark.parametrize(
    "sim_version, legacy_requested",
    [(SIMULATION_VERSION.PH_2022_H1, True), (SIMULATION_VERSION.PH_01_2021, False)],
)
def test_get_stats_legacy_requested(mocker, site, sim_version, legacy_requested):
    SiteDBHandler.update(
        item_pks={"id": site["id"]}, new_values={"simulation_version": sim_version}
    )
    mocked_get_stats = mocker.patch.object(
        StatsHandler, StatsHandler.get_area_stats.__name__, return_value=None
    )
    get_area_stats(site_id=site["id"])

    assert (
        mocked_get_stats.call_args_list[0].kwargs["legacy_dimensions_compatible"]
        == legacy_requested
    )
