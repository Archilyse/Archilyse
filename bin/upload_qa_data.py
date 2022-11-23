import codecs
import csv
from collections import Counter, defaultdict
from enum import Enum
from pathlib import Path
from typing import Dict

from tqdm import tqdm

from common_utils.logger import logger
from handlers.db import ClientDBHandler, QADBHandler, SiteDBHandler


class Clients(Enum):
    portfolio_client = "Portfolio Client"
    other_portfolio_client = "Other Portfolio Client"


def get_index_info(client: Clients):
    """Get the file from an architect"""
    filename = Path.home().joinpath("Downloads/some_file.csv").as_posix()
    index = defaultdict(list)
    with codecs.open(filename, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            row_cleaning(row=row)
            client_site_id = get_client_site_id(row=row, client_name=client)
            index[client_site_id].append(row)
        return index


def get_client_site_id(row, client_name: Clients) -> str:
    if client_name == Clients.portfolio_client:
        return row.pop("Client site id")
    return row["apartment_client_id"].split(".")[0]


def row_cleaning(row):
    if "EG" in row["floor"]:
        row["floor"] = "0"
    elif "OG" in row["floor"]:
        row["floor"] = str(int(row["floor"].replace("OG", "").replace(".", "")))
    elif "UG" in row["floor"]:
        row["floor"] = str(int(row["floor"].replace("UG", "").replace(".", "")) * -1)
    else:
        # we can ignore this, but some entries will not have floor number
        try:
            float(row["floor"])
        except ValueError:
            row["floor"] = ""

    if row["net_area"]:
        row["net_area"] = str(float(row["net_area"].replace(",", "")))
    else:
        row["net_area"] = "0.0"
    if row["HNF"]:
        row["HNF"] = str(float(row["HNF"].replace(",", "")))
    else:
        row["HNF"] = "0.0"

    try:
        float(row["number_of_rooms"])
    except ValueError:
        row["number_of_rooms"] = ""
    row.pop("building_number", None)


def normalize_client_site_id(site_info: Dict) -> str:
    new_client_site_id = site_info["client_site_id"].replace("_", "")
    if new_client_site_id != site_info["client_site_id"]:
        logger.info(f"Removing underscore for site {site_info['client_site_id']}")
        SiteDBHandler.update(
            item_pks={"id": site_info["id"]},
            new_values={"client_site_id": new_client_site_id},
        )
    return new_client_site_id


def add_qa_for_non_existing_site(
    client_id, client_site_id, new_site_data, qa_entry, stats
):
    if qa_entry:
        QADBHandler.update(
            item_pks={"id": qa_entry["id"]},
            new_values={
                "data": new_site_data,
                "client_site_id": client_site_id,
            },
        )
        stats["updates_qa_no_site"] += 1
    else:
        QADBHandler.add(
            client_site_id=client_site_id,
            client_id=client_id,
            data=new_site_data,
        )
        stats["adds_qa_no_site"] += 1


def add_qa_for_existing_site(
    client_id, new_site_data, qa_entry, site_info, stats, normalized_client_id
):
    if qa_entry:
        QADBHandler.update(
            item_pks={"id": qa_entry["id"]},
            new_values={
                "data": new_site_data,
                "client_site_id": normalized_client_id,
            },
        )
        stats["updates_qa_existing_site"] += 1
    else:
        QADBHandler.add(
            client_site_id=normalized_client_id,
            client_id=client_id,
            site_id=site_info["id"],
            data=new_site_data,
        )
        stats["adds_qa_existing_site"] += 1


missing = Counter()


def check_missing_hnf(new_site_data):
    for apartment_id, values in new_site_data.items():
        if not values["HNF"]:
            if values["net_area"]:
                values["HNF"] = values["net_area"]
                if not values["HNF"]:
                    values["HNF"] = "0.0"
            else:
                missing[apartment_id.split(".")[0]] += 1


def add_qa_data(client=Clients.portfolio_client):
    stats = Counter()
    client_id = ClientDBHandler.get_by(name=client.value)["id"]
    sites_info = {
        site["client_site_id"]: site
        for site in SiteDBHandler.find(
            client_id=client_id, output_columns=["client_site_id", "id"]
        )
    }
    qa_db_data = {
        data["client_site_id"]: data for data in QADBHandler.find(client_id=client_id)
    }

    for client_site_id, all_units in tqdm(get_index_info(client=client).items()):
        new_site_data = {
            unit["apartment_client_id"]: dict(
                **{
                    k: v
                    for k, v in unit.items()
                    if k not in ("apartment_client_id", "client_site_id")
                },
            )
            for unit in all_units
        }

        check_missing_hnf(new_site_data=new_site_data)
        stats["total_apartments"] += len(all_units)
        stats["total_sites"] += 1
        client_site_id = str(client_site_id)
        underscore_site = f"{client_site_id[:2]}_{client_site_id[2:]}"
        site_info = sites_info.get(client_site_id, sites_info.get(underscore_site))
        common_args = {
            "client_id": client_id,
            "new_site_data": new_site_data,
            "qa_entry": qa_db_data.get(client_site_id, qa_db_data.get(underscore_site)),
            "stats": stats,
        }
        if site_info:
            normalized_client_id = normalize_client_site_id(site_info=site_info)
            add_qa_for_existing_site(
                **common_args,
                site_info=site_info,
                normalized_client_id=normalized_client_id,
            )
        else:
            add_qa_for_non_existing_site(**common_args, client_site_id=client_site_id)

    logger.info(stats)
    logger.info(missing)
