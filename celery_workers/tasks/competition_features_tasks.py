from shapely import wkt

from brooks.classifications import UnifiedClassificationScheme
from common_utils.constants import NOISE_SURROUNDING_TYPE, SIMULATION_VERSION, TASK_TYPE
from handlers import PlanHandler, SiteHandler, SlamSimulationHandler, StatsHandler
from handlers.competition import CompetitionFeaturesCalculator
from handlers.db import CompetitionFeaturesDBHandler, SiteDBHandler
from simulations.noise.utils import get_noise_window_per_area
from simulations.suntimes.suntimes_handler import SuntimesHandler
from tasks.utils.utils import celery_retry_task


@celery_retry_task
def competition_features_calculation_task(self, site_id: int, run_id: str):

    units_layouts_w_info = list(
        SiteHandler.get_unit_layouts(site_id=site_id, scaled=True)
    )
    site_plans = PlanHandler.get_site_plans_layouts_with_building_floor_numbers(
        site_id=site_id
    )
    public_layouts = dict(SiteHandler.get_public_layouts(site_id=site_id, scaled=True))

    view_unit_area_stats, sun_unit_area_stats, noise_unit_area_stats = get_area_stats(
        site_id=site_id
    )
    noise_window_per_area = get_noise_window_per_area(site_id=site_id)
    max_rectangle_by_area_id = {
        int(area_id): wkt.loads(biggest_rectangle_wkt)
        for unit_id, area_results in SlamSimulationHandler.get_latest_results(
            site_id=site_id, task_type=TASK_TYPE.BIGGEST_RECTANGLE
        ).items()
        for area_id, biggest_rectangle_wkt in area_results.items()
    }

    competition_features = CompetitionFeaturesCalculator(
        classification_schema=UnifiedClassificationScheme()
    ).calculate_all_features(
        plans=site_plans,
        public_layouts=public_layouts,
        units_layouts_w_info=units_layouts_w_info,
        sun_unit_area_stats=sun_unit_area_stats,
        noise_unit_area_stats=noise_unit_area_stats,
        view_unit_area_stats=view_unit_area_stats,
        noise_window_per_area=noise_window_per_area,
        max_rectangle_by_area_id=max_rectangle_by_area_id,
    )

    CompetitionFeaturesDBHandler.add(run_id=run_id, results=competition_features)


def get_area_stats(site_id: int):
    from handlers.competition.competition_features_calculator import (
        map_automated_features_view_dimension,
    )

    site_sim_version = SiteDBHandler.get_by(
        id=site_id, output_columns=["simulation_version"]
    )["simulation_version"]
    relevant_view_dimensions = {
        dimension.value for dimension in map_automated_features_view_dimension.values()
    }
    map_to_legacy_dimensions = site_sim_version == SIMULATION_VERSION.PH_2022_H1.value

    view_unit_area_stats = StatsHandler.get_area_stats(
        site_id=site_id,
        task_type=TASK_TYPE.VIEW_SUN,
        desired_dimensions=relevant_view_dimensions,
        legacy_dimensions_compatible=map_to_legacy_dimensions,
    )
    sun_unit_area_stats = StatsHandler.get_area_stats(
        site_id=site_id,
        task_type=TASK_TYPE.SUN_V2,
        desired_dimensions={
            SuntimesHandler.get_sun_key_from_datetime(dt=sun_obs_date)
            for sun_obs_date in SuntimesHandler.get_sun_times_v2(site_id=site_id)
        },
    )
    noise_unit_area_stats = StatsHandler.get_area_stats(
        site_id=site_id,
        task_type=TASK_TYPE.NOISE,
        desired_dimensions={noise_type.value for noise_type in NOISE_SURROUNDING_TYPE},
    )
    return view_unit_area_stats, sun_unit_area_stats, noise_unit_area_stats
