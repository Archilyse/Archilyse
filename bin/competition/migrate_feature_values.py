from collections import defaultdict

from tqdm import tqdm

from common_utils.competition_constants import CompetitionFeatures
from handlers import SiteHandler
from handlers.competition import CompetitionFeaturesCalculator
from handlers.db.competition.competition_features_db_handler import (
    CompetitionFeaturesDBHandler,
)
from handlers.db.competition.competition_handler import CompetitionDBHandler

sites_ids = [
    site_id
    for competition in CompetitionDBHandler.find()
    for site_id in competition["competitors"]
]

for site_id in tqdm(sites_ids):
    units_layouts_w_info = list(
        SiteHandler.get_unit_layouts(site_id=site_id, scaled=True)
    )

    layouts_by_type = defaultdict(list)

    for unit_info, layout in units_layouts_w_info:
        if unit_info["client_id"]:
            layouts_by_type[unit_info["unit_usage"]].append(layout)

    residential_ratio = CompetitionFeaturesCalculator.m2_by_usage_type(
        layouts_by_type=layouts_by_type
    )

    CompetitionFeaturesDBHandler.update_data_feature(
        competitor_id=site_id,
        **{
            CompetitionFeatures.RESIDENTIAL_USE.value: residential_ratio,
            CompetitionFeatures.RESIDENTIAL_USE_RATIO.value: residential_ratio,
        }
    )
