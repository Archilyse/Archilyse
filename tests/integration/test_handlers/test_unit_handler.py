from collections import Counter

import numpy as np
import pytest
from deepdiff import DeepDiff
from shapely import wkt

from brooks.models.violation import ViolationType
from brooks.types import AreaType
from common_utils.constants import (
    DEFAULT_GRID_BUFFER,
    DEFAULT_GRID_RESOLUTION,
    DEFAULT_OBSERVATION_HEIGHT,
    SIMULATION_VERSION,
)
from common_utils.exceptions import DBNotFoundException, ValidationException
from handlers import AreaHandler, PlanLayoutHandler, UnitHandler
from handlers.db import (
    AreaDBHandler,
    ClusteringSubsamplingDBHandler,
    PlanDBHandler,
    ReactPlannerProjectsDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from handlers.validators import UnitKitchenCountValidator


def test_get_unit_layout_post_processed(plan, building, make_classified_split_plans):
    """Not entirely clear what this test is really checking. It could be that is testing the spaces are not glued
    together due to the unary union of the walls"""
    make_classified_split_plans(
        plan, annotations_plan_id=5825, floor_number=1, building=building
    )
    spaces_counter = Counter()
    for unit in UnitDBHandler.find():
        unit_layout = UnitHandler().get_unit_layout(
            unit["id"],
            postprocessed=True,
        )
        spaces_counter[len(unit_layout.spaces)] += 1
    assert spaces_counter == {12: 1, 10: 1, 9: 1}


def test_get_unit_layout_additional_areas(unit, make_classified_plans, plan):
    """Check the validation of a unit where 1 area of a space containing 3 areas is assigned"""
    make_classified_plans(plan, annotations_plan_id=3332)
    PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        classified=True, scaled=True, raise_on_inconsistency=True
    )
    # Any of the 2 kitchen will do, as they are in a living room with corridor + kitchen
    area = AreaDBHandler.find(area_type="KITCHEN")[0]
    AreaHandler.update_relationship_with_units(
        plan_id=plan["id"],
        apartment_no=unit["apartment_no"],
        area_ids=[area["id"]],
    )
    violations = UnitHandler().validate_unit(unit_id=unit["id"])

    assert ViolationType.SPACE_MISSING_AREA_SELECTION.name not in {
        v.type for v in violations
    }
    unit_areas = UnitAreaDBHandler.find(unit_id=unit["id"])
    layout = UnitHandler().get_unit_layout(unit_id=unit["id"], postprocessed=False)

    assert len(layout.areas) == len(unit_areas)


def test_get_unit_layout_empty(plan, make_classified_plans, make_units, floor):
    """
    Given a classified plan
    and a unit with areas_ids empty
    when requesting the unit layout
    it will be empty
    """
    make_classified_plans(plan)
    (unit,) = make_units(floor)
    UnitDBHandler.update(
        item_pks=dict(id=unit["id"]), new_values=dict(plan_id=plan["id"])
    )
    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(georef_scale=0.001, georef_rot_x=1.0, georef_rot_y=1.0),
    )
    unit_layout = UnitHandler().get_unit_layout(unit_id=unit["id"], postprocessed=False)
    assert len(unit_layout.spaces) == 0

    """
    when adding area_ids to unit
    and requesting the unit_layout
    then the unit_layout will have one area
    """
    plan_areas = AreaDBHandler.find(plan_id=plan["id"])

    AreaHandler.update_relationship_with_units(
        plan_id=plan["id"],
        apartment_no=unit["apartment_no"],
        area_ids=[plan_areas[0]["id"]],
    )
    unit_layout = UnitHandler().get_unit_layout(unit_id=unit["id"], postprocessed=False)
    assert len(unit_layout.spaces) == 1


@pytest.mark.parametrize(
    "default_area_type, overwrite_area_types, expect_violation",
    [
        (
            AreaType.ROOM,
            [AreaType.COMMON_KITCHEN],
            None,
        ),
        (
            AreaType.ROOM,
            [
                AreaType.COMMON_KITCHEN,
                AreaType.COMMON_KITCHEN,
            ],
            None,
        ),
        (AreaType.ROOM, [AreaType.KITCHEN], None),
        (
            AreaType.ROOM,
            [AreaType.KITCHEN_DINING],
            None,
        ),
        (
            AreaType.ROOM,
            [AreaType.KITCHEN, AreaType.KITCHEN],
            ViolationType.APARTMENT_MULTIPLE_KITCHENS,
        ),
        # NOTE: For now we allow KITCHEN_DINING freely since it might
        #       be needed sometimes
        (
            AreaType.ROOM,
            [AreaType.KITCHEN, AreaType.KITCHEN_DINING],
            None,
        ),
        (
            AreaType.ROOM,
            [AreaType.KITCHEN_DINING, AreaType.KITCHEN_DINING],
            None,
        ),
    ],
)
def test_apartment_has_one_kitchen(
    mocker,
    fixtures_path,
    plan,
    default_area_type,
    overwrite_area_types,
    expect_violation,
    annotations_accessible_areas,
):
    # add annotations and create areas
    ReactPlannerProjectsDBHandler.add(
        plan_id=plan["id"], data=annotations_accessible_areas
    )
    AreaHandler.recover_and_upsert_areas(plan_id=plan["id"])

    PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values={"georef_rot_x": 0, "georef_rot_y": 0, "georef_scale": 0.01},
    )

    # get plan layout and update area types
    plan_layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        validate=False, classified=True
    )
    for area in plan_layout.areas:
        area._type = AreaType.ROOM

    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=plan_layout)
    db_area_ids = [db_area["id"] for db_area in AreaDBHandler.find()]

    for area in plan_layout.areas:
        area._type = default_area_type

    for area_type, area in zip(overwrite_area_types, plan_layout.areas):
        area._type = area_type

    violations = UnitKitchenCountValidator(
        plan_id=plan["id"],
        new_area_ids=db_area_ids,
        apartment_no=0,
        unit_handler=UnitHandler(),
    ).validate()

    if expect_violation:
        assert len(violations) == 1
        assert violations[0].violation_type == expect_violation
        assert (violations[0].position.x, violations[0].position.y) == (
            2042.5000000000002,
            -274.00000000000006,
        )
    else:
        assert not violations


def test_get_unit_layout_triangles(first_pipeline_complete_db_models, visualize=False):
    unit = first_pipeline_complete_db_models["units"][0]
    unit_handler = UnitHandler()
    layout = unit_handler.get_unit_layout(
        unit_id=unit["id"], georeferenced=True, postprocessed=False
    )
    triangles = unit_handler.get_layout_triangles(
        unit_id=unit["id"],
        layout=layout,
        layouts_upper_floor=[],
        building_elevation=100,
        simulation_version=SIMULATION_VERSION.PH_01_2021,
    )

    if visualize:
        from surroundings.visualization.sourroundings_3d_figure import (
            create_3d_surroundings_from_triangles_per_type,
        )

        create_3d_surroundings_from_triangles_per_type(
            filename="salpica",
            triangles_per_layout=[("a", triangles)],
            triangles_per_surroundings_type=[],
        )

    assert triangles.shape == (360, 3, 3)
    assert triangles.dtype.type == np.float64

    values = {
        "min_x": float(min([element[0] for row in triangles for element in row])),
        "min_y": float(min([element[1] for row in triangles for element in row])),
        "min_z": float(min([element[2] for row in triangles for element in row])),
        "max_x": float(max([element[0] for row in triangles for element in row])),
        "max_y": float(max([element[1] for row in triangles for element in row])),
        "max_z": float(max([element[2] for row in triangles for element in row])),
    }
    assert not DeepDiff(
        {
            "min_x": 1242383.0169182234,
            "min_y": 2715741.1925579486,
            "min_z": 102.8999,
            "max_x": 1242390.2695799854,
            "max_y": 2715746.441227982,
            "max_z": 105.5001,
        },
        values,
        significant_digits=2,
    )


def test_build_unit_georef(
    plan_georeferenced,
    make_classified_plans,
):
    areas = make_classified_plans(plan_georeferenced, annotations_plan_id=863)

    # we pick the 8 more left units :)
    splitting_areas = sorted(areas, key=lambda x: x["coord_x"])[:8]
    unit_layout = UnitHandler().build_unit_from_area_ids(
        plan_id=plan_georeferenced["id"],
        area_ids=[a["id"] for a in splitting_areas],
        georeference_plan_layout=False,
    )
    unit_layout_georef = UnitHandler().build_unit_from_area_ids(
        plan_id=plan_georeferenced["id"],
        area_ids=[a["id"] for a in splitting_areas],
        georeference_plan_layout=True,
    )

    assert len(unit_layout.spaces) == len(unit_layout_georef.spaces)
    assert len(unit_layout.areas) == len(unit_layout_georef.areas)
    assert sum(a.footprint.area for a in unit_layout.areas) == pytest.approx(
        sum(a.footprint.area for a in unit_layout_georef.areas)
    )

    assert unit_layout.footprint.centroid != unit_layout_georef.footprint.centroid


def test_get_obs_pts_by_area(plan, unit, make_classified_plans, site_coordinates):
    expected_obs_pts_by_area = {
        408640: 5,
        408633: 74,
        408595: 86,
        408656: 109,
        408596: 199,
        408608: 240,
        408606: 224,
        408627: 276,
        408634: 280,
        408620: 421,
    }
    PlanDBHandler.update(
        item_pks={"id": plan["id"]},
        new_values={
            "georef_rot_angle": 287.863360643585,
            "georef_x": site_coordinates["lon"],
            "georef_y": site_coordinates["lat"],
            "georef_scale": 1.78614621038232e-05,
            "georef_rot_x": 6648.5,
            "georef_rot_y": -3302.5,
        },
    )
    make_classified_plans(plan, annotations_plan_id=6380)
    AreaHandler.update_relationship_with_units(
        plan_id=plan["id"],
        apartment_no=0,
        area_ids=[
            408640,
            408633,
            408595,
            408656,
            408596,
            408608,
            408606,
            408627,
            408634,
            408620,
        ],
    )
    pts = UnitHandler().get_obs_points_by_area(
        unit_id=unit["id"],
        grid_resolution=DEFAULT_GRID_RESOLUTION,
        grid_buffer=DEFAULT_GRID_BUFFER,
        obs_height=DEFAULT_OBSERVATION_HEIGHT,
    )
    assert {
        area_id: len(obs_pts) for area_id, obs_pts in pts.items()
    } == expected_obs_pts_by_area


def test_apartment_validation_error_correctly_displayed_react(
    make_react_annotation_fully_pipelined,
    react_planner_background_image_one_unit,
):
    full_pipeline = make_react_annotation_fully_pipelined(
        react_planner_background_image_one_unit
    )
    plan_id = full_pipeline["plan"]["id"]
    areas = AreaDBHandler.find(plan_id=plan_id, output_columns=["id", "scaled_polygon"])
    left_out_area = sorted(
        areas, key=lambda area: wkt.loads(area["scaled_polygon"]).area, reverse=False
    )[0]

    errors = UnitHandler().validate_unit_given_area_ids(
        plan_id=plan_id,
        new_area_ids=[
            area["id"] for area in areas if area["id"] != left_out_area["id"]
        ],
        apartment_no=1,
    )

    layout = PlanLayoutHandler(plan_id=full_pipeline["plan"]["id"]).get_layout(
        postprocessed=False
    )

    smallest_area = sorted(layout.areas, key=lambda area: area.footprint.area)[0]

    assert len(errors) == 1
    assert errors[0].type == "CONNECTED_SPACES_MISSING"
    assert errors[0].position.within(smallest_area.footprint)
    assert errors[0].position.x == pytest.approx(expected=661.95, abs=0.01)
    assert errors[0].position.y == pytest.approx(expected=573.01, abs=0.01)


@pytest.mark.parametrize(
    "clusters_data, expected",
    [
        ({"foo": ["bar"]}, "foo"),
        ({"foo": ["no match"]}, None),
    ],
)
def test_update_units_representative_cluster_data(
    site, plan, floor, clusters_data, expected
):
    unit = UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=0,
        client_id="bar",
    )
    UnitHandler.update_units_representative(
        site_id=site["id"], clustering_subsampling=clusters_data
    )
    unit = UnitDBHandler.get_by(id=unit["id"])
    assert unit["representative_unit_client_id"] == expected


@pytest.mark.parametrize(
    "clusters_data, expected",
    [
        ({"foo": ["bar"]}, "foo"),
        ({"foo": ["no match"]}, None),
    ],
)
def test_update_units_representative_cluster_id(
    site, plan, floor, clusters_data, expected
):
    unit = UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=0,
        client_id="bar",
    )
    # prepare_simulation
    cluster_db = ClusteringSubsamplingDBHandler.add(
        site_id=site["id"], results=clusters_data
    )

    UnitHandler.update_units_representative(
        site_id=site["id"], clustering_id=cluster_db["id"]
    )

    unit = UnitDBHandler.get_by(id=unit["id"])
    assert unit["representative_unit_client_id"] == expected


def test_update_units_representative_empty_args(site, plan, floor):
    UnitDBHandler.add(
        site_id=site["id"],
        plan_id=plan["id"],
        floor_id=floor["id"],
        apartment_no=0,
        client_id="foo",
    )
    with pytest.raises(DBNotFoundException):
        UnitHandler.update_units_representative(site_id=site["id"])


def test_bulk_upsert_units():
    with pytest.raises(
        ValidationException,
        match="No floors found for plan 1 while trying to create units",
    ):
        UnitHandler().bulk_upsert_units(plan_id=1, apartment_no=0)
