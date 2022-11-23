import pytest

from brooks.types import AreaType
from common_utils.exceptions import DBNotFoundException
from handlers import PlanHandler, SiteHandler
from handlers.copy_site import CopySite
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    ClientDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    QADBHandler,
    ReactPlannerProjectsDBHandler,
    SiteDBHandler,
    UnitDBHandler,
)
from handlers.utils import get_client_bucket_name
from tasks.dev_helper_tasks import copy_site_task


@pytest.fixture
def mocked_image_as_bytes(fixtures_path, mocker):
    with fixtures_path.joinpath("images/image_plan_332.jpg").open(mode="rb") as f:
        image_bytes = f.read()

    mocker.patch.object(
        PlanHandler, "get_plan_image_as_bytes", return_value=image_bytes
    )


class TestCopySite:
    def test_copy_plan_without_annotation_not_failing(
        self,
        make_sites,
        client_db,
        make_plans,
        make_buildings,
        mocked_image_as_bytes,
    ):

        site1, site2 = make_sites(*(client_db, client_db))
        building1, building2 = make_buildings(*(site1, site2))
        (plan_1,) = make_plans(*(building1,))
        with pytest.raises(DBNotFoundException):
            ReactPlannerProjectsDBHandler.get_by(plan_id=plan_1["id"])

        site_copier = CopySite()
        site_copier.building_mapping = {building1["id"]: building2["id"]}
        site_copier.new_site_id = site2["id"]
        site_copier._copy_plan_info(plan_1)

        assert len(PlanDBHandler.find(site_id=site2["id"])) == 1

    @pytest.mark.parametrize("copy_area_types", [True, False])
    def test_copy_plan(
        self, copy_area_types, client_db, make_sites, make_buildings, make_plans
    ):
        old_site, new_site = make_sites(*(client_db, client_db))
        old_building, new_building = make_buildings(*(old_site, new_site))
        old_plan, new_plan = make_plans(*(old_building, new_building))
        area_types_old_plan = [
            AreaType.ROOM.name,
            AreaType.BALCONY.name,
            AreaType.BATHROOM.name,
        ]
        AreaDBHandler.bulk_insert(
            [
                {
                    "coord_x": 1,
                    "coord_y": 2,
                    "plan_id": old_plan["id"],
                    "scaled_polygon": "Fake",
                    "area_type": area_type,
                }
                for area_type in area_types_old_plan
            ]
        )  # create old areas
        site_copier = CopySite()
        site_copier.plan_mapping[old_plan["id"]] = new_plan["id"]
        site_copier._copy_areas(plan=old_plan, copy_area_types=copy_area_types)

        area_types_new_plan = {
            area["area_type"]
            for area in AreaDBHandler.find(
                plan_id=new_plan["id"], output_columns=["area_type"]
            )
        }

        expected_area_types = (
            set(area_types_old_plan) if copy_area_types else {AreaType.NOT_DEFINED.name}
        )

        assert area_types_new_plan == expected_area_types

    def test_copy_annotation(
        self,
        mocker,
        client_db,
        make_sites,
        make_buildings,
        make_plans,
        mocked_image_as_bytes,
    ):
        site1, site2 = make_sites(*(client_db, client_db))
        building1, building2 = make_buildings(*(site1, site2))
        (plan_1,) = make_plans(*(building1,))
        annotations_data = {"foo": "bar"}
        ReactPlannerProjectsDBHandler.add(plan_id=plan_1["id"], data=annotations_data)

        db_handler_get_by_spy = mocker.spy(ReactPlannerProjectsDBHandler, "get_by")
        db_handler_add_spy = mocker.spy(ReactPlannerProjectsDBHandler, "add")

        site_copier = CopySite()
        site_copier.building_mapping = {building1["id"]: building2["id"]}
        site_copier.new_site_id = site2["id"]
        site_copier._copy_plan_info(plan=plan_1)
        new_plan_id = site_copier.plan_mapping[plan_1["id"]]

        site_copier._copy_annotation(plan=plan_1, site_id=site1["id"])

        db_handler_get_by_spy.assert_called_once_with(
            plan_id=plan_1["id"], output_columns=["data"]
        )
        db_handler_add_spy.assert_called_once_with(
            plan_id=new_plan_id, data=annotations_data
        )
        assert ReactPlannerProjectsDBHandler.get_by(
            plan_id=new_plan_id, output_columns=["data"]
        ) == dict(data=annotations_data)

    def test_full_copy_of_a_site(
        self, site_834, mocked_image_as_bytes, celery_eager, mocker, client_db
    ):

        site_id = site_834["site"]["id"]

        nbr_of_buildings = len(BuildingDBHandler.find())
        nbr_of_plans = len(PlanDBHandler.find())
        nbr_of_floors = len(FloorDBHandler.find())
        nbr_of_units = len(UnitDBHandler.find())
        nbr_of_annotations = len(ReactPlannerProjectsDBHandler.find())
        nbr_of_areas = len(AreaDBHandler.find())
        nbr_of_qa = len(QADBHandler.find())

        new_client = ClientDBHandler.add(name="Client2")

        mocked_plan_upload = mocker.spy(
            PlanHandler, "upload_plan_image_to_google_cloud"
        )

        new_site_id = copy_site_task(
            target_client_id=new_client["id"],
            site_id_to_copy=site_id,
            copy_area_types=True,
        )

        assert len(SiteDBHandler.find(client_id=new_client["id"])) == 1
        assert len(SiteDBHandler.find()) == 2
        assert len(BuildingDBHandler.find()) == 2 * nbr_of_buildings
        assert len(PlanDBHandler.find()) == 2 * nbr_of_plans
        assert len(FloorDBHandler.find()) == 2 * nbr_of_floors
        assert len(UnitDBHandler.find()) == 2 * nbr_of_units
        assert len(ReactPlannerProjectsDBHandler.find()) == 2 * nbr_of_annotations
        assert len(AreaDBHandler.find()) == 2 * nbr_of_areas
        assert len(QADBHandler.find()) == 2 * nbr_of_qa

        assert mocked_plan_upload.call_args_list[0].kwargs[
            "destination_bucket"
        ] == get_client_bucket_name(client_id=new_client["id"])

        old_results = SiteHandler.generate_basic_features(site_id=site_id)
        new_results = SiteHandler.generate_basic_features(site_id=new_site_id)
        for old_unit_result, new_unit_result in zip(old_results, new_results):
            old_basic_features = old_unit_result[1][0]
            new_basic_features = new_unit_result[1][0]
            for key, value in old_basic_features.items():
                assert new_basic_features[key] == pytest.approx(
                    expected=value, abs=0.01
                )

    def test_copy_to_existing_site(
        self, site_834, mocked_image_as_bytes, celery_eager, mocker, client_db
    ):

        site_id = site_834["site"]["id"]

        nbr_of_buildings = len(BuildingDBHandler.find())
        nbr_of_plans = len(PlanDBHandler.find())
        nbr_of_floors = len(FloorDBHandler.find())
        nbr_of_units = len(UnitDBHandler.find())
        nbr_of_annotations = len(ReactPlannerProjectsDBHandler.find())
        nbr_of_areas = len(AreaDBHandler.find())
        nbr_of_qa = len(QADBHandler.find())

        new_site_info = site_834["site"].copy()
        new_site_info.update(
            {
                "client_site_id": "target_site",
            }
        )
        new_site_info.pop("id")
        new_site_info = SiteDBHandler.add(**new_site_info)

        mocked_plan_upload = mocker.spy(
            PlanHandler, "upload_plan_image_to_google_cloud"
        )

        new_site_id = copy_site_task(
            target_client_id=new_site_info["client_id"],
            site_id_to_copy=site_id,
            copy_area_types=True,
            target_existing_site_id=new_site_info["id"],
        )

        assert len(SiteDBHandler.find()) == 2
        assert len(BuildingDBHandler.find()) == 2 * nbr_of_buildings
        assert len(PlanDBHandler.find()) == 2 * nbr_of_plans
        assert len(FloorDBHandler.find()) == 2 * nbr_of_floors
        assert len(UnitDBHandler.find()) == 2 * nbr_of_units
        assert len(ReactPlannerProjectsDBHandler.find()) == 2 * nbr_of_annotations
        assert len(AreaDBHandler.find()) == 2 * nbr_of_areas
        assert len(QADBHandler.find()) == 1 * nbr_of_qa

        assert mocked_plan_upload.call_args_list[0].kwargs[
            "destination_bucket"
        ] == get_client_bucket_name(client_id=new_site_info["client_id"])

        old_results = SiteHandler.generate_basic_features(site_id=site_id)
        new_results = SiteHandler.generate_basic_features(site_id=new_site_id)
        for old_unit_result, new_unit_result in zip(old_results, new_results):
            old_basic_features = old_unit_result[1][0]
            new_basic_features = new_unit_result[1][0]
            for key, value in old_basic_features.items():
                assert new_basic_features[key] == pytest.approx(
                    expected=value, abs=0.01
                )
