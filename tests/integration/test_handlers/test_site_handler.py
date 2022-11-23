import json
from collections import defaultdict
from pathlib import Path
from unittest.mock import create_autospec

import pytest
from shapely import wkt
from shapely.geometry import Point

from common_utils.constants import (
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION,
    DEFAULT_OBSERVATION_HEIGHT,
    SIMULATION_VERSION,
)
from handlers import PlanHandler, SiteHandler
from handlers.db import FloorDBHandler, SiteDBHandler, UnitAreaDBHandler, UnitDBHandler
from tests.utils import check_3d_mesh_format


def test_get_site_layout_triangles(first_pipeline_complete_db_models):
    site_id = first_pipeline_complete_db_models["site"]["id"]

    meshes = list(
        SiteHandler.get_layout_triangles(
            site_id=site_id,
            simulation_version=SIMULATION_VERSION.PH_01_2021,
            by_unit=False,
        )
    )

    check_3d_mesh_format(
        meshes=meshes,
        expected_dimensions={(3742, 3, 3)},
        expected_mesh_names={
            first_pipeline_complete_db_models["floor"]["floor_number"]
        },
        expected_nbr_of_meshes=1,
    )


def test_get_site_layout_triangles_editor_v2(
    mocker,
    site,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
):
    react_plan_extended_fully_pipelined = make_react_annotation_fully_pipelined(
        react_planner_background_image_full_plan,
        update_plan_rotation_point=False,
    )
    mocker.patch.object(PlanHandler, "translation_point", spec=Point, x=1, y=1)
    floors = FloorDBHandler.find(
        plan_id=react_plan_extended_fully_pipelined["plan"]["id"],
        output_columns=["floor_number"],
    )
    meshes = list(
        SiteHandler.get_layout_triangles(
            site_id=site["id"],
            simulation_version=SIMULATION_VERSION.PH_01_2021,
            by_unit=False,
        )
    )

    """
    from surroundings.visualization.sourroundings_3d_figure import (
        create_3d_surroundings_from_triangles_per_type,
    )
    create_3d_surroundings_from_triangles_per_type(
        filename="salpica_void",
        triangles_per_layout=meshes,
        triangles_per_surroundings_type=[],
    )
    """
    check_3d_mesh_format(
        meshes=meshes,
        expected_dimensions={(1672, 3, 3)},
        expected_bounds=(1.842, 9.501, 14.854, 22.038),
        expected_nbr_of_meshes=len(floors),
        expected_mesh_names={floor["floor_number"] for floor in floors},
    )


def test_generate_surroundings_for_georeferencing(
    mocker, fixtures_path, site, mocked_gcp_upload_file_to_bucket
):
    from surroundings.base_building_handler import Building
    from surroundings.swisstopo.building_surrounding_handler import (
        SwissTopoBuildingSurroundingHandler,
    )

    with fixtures_path.joinpath("georeferencing/georef_buildings.json").open(
        mode="r"
    ) as f:
        mocked_building_data = json.load(f)
        mocked_building = Building(
            geometry=wkt.loads(mocked_building_data["geometry"]),
            footprint=wkt.loads(mocked_building_data["footprint"]),
        )
        mocker.patch.object(
            SwissTopoBuildingSurroundingHandler,
            "get_buildings",
            return_value=[mocked_building],
        )

    mocker.patch.object(
        SiteHandler,
        "get_building_json_surroundings_path",
        return_value=create_autospec(Path),
    )
    mocker.patch.object(json, "dump")

    SiteHandler.generate_georeferencing_surroundings_slam(site_id=site["id"])
    updated_site_db = SiteDBHandler.get_by(id=site["id"])
    assert updated_site_db["gcs_buildings_link"] is not None


def tests_site_observation_points(first_pipeline_complete_db_models):
    site_id = first_pipeline_complete_db_models["site"]["id"]
    obs_points_by_unit_and_area = SiteHandler.get_obs_points_by_unit_and_area(
        site_id=site_id,
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_OBSERVATION_HEIGHT,
    )

    db_area_ids = list(
        UnitAreaDBHandler.find_in(
            unit_id=list(UnitDBHandler.find_ids(site_id=site_id)),
        )
    )

    obs_by_unit_and_area = defaultdict(set)
    for unit, areas_obs in obs_points_by_unit_and_area.items():
        for values in areas_obs.values():
            obs_by_unit_and_area[unit].add(len(values))

    area_ids_in_obs = {
        area_id
        for unit, areas_obs in obs_points_by_unit_and_area.items()
        for area_id, values in areas_obs.items()
    }
    assert {x["area_id"] for x in db_area_ids} >= area_ids_in_obs

    assert {100: {350}, 200: {329}, 300: {285}, 301: {266}} == obs_by_unit_and_area


def test_get_public_layouts(site, plan_classified_scaled, floor):
    public_layouts = list(
        SiteHandler.get_public_layouts(site_id=site["id"], scaled=True)
    )
    assert len(public_layouts) == 1
    floor_id, public_layout = public_layouts[0]
    assert floor_id == floor["id"]


@pytest.mark.parametrize(
    "floor_number, plans_returned, with_underground",
    [(0, True, False), (1, True, True), (-1, False, False), (-2, True, True)],
)
def test_plan_footprints_per_building_underground_floors_selectable(
    site,
    plan_classified_scaled_georeferenced,
    floor,
    floor_number,
    plans_returned,
    with_underground,
):
    FloorDBHandler.update(
        item_pks={"id": floor["id"]}, new_values={"floor_number": floor_number}
    )
    plans = SiteHandler._plan_footprints_per_building(
        site_id=site["id"], with_underground=with_underground
    )
    assert bool(plans) == plans_returned


@pytest.mark.parametrize(
    "floor_numbers, plans_returned",
    [
        ([0, 1], True),
        ([1, 2], True),
        ([-1, -2], False),
        ([-1, -5], False),
        ([-1, 0], True),
        ([-2, 0], True),
    ],
)
def test_plan_footprints_per_building_2_floors(
    site,
    plan_classified_scaled_georeferenced,
    building,
    floor,
    floor_numbers,
    plans_returned,
):
    FloorDBHandler.update(
        item_pks={"id": floor["id"]}, new_values={"floor_number": floor_numbers[0]}
    )
    FloorDBHandler.add(
        plan_id=plan_classified_scaled_georeferenced["id"],
        building_id=building["id"],
        floor_number=floor_numbers[1],
    )
    plans = SiteHandler._plan_footprints_per_building(site_id=site["id"])
    assert bool(plans) == plans_returned
