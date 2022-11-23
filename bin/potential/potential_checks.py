from collections import defaultdict

import numpy as np
from tqdm import tqdm

from common_utils.logger import logger
from handlers.db import PotentialSimulationDBHandler

HIGH_BUILDING_VIEW_THRESHOLD = 10
LOW_SUN_THRESHOLD = 0.5
sun_key = "sun-2018-06-21 14:00:00+02:00"
alt_sun_key = "sun-2018-06-21 14:00:00+0:00"

ZURICH = {
    "min_lon": 8.488388181714749,
    "min_lat": 47.350107191888505,
    "max_lon": 8.58034475941714,
    "max_lat": 47.39141758169881,
}
sims = PotentialSimulationDBHandler.get_simulations_list(bounding_box=ZURICH)
# Needs to remove filter for last 100 and add filter for type, etc...

errors = defaultdict(list)

for sim in tqdm(sims):
    if len(sim["result"]["observation_points"]) < 5:
        errors["observation_points_few"].append(sim["id"])

    building_values = sim["result"]["buildings"]
    if np.percentile(building_values, 80) >= HIGH_BUILDING_VIEW_THRESHOLD:
        errors["high_building_view"].append(sim["id"])

logger.info(f"Found {len(errors)} issues so far.... Continuing")

sims = PotentialSimulationDBHandler.get_simulations_list(bounding_box=ZURICH)

for sim in tqdm(sims):
    sun_values = sim["result"].get(sun_key)
    if not sun_values:
        sun_values = sim["result"][alt_sun_key]
    if np.percentile(sun_values, 80) <= LOW_SUN_THRESHOLD:
        errors["low_sun_values"].append(sim["id"])

for key, vals in errors.items():
    logger.info(f"Found {len(vals)} issues for {key}")
    logger.info(vals)


"""Checks
 - Too few observation points
 - All observation points have high building view
 - All observation points have too low sun view
"""
