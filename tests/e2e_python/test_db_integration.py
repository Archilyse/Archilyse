import mimetypes
from http import HTTPStatus

import pytest
from werkzeug.datastructures import FileStorage

from common_utils.exceptions import DBValidationException
from handlers import FloorHandler, PlanHandler
from handlers.db import BuildingDBHandler, FloorDBHandler, PlanDBHandler
from handlers.ifc import IfcToSiteHandler
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from slam_api.apis.floor import FloorView, floor_app
from tests.db_fixtures import login_as
from tests.flask_utils import get_address_for


@login_as(["TEAMMEMBER"])
def test_update_floor_already_existing_number(
    client, floor, plan, building, make_floor, login
):
    MOCK_FLOOR_NUMBER = 50
    make_floor(building=building, plan=plan, floornumber=MOCK_FLOOR_NUMBER)
    url = get_address_for(
        blueprint=floor_app,
        view_function=FloorView,
        floor_id=floor["id"],
        use_external_address=False,
    )
    request_body = {"floor_number": MOCK_FLOOR_NUMBER}
    response = client.put(url, json=request_body)
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.data
    assert (
        FloorDBHandler.get_by(id=floor["id"])["floor_number"]
        != request_body["floor_number"]
    )


def test_floor_handler_add_nothing_in_db_if_error(
    mocked_plan_image_upload_to_gc, building, floor, fixtures_path
):
    """
    1) The default floor have floor number 1 already used in the building
    2) Adding a new plan with a floor that is causing a conflict in the DB with the existing floors,
    it should rollback the plan and the floor creation
    """
    pdf_path = fixtures_path.joinpath("images/pdf_sample.pdf")
    with pdf_path.open("rb") as fp:
        file = FileStorage(fp, content_type=mimetypes.types_map[".pdf"])
        with pytest.raises(DBValidationException):
            FloorHandler.create_floors_from_plan_file(
                floorplan=file, building_id=building["id"], new_floor_numbers={0, 1, 2}
            )

    assert len(FloorDBHandler.find()) == 1
    assert len(PlanDBHandler.find()) == 1


def test_create_site_ifc_entities_rollback_on_errors(
    mocker,
    site,
    mocked_gcp_upload_bytes_to_bucket,
    random_image,
    ac20_fzk_haus_ifc_reader,
):
    class IfcTestException(Exception):
        pass

    mocker.patch.object(IfcStoreyHandler, "storey_figure")

    plan_handler_mock = mocker.patch.object(
        PlanHandler, "add", side_effect=IfcTestException()
    )

    with pytest.raises(IfcTestException):
        handler = IfcToSiteHandler(ifc_reader=ac20_fzk_haus_ifc_reader)
        handler.create_and_save_site_entities(
            site_id=site["id"],
            ifc_filename="ifcfilename",
        )
    assert not BuildingDBHandler.find()
    plan_handler_mock.assert_called_once()
