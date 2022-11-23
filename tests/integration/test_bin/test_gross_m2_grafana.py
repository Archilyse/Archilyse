from decimal import Decimal

import pytest
from deepdiff import DeepDiff
from shapely.ops import unary_union
from sqlalchemy import text

from connectors.db_connector import get_db_session_scope
from handlers import PlanLayoutHandler
from tasks.pipeline_tasks import split_plan_task


@pytest.mark.freeze_time("2020-04-08")
def test_query_grafana_calculates_correctly(
    client_db,
    site,
    building,
    plan_annotated,
    make_buildings,
    make_plans,
    make_floor,
    test_path,
    make_sites,
):
    make_floor(building=building, plan=plan_annotated, floornumber=0)
    make_floor(building=building, plan=plan_annotated, floornumber=1)
    split_plan_task(plan_id=plan_annotated["id"])

    # Create additional sites in the DB
    (other_site,) = make_sites(client_db)
    (other_building,) = make_buildings(*(other_site,))
    (other_plan,) = make_plans(*(other_building,))
    make_floor(building=other_building, plan=other_plan, floornumber=1)

    layout = PlanLayoutHandler(plan_id=1).get_layout(scaled=True)
    expected_walls_area_in_meters = unary_union(
        [sep.footprint for sep in layout.separators]
    ).area
    with test_path.parent.joinpath("bin/reports/gross_m2_grafana.sql").open() as f:
        sql_query = text(f.read())
        with get_db_session_scope() as session:
            res = session.execute(sql_query, {"site_id": site["id"]})
            res = [dict(row) for row in res]
            for row in res:
                wall_area = row.pop("wall_area")
                assert (
                    pytest.approx(float(wall_area), abs=0.3)
                    == expected_walls_area_in_meters
                )
            assert not DeepDiff(
                [
                    {
                        "client_site_id": "Leszku-payaso",
                        "site_id": 1,
                        "month_created": "April    ",
                        "name": "test_archilyse_client",
                        "number_of_floors": 2,
                        "plan_id": 1,
                        "public_area": Decimal("0.0"),
                        "total_floor_area": Decimal("115.90"),
                        "total_plan_area": Decimal("57.95"),
                        "unit_area": Decimal("48.1"),
                        "week_created": 15.0,
                        "year_created": 2020.0,
                    },
                ],
                res,
                ignore_order=True,
                significant_digits=6,
            )
