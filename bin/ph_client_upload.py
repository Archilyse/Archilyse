from collections import defaultdict
from csv import DictReader

import click

from connectors.db_connector import get_db_session_scope
from handlers.db import UnitDBHandler

# File format example:
# client_unit_id	ph_final_gross_rent_annual_m2	ph_final_gross_rent_adj_factor
# 0003.10205.0008	294	-0.0435
# 0003.10205.0004	315	-0.0191


@click.command()
@click.argument("client_id", type=click.INT)
@click.argument("file_name", type=click.File("r"))
def main(client_id, file_name):
    """In the makefile you'd need to add the filename and client argument like:
    $(python) bin/ph_client_upload.py 88 ~/Downloads/data_to_update.csv
    """
    reader = DictReader(file_name)
    with get_db_session_scope() as s:
        unit_info = defaultdict(list)
        for row in s.execute(
            f"select a.id, a.client_id from units as a "
            f"join sites as b on a.site_id = b.id "
            f"where b.client_id = {client_id};"
        ):
            unit_info[row.client_id].append(row.id)

    data_to_update = {
        row["client_unit_id"]: {
            "ph_final_gross_rent_annual_m2": row["ph_final_gross_rent_annual_m2"],
            "ph_final_gross_rent_adj_factor": row["ph_final_gross_rent_adj_factor"],
        }
        for row in reader
    }

    UnitDBHandler.bulk_update(
        ph_final_gross_rent_annual_m2={
            unit_id: data["ph_final_gross_rent_annual_m2"]
            for client_unit_id, data in data_to_update.items()
            for unit_id in unit_info[client_unit_id]
        },
        ph_final_gross_rent_adj_factor={
            unit_id: data["ph_final_gross_rent_adj_factor"]
            for client_unit_id, data in data_to_update.items()
            for unit_id in unit_info[client_unit_id]
        },
    )


if __name__ == "__main__":
    main()
