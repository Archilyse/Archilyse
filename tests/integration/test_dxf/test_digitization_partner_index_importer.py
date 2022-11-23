from bin.digitization_partner_importer.digitization_partner_site_building_import_from_qa import (
    create_sites_buildings_qa_from_index,
)
from handlers.db import BuildingDBHandler, QADBHandler, SiteDBHandler


def test_importing_index_creates_sites_buildings_and_qa(fixtures_path, client_db):
    create_sites_buildings_qa_from_index(
        file_name=fixtures_path.joinpath(
            "dxf/digitization_partner_import/main_index_sample.xlsx"
        ),
        client_file_nbr_of_rooms=fixtures_path.joinpath(
            "dxf/digitization_partner_import/net_area_index_sample.xlsx"
        ),
        client_name=client_db["name"],
    )
    sites = SiteDBHandler.find()
    assert len(sites) == 2
    assert {site["client_site_id"] for site in sites} == {"84006", "84007"}
    buildings = BuildingDBHandler.find()
    assert len(buildings) == 3
    assert [
        {
            "id": building["client_building_id"],
            "street": building["street"],
            "housenumber": building["housenumber"],
        }
        for building in buildings
    ] == [
        {"id": "01", "street": "street_one", "housenumber": "24"},
        {"id": "02", "street": "street_one", "housenumber": "26"},
        {"id": "01", "street": "street_two", "housenumber": "8"},
    ]

    qa_infos = QADBHandler.find()

    assert len(qa_infos) == 2

    assert [qa_info["data"] for qa_info in qa_infos] == [
        {
            "84006.01.0049": {
                "ANF": None,
                "HNF": None,
                "floor": 0,
                "client_building_id": "01",
                "street": "street_one",
                "net_area": 60.9,
                "number_of_rooms": 2.5,
            },
            "84006.01.0050": {
                "ANF": None,
                "HNF": None,
                "floor": 0,
                "client_building_id": "01",
                "street": "street_one",
                "net_area": 79.6,
                "number_of_rooms": None,
            },
            "84006.02.0001": {
                "ANF": None,
                "HNF": None,
                "floor": 0,
                "client_building_id": "02",
                "street": "street_one",
                "net_area": 60.7,
                "number_of_rooms": 2.5,
            },
        },
        {
            "84007.01.0005": {
                "ANF": None,
                "HNF": None,
                "floor": 0,
                "client_building_id": "01",
                "street": "street_two",
                "net_area": 65.5,
                "number_of_rooms": 3.0,
            },
            "84007.01.0006": {
                "ANF": None,
                "HNF": None,
                "floor": 0,
                "client_building_id": "01",
                "street": "street_two",
                "net_area": 64.7,
                "number_of_rooms": None,
            },
        },
    ]
