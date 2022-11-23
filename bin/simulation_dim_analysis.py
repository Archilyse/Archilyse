import contextlib
import json
from collections import defaultdict

import plotly.graph_objects as go

from common_utils.constants import TASK_TYPE, VIEW_DIMENSION
from handlers import SlamSimulationHandler
from handlers.db import SiteDBHandler, UnitDBHandler

valid_view_dimensions = [
    view_dimension
    for view_dimension in VIEW_DIMENSION
    if view_dimension not in (VIEW_DIMENSION.VIEW_ISOVIST, VIEW_DIMENSION.VIEW_SITE)
]


LIMITS_PER_DIMENSION = {
    VIEW_DIMENSION.VIEW_GROUND: 8.0,
    VIEW_DIMENSION.VIEW_BUILDINGS: 8.0,
    VIEW_DIMENSION.VIEW_GREENERY: 8.0,
    VIEW_DIMENSION.VIEW_SKY: 6.5,
    VIEW_DIMENSION.VIEW_STREETS: 11.0,
    VIEW_DIMENSION.VIEW_RAILWAY_TRACKS: 1.5,
    VIEW_DIMENSION.VIEW_WATER: 1.25,
    VIEW_DIMENSION.VIEW_MOUNTAINS: 12.56,  # Not worth to invest time on this
}

values_per_dimension = defaultdict(list)
worst_values_per_dimension = defaultdict(lambda: defaultdict(list))

for site in SiteDBHandler.find(
    client_id=1, output_columns=["id"], full_slam_results="SUCCESS"
):
    unit_results = SlamSimulationHandler.get_all_results(
        site_id=site["id"], task_type=TASK_TYPE.VIEW_SUN, check_status=False
    )
    for dimension in valid_view_dimensions:
        for unit_result in unit_results:
            unit_values = []
            for _, result in unit_result["results"].items():
                with contextlib.suppress(KeyError):
                    # Missing dimension in one of the areas
                    unit_values.append(max(result[dimension.value]))

            max_unit_value = max(unit_values)
            if max_unit_value >= LIMITS_PER_DIMENSION[dimension]:
                worst_values_per_dimension[dimension.name][site["id"]].append(
                    {
                        UnitDBHandler.get_by(id=unit_result["unit_id"])[
                            "client_id"
                        ]: max_unit_value
                    }
                )
            values_per_dimension[dimension].append(max(unit_values))


with open(".results.json", "w") as f:
    json.dump(worst_values_per_dimension, f)

fig = go.Figure()
# Use x instead of y argument for horizontal plot
for dimension in valid_view_dimensions:
    fig.add_trace(go.Box(x=values_per_dimension[dimension], name=dimension.value))
fig.show()
