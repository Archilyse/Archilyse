import json
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from deepdiff import DeepDiff

from brooks.models import SimLayout
from brooks.types import SeparatorType
from handlers import PlanLayoutHandler
from handlers.db import FloorDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import (
    ReactPlannerData,
    ReactPlannerSchema,
    ReactPlannerType,
)
from handlers.ifc import IfcToSiteHandler
from handlers.ifc.exporter.ifc_export_handler import IfcExportHandler
from handlers.ifc.importer.ifc_storey_handler import IfcStoreyHandler
from ifc_reader.constants import IFC_DOOR, IFC_SPACE, IFC_WINDOW
from ifc_reader.reader import IfcReader


@pytest.fixture
def expected_ifc_entities(fixtures_path):
    with fixtures_path.joinpath("ifc/export_plan_5797.json").open() as f:
        return json.load(f)


def test_ifc_export_plan_5797(
    floor,
    plan,
    expected_ifc_entities,
    gereferenced_annotation_for_plan_5797,
    populate_plan_areas_db,
    mocker,
    site,
):
    from handlers.ifc.exporter.mappers.entities import EntityIfcMapper

    add_separator_spy = mocker.spy(EntityIfcMapper, "add_wall_railing_slab_furniture")

    FloorDBHandler.add(
        plan_id=plan["id"], building_id=plan["building_id"], floor_number=0
    )
    populate_plan_areas_db(fixture_plan_id=5797, populate=True, db_plan_id=plan["id"])

    origin_layout = PlanLayoutHandler(plan_id=plan["id"]).get_layout(
        scaled=True, georeferenced=True, classified=True
    )

    handler = IfcExportHandler(site_id=plan["site_id"])
    origin_centroid = handler._site_centroid

    with NamedTemporaryFile() as f:
        output_file_name = f.name
        handler.export_site(output_filename=output_file_name)

        ifc_reader = IfcReader(filepath=Path(output_file_name))
        site_ifc_handler = IfcToSiteHandler(ifc_reader=ifc_reader)
        entities = site_ifc_handler._create_site_entities(
            site_id=plan["site_id"], ifc_filename=output_file_name
        )
        imported_layout_centroid = handler._site_centroid
        assert imported_layout_centroid.x == pytest.approx(
            expected=origin_centroid.x, abs=0.5
        )
        assert imported_layout_centroid.y == pytest.approx(
            expected=origin_centroid.y, abs=0.1
        )

        for floor_number in range(2):
            assert entities[0]["plans"][floor_number].pop("plan_content") is not None
            assert entities[0]["plans"][floor_number].pop("site_id") == plan["site_id"]
        assert entities[0]["building"].pop("client_building_id") == output_file_name
        assert entities[0]["building"].pop("housenumber") is not None
        assert [
            ifc_reader.reference_point.x,
            ifc_reader.reference_point.y,
        ] == pytest.approx(
            expected=[9.22661236888889, 46.906436570277776], abs=10**-5
        )

        annotations_react_planner = entities[0]["annotations_react_planner"][0]
        planner_data: ReactPlannerData = ReactPlannerSchema().load(
            annotations_react_planner
        )
        hole_types_counter = Counter(
            [hole.type for hole in planner_data.holes_by_id.values()]
        )
        assert hole_types_counter == {
            ReactPlannerType.DOOR.value: 18,
            ReactPlannerType.WINDOW.value: 12,
        }

        separators_types_counter = Counter(
            [separator.type for separator in planner_data.lines_by_id.values()]
        )
        assert separators_types_counter == {
            ReactPlannerType.WALL.value: 72,
            ReactPlannerType.RAILING.value: 3,
        }

        expected_separator_areas = {
            SeparatorType.WALL: 326377.94,
            SeparatorType.RAILING: 10858.89,
        }

        for separator_type, expected_area in expected_separator_areas.items():
            assert sum(
                [
                    polygon.area
                    for polygon in planner_data.separator_polygons_by_id(
                        separator_type=separator_type
                    ).values()
                ]
            ) == pytest.approx(expected=expected_area, abs=0.01)

        expected_opening_area = {
            ReactPlannerType.WINDOW.value: 41123.10,
            ReactPlannerType.DOOR.value: 27451.95,
        }
        area_by_opening_type = Counter()
        for hole in planner_data.holes_by_id.values():
            area_by_opening_type[
                hole.type
            ] += ReactPlannerToBrooksMapper.get_element_polygon(element=hole).area
        assert area_by_opening_type == pytest.approx(
            expected=expected_opening_area, abs=0.01
        )

        assert_slabs_created_correctly(add_separator_spy=add_separator_spy)
        assert_ifc_space_sizes(ifc_reader=ifc_reader, origin_layout=origin_layout)
        assert_element_properties_and_quantities(
            storey_handler=site_ifc_handler.storey_handler,
            storey_ids=list(ifc_reader.storeys_by_building.values())[0],
        )


def assert_element_properties_and_quantities(
    storey_handler: IfcStoreyHandler, storey_ids
):
    expected_quantities = {
        "IfcSpace": {
            "Qto_SpaceBaseQuantities_Height",
            "Qto_SpaceBaseQuantities_GrossPerimeter",
            "Qto_SpaceBaseQuantities_NetFloorArea",
            "Qto_SpaceBaseQuantities_GrossWallArea",
            "Qto_SpaceBaseQuantities_NetVolume",
        },
        "IfcWindow": {
            "Qto_WindowBaseQuantities_Width",
            "Qto_WindowBaseQuantities_Height",
            "Qto_WindowBaseQuantities_Perimeter",
            "Qto_WindowBaseQuantities_Area",
        },
        "IfcDoor": {
            "Qto_DoorBaseQuantities_Width",
            "Qto_DoorBaseQuantities_Height",
            "Qto_DoorBaseQuantities_Perimeter",
            "Qto_DoorBaseQuantities_Area",
        },
    }
    expected_properties = {
        IFC_SPACE: {
            "Pset_SpaceCommon_PubliclyAccessible",
            "Pset_SpaceCommon_Reference",
            "name",
        },
        IFC_WINDOW: {"name"},
        IFC_DOOR: {"name"},
    }
    for ifc_product_type in {IFC_SPACE, IFC_WINDOW, IFC_DOOR}:
        for storey_id in storey_ids:
            for ifc_product in storey_handler.get_storey_entities_by_ifc_type(
                storey_id
            )[ifc_product_type]:
                assert (
                    set(ifc_product.properties.keys())
                    == expected_properties[ifc_product_type]
                ), ifc_product_type
                assert (
                    set(ifc_product.quantities.keys())
                    == expected_quantities[ifc_product_type]
                ), ifc_product_type


def assert_ifc_space_sizes(ifc_reader, origin_layout: SimLayout):
    ifc_space_size_by_name = {}
    for (
        floor_spaces
    ) in ifc_reader.get_space_geometry_and_properties_by_storey_id.values():
        for floor_space in floor_spaces:
            ifc_space_size_by_name[floor_space.area_type] = floor_space.geometry.area

    ifc_floor_0_area_size_by_type = defaultdict(list)
    ifc_floor_1_area_size_by_type = defaultdict(list)
    for space_name, space_size in ifc_space_size_by_name.items():
        if "0." in space_name:
            ifc_floor_0_area_size_by_type[space_name.split("-")[0].upper()].append(
                space_size
            )
        elif "1." in space_name:
            ifc_floor_1_area_size_by_type[space_name.split("-")[0].upper()].append(
                space_size
            )

    layout_area_size_by_type = defaultdict(list)
    for area in sorted(origin_layout.areas, key=lambda x: x.footprint.area):
        layout_area_size_by_type[area.type.name].append(area.footprint.area)

    assert not DeepDiff(
        ifc_floor_0_area_size_by_type,
        layout_area_size_by_type,
        ignore_order=True,
        significant_digits=3,
    )
    assert not DeepDiff(
        ifc_floor_1_area_size_by_type,
        layout_area_size_by_type,
        ignore_order=True,
        significant_digits=3,
    )


def assert_slabs_created_correctly(add_separator_spy):
    slab_calls = [
        call
        for call in add_separator_spy.call_args_list
        if "PredefinedType" in call.kwargs
        and call.kwargs["PredefinedType"]
        in [type for type in {"FLOOR", "ROOF", "BASESLAB"}]
    ]

    assert (
        len(slab_calls) == 6
    )  # we got 2 calls for each floor as the footprint is a multipolygon
    assert slab_calls[0].kwargs["PredefinedType"] == "BASESLAB"
    assert slab_calls[1].kwargs["PredefinedType"] == "BASESLAB"
    assert slab_calls[2].kwargs["PredefinedType"] == "FLOOR"
    assert slab_calls[3].kwargs["PredefinedType"] == "FLOOR"
    assert slab_calls[4].kwargs["PredefinedType"] == "ROOF"
    assert slab_calls[5].kwargs["PredefinedType"] == "ROOF"
