"""Query report for full gross m2"""

import csv
import multiprocessing
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path
from typing import Dict, Optional, Tuple

import click
import pendulum
from shapely.ops import unary_union
from tqdm import tqdm

from brooks.models import SimLayout
from common_utils.constants import ADMIN_SIM_STATUS
from common_utils.logger import logger
from db_models import SiteDBModel
from handlers import PlanLayoutHandler
from handlers.db import (
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    SiteDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)

project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


from bin.reports.common_bin_utils import parse_month  # noqa: E402


def calculate_areas_by_plan(site_id: int) -> Tuple[int, Dict[int, Dict[str, float]]]:
    values_by_plans = {}
    for plan in PlanDBHandler.find(site_id=site_id, output_columns=["id"]):
        layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
            scaled=True,
            classified=True,  # classified is necessary as it adds the area db ids to the layout areas
        )
        unit_area, public_area, wall_area = calculate_plan_area(
            plan_id=plan["id"], layout=layout
        )
        nbr_of_floors = len(
            FloorDBHandler.find(plan_id=plan["id"], output_columns=["id"])
        )
        values_by_plans[plan["id"]] = {
            "unit_area": unit_area,
            "public_area": public_area,
            "wall_area": wall_area,
            "nbr_of_floors": nbr_of_floors,
        }
    return site_id, values_by_plans


def calculate_plan_area(plan_id: int, layout: SimLayout) -> Tuple[float, float, float]:
    area_ids_of_units = {
        unit_area["area_id"]
        for unit_area in UnitAreaDBHandler.find_in(
            unit_id=list(UnitDBHandler.find_ids(plan_id=plan_id)),
            output_columns=["area_id"],
        )
    }

    sum_area_of_units = sum(
        [
            area.footprint.area
            for area in layout.areas
            if area.db_area_id in area_ids_of_units
        ]
    )
    sum_public_area = sum(
        [
            area.footprint.area
            for area in layout.areas
            if area.db_area_id not in area_ids_of_units
        ]
    )
    sum_wall_area = unary_union(
        [separator.footprint for separator in layout.separators]
    ).area
    return (
        sum_area_of_units,
        sum_public_area,
        sum_wall_area,
    )


def calculate_all_sites_areas(
    sites_info: Dict[str, Dict]
) -> Dict[int, Dict[int, Dict[str, float]]]:
    values_per_site_and_plan = {}

    logger.info(
        "The program doesn't run in order so the "
        "monitoring might return dozens of results together"
    )
    with Pool(processes=multiprocessing.cpu_count()) as pool:
        multiple_results = [
            pool.apply_async(calculate_areas_by_plan, (site_id,))
            for site_id in sites_info
        ]
        for res in tqdm(multiple_results):
            site_id, values_by_plans = res.get()
            values_per_site_and_plan[site_id] = values_by_plans

    return values_per_site_and_plan


def write_report_by_site(
    areas_by_site_and_plans: Dict[int, Dict[str, float]],
    sites_info: Dict[int, Dict],
    client_by_id: Dict[int, Dict],
    filename: str,
):

    with Path(filename).open("wt") as csvfile:

        csv_writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "client_name",
                "site_id",
                "client_site_id",
                "plan_id",
                "unit_area",
                "public_area",
                "wall_area",
                "total_plan_area",
                "nbr_of_floors",
                "total_floor_area",
                "year_created",
                "month_created",
                "week_created",
            ],
        )
        csv_writer.writeheader()

        for site_id, values_per_plan in areas_by_site_and_plans.items():
            created_parsed = pendulum.parse(sites_info[site_id]["created"])
            client_site_id = sites_info[site_id]["client_site_id"]
            for plan_id, values in values_per_plan.items():
                unit_area = values["unit_area"]
                public_area = values["public_area"]
                wall_area = values["wall_area"]
                nbr_of_floors = values["nbr_of_floors"]
                total_plan_area = sum([unit_area, public_area, wall_area])
                row = {
                    "client_name": client_by_id[sites_info[site_id]["client_id"]][
                        "name"
                    ],
                    "site_id": site_id,
                    "client_site_id": client_site_id,
                    "plan_id": plan_id,
                    "unit_area": round(unit_area, 2),
                    "public_area": round(public_area, 2),
                    "wall_area": round(wall_area, 2),
                    "nbr_of_floors": nbr_of_floors,
                    "total_plan_area": round(total_plan_area, 2),
                    "total_floor_area": round(total_plan_area * nbr_of_floors, 2),
                    "year_created": created_parsed.year,
                    "month_created": created_parsed.format("MMMM"),
                    "week_created": created_parsed.week_of_year,
                }

                csv_writer.writerow(row)


def log_stats(
    areas_by_site_and_plans: Dict[int, Dict[int, Dict[str, float]]],
    sites_info: Dict[int, Dict],
):
    total_area_by_site = {
        site_id: sum(
            (values["public_area"] + values["unit_area"] + values["wall_area"])
            * values["nbr_of_floors"]
            for values in areas_by_plans.values()
        )
        for site_id, areas_by_plans in areas_by_site_and_plans.items()
    }
    total_sum = sum(total_area_by_site.values())
    month_sum = Counter()
    week_sum = Counter()
    for site_id in areas_by_site_and_plans.keys():
        created_parsed = pendulum.parse(sites_info[site_id]["created"])
        month_sum[
            f"{created_parsed.year}-{created_parsed.format('MMMM')}"
        ] += total_area_by_site[site_id]
        week_sum[
            f"{created_parsed.year}-{created_parsed.week_of_year}"
        ] += total_area_by_site[site_id]

    logger.info(f"YTD: {total_sum} m2")
    logger.info(month_sum)


def log_units_for_report(sites_info):
    client_ids = {
        unit["client_id"]
        for unit in UnitDBHandler.find_in(
            site_id=[site_id for site_id in sites_info], output_columns=["client_id"]
        )
    }
    logger.info(f"Units processed in the month: {len(client_ids)}")


@click.command()
@click.option("--investors", is_flag=True)
@click.option(
    "--month",
    default=None,
    help='The month to generate the summary for in the format "YYYY-MM" or a month name like "March". '
    "If not provided, the current month is used.",
)
def report_by_site(investors: bool, month: Optional[str]):
    start_date, end_date = parse_month(month)

    if investors:
        # This is used for the investors report, YTD gross m2 pipelined and simulated
        sites_by_id = {
            site["id"]: site
            for site in SiteDBHandler.find(
                special_filter=(
                    SiteDBModel.created >= start_date,
                    SiteDBModel.created <= end_date,
                ),
                full_slam_results=ADMIN_SIM_STATUS.SUCCESS.name,
                output_columns=["id", "client_site_id", "client_id", "created"],
            )
        }
    else:
        sites_ids = [11406, 11419, 11420]
        sites_by_id = {
            site["id"]: site
            for site in SiteDBHandler.find_in(
                id=sites_ids,
                output_columns=["id", "client_site_id", "client_id", "created"],
            )
        }

    client_by_id = {
        client["id"]: client
        for client in ClientDBHandler.find_in(
            id=list({site["client_id"] for site in sites_by_id.values()}),
        )
    }

    areas_by_site_and_plans = calculate_all_sites_areas(sites_info=sites_by_id)
    log_stats(areas_by_site_and_plans=areas_by_site_and_plans, sites_info=sites_by_id)
    log_units_for_report(sites_info=sites_by_id)

    write_report_by_site(
        areas_by_site_and_plans=areas_by_site_and_plans,
        sites_info=sites_by_id,
        client_by_id=client_by_id,
        filename="query_report_by_site.csv",
    )


if __name__ == "__main__":
    report_by_site()
