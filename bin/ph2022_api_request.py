import csv

import click

from common_utils.constants import UNIT_USAGE
from handlers import CVResultUploadHandler
from handlers.custom_valuator_pricing import CustomValuatorApiHandler
from handlers.db import UnitDBHandler


def export_prices(site_id: int):
    units = UnitDBHandler.find(
        site_id=site_id,
        unit_usage=UNIT_USAGE.RESIDENTIAL.name,
        output_columns=[
            "id",
            "client_id",
            "ph_final_gross_rent_annual_m2",
            "ph_final_gross_rent_adj_factor",
        ],
    )
    units = [
        {"unit_id": u.pop("id"), "client_unit_id": u.pop("client_id"), **u}
        for u in units
    ]
    save_as_csv(filename=f"ph_valuation_{site_id}.csv", rows=units)


def save_as_csv(filename: str, rows: list[dict]):
    with open(filename, mode="w") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "unit_id",
                "client_unit_id",
                "ph_final_gross_rent_annual_m2",
                "ph_final_gross_rent_adj_factor",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


@click.command()
@click.option("--site_id", "-s", prompt=True, type=click.INT)
@click.option("--building_year", "-y", prompt=True, type=click.INT)
def upload_prices(site_id: int, building_year: int):
    custom_valuator_results = CustomValuatorApiHandler.get_valuation_results(
        site_id=site_id, building_year=building_year
    )
    CVResultUploadHandler.update_custom_valuator_results(
        site_id=site_id, custom_valuator_results=custom_valuator_results
    )
    export_prices(site_id=site_id)


if __name__ == "__main__":
    upload_prices()
