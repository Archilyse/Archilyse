from dataclasses import asdict

import pytest

from handlers.db import (
    BuildingDBHandler,
    FloorDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
)
from handlers.ifc import IfcToSiteHandler
from handlers.ifc.constants import PIXELS_PER_METER
from ifc_reader.constants import IFC_BUILDING


@pytest.fixture
def entities_for_deduplication(fixtures_path, site):
    from handlers.editor_v2.schema import ReactPlannerData

    with fixtures_path.joinpath("images/image_plan_332.jpg").open("rb") as f:
        plan = {
            "plan_mime_type": "image/jpg",
            "plan_content": f.read(),
            "site_id": site["id"],
        }

    buildings = {
        "housenumber": "1",
        "city": "Zurich",
        "zipcode": "1111",
        "street": "something",
    }
    floors = [{"floor_number": 0}, {"floor_number": 1}]
    plans = [plan for _ in range(2)]
    annotations_react_data = [asdict(ReactPlannerData()) for _ in range(2)]
    return [
        {
            "building": buildings,
            "floors": floors,
            "plans": plans,
            "annotations_react_planner": annotations_react_data,
        }
    ]


def building_address_data(
    wrapper, city: str = None, street: str = None, zipcode: str = None
):
    if all([city, street, zipcode]):
        address = wrapper.create_entity(
            "IfcPostalAddress",
            Town="Zuerich",
            AddressLines=["somewhere 1"],
            PostalCode="1111",
        )
        return address


@pytest.mark.parametrize(
    "input_address",
    [{"city": "Zuerich", "street": "somewhere 1", "zipcode": "1111"}, {}],
)
def test_create_site_entities(
    fixtures_path,
    site,
    mocked_gcp_upload_bytes_to_bucket,
    input_address,
    ac20_fzk_haus_ifc_reader,
):
    address = building_address_data(
        wrapper=ac20_fzk_haus_ifc_reader.wrapper, **input_address
    )

    ifc_building = ac20_fzk_haus_ifc_reader.wrapper.by_type(IFC_BUILDING)[0]
    ifc_building.BuildingAddress = address

    handler = IfcToSiteHandler(ifc_reader=ac20_fzk_haus_ifc_reader)
    handler.create_and_save_site_entities(
        site_id=site["id"], ifc_filename="AC20-FZK-Haus.ifc"
    )

    buildings = BuildingDBHandler.find(site_id=site["id"])
    assert len(buildings) == 1

    building = buildings[0]

    assert building["id"]
    assert building["city"] == input_address.get("city", "N/A")
    assert building["street"] == input_address.get("street", "N/A")
    assert building["zipcode"] == input_address.get("zipcode", "N/A")
    assert building["housenumber"] == ifc_building.GlobalId
    assert building["client_building_id"] == "AC20-FZK-Haus.ifc"

    floors = FloorDBHandler.find(building_id=building["id"])
    assert all(f["floor_number"] in [0, 1] for f in floors)
    assert len(floors) == 2

    plans = PlanDBHandler.find(building_id=building["id"])
    assert len(plans) == 2
    assert all(p["image_mime_type"] == "image/jpg" for p in plans)

    assert len(ReactPlannerProjectsDBHandler.find()) == 2

    plans = sorted(plans, key=lambda x: x["id"])
    assert len(plans) == 2
    for plan, expected_georef_scale in zip(plans, [1 / PIXELS_PER_METER**2] * 2):
        assert plan["georef_scale"] == pytest.approx(expected_georef_scale, abs=1e-9)
        assert plan["georef_rot_x"] == pytest.approx(0.0, abs=1e-3)
        assert plan["georef_rot_y"] == pytest.approx(0.0, abs=1e-3)
        assert plan["georef_rot_angle"] == pytest.approx(49.999, abs=1e-3)

    plans_by_id = {plan["id"]: plan for plan in plans}
    plan_by_floor_number = {
        floor["floor_number"]: plans_by_id[floor["plan_id"]] for floor in floors
    }

    expected_heights_value_by_floor = {
        0: {
            "default_wall_height": 2.7,
            "default_door_height": 2.38,
            "default_window_upper_edge": 2.15,
            "default_window_lower_edge": 0.8,
            "default_ceiling_slab_height": 0.3,
        },
        1: {
            "default_wall_height": 3.39,
            "default_door_height": 2.0,
            "default_window_upper_edge": 1.8,
            "default_window_lower_edge": 0.8,
            "default_ceiling_slab_height": 0.3,
        },
    }
    keys = (
        "default_wall_height",
        "default_door_height",
        "default_window_upper_edge",
        "default_window_lower_edge",
        "default_ceiling_slab_height",
    )
    heights_by_floor_number = {}
    for floor_number, plan in plan_by_floor_number.items():
        heights_by_floor_number[floor_number] = {key: plan[key] for key in keys}
    assert expected_heights_value_by_floor == heights_by_floor_number


def test_save_site_entities_duplicate_floor_images(
    client_db,
    site,
    mocked_gcp_upload_file_to_bucket,
    ac20_fzk_haus_ifc_reader,
    mocked_plan_image_upload_to_gc,
    entities_for_deduplication,
):
    handler = IfcToSiteHandler(ac20_fzk_haus_ifc_reader)
    handler._save_site_entities(
        site_id=site["id"], buildings=entities_for_deduplication
    )
    inserted_plans = PlanDBHandler.find(site_id=site["id"])
    inserted_floors = FloorDBHandler.find()
    inserted_annotations = ReactPlannerProjectsDBHandler.find()
    assert len(inserted_plans) == 1
    assert len(inserted_floors) == 2
    assert len(inserted_annotations) == len(inserted_plans)
