from collections import defaultdict

from common_utils.constants import TASK_TYPE, VIEW_DIMENSION
from common_utils.exceptions import DBNotFoundException
from common_utils.utils import post_message_to_slack
from handlers import StatsHandler
from handlers.db.slam_simulation_validation import SlamSimulationValidationDBHandler
from handlers.sim_validators import (
    SUN_DIMENSION_JUNE_MIDDAY,
    UnitsHighSiteViewValidator,
    UnitsLowSunValidator,
)
from simulations.suntimes.suntimes_handler import SuntimesHandler
from tasks.utils.utils import celery_retry_task

validators = [UnitsHighSiteViewValidator, UnitsLowSunValidator]


@celery_retry_task
def validate_simulations_task(self, site_id: int):
    units_stats = get_aggregated_stats(site_id=site_id)

    violations = defaultdict(list)
    for validator in validators:
        new_violations = validator(units_stats=units_stats).validate()
        for unit_id, msg in new_violations.items():
            violations[unit_id].append(msg)
    try:
        old_validation = SlamSimulationValidationDBHandler.get_by(site_id=site_id)[
            "results"
        ]
    except DBNotFoundException:
        old_validation = {}

    if not violations and not old_validation:
        # Avoids creating a lot of empty entries in the DB
        return
    SlamSimulationValidationDBHandler.upsert(
        site_id=site_id, new_values={"results": violations}
    )

    if violations:
        from handlers.db import ClientDBHandler, SiteDBHandler

        site = SiteDBHandler.get_by(id=site_id)
        client = ClientDBHandler.get_by(id=site["client_id"])
        post_message_to_slack(
            f"Site {site['client_site_id']} - {site_id} from client {client['name']} may have some heatmap issues. "
            f"Please review: https://app.archilyse.com/dashboard/qa/{site_id}",
            channel="heatmaps-analysis",
        )


def get_aggregated_stats(site_id: int):
    unit_stats = StatsHandler.get_unit_stats(
        site_id=site_id,
        interior_only=True,
        task_type=TASK_TYPE.VIEW_SUN,
        desired_dimensions={VIEW_DIMENSION.VIEW_SITE.value},
    )
    sun_dimension = SuntimesHandler.get_first_sun_key_summer_midday(site_id=site_id)
    sun_stats = StatsHandler.get_unit_stats(
        site_id=site_id,
        interior_only=True,
        task_type=TASK_TYPE.SUN_V2,
        desired_dimensions={sun_dimension},
    )
    for unit_id, view_values in unit_stats.items():
        # Renames the sun dimension for easier use later
        view_values[SUN_DIMENSION_JUNE_MIDDAY] = sun_stats[unit_id][sun_dimension]
    return unit_stats
