import mimetypes
from collections import Counter
from typing import Dict, List
from unittest.mock import PropertyMock

import pytest
from shapely.geometry import box

from brooks.models import SimArea, SimLayout
from brooks.types import AreaType
from handlers import PlanHandler, PlanLayoutHandler
from handlers.db import (
    AreaDBHandler,
    BuildingDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
)
from handlers.editor_v2.schema import ReactPlannerData
from tasks.pipeline_tasks import auto_classify_areas_for_plan


def test_add_plan_should_return_existing_plan_id(
    mocked_plan_image_upload_to_gc, building, plan, fixtures_path
):
    floorplan_path = fixtures_path.joinpath("images/image_plan_332.jpg")
    with floorplan_path.open("rb") as fp:
        content_type = "image/jpg"
        assert len(PlanDBHandler.find()) == 1
        new_plan = PlanHandler.add(
            plan_content=fp.read(),
            plan_mime_type=content_type,
            site_id=plan["site_id"],
            building_id=building["id"],
        )
        assert len(PlanDBHandler.find()) == 1
        assert new_plan["id"] == plan["id"]


def test_add_plan_different_image_same_building_should_be_valid(
    mocked_plan_image_upload_to_gc, building, plan, fixtures_path, monkeypatch
):
    floorplan_b_path = fixtures_path.joinpath("images/floorplan_b.jpg")
    with floorplan_b_path.open("rb") as fp:
        content_type = "image/jpg"
        assert len(PlanDBHandler.find()) == 1
        new_plan_info = PlanHandler.add(
            plan_content=fp.read(),
            plan_mime_type=content_type,
            site_id=building["site_id"],
            building_id=building["id"],
        )
        all_plans = PlanDBHandler.find()

        assert new_plan_info["id"] != plan["id"]
        assert len(all_plans) == 2
        latest_inserted_plan = list(
            sorted(all_plans, key=lambda pl: pl["id"], reverse=True)
        )[0]
        assert latest_inserted_plan["building_id"] == building["id"]


def test_add_plan_different_image_different_building_be_valid(
    mocked_plan_image_upload_to_gc, site, plan, fixtures_path, monkeypatch
):
    building = BuildingDBHandler.add(
        site_id=site["id"],
        housenumber="test",
        city="test",
        zipcode="test",
        street="test",
    )

    floorplan_b_path = fixtures_path.joinpath("images/floorplan_b.jpg")
    with floorplan_b_path.open("rb") as fp:
        content_type = "image/jpg"
        new_plan_info = PlanHandler.add(
            plan_content=fp.read(),
            plan_mime_type=content_type,
            site_id=site["id"],
            building_id=building["id"],
        )
        all_plans = PlanDBHandler.find()
        assert new_plan_info["id"] != plan["id"]

        assert len(all_plans) == 2
        latest_inserted_plan = list(
            sorted(all_plans, key=lambda pl: pl["id"], reverse=True)
        )[0]
        assert latest_inserted_plan["building_id"] == building["id"]


def test_adding_new_plan_is_copying_georef_data_from_masterplan(
    mocked_plan_image_upload_to_gc, site, building, mocker, plan
):
    georef_data = {
        "georef_rot_angle": 1,
        "georef_x": 2,
        "georef_y": 3,
        "georef_rot_x": 4,
        "georef_rot_y": 5,
    }
    new_values = {"is_masterplan": True, **georef_data}
    PlanDBHandler.update(item_pks={"id": plan["id"]}, new_values=new_values)
    mocker.patch.object(
        PlanHandler, "_extract_image_parameters_for_plan", return_value=[100, 100]
    )
    new_plan = PlanHandler.add(
        plan_content=b"random",
        plan_mime_type="image/jpg",
        site_id=site["id"],
        building_id=building["id"],
    )
    for key, value in georef_data.items():
        assert value == new_plan[key]


def test_add_plan_as_pdf(
    mocked_plan_image_upload_to_gc, site, fixtures_path, monkeypatch
):
    building = BuildingDBHandler.add(
        site_id=site["id"],
        housenumber="test",
        city="test",
        zipcode="test",
        street="test",
    )

    floorplan_b_path = fixtures_path.joinpath("images/pdf_sample.pdf")
    with floorplan_b_path.open("rb") as fp:
        new_plan_info = PlanHandler.add(
            plan_content=fp.read(),
            plan_mime_type=mimetypes.types_map[".pdf"],
            site_id=site["id"],
            building_id=building["id"],
        )

        assert new_plan_info["image_gcs_link"]
        assert new_plan_info["image_width"] == 2550
        assert new_plan_info["image_height"] == 3300
        assert new_plan_info["image_mime_type"] == "image/jpeg"


@pytest.mark.parametrize("file_format", [".dxf", ".dwg"])
def test_add_plan_as_dxf_dwg(
    mocker,
    mocked_plan_image_upload_to_gc,
    site,
    fixtures_path,
    monkeypatch,
    dxf_sample,
    file_format,
):
    import handlers.plan_utils
    from handlers import CloudConvertHandler

    cloud_convert_mock = mocker.patch.object(
        CloudConvertHandler, "transform", return_value=dxf_sample
    )

    georef_params = {"georef_scale": 1.0, "georef_rot_angle": 99}
    with open(fixtures_path.joinpath("images/dxf_sample.png"), "rb") as fh:
        mocker.patch.object(
            PlanHandler,
            "load_dxf",
            return_value=(
                fh.read(),
                ReactPlannerData(),
                georef_params,
            ),
        )

    mocked_sim_area = SimArea(footprint=box(0, 0, 1, 1))
    mocked_sim_area._type = AreaType.ROOM
    mocked_sim_area.db_area_id = 1
    mocker.patch.object(
        SimLayout, "areas", PropertyMock(return_value={mocked_sim_area})
    )
    mocked_get_raw_layout = mocker.patch.object(
        PlanLayoutHandler, "_get_raw_layout_from_react_data", return_value=SimLayout()
    )

    spy_create_areas_for_plan = mocker.spy(handlers.plan_utils, "create_areas_for_plan")
    spy_auto_classify_areas_for_plan_task_called_async = mocker.spy(
        auto_classify_areas_for_plan, "apply_async"
    )

    building = BuildingDBHandler.add(
        site_id=site["id"],
        housenumber="test",
        city="test",
        zipcode="test",
        street="test",
    )
    new_plan_info = PlanHandler.add(
        plan_content=dxf_sample if file_format == ".dxf" else b"dwg_dummy",
        plan_mime_type=mimetypes.types_map[file_format],
        site_id=site["id"],
        building_id=building["id"],
    )

    assert (
        not spy_create_areas_for_plan.called
    )  # We should not call task async inside a db session
    assert not spy_auto_classify_areas_for_plan_task_called_async.called

    assert new_plan_info["image_gcs_link"]
    assert new_plan_info["image_width"] == 2049
    assert new_plan_info["image_height"] == 1419
    assert {
        key: new_plan_info[key] for key in ("georef_scale", "georef_rot_angle")
    } == georef_params
    assert new_plan_info["image_mime_type"] == "image/jpeg"
    assert ReactPlannerProjectsDBHandler.get_by(plan_id=new_plan_info["id"])

    assert mocked_get_raw_layout.call_args_list[0].kwargs == {
        "postprocessed": False,
        "set_area_types_by_features": False,
        "set_area_types_from_react_areas": True,
        "deep_copied": True,
    }
    assert mocked_get_raw_layout.call_args_list[1].kwargs == {
        "postprocessed": False,
        "set_area_types_by_features": False,
        "set_area_types_from_react_areas": False,
        "deep_copied": True,
    }
    db_areas = AreaDBHandler.find(plan_id=new_plan_info["id"])
    assert len(db_areas) == 1
    assert db_areas[0]["area_type"] == AreaType.ROOM.name

    if file_format == ".dwg":
        cloud_convert_mock.assert_called_once()
        assert cloud_convert_mock.call_args.kwargs["input_format"] == "dwg"
        assert cloud_convert_mock.call_args.kwargs["output_format"] == "dxf"


def test_get_site_plans_layouts_with_floor_numbers(
    building, make_classified_plans, make_plans, make_floor
):
    plans = make_plans(building, building)
    make_classified_plans(*plans, annotations_plan_id=332, db_fixture_ids=False)
    for i, plan in enumerate(plans):
        make_floor(plan=plan, floornumber=i, building=building)
    site_plan_layouts_w_floor = (
        PlanHandler.get_site_plans_layouts_with_building_floor_numbers(
            site_id=building["site_id"]
        )
    )
    assert all(
        isinstance(x["plan_layout"], SimLayout) and isinstance(x["building_id"], int)
        for x in site_plan_layouts_w_floor
    )
    assert Counter(
        [y for x in site_plan_layouts_w_floor for y in x["floor_numbers"]]
    ) == Counter({0: 1, 1: 1})


def test_get_other_georeferenced_footprints_under_same_site(
    mocker,
    client_db,
    make_sites,
    make_buildings,
    make_plans,
    make_annotations,
    make_floor,
):
    site, *_ = make_sites(client_db)
    building, *_ = make_buildings(site)
    plans: List[Dict] = make_plans(
        building,
        building,
        building,
        building,
    )
    # note plans[3] doesn't have a floor
    make_floor(building, plans[0], floornumber=3)
    make_floor(building, plans[1], floornumber=2)
    make_floor(building, plans[1], floornumber=4)
    make_floor(building, plans[2], floornumber=1)
    make_annotations(*plans)

    payload = {
        attr: {p["id"]: 1 for p in plans}
        for attr in {
            "georef_scale",
            "georef_x",
            "georef_y",
            "georef_rot_angle",
            "georef_rot_x",
            "georef_rot_y",
        }
    }
    PlanDBHandler.bulk_update(**payload)
    first_plan, *rest = plans

    get_other_georefd_plans_by_site_spy = mocker.spy(
        PlanDBHandler, "get_other_georeferenced_plans_by_site"
    )
    get_plan_from_db_spy = mocker.spy(PlanDBHandler, "get_by")

    other_plans = list(
        PlanHandler(
            plan_id=first_plan["id"], plan_info=first_plan
        ).get_other_georeferenced_footprints_under_same_site()
    )
    # make sure only one plan per floor and ordered by floor number such that the closest
    # floor is first to the queried plan comes first.
    assert len(other_plans) == 3
    assert [p["id"] for p in other_plans] == [
        plans[1]["id"],
        plans[2]["id"],
        plans[3]["id"],
    ]
    get_other_georefd_plans_by_site_spy.assert_called_once_with(
        plan_id=first_plan["id"]
    )
    get_plan_from_db_spy.assert_not_called()
