from collections import defaultdict
from pathlib import Path
from typing import DefaultDict, Dict, Optional, Set, Tuple, Union

from numpy import nan
from pandas import DataFrame, read_excel

from bin.digitization_partner_importer.digitization_partner_address_handler import (
    DigitizationPartnerAddressHandler,
)
from bin.digitization_partner_importer.digitization_partner_importer_constants import (
    INDEX_HEADER_LENGTH,
    SHEET_NAME,
)
from bin.digitization_partner_importer.geo_locations import cached_geo_location
from common_utils.constants import REGION, SIMULATION_VERSION
from common_utils.exceptions import DBNotFoundException, GoogleGeocodeAPIException
from common_utils.logger import logger
from handlers.db import BuildingDBHandler, ClientDBHandler, QADBHandler, SiteDBHandler
from handlers.geo_location import GeoLocator, LatLong


def get_floor_number(text: str) -> Union[int, str]:
    text = text.strip().rstrip().lower()
    if "eg" in text:
        # eg or zg eg
        return 0
    if text == "nicht definiert":
        return -999
    number = int("".join([s for s in text if s.isdigit()]))
    if "ug" in text:
        return -number
    return number


def create_or_update_sites(client_id: int, dfs) -> Dict[str, dict]:
    sites_by_client_site_id = get_sites_info(client_id=client_id, dfs=dfs)
    existing_site_id_by_client_site_ids = get_existing_site_ids_by_client_site_ids(
        client_id=client_id
    )
    sites_to_insert = [
        site_info
        for client_site_id, site_info in sites_by_client_site_id.items()
        if client_site_id not in existing_site_id_by_client_site_ids
    ]
    SiteDBHandler.bulk_insert(items=sites_to_insert)

    for client_site_id, site_info in sites_by_client_site_id.items():
        if client_site_id in existing_site_id_by_client_site_ids:
            site_id = existing_site_id_by_client_site_ids[site_info["client_site_id"]]
            SiteDBHandler.update(item_pks={"id": site_id}, new_values=site_info)
    return sites_by_client_site_id


def get_sites_info(client_id: int, dfs: DataFrame):
    geo_location_by_address = cached_geo_location
    sites_by_client_site_id = {}
    for _, row in dfs.iterrows():
        if row["client_site_id"] in sites_by_client_site_id:
            continue

        address_to_lookup = f"{row['street']}, {row['zipcode']}, {row['city']}"
        lat_lon = geo_location_by_address.get(address_to_lookup)
        if not lat_lon:
            try:
                lat_lon = GeoLocator.get_lat_lon_from_address(address=address_to_lookup)
            except GoogleGeocodeAPIException:
                logger.info(
                    f"Assigning a default location to address {address_to_lookup}"
                )
                lat_lon = LatLong(lat=47.4047366, lon=8.4864537)
            geo_location_by_address[address_to_lookup] = lat_lon

        sites_by_client_site_id[row["client_site_id"]] = {
            "client_site_id": row["client_site_id"],
            "name": f"{row['city']}-{row['street']}",
            "region": row["city"],
            "priority": 3,
            "client_id": client_id,
            "lat": lat_lon.lat,
            "lon": lat_lon.lon,
            "georef_region": REGION.CH.name,
            "simulation_version": SIMULATION_VERSION.PH_2022_H1.name,
        }
    return sites_by_client_site_id


def get_existing_site_ids_by_client_site_ids(client_id: int):
    return {
        s["client_site_id"]: s["id"]
        for s in SiteDBHandler.find(
            client_id=client_id, output_columns=["client_site_id", "id"]
        )
        if s["client_site_id"] is not None
    }


def add_or_update_qa_entries(
    client_id: int, dfs: DataFrame, client_file_nbr_of_rooms: Optional[Path] = None
):
    qa_entries_per_apartment = dfs.to_dict(orient="records")
    existing_site_id_by_client_site_ids = get_existing_site_ids_by_client_site_ids(
        client_id=client_id
    )
    qa_data_by_site_id = defaultdict(dict)
    qa_keys = {
        "client_building_id",
        "number_of_rooms",
        "net_area",
        "HNF",
        "ANF",
        "street",
        "floor",
    }

    if client_file_nbr_of_rooms or "number_of_rooms" not in dfs.columns:
        nbr_of_rooms_index_by_apartment_client_id = nbr_of_rooms_by_apartment_client_id(
            client_file_nbr_of_rooms=client_file_nbr_of_rooms
        )
        for qa_value in qa_entries_per_apartment:
            qa_value["number_of_rooms"] = nbr_of_rooms_index_by_apartment_client_id.get(
                qa_value["apartment_client_id"]
            )

    for qa_value in qa_entries_per_apartment:
        site_id = existing_site_id_by_client_site_ids[qa_value["client_site_id"]]
        qa_data_by_site_id[site_id][qa_value["apartment_client_id"]] = {
            k: v for k, v in qa_value.items() if k in qa_keys
        }

    for client_site_id, site_id in existing_site_id_by_client_site_ids.items():
        try:
            existing_qa = QADBHandler.get_by(
                client_site_id=client_site_id,
                site_id=site_id,
                client_id=client_id,
            )
            QADBHandler.update(
                item_pks={"id": existing_qa["id"]},
                new_values={"data": qa_data_by_site_id[site_id]},
            )
        except DBNotFoundException:
            QADBHandler.add(
                client_site_id=client_site_id,
                site_id=site_id,
                client_id=client_id,
                data=qa_data_by_site_id[site_id],
            )


def read_and_post_process_excel(file_name: Path):
    dfs = read_excel(
        file_name.as_posix(), sheet_name=SHEET_NAME, skiprows=INDEX_HEADER_LENGTH
    )
    dfs = dfs.rename(
        columns={
            "Mietobjekt": "apartment_client_id",
            "Adresse": "address",
            "PLZ": "zipcode",
            "Ort": "city",
            "Objektart": "type",
            "Stock": "floor",
            "Fläche": "net_area",
            "NBR": "number_of_rooms",
        },
    )
    if "Mieter" in dfs.columns:
        dfs = dfs.drop(columns="Mieter")

    dfs.insert(
        1,
        "client_site_id",
        dfs["apartment_client_id"].apply(func=lambda x: x.split(".")[0]),
    )
    dfs.insert(
        2,
        "client_building_id",
        dfs["apartment_client_id"].apply(func=lambda x: x.split(".")[1]),
    )
    dfs["floor"] = dfs["floor"].apply(func=get_floor_number)
    dfs["net_area"] = dfs["net_area"].apply(float)

    if "number_of_rooms" in dfs.columns:
        dfs["number_of_rooms"] = dfs["number_of_rooms"].apply(float).fillna("")

    if not ("housenumber" in dfs.columns and "street" in dfs.columns):
        dfs = DigitizationPartnerAddressHandler.split_address_into_streetname_and_housenumber(
            dfs=dfs
        )
    dfs["housenumber"] = dfs["housenumber"].fillna("")

    return dfs


def create_or_update_buildings(client_id: int, dfs: DataFrame):
    buildings_by_client_site_id = defaultdict(dict)
    existing_site_ids_by_client_site_ids = get_existing_site_ids_by_client_site_ids(
        client_id=client_id
    )
    building_entities = []
    for _, row in dfs.iterrows():
        building_appended = buildings_by_client_site_id.get(
            row["client_site_id"], {}
        ).get(row["client_building_id"])
        if not building_appended:
            buildings_by_client_site_id[row["client_site_id"]][
                row["client_building_id"]
            ] = True
            building_entities.append(
                {
                    "site_id": existing_site_ids_by_client_site_ids[
                        row["client_site_id"]
                    ],
                    "client_building_id": row["client_building_id"],
                    "housenumber": row["housenumber"],
                    "city": row["city"],
                    "zipcode": str(row["zipcode"]),
                    "street": row["street"],
                }
            )
    existing_buildings = {
        (b["site_id"], b["street"], b["housenumber"]): b["id"]
        for b in BuildingDBHandler.find_in(
            site_id=existing_site_ids_by_client_site_ids.values()
        )
    }
    building_to_insert = [
        b
        for b in building_entities
        if (b["site_id"], b["street"], b["housenumber"]) not in existing_buildings
    ]

    BuildingDBHandler.bulk_insert(items=building_to_insert)
    for building in building_entities:
        if existing_building_id := existing_buildings.get(
            (building["site_id"], building["street"], building["housenumber"])
        ):
            BuildingDBHandler.update(
                item_pks={"id": existing_building_id}, new_values=building
            )


def check_for_duplicated_buildings(dfs) -> Set[Tuple[str, str]]:
    duplicates = set()
    adress_building_id_index_per_site: DefaultDict[str, Dict[str, str]] = defaultdict(
        dict
    )
    for _, row in dfs.iterrows():
        client_site_id = row["client_site_id"]
        building_id = row["client_building_id"]
        adress_building_id_index = adress_building_id_index_per_site[client_site_id]
        address = row["street"] + " " + row["housenumber"]
        if existing_building_id := adress_building_id_index.get(address, None):
            if not building_id == existing_building_id:
                duplicates.add(address)
        else:
            adress_building_id_index[address] = building_id

    return duplicates


def nbr_of_rooms_by_apartment_client_id(
    client_file_nbr_of_rooms: Path,
) -> Dict[str, float]:
    dfs: DataFrame = read_excel(
        client_file_nbr_of_rooms.as_posix(),
        dtype={"Anz. Zi": str, "Lieg-Nr.": str, "Geb Nr.": str, "MObj-Nr.": str},
        sheet_name=0,
        skiprows=0,
    )
    dfs = dfs.rename(
        columns={
            "Anz. Zi": "nbr_of_rooms",
            "Lieg-Nr.": "client_site_id",
            "Geb Nr.": "client_building_id",
            "MObj-Nr.": "client_unit_id",
        },
    )
    nbr_of_room_by_unit_id = {}
    for _, row in dfs.iterrows():
        if row["nbr_of_rooms"] is nan:
            continue
        nbr_of_rooms = float(row["nbr_of_rooms"])
        full_unit_client_id = (
            row["client_site_id"]
            + "."
            + row["client_building_id"]
            + "."
            + row["client_unit_id"]
        )
        nbr_of_room_by_unit_id[full_unit_client_id] = nbr_of_rooms

    return nbr_of_room_by_unit_id


def create_sites_buildings_qa_from_index(
    file_name: Path,
    client_name: str,
    client_file_nbr_of_rooms: Optional[Path] = None,
):
    client_id = ClientDBHandler.get_by(name=client_name, output_columns=["id"])["id"]
    dfs = read_and_post_process_excel(file_name=file_name)

    if duplicated_buildings_in_index := check_for_duplicated_buildings(dfs=dfs):
        raise Exception(
            f"There are different buildings sharing the same address: \n {duplicated_buildings_in_index}"
        )
    create_or_update_sites(client_id=client_id, dfs=dfs)

    add_or_update_qa_entries(
        client_id=client_id, dfs=dfs, client_file_nbr_of_rooms=client_file_nbr_of_rooms
    )
    create_or_update_buildings(client_id=client_id, dfs=dfs)


if __name__ == "__main__":
    """

    Main Index (cleaned and adress splitted)(UBS) can be found here https://docs.google.com/spreadsheets/d/1v1yC1x0OX1pTr8oE2aFb2P1va3Ealiq5/edit?usp=sharing&ouid=111689039201933989021&rtpof=true&sd=true
    Index for number of rooms (UBS) can be found here https://docs.google.com/spreadsheets/d/1w1WnAsjYrdT2926OONp4OM6hbTQpqypf/edit?usp=sharing&ouid=111689039201933989021&rtpof=true&sd=true

    """
    create_sites_buildings_qa_from_index(
        file_name=Path().home().joinpath("Downloads/CustomClient2/16211_index.xlsx"),
        client_name="CustomClient2",
    )
