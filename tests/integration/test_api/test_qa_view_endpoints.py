import uuid
from http import HTTPStatus
from typing import Dict, List

import pytest
import pytest_flask

from common_utils.exceptions import DBNotFoundException
from handlers import PlanHandler
from handlers.db import BuildingDBHandler, QADBHandler
from handlers.db.qa_handler import (
    INDEX_ANF_AREA,
    INDEX_CLIENT_BUILDING_ID,
    INDEX_FLOOR_NUMBER,
    INDEX_HNF_AREA,
    INDEX_NET_AREA,
    INDEX_ROOM_NUMBER,
    INDEX_STREET,
    QA_COLUMN_HEADERS,
)
from slam_api.apis.qa import (
    QaTemplateHeaderFields,
    QATemplateView,
    QAView,
    QAViewCollection,
    qa_app,
)
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


@login_as(["TEAMMEMBER"])
def test_qa_data_add_trim_client_ids(client, site, qa_rows, login):
    url = get_address_for(
        blueprint=qa_app, view_function=QAViewCollection, use_external_address=False
    )
    qa_rows = {
        f"\t {client_unit_id} \t": data for client_unit_id, data in qa_rows.items()
    }
    request_body = {
        "site_id": site["id"],
        "client_id": site["client_id"],
        "data": qa_rows,
    }
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.CREATED, response.data
    assert response.json["data"] == {
        "2273211.01.01.0001": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": 94.0, "number_of_rooms": 4.5},
        ),
        "2273211.01.01.0002": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": 90.0, "number_of_rooms": 3.5},
        ),
    }


@login_as(["TEAMMEMBER"])
def test_qa_data_add(client, site, qa_rows, login):
    url = get_address_for(
        blueprint=qa_app, view_function=QAViewCollection, use_external_address=False
    )
    request_body = {
        "site_id": site["id"],
        "client_id": site["client_id"],
        "data": qa_rows,
    }
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.CREATED, response.data
    assert response.json["site_id"] == site["id"]
    assert response.json["data"] == {
        "2273211.01.01.0001": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": 94.0, "number_of_rooms": 4.5},
        ),
        "2273211.01.01.0002": dict(
            {column_header: None for column_header in QA_COLUMN_HEADERS},
            **{"net_area": 90.0, "number_of_rooms": 3.5},
        ),
    }


@login_as(["TEAMMEMBER"])
def test_qa_data_add_wrong_data_format(client, site, login):
    url = get_address_for(
        blueprint=qa_app, view_function=QAViewCollection, use_external_address=False
    )
    request_body = {"site_id": site["id"], "client_id": site["client_id"], "data": []}
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data
    assert len(QADBHandler.find()) == 0


@login_as(["TEAMMEMBER"])
def test_qa_data_add_no_client_id(client, site, qa_rows, login):
    url = get_address_for(
        blueprint=qa_app, view_function=QAViewCollection, use_external_address=False
    )
    request_body = {"site_id": site["id"], "data": {}}
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.data
    assert len(QADBHandler.find()) == 0

    request_body = {"client_site_id": site["id"], "data": qa_rows}
    response = client.post(url, json=request_body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data
    assert len(QADBHandler.find()) == 0


@login_as(["TEAMMEMBER"])
def test_qa_data_delete(client, qa_db, site, login):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAView,
        qa_id=qa_db["id"],
        use_external_address=False,
    )
    response = client.delete(url)
    assert response.status_code == HTTPStatus.OK, response.data
    with pytest.raises(DBNotFoundException):
        QADBHandler.get_by(id=qa_db["id"])


@login_as(["TEAMMEMBER"])
def test_qa_data_update_data_field(client, qa_db, site, login):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAView,
        qa_id=qa_db["id"],
        use_external_address=False,
    )
    request_body = {
        "data": {
            "random_client_unit_id": dict(
                {header: None for header in QA_COLUMN_HEADERS}, **{INDEX_NET_AREA: 90}
            )
        }
    }
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.OK, response.data
    assert QADBHandler.get_by(id=qa_db["id"])["data"] == request_body["data"]


@login_as(["TEAMMEMBER"])
def test_qa_data_update_site_id(client, qa_db, site, login):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAView,
        qa_id=qa_db["id"],
        use_external_address=False,
    )
    request_body = {"site_id": 31416}
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.OK, response.data
    assert QADBHandler.get_by(id=qa_db["id"])["site_id"] == request_body["site_id"]


@pytest.mark.parametrize(
    "client_id,client_site_id,site_id,expected_code",
    [
        (True, True, False, HTTPStatus.OK),
        (False, False, True, HTTPStatus.OK),
        # Not allowed combinations:
        (True, False, False, HTTPStatus.BAD_REQUEST),
        (False, True, False, HTTPStatus.BAD_REQUEST),
        (False, False, False, HTTPStatus.BAD_REQUEST),
        (False, True, True, HTTPStatus.BAD_REQUEST),
        (True, True, True, HTTPStatus.BAD_REQUEST),
        (True, False, True, HTTPStatus.BAD_REQUEST),
    ],
)
@login_as(["TEAMMEMBER"])
def test_get_qa_by(
    client,
    make_clients,
    make_sites,
    make_qa_data,
    client_id,
    client_site_id,
    site_id,
    expected_code,
    login,
):
    client1, client2 = make_clients(2)
    site1, site2 = make_sites(client1, client1)
    make_sites(
        client2, client_site_id=site1["client_site_id"]
    )  # Different client_id but repeated client_site_id
    make_qa_data(site1, site2)
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAViewCollection,
        client_id=site1["client_id"] if client_id else None,
        client_site_id=site1["client_site_id"] if client_site_id else None,
        site_id=site1["id"] if site_id else None,
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == expected_code


@login_as(["TEAMMEMBER"])
def test_get_qa_by_wrong_param(client, qa_db, login):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAViewCollection,
        salpica="payaso",
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.data


@login_as(["TEAMMEMBER"])
def test_get_qa_by_undefined(client, qa_db, login):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAViewCollection,
        client_id="undefined",
        client_site_id="undefined",
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.BAD_REQUEST, response.data


@login_as(["TEAMMEMBER"])
def test_get_qa_data_plan_id(
    site, random_image, make_floor, client, login, mocked_plan_image_upload_to_gc
):
    def create_buildings(site: Dict) -> List[Dict]:
        return [
            BuildingDBHandler.add(
                site_id=site["id"],
                housenumber=housenumber,
                city="Zurich",
                zipcode="8000",
                street="somestreet",
                elevation=100.0,
                client_building_id=housenumber,
            )
            for housenumber in ("20", "22")
        ]

    def create_floors(buildings: List[Dict]) -> List[Dict]:
        floors = []
        for building in buildings:
            plan = PlanHandler.add(
                plan_content=random_image(),
                plan_mime_type="image/jpg",
                site_id=building["site_id"],
                building_id=building["id"],
            )
            for i in range(0, 2):
                floors.append(make_floor(building=building, plan=plan, floornumber=i))
        return floors

    def _create_qa_row(values: Dict = None) -> Dict:
        if values is None:
            values = dict()
        return {
            str(uuid.uuid4()): dict(
                {
                    INDEX_ROOM_NUMBER: "4.5",
                    INDEX_NET_AREA: "94",
                    INDEX_HNF_AREA: None,
                    INDEX_ANF_AREA: None,
                    INDEX_STREET: None,
                    INDEX_CLIENT_BUILDING_ID: None,
                    INDEX_FLOOR_NUMBER: None,
                },
                **values,
            )
        }

    def create_qa_data(site: Dict, floors: List[Dict], buildings):
        qa_data = dict()
        for floor in floors:
            building = [
                building
                for building in buildings
                if building["id"] == floor["building_id"]
            ][0]
            qa_data.update(
                _create_qa_row(
                    values={
                        INDEX_CLIENT_BUILDING_ID: building["client_building_id"],
                        INDEX_FLOOR_NUMBER: floor["floor_number"],
                    }
                )
            )

        # Entity with missing client_building_id
        qa_data.update(_create_qa_row(values={INDEX_FLOOR_NUMBER: 1}))
        # Entity with not matching client_building_id
        qa_data.update(
            _create_qa_row(
                values={
                    INDEX_CLIENT_BUILDING_ID: "not-matching-id",
                    INDEX_FLOOR_NUMBER: 1,
                }
            )
        )
        # Entity with not matching client_building_id and floor not defined
        qa_data.update(
            _create_qa_row(values={INDEX_CLIENT_BUILDING_ID: "not-matching-id"})
        )

        return QADBHandler.add(
            client_id=site["client_id"],
            client_site_id=site["client_site_id"],
            site_id=site["id"],
            data=qa_data,
        )

    def check_qa_http_response(response: pytest_flask.plugin.JSONResponse):
        assert response.status_code == HTTPStatus.OK
        plan_ids = []
        for apartment_client_id, apartment_qa_data in response.json["data"].items():
            for key, qa_value in apartment_qa_data.items():
                if key == "plan_id":
                    plan_ids.append(qa_value)
                else:
                    assert qa_value == qa_db["data"][apartment_client_id][key]

        assert sum([1 for plan_id in plan_ids if plan_id is None]) == 3

    buildings = create_buildings(site=site)
    floors = create_floors(buildings=buildings)
    qa_db = create_qa_data(site=site, floors=floors, buildings=buildings)

    url = get_address_for(
        blueprint=qa_app,
        view_function=QAViewCollection,
        site_id=site["id"],
        use_external_address=False,
    )
    response = client.get(url)

    check_qa_http_response(response=response)


@pytest.mark.parametrize("login", ["TEAMMEMBER", "ADMIN"], indirect=True)
def test_qa_template_view_should_serve_csv_generated_from_schema(login, client, site):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QATemplateView,
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    assert response.mimetype == "text/csv"
    expected_csv_header = (
        ",".join([fieldname for fieldname in QaTemplateHeaderFields().fields.keys()])
        + "\r\n"
    )
    assert response.data == bytes(expected_csv_header, "UTF-8")


@pytest.mark.parametrize(
    "login",
    ["ARCHILYSE_ONE_ADMIN", "COMPETITION_ADMIN"],
    indirect=True,
)
def test_qa_template_view_should_be_accessible_only_teammembers_or_pipeline_admins(
    login, client, site
):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QATemplateView,
        use_external_address=False,
    )
    response = client.get(url)
    assert response.status_code == HTTPStatus.FORBIDDEN


@pytest.fixture
def invalid_qa_data(qa_rows):
    qa_rows["wHy_arE_thE_simUlati0ns_tAkIng_so_loOoOnG"] = 123
    return qa_rows


@pytest.mark.parametrize(
    "qa_data,expected_http_code",
    [
        (pytest.lazy_fixture("invalid_qa_data"), HTTPStatus.UNPROCESSABLE_ENTITY),
        (pytest.lazy_fixture("qa_rows"), HTTPStatus.CREATED),
    ],
)
def test_post_qa_validates_payload(client, qa_data, expected_http_code, site):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAViewCollection,
        use_external_address=False,
    )
    request_body = {
        "client_site_id": site["client_site_id"],
        "client_id": site["client_id"],
        "data": qa_data,
    }
    response = client.post(url, json=request_body)
    assert response.status_code == expected_http_code


@pytest.mark.parametrize(
    "qa_data,expected_http_code",
    [
        (pytest.lazy_fixture("invalid_qa_data"), HTTPStatus.UNPROCESSABLE_ENTITY),
        (pytest.lazy_fixture("qa_rows"), HTTPStatus.OK),
    ],
)
def test_put_qa_validates_payload(client, qa_data, expected_http_code, site, qa_db):
    url = get_address_for(
        blueprint=qa_app,
        view_function=QAView,
        use_external_address=False,
        qa_id=qa_db["id"],
    )
    request_body = {
        "client_site_id": site["client_site_id"],
        "client_id": site["client_id"],
        "data": qa_data,
    }
    response = client.put(url, json=request_body)
    assert response.status_code == expected_http_code
