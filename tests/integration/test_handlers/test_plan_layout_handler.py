from collections import Counter

import pytest

from brooks.types import AreaType, get_valid_area_type_from_string
from common_utils.exceptions import AreaMismatchException
from handlers import AreaHandler, PlanLayoutHandler, ReactPlannerHandler
from handlers.db import AreaDBHandler, PlanDBHandler, UnitAreaDBHandler, UnitDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper


def test_get_brooks_model_classified_updates_model_with_areadbmodel_info(
    plan, areas_in_db
):
    plan_id = plan["id"]

    # given
    # update the area db models in the db simulating some user defined areas
    for db_area in AreaDBHandler.find(plan_id=plan_id):
        AreaDBHandler.update(
            item_pks=dict(id=db_area["id"]),
            new_values=dict(area_type=AreaType.BATHROOM.name),
        )

    # when
    plan_layout = PlanLayoutHandler(plan_id=plan_id).get_layout(classified=True)

    # then
    assert plan_layout.areas
    for brooks_area in plan_layout.areas:
        assert brooks_area.type == AreaType.BATHROOM


def test_get_layout_classified_raises_area_mismatch_exception(
    plan, annotations_finished
):
    with pytest.raises(AreaMismatchException):
        PlanLayoutHandler(plan_id=plan["id"]).get_layout(
            classified=True, raise_on_inconsistency=True
        )


def test_get_layout_classified_raises_area_mismatch_exception_on_extra_area(
    site_with_3_units,
):
    assert PlanLayoutHandler(plan_id=site_with_3_units["plan"]["id"]).get_layout(
        classified=True, raise_on_inconsistency=True
    )

    # When we add an extra area
    AreaDBHandler.add(
        coord_x=1,
        scaled_polygon="",
        area_type=AreaType.ROOM.value,
        coord_y=1,
        plan_id=site_with_3_units["plan"]["id"],
    )

    with pytest.raises(AreaMismatchException):
        PlanLayoutHandler(plan_id=site_with_3_units["plan"]["id"]).get_layout(
            classified=True, raise_on_inconsistency=True
        )


def test_get_layout_classified_raises_area_mismatch_exception_on_not_matching_area(
    site_with_3_units,
):
    assert PlanLayoutHandler(plan_id=site_with_3_units["plan"]["id"]).get_layout(
        classified=True, raise_on_inconsistency=True
    )

    areas = AreaDBHandler.find(plan_id=site_with_3_units["plan"]["id"])

    # When we change an area to not match
    AreaDBHandler.update(
        item_pks=areas[0],
        new_values=dict(
            coord_x=areas[0]["coord_x"] + 10000, coord_y=areas[0]["coord_y"] + 10000
        ),
    )

    with pytest.raises(AreaMismatchException):
        PlanLayoutHandler(plan_id=site_with_3_units["plan"]["id"]).get_layout(
            classified=True, raise_on_inconsistency=True
        )


def test_get_unit_layouts_empty_unit_areas(
    plan, make_classified_plans, make_units, floor
):
    make_classified_plans(plan)
    (unit,) = make_units(floor)
    UnitDBHandler.update(
        item_pks=dict(id=unit["id"]), new_values=dict(plan_id=plan["id"])
    )
    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(georef_scale=0.001, georef_rot_x=1.0, georef_rot_y=1.0),
    )

    unit_layouts = list(
        PlanLayoutHandler(plan_id=plan["id"]).get_unit_layouts(floor_id=floor["id"])
    )

    assert len(unit_layouts) == 1
    assert len(unit_layouts[0][1].spaces) == 0


def test_get_unit_layouts_raises_area_mismatch_exception(
    plan, make_classified_plans, make_units, floor
):
    # given
    make_classified_plans(plan)
    (unit,) = make_units(floor)
    UnitDBHandler.update(
        item_pks=dict(id=unit["id"]), new_values=dict(plan_id=plan["id"])
    )
    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(georef_scale=0.001, georef_rot_x=1.0, georef_rot_y=1.0),
    )
    plan_areas = AreaDBHandler.find(plan_id=plan["id"])
    AreaDBHandler.delete(item_pk={"id": plan_areas[0]["id"]})

    # then
    with pytest.raises(AreaMismatchException):
        # when
        list(
            PlanLayoutHandler(plan_id=plan["id"]).get_unit_layouts(floor_id=floor["id"])
        )


def test_get_unit_layouts(plan, make_classified_plans, make_units, floor):
    # given
    make_classified_plans(plan)
    (unit,) = make_units(floor)
    UnitDBHandler.update(
        item_pks=dict(id=unit["id"]), new_values=dict(plan_id=plan["id"])
    )
    PlanDBHandler.update(
        item_pks=dict(id=plan["id"]),
        new_values=dict(georef_scale=0.001, georef_rot_x=1.0, georef_rot_y=1.0),
    )
    plan_areas = AreaDBHandler.find(plan_id=plan["id"])
    AreaHandler.update_relationship_with_units(
        plan_id=plan["id"],
        apartment_no=unit["apartment_no"],
        area_ids=[plan_areas[0]["id"]],
    )

    # when
    unit_layouts = list(
        PlanLayoutHandler(plan_id=plan["id"]).get_unit_layouts(floor_id=floor["id"])
    )

    # then
    assert len(unit_layouts) == 1
    assert len(unit_layouts[0][1].spaces) == 1
    assert len([a for _, l in unit_layouts for s in l.spaces for a in s.areas]) == len(
        UnitAreaDBHandler.find()
    )

    # classification is as expected
    db_areas = {a["id"]: a for a in plan_areas}
    brooks_area_id_to_db_area_id = {
        brooks_area.id: db_area["id"]
        for brooks_area, db_area in AreaHandler.map_existing_areas(
            brooks_areas={
                a
                for unit_id, layout in unit_layouts
                for s in layout.spaces
                for a in s.areas
            },
            db_areas=plan_areas,
        )
    }
    assert all(
        a.type
        == get_valid_area_type_from_string(
            db_areas[brooks_area_id_to_db_area_id[a.id]]["area_type"]
        )
        for _, l in unit_layouts
        for s in l.spaces
        for a in s.areas
    )


def test_get_public_layout(plan_classified_scaled, unit):
    # Given
    # a classified plan
    plan_handler = PlanLayoutHandler(plan_id=plan_classified_scaled["id"])
    plan_spaces = list(plan_handler.get_layout(classified=True).spaces)
    # with one unit area and lots of public spaces
    unit_area = list(plan_spaces[0].areas)[0]
    UnitAreaDBHandler.add(unit_id=unit["id"], area_id=unit_area.db_area_id)
    # When
    public_spaces = plan_handler.get_public_layout().spaces
    # Then
    assert len(public_spaces) == len(plan_spaces) - 1


def test_get_layout_experimental_for_pipeline_areas_should_match(
    celery_eager,
    plan,
    react_planner_background_image_one_unit,
):
    """
    Tests whether the requested brooks model for pipeline and areas for pipeline are
    matching and classification can be done
    """
    ReactPlannerHandler().store_plan_data(
        plan_id=plan["id"],
        plan_data=react_planner_background_image_one_unit,
        validated=True,
    )
    for area in AreaDBHandler.find(plan_id=plan["id"]):
        AreaDBHandler.update(
            item_pks={"id": area["id"]}, new_values={"area_type": AreaType.ROOM.value}
        )

    layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        scaled=False, classified=False, postprocessed=False
    )

    db_areas = AreaDBHandler.find(plan_id=plan["id"])

    assert len(
        [
            True
            for _ in AreaHandler.map_existing_areas(
                brooks_areas=layout.areas,
                db_areas=db_areas,
                raise_on_inconsistency=True,
            )
        ]
    ) == len(layout.areas)


def test_get_postprocessed_react_planner_layout_all_areas_valid(
    plan,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
):
    make_react_annotation_fully_pipelined(react_planner_background_image_full_plan)
    layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        scaled=True, classified=True, georeferenced=True, postprocessed=False
    )
    assert all([not area.footprint.is_empty for area in layout.areas])
    assert all([area.footprint.is_valid for area in layout.areas])


def test_get_layout_react_should_be_implicitly_scaled(
    mocker,
    plan,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
):
    make_react_annotation_fully_pipelined(react_planner_background_image_full_plan)
    plan_handler = PlanLayoutHandler(plan_id=plan["id"])
    mapper_spy = mocker.spy(ReactPlannerToBrooksMapper, "get_layout")

    plan_layout = plan_handler.get_layout(scaled=False, classified=True)
    spy_kwargs = {
        k: v
        for k, v in mapper_spy.call_args.kwargs.items()
        if k not in ("default_element_heights", "planner_elements")
    }
    assert spy_kwargs == {
        "post_processed": False,
        "scaled": True,
        "set_area_types_by_features": True,
        "set_area_types_from_react_areas": False,
    }
    assert plan_layout.scale_factor == 1.0


def test_get_layout_react_unscaled_symmetric_geometries_to_get_raw_layout_react_unscaled(
    plan,
    react_planner_background_image_full_plan,
    make_react_annotation_fully_pipelined,
):
    make_react_annotation_fully_pipelined(react_planner_background_image_full_plan)
    plan_handler = PlanLayoutHandler(plan_id=plan["id"])
    scaled_unscaled_plan_layout = plan_handler.get_layout(scaled=False)
    assert (
        pytest.approx(1739670.999, abs=1e-3)
        == scaled_unscaled_plan_layout.footprint.area
    )


def test_get_raw_layout_classification_based_on_features(
    site, plan, annotations_finished
):
    expected = {
        AreaType.SHAFT: 2,
        AreaType.NOT_DEFINED: 12,
        AreaType.BATHROOM: 1,
        AreaType.STAIRCASE: 1,
    }
    layout = PlanLayoutHandler(plan_id=plan["id"])._get_raw_layout_from_react_data()
    assert Counter([area.type for area in layout.areas]) == expected
