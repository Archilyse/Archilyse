import pytest
from shapely.geometry import Point

from common_utils.constants import ADMIN_SIM_STATUS, REGION
from common_utils.exceptions import IfcEmptyStoreyException
from handlers.db import SiteDBHandler
from handlers.ifc import IfcToSiteHandler
from ifc_reader.reader import IfcReader
from tasks.site_ifc_tasks import (
    create_ifc_entities_from_site_task,
    get_ifc_import_task_chain,
    ifc_create_plan_areas_task,
    ifc_import_success,
)


@pytest.fixture
def site_with_ifc_file(site):
    return SiteDBHandler.update(
        item_pks={"id": site["id"]},
        new_values={"gcs_ifc_file_links": {"some": "ifc_file"}},
    )


def test_get_ifc_import_task_chain(
    mocker,
    celery_eager,
    site_with_ifc_file,
    mocked_gcp_download,
    mocked_geolocator,
    mocked_generate_geo_referencing_surroundings_for_site_task,
):
    from tasks import site_ifc_tasks

    mocker.patch.object(site_ifc_tasks, "NamedTemporaryFile")
    mocker.patch.object(
        IfcToSiteHandler,
        "_create_site_entities",
    )
    mocker.patch.object(
        IfcReader,
        "reference_point",
        mocker.PropertyMock(return_value=Point(8.100963474961297, 47.39892497922304)),
    )
    spy_create_ifc_entities = mocker.spy(create_ifc_entities_from_site_task, "si")
    spy_import_success = mocker.spy(ifc_import_success, "si")
    spy_ifc_create_plan_areas_task = mocker.spy(ifc_create_plan_areas_task, "si")

    chain = get_ifc_import_task_chain(site_id=site_with_ifc_file["id"])
    chain.delay(site_id=site_with_ifc_file["id"])

    spy_create_ifc_entities.assert_called_once_with(site_id=site_with_ifc_file["id"])
    spy_import_success.assert_called_once_with(site_id=site_with_ifc_file["id"])
    spy_ifc_create_plan_areas_task.assert_called_once_with(
        site_id=site_with_ifc_file["id"]
    )

    site_updated = SiteDBHandler.get_by(id=site_with_ifc_file["id"])
    assert ADMIN_SIM_STATUS.SUCCESS == site_updated["ifc_import_status"]
    assert site_updated["georef_region"] == REGION.CH.name
    assert mocked_generate_geo_referencing_surroundings_for_site_task.call_count == 1


def test_ifc_create_plan_areas_task_should_create_areas_with_preclassification(
    mocker,
    celery_eager,
    site,
    plan_annotated,
):
    import handlers.plan_utils
    from handlers import AreaHandler

    recover_and_upsert_areas_mock = mocker.patch.object(
        AreaHandler, "recover_and_upsert_areas"
    )
    spy_ifc_create_plan_areas = mocker.spy(handlers.plan_utils, "create_areas_for_plan")

    ifc_create_plan_areas_task(site_id=site["id"])
    spy_ifc_create_plan_areas.assert_called_once_with(
        plan_id=plan_annotated["id"], preclassify=True
    )
    recover_and_upsert_areas_mock.assert_called_once_with(
        plan_id=plan_annotated["id"], set_area_types_from_react_areas=True
    )


def test_ifc_import_on_error_persist_exception(
    mocker,
    celery_eager,
    site_with_ifc_file,
    mocked_gcp_download,
):
    from tasks import site_ifc_tasks

    mocker.patch.object(site_ifc_tasks, "NamedTemporaryFile")
    mocker.patch.object(
        IfcToSiteHandler,
        "_create_site_entities",
        side_effect=IfcEmptyStoreyException("You just failed"),
    )

    with pytest.raises(IfcEmptyStoreyException):
        chain = get_ifc_import_task_chain(site_id=site_with_ifc_file["id"])
        # prevent celery from reraising exception when in eager mode
        chain.apply_async(site_id=site_with_ifc_file["id"], throw=False)

    assert (
        ADMIN_SIM_STATUS.FAILURE
        == SiteDBHandler.get_by(id=site_with_ifc_file["id"])["ifc_import_status"]
    )
    assert {
        "msg": "You just failed",
        "code": "IfcEmptyStoreyException",
    } == SiteDBHandler.get_by(id=site_with_ifc_file["id"])["ifc_import_exceptions"]
