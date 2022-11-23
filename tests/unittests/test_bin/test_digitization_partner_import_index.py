from pathlib import Path

import pytest
from numpy import nan
from pandas import DataFrame

from bin.digitization_partner_importer.digitization_partner_address_handler import (
    DigitizationPartnerAddressHandler,
)
from bin.digitization_partner_importer.digitization_partner_site_building_import_from_qa import (
    add_or_update_qa_entries,
    check_for_duplicated_buildings,
    nbr_of_rooms_by_apartment_client_id,
    read_and_post_process_excel,
)
from common_utils.exceptions import DBNotFoundException
from handlers.db import QADBHandler


@pytest.mark.parametrize(
    "index_data,expected_duplicated_address",
    [
        (
            [
                {
                    "client_site_id": "111",
                    "client_building_id": "03",
                    "street": "street_1",
                    "housenumber": "3",
                },
                {
                    "client_site_id": "111",
                    "client_building_id": "02",
                    "street": "street_1",
                    "housenumber": "3",
                },
            ],
            {"street_1 3"},
        ),  # Case Same site and same address for more than 1 building is not allowed by the db
        (
            [
                {
                    "client_site_id": "111",
                    "client_building_id": "03",
                    "street": "street_1",
                    "housenumber": "3",
                },
                {
                    "client_site_id": "112",
                    "client_building_id": "02",
                    "street": "street_1",
                    "housenumber": "3",
                },
            ],
            set(),
        ),  # Case different site but same address is allowed
    ],
)
def test_find_duplicated_buildings(mocker, index_data, expected_duplicated_address):
    mocker.patch.object(
        DataFrame,
        "iterrows",
        return_value=[(None, row) for row in index_data],
    )
    assert (
        check_for_duplicated_buildings(dfs=DataFrame()) == expected_duplicated_address
    )


@pytest.mark.parametrize("with_nbr", [True, False])
def test_read_and_post_process_excel(mocker, with_nbr):
    data = {
        "Mietobjekt": ["111.01.01"],
        "Adresse": ["Address.5"],
        "PLZ": ["1111"],
        "Ort": ["City"],
        "Objektart": ["room"],
        "Stock": ["EG"],
        "Fläche": ["14"],
        "Mieter": ["foobar"],
    }

    if with_nbr:
        data["NBR"] = ["3.5"]

    data_frame = DataFrame(data=data)
    from bin.digitization_partner_importer import (
        digitization_partner_site_building_import_from_qa,
    )

    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "read_excel",
        return_value=data_frame,
    )

    cleaned_data_frame = read_and_post_process_excel(file_name=Path())
    assert cleaned_data_frame["apartment_client_id"][0] == "111.01.01"
    assert cleaned_data_frame["street"][0] == "Address."
    assert cleaned_data_frame["housenumber"][0] == "5"
    assert cleaned_data_frame["zipcode"][0] == "1111"
    assert cleaned_data_frame["city"][0] == "City"
    assert cleaned_data_frame["type"][0] == "room"
    assert cleaned_data_frame["floor"][0] == 0
    assert cleaned_data_frame["net_area"][0] == 14.0

    if with_nbr:
        assert cleaned_data_frame["number_of_rooms"][0] == 3.5


def test_skip_address_splitting_if_street_and_housenumber_already_exist(mocker):
    mocked_address_splitting = mocker.patch.object(
        DigitizationPartnerAddressHandler,
        "split_address_into_streetname_and_housenumber",
    )
    data_frame = DataFrame(
        data={
            "Mietobjekt": ["111.00.11"],
            "Adresse": ["Address.15"],
            "street": ["address."],
            "housenumber": ["1"],
            "PLZ": ["1111"],
            "Ort": ["City"],
            "Objektart": ["room"],
            "Stock": ["EG"],
            "Fläche": ["14"],
            "Mieter": ["foobar"],
        }
    )
    from bin.digitization_partner_importer import (
        digitization_partner_site_building_import_from_qa,
    )

    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "read_excel",
        return_value=data_frame,
    )

    cleaned_data_frame = read_and_post_process_excel(file_name=Path())
    assert not mocked_address_splitting.called
    assert cleaned_data_frame["apartment_client_id"][0] == "111.00.11"
    assert cleaned_data_frame["street"][0] == "address."
    assert cleaned_data_frame["housenumber"][0] == "1"
    assert cleaned_data_frame["zipcode"][0] == "1111"
    assert cleaned_data_frame["city"][0] == "City"
    assert cleaned_data_frame["type"][0] == "room"
    assert cleaned_data_frame["floor"][0] == 0
    assert cleaned_data_frame["net_area"][0] == 14


def test_read_and_post_process_excel_empty_housenumber_is_handled_as_empty_string(
    mocker,
):
    data_frame = DataFrame(
        data={
            "Mietobjekt": ["111.11.11"],
            "Adresse": ["Address.Number"],
            "street": ["Address."],
            "housenumber": [nan],
            "PLZ": ["1111"],
            "Ort": ["City"],
            "Objektart": ["room"],
            "Stock": ["EG"],
            "Fläche": ["14"],
            "Mieter": ["foobar"],
        }
    )
    from bin.digitization_partner_importer import (
        digitization_partner_site_building_import_from_qa,
    )

    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "read_excel",
        return_value=data_frame,
    )

    cleaned_data_frame = read_and_post_process_excel(file_name=Path())
    assert cleaned_data_frame["housenumber"][0] == ""


def test_nbr_of_rooms_index_from_file(mocker):

    data_frame = DataFrame(
        data={
            "Lieg-Nr.": ["111", "112"],
            "Geb Nr.": ["01", "03"],
            "MObj-Nr.": ["0001", "0005"],
            "Anz. Zi": ["4.5", nan],
            "random additional column": ["random", "random"],
        }
    )
    from bin.digitization_partner_importer import (
        digitization_partner_site_building_import_from_qa,
    )

    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "read_excel",
        return_value=data_frame,
    )

    index = nbr_of_rooms_by_apartment_client_id(client_file_nbr_of_rooms=Path())
    assert index == {"111.01.0001": 4.5}


def test_add_or_update_qa_entries_enriches_data_with_nbr_of_rooms(mocker):
    from bin.digitization_partner_importer import (
        digitization_partner_site_building_import_from_qa,
    )

    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "nbr_of_rooms_by_apartment_client_id",
        return_value={"111.01.0001": 4.5},
    )
    mocker.patch.object(
        digitization_partner_site_building_import_from_qa,
        "get_existing_site_ids_by_client_site_ids",
        return_value={"111": 1},
    )
    mocker.patch.object(QADBHandler, "get_by", side_effect=DBNotFoundException())
    mocked_db_qa_add = mocker.patch.object(QADBHandler, "add")
    data_frame = DataFrame(
        data={
            "client_site_id": ["111", "111"],
            "apartment_client_id": ["111.01.0001", "111.01.0002"],
        }
    )
    add_or_update_qa_entries(
        client_id=None, dfs=data_frame, client_file_nbr_of_rooms=None
    )
    assert mocked_db_qa_add.called
    assert (
        mocked_db_qa_add.call_args[1]["data"]["111.01.0001"]["number_of_rooms"] == 4.5
    )
    assert (
        mocked_db_qa_add.call_args[1]["data"]["111.01.0002"]["number_of_rooms"] is None
    )  # If no nbr of rooms in index just add none
