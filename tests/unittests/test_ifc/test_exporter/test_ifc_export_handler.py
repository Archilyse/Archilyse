"""
These tests aim to fully assert that the data coming from the database / layouts is correctly
forwarded to the EntityIfcMapper.

First we test that the export_site method calls the correct methods, then each method (add_buildings, ...)
is tested individually while we mock & assert the EntityIfcMapper calls.
"""

import random
from collections import Counter, defaultdict
from functools import lru_cache, partial
from itertools import groupby
from tempfile import NamedTemporaryFile
from unittest.mock import MagicMock, Mock, PropertyMock

import numpy as np
import pytest
from shapely.geometry import Point

from brooks.classifications import UnifiedClassificationScheme
from brooks.types import (
    AllAreaTypes,
    AreaType,
    FeatureType,
    OpeningType,
    SeparatorType,
    get_valid_area_type_from_string,
)
from common_utils.constants import REGION
from handlers.ifc.constants import SURFACE_MODEL_MATRICES, SURFACE_MODELS
from handlers.ifc.exporter.mappers import EntityIfcMapper
from tests.constants import FLAKY_RERUNS


@pytest.mark.flaky(reruns=FLAKY_RERUNS)
def test_site_ifc_handler_export_site(mocker):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter import utils

    site_id = 1337
    add_site_mock = mocker.patch.object(
        IfcExportHandler, "add_site", return_value="site_placeholder"
    )
    add_buildings_mock = mocker.patch.object(
        IfcExportHandler, "add_buildings", return_value="buildings_by_id_placeholder"
    )
    add_floors_mock = mocker.patch.object(
        IfcExportHandler, "add_floors", return_value="floors_by_id_placeholder"
    )
    add_units_mock = mocker.patch.object(
        IfcExportHandler, "add_units", return_value="units_by_id_placeholder"
    )
    add_areas_mock = mocker.patch.object(
        IfcExportHandler, "add_areas", return_value="areas_by_id_and_floor_id"
    )
    add_elements_mock = mocker.patch.object(IfcExportHandler, "add_elements")
    add_slabs_mock = mocker.patch.object(IfcExportHandler, "add_slabs")

    with NamedTemporaryFile() as temp_file:
        mocker.patch.object(
            utils, "create_ifc_guid", return_value="01TXnR2zSHxAYLfCFmc6J6"
        )
        IfcExportHandler(site_id=site_id).export_site(temp_file.name)

        add_site_mock.assert_called_once()
        add_buildings_mock.assert_called_once_with(ifc_site=add_site_mock.return_value)
        add_floors_mock.assert_called_once_with(
            ifc_buildings_by_id=add_buildings_mock.return_value
        )
        add_units_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value
        )
        add_areas_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value,
            ifc_units_by_id=add_units_mock.return_value,
        )
        add_elements_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value,
            ifc_areas_by_id_and_floor_id=add_areas_mock.return_value,
        )
        add_slabs_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value
        )

        temp_file.seek(0)
        assert (
            temp_file.read().strip()
            == str.encode(utils.default_ifc_template(f"Site {site_id}")).strip()
        )


@pytest.fixture
def mocked_site_info(mocker):
    from handlers.ifc import IfcExportHandler

    site_info = {
        "client_site_id": "site:client_site_id",
        "name": "site:name",
        "georef_region": REGION.CH.name,
    }

    mock = mocker.patch.object(IfcExportHandler, "site_info", return_value=site_info)
    mock.__getitem__.side_effect = site_info.__getitem__
    return site_info


@pytest.fixture
def mocked_building_infos(mocker):
    from handlers.ifc import IfcExportHandler

    building_infos = [
        {
            "id": building_id,
            "street": "floor:street",
            "housenumber": f"floor: {housenumber}",
        }
        for building_id, housenumber in zip(range(2), range(1337, 1339))
    ]
    mocker.patch.object(
        IfcExportHandler,
        "building_infos",
        mocker.PropertyMock(return_value=building_infos),
    )

    return building_infos


@pytest.fixture
def mocked_floor_infos(mocker):
    from handlers.ifc import IfcExportHandler

    floor_infos = [
        {
            "id": floor_id,
            "building_id": building_id,
            "floor_number": floor_number,
            "plan_id": plan_id,
        }
        for floor_id, (building_id, floor_number, plan_id) in enumerate(
            zip(
                (1, 1, 1, 2, 2),  # building_id
                (-1, 0, 1, 4, 5),  # floor number
                (1, 1, 2, 3, 3),  # plan_id
            )
        )
    ]

    mocker.patch.object(
        IfcExportHandler, "floor_infos", mocker.PropertyMock(return_value=floor_infos)
    )

    return floor_infos


@pytest.fixture
def mocked_unit_infos(mocker, mocked_floor_infos):
    from handlers.ifc import IfcExportHandler

    unit_infos = [
        {
            "id": floor["id"] * len(mocked_floor_infos) + unit_id,
            "floor_id": floor["id"],
            "client_id": f"cient_id_{unit_id}",
        }
        for floor in mocked_floor_infos
        for unit_id in range(3)
    ]

    mocker.patch.object(
        IfcExportHandler, "unit_infos", mocker.PropertyMock(return_value=unit_infos)
    )
    return unit_infos


@pytest.fixture
def make_mocked_area_and_unit_area_infos(mocker, mocked_floor_infos, mocked_unit_infos):
    from handlers.ifc import IfcExportHandler

    def _make_mocked_area_infos(
        mocked_floor_infos,
        n_areas_per_plan=15,
        n_areas_per_unit=3,
    ):
        area_type_candidates = list(UnifiedClassificationScheme().leaf_area_types)
        area_infos = [
            {
                "id": plan_id * n_areas_per_plan + area_index,
                "plan_id": plan_id,
                "area_type": area_type.value,
            }
            for plan_id in sorted(
                set([floor_info["plan_id"] for floor_info in mocked_floor_infos])
            )
            for area_index, area_type in enumerate(
                random.choices(area_type_candidates, k=n_areas_per_plan)
            )
        ]

        unit_area_infos = []
        for plan_id, floor_infos in groupby(
            mocked_floor_infos, key=lambda z: z["plan_id"]
        ):
            for floor_info in floor_infos:
                areas_in_plan = [
                    area_info
                    for area_info in area_infos
                    if area_info["plan_id"] == plan_id
                ]
                units_in_floor = [
                    unit_info
                    for unit_info in mocked_unit_infos
                    if unit_info["floor_id"] == floor_info["id"]
                ]
                for unit_info in units_in_floor:
                    for _ in range(n_areas_per_unit):
                        unit_area_infos.append(
                            {
                                "unit_id": unit_info["id"],
                                "area_id": areas_in_plan.pop()["id"],
                            }
                        )

        mocker.patch.object(
            IfcExportHandler, "area_infos", mocker.PropertyMock(return_value=area_infos)
        )
        mocker.patch.object(
            IfcExportHandler,
            "unit_area_infos",
            mocker.PropertyMock(return_value=unit_area_infos),
        )

        return area_infos, unit_area_infos

    return partial(_make_mocked_area_infos, mocked_floor_infos=mocked_floor_infos)


@pytest.fixture
def mocked_site_centroid_long_lat(mocker):
    from handlers.ifc import IfcExportHandler

    return mocker.patch.object(
        IfcExportHandler, "site_centroid_long_lat", spec=Point, x=47.3769, y=8.5417
    )


def test_ifc_export_handler_add_site(
    mocker, mocked_site_info, mocked_site_centroid_long_lat
):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    ifc_mapper_mock_add_site = mocker.patch.object(EntityIfcMapper, "add_site")
    IfcExportHandler(site_id=1337).add_site()
    assert (
        ifc_mapper_mock_add_site.call_args.kwargs["client_site_id"]
        == mocked_site_info["client_site_id"]
    )
    assert (
        ifc_mapper_mock_add_site.call_args.kwargs["site_name"]
        == mocked_site_info["name"]
    )
    assert ifc_mapper_mock_add_site.call_args.kwargs["latitude"] == (8, 32, 30, 120000)
    assert ifc_mapper_mock_add_site.call_args.kwargs["longitude"] == (
        47,
        22,
        36,
        839999,
    )


def test_ifc_export_handler_add_buildings(mocker, mocked_building_infos):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    ifc_mapper_mock_add_building_mock = mocker.patch.object(
        EntityIfcMapper, "add_building", return_value="building_placeholder"
    )
    ifc_mapper_add_building_to_site_mock = mocker.patch.object(
        EntityIfcMapper, "add_buildings_to_site"
    )

    IfcExportHandler(site_id=1337).add_buildings(ifc_site="ifc_site_placeholder")
    assert ifc_mapper_mock_add_building_mock.call_count == len(mocked_building_infos)
    assert ifc_mapper_add_building_to_site_mock.call_count == 1
    assert (
        ifc_mapper_add_building_to_site_mock.call_args.kwargs["site"]
        == "ifc_site_placeholder"
    )
    assert ifc_mapper_add_building_to_site_mock.call_args.kwargs["buildings"] == [
        "building_placeholder"
    ] * len(mocked_building_infos)
    for call, building_info in zip(
        ifc_mapper_mock_add_building_mock.call_args_list, mocked_building_infos
    ):
        assert call.kwargs["ifc_site"] == "ifc_site_placeholder"
        assert call.kwargs["street"] == building_info["street"]
        assert call.kwargs["housenumber"] == building_info["housenumber"]


def test_ifc_export_handler_add_floors(mocker, mocked_floor_infos):
    from handlers import FloorHandler
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    mocker.patch.object(
        FloorHandler, "get_level_baseline", side_effect=[-1, 0, 1, 2, 3]
    )

    ifc_mapper_add_floor_mock = mocker.patch.object(
        EntityIfcMapper, "add_floor", return_value="floor_placeholder"
    )
    ifc_mapper_add_floors_to_building_mock = mocker.patch.object(
        EntityIfcMapper, "add_floors_to_building"
    )
    buildings_by_id = {
        building_id: building_id
        for building_id in set([floor["building_id"] for floor in mocked_floor_infos])
    }
    IfcExportHandler(site_id=1337).add_floors(ifc_buildings_by_id=buildings_by_id)
    assert ifc_mapper_add_floor_mock.call_count == len(mocked_floor_infos)
    assert ifc_mapper_add_floors_to_building_mock.call_count == len(
        buildings_by_id.keys()
    )
    assert Counter([floor["building_id"] for floor in mocked_floor_infos]) == Counter(
        [
            call.kwargs["ifc_building"]
            for call in ifc_mapper_add_floor_mock.call_args_list
        ]
    )
    assert Counter([floor["floor_number"] for floor in mocked_floor_infos]) == Counter(
        [
            call.kwargs["floor_number"]
            for call in ifc_mapper_add_floor_mock.call_args_list
        ]
    )
    assert [
        call.kwargs["elevation"] for call in ifc_mapper_add_floor_mock.call_args_list
    ] == pytest.approx([-1, 0, 1, 2, 3])


def test_ifc_export_handler_add_units(mocker, mocked_floor_infos, mocked_unit_infos):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    ifc_mapper_mock_add_unit_mock = mocker.patch.object(
        EntityIfcMapper, "add_unit", return_value="unit_placeholder"
    )
    ifc_mapper_add_units_to_floor_mock = mocker.patch.object(
        EntityIfcMapper, "add_units_to_floor"
    )

    IfcExportHandler(site_id=1337).add_units(
        ifc_floors_by_id={
            floor_info["id"]: f"floor_placeholder_{floor_info['id']}"
            for floor_info in mocked_floor_infos
        }
    )

    assert [
        call.kwargs["client_id"]
        for call in ifc_mapper_mock_add_unit_mock.call_args_list
    ] == [unit_info["client_id"] for unit_info in mocked_unit_infos]
    assert (
        ifc_mapper_add_units_to_floor_mock.call_args.kwargs["units"]
        == ["unit_placeholder"] * 3
    )
    assert [
        call.kwargs["floor"]
        for call in ifc_mapper_add_units_to_floor_mock.call_args_list
    ] == [
        "floor_placeholder_0",
        "floor_placeholder_1",
        "floor_placeholder_2",
        "floor_placeholder_3",
        "floor_placeholder_4",
    ]


def test_ifc_export_no_units(mocker, mocked_site_info, mocked_floor_infos):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter import utils

    add_site_mock = mocker.patch.object(
        IfcExportHandler, "add_site", return_value="site_placeholder"
    )
    add_buildings_mock = mocker.patch.object(
        IfcExportHandler, "add_buildings", return_value="buildings_by_id_placeholder"
    )
    add_floors_mock = mocker.patch.object(
        IfcExportHandler, "add_floors", return_value="floors_by_id_placeholder"
    )
    add_units_mock = mocker.spy(IfcExportHandler, "add_units")
    add_areas_mock = mocker.patch.object(
        IfcExportHandler, "add_areas", return_value="areas_by_id_and_floor_id"
    )
    add_elements_mock = mocker.patch.object(IfcExportHandler, "add_elements")
    add_slabs_mock = mocker.patch.object(IfcExportHandler, "add_slabs")
    unit_info_mock = mocker.patch.object(
        IfcExportHandler, "unit_infos", mocker.PropertyMock(return_value=[])
    )
    entity_mapper_add_unit_spy = mocker.spy(EntityIfcMapper, "add_unit")
    entity_mapper_add_units_to_floor_spy = mocker.spy(
        EntityIfcMapper, "add_units_to_floor"
    )

    with NamedTemporaryFile() as temp_file:
        mocker.patch.object(
            utils, "create_ifc_guid", return_value="01TXnR2zSHxAYLfCFmc6J6"
        )
        IfcExportHandler(site_id=1).export_site(output_filename=temp_file.name)

        add_site_mock.assert_called_once()
        add_buildings_mock.assert_called_once_with(ifc_site=add_site_mock.return_value)
        add_floors_mock.assert_called_once_with(
            ifc_buildings_by_id=add_buildings_mock.return_value
        )
        add_units_mock.assert_called_once_with(
            mocker.ANY, ifc_floors_by_id=add_floors_mock.return_value
        )
        add_areas_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value,
            ifc_units_by_id=add_units_mock.spy_return,
        )
        add_elements_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value,
            ifc_areas_by_id_and_floor_id=add_areas_mock.return_value,
        )
        add_slabs_mock.assert_called_once_with(
            ifc_floors_by_id=add_floors_mock.return_value
        )
        unit_info_mock.assert_has_calls([mocker.call(), mocker.call()])
        entity_mapper_add_unit_spy.assert_not_called()
        entity_mapper_add_units_to_floor_spy.assert_not_called()


def _mock_layout_areas(
    IfcExportHandler,
    mocker,
    mocked_floor_infos,
    mocked_area_infos,
):
    @lru_cache(maxsize=None)
    def _fake_layout(plan_id, default_element_heights=None):
        def _fake_areas():
            for area_info in mocked_area_infos:
                if area_info["plan_id"] == plan_id:
                    area_mock = mocker.MagicMock()
                    area_mock.footprint = mocker.PropertyMock(
                        return_value=f"footprint_{area_info['id']}"
                    )
                    area_mock.footprint.area = area_info["id"]
                    area_mock.type = get_valid_area_type_from_string(
                        AllAreaTypes(area_info["area_type"]).name
                    )
                    area_mock.db_area_id = area_info["id"]
                    yield area_mock

        mock_layout = mocker.MagicMock()
        mock_layout.default_element_heights = default_element_heights
        mock_layout.areas = set(_fake_areas())
        mock_layout.areas_by_type = defaultdict(
            set,
            [
                (x[0], list(x[1]))
                for x in groupby(mock_layout.areas, key=lambda z: z.type)
            ],
        )
        return mock_layout

    mocker.patch.object(
        IfcExportHandler,
        "floor_layouts_relative_by_floor_id",
        mocker.PropertyMock(
            return_value={
                floor_info["id"]: _fake_layout(plan_id=floor_info["plan_id"])
                for floor_info in mocked_floor_infos
            }
        ),
    )


def test_ifc_export_handler_add_areas(
    mocker,
    mocked_floor_infos,
    mocked_unit_infos,
    make_mocked_area_and_unit_area_infos,
):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    random.seed(42)

    ifc_mapper_add_areas_to_floor_mock = mocker.patch.object(
        EntityIfcMapper, "add_areas_to_floor"
    )
    ifc_mapper_add_areas_to_unit_mock = mocker.patch.object(
        EntityIfcMapper, "add_areas_to_unit"
    )

    mocked_area_infos, mocked_unit_area_infos = make_mocked_area_and_unit_area_infos()
    _mock_layout_areas(
        IfcExportHandler,
        mocker,
        mocked_floor_infos,
        mocked_area_infos,
    )

    ifc_mapper_add_area_mock = mocker.patch.object(
        EntityIfcMapper,
        "add_area",
        side_effect=lambda *args, **kwargs: f"area_placeholder_{kwargs['polygon'].area}",
    )

    export_handler = IfcExportHandler(site_id=1337)
    export_handler.add_areas(
        ifc_floors_by_id={
            floor_info["id"]: f"floor_placeholder_{floor_info['id']}"
            for floor_info in mocked_floor_infos
        },
        ifc_units_by_id={
            unit_info["id"]: f"unit_placeholder_{unit_info['id']}"
            for unit_info in mocked_unit_infos
        },
    )

    area_infos_by_area_db_id = {
        area_info["id"]: area_info for area_info in mocked_area_infos
    }
    for unit_area_info in mocked_unit_area_infos:
        area_info = area_infos_by_area_db_id[unit_area_info["area_id"]]

    # assert floor, footprint, area_type, floor_number and is_public,
    expected_areas_added = set()
    for area_info in mocked_area_infos:
        for floor_info in [
            floor_info
            for floor_info in mocked_floor_infos
            if floor_info["plan_id"] == area_info["plan_id"]
        ]:
            is_public = (
                len(
                    [
                        a
                        for a in mocked_unit_area_infos
                        if a["area_id"] == area_info["id"]
                    ]
                )
                == 0
            )
            expected_areas_added.add(
                (
                    f"floor_placeholder_{floor_info['id']}",
                    f"footprint_{area_info['id']}",
                    AllAreaTypes(area_info["area_type"]).name,
                    floor_info["floor_number"],
                    is_public,
                    export_handler.area_building_code_type_by_id.get(area_info["id"]),
                )
            )

    areas_added = {
        (
            call.kwargs["ifc_floor"],
            call.kwargs["polygon"].return_value,
            call.kwargs["area_type"],
            call.kwargs["floor_number"],
            call.kwargs["is_public"],
            call.kwargs["building_code_type"],
        )
        for call in ifc_mapper_add_area_mock.call_args_list
    }
    assert areas_added == expected_areas_added

    # assert area_number_in_floor and constants
    for _, calls in groupby(
        ifc_mapper_add_area_mock.call_args_list, key=lambda c: c.kwargs["floor_number"]
    ):
        area_numbers_in_floor, footprint_areas = zip(
            *[
                (call.kwargs["area_number_in_floor"], call.kwargs["polygon"].area)
                for call in calls
            ]
        )
        assert [
            a[0]
            for a in sorted(
                zip(area_numbers_in_floor, footprint_areas), key=lambda z: z[1]
            )
        ] == list(range(len(area_numbers_in_floor)))

    # assert constants
    for call in ifc_mapper_add_area_mock.call_args_list:
        assert call.kwargs["height"] == 2.6
        assert call.kwargs["start_elevation_relative_to_floor"] == 0

    # assert unit assignemnts
    expected_unit_assignments = {
        (unit_area_info["area_id"], unit_area_info["unit_id"])
        for unit_area_info in mocked_unit_area_infos
    }
    actual_unit_assignments = set()
    for call in ifc_mapper_add_areas_to_unit_mock.call_args_list:
        unit_id = int(call.kwargs["unit"].split("unit_placeholder_")[1])
        for area in call.kwargs["areas"]:
            area_id = int(area.split("area_placeholder_")[1])
            actual_unit_assignments.add((area_id, unit_id))
    assert actual_unit_assignments == expected_unit_assignments

    # assert floor assignments
    expected_floor_assignments = set()
    for plan_id, area_infos in groupby(mocked_area_infos, key=lambda z: z["plan_id"]):
        for area_info in area_infos:
            floor_infos = [
                floor_info
                for floor_info in mocked_floor_infos
                if floor_info["plan_id"] == plan_id
            ]
            for floor_info in floor_infos:
                expected_floor_assignments.add((floor_info["id"], area_info["id"]))
    actual_floor_assignments = set()
    for call in ifc_mapper_add_areas_to_floor_mock.call_args_list:
        floor_id = int(call.kwargs["floor"].split("floor_placeholder_")[1])
        for area in call.kwargs["spaces"]:
            area_id = int(area.split("area_placeholder_")[1])
            actual_floor_assignments.add((floor_id, area_id))
    assert actual_floor_assignments == expected_floor_assignments


def test_ifc_export_handler_add_elements_wall_railing(mocker, custom_element_heights):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    def _fake_layout(floor_id: int):
        def _make_fake_element(element_type, name, height):
            fake_element = mocker.MagicMock()
            fake_element.footprint = f"fake_element_footprint_{name}_{floor_id}"
            fake_element.type = element_type
            fake_element.height = height

            return fake_element

        wall = _make_fake_element(
            SeparatorType.WALL,
            "wall",
            custom_element_heights[SeparatorType.WALL],
        )
        railing = _make_fake_element(
            SeparatorType.RAILING,
            "railing",
            custom_element_heights[SeparatorType.RAILING],
        )
        column = _make_fake_element(
            SeparatorType.COLUMN,
            "column",
            custom_element_heights[SeparatorType.COLUMN],
        )
        door = _make_fake_element(
            OpeningType.DOOR,
            "door",
            custom_element_heights[OpeningType.DOOR],
        )
        window = _make_fake_element(
            OpeningType.WINDOW,
            "window",
            custom_element_heights[OpeningType.WINDOW],
        )

        fake_layout = mocker.MagicMock()
        fake_layout.seperators = [wall, railing, column]
        fake_layout.non_overlapping_separators = [wall, railing, column]
        wall.openings = [door, window]
        fake_layout.areas = set()

        return fake_layout

    ifc_mapper_add_add_wall_railing_slab_furniture_mock = mocker.patch.object(
        EntityIfcMapper,
        "add_wall_railing_slab_furniture",
        return_value="separator_placeholder",
    )
    ifc_mapper_add_door_window = mocker.patch.object(
        EntityIfcMapper,
        "add_door_window",
        return_value=("opening_placeholder", "hole_placeholder"),
    )
    ifc_mapper_add_elements_to_floor_mock = mocker.patch.object(
        EntityIfcMapper, "add_elements_to_floor"
    )
    mocker.patch.object(
        IfcExportHandler,
        "floor_layouts_relative_by_floor_id",
        mocker.PropertyMock(
            return_value={0: _fake_layout(floor_id=0), 1: _fake_layout(floor_id=1)}
        ),
    )

    IfcExportHandler(site_id=1337).add_elements(
        ifc_floors_by_id={0: "floor_placeholder_0", 1: "floor_placeholder_1"},
        ifc_areas_by_id_and_floor_id={},
    )

    assert [
        [call.kwargs["floor"], set(call.kwargs["elements"])]
        for call in ifc_mapper_add_elements_to_floor_mock.call_args_list
    ] == [
        ["floor_placeholder_0", {"separator_placeholder", "opening_placeholder"}],
        ["floor_placeholder_1", {"separator_placeholder", "opening_placeholder"}],
    ]

    actual_added_separators = {
        (
            call.kwargs["polygon"],
            call.kwargs["start_elevation_relative_to_floor"],
            call.kwargs["height"],
            call.kwargs["element_type"].__name__,
            call.kwargs["Name"],
        )
        for call in ifc_mapper_add_add_wall_railing_slab_furniture_mock.call_args_list
    }
    assert actual_added_separators == {
        (
            "fake_element_footprint_wall_0",
            custom_element_heights[SeparatorType.WALL][0],
            custom_element_heights[SeparatorType.WALL][1]
            - custom_element_heights[SeparatorType.WALL][0],
            "IfcWallStandardCase",
            "Wall",
        ),
        (
            "fake_element_footprint_wall_1",
            custom_element_heights[SeparatorType.WALL][0],
            custom_element_heights[SeparatorType.WALL][1]
            - custom_element_heights[SeparatorType.WALL][0],
            "IfcWallStandardCase",
            "Wall",
        ),
        (
            "fake_element_footprint_railing_0",
            custom_element_heights[SeparatorType.RAILING][0],
            custom_element_heights[SeparatorType.RAILING][1]
            - custom_element_heights[SeparatorType.RAILING][0],
            "IfcRailing",
            "Railing",
        ),
        (
            "fake_element_footprint_railing_1",
            custom_element_heights[SeparatorType.RAILING][0],
            custom_element_heights[SeparatorType.RAILING][1]
            - custom_element_heights[SeparatorType.RAILING][0],
            "IfcRailing",
            "Railing",
        ),
        (
            "fake_element_footprint_column_0",
            custom_element_heights[SeparatorType.COLUMN][0],
            custom_element_heights[SeparatorType.COLUMN][1]
            - custom_element_heights[SeparatorType.COLUMN][0],
            "IfcColumn",
            "Column",
        ),
        (
            "fake_element_footprint_column_1",
            custom_element_heights[SeparatorType.COLUMN][0],
            custom_element_heights[SeparatorType.COLUMN][1]
            - custom_element_heights[SeparatorType.COLUMN][0],
            "IfcColumn",
            "Column",
        ),
    }

    assert {
        (
            call.kwargs["polygon"],
            call.kwargs["start_elevation_relative_to_floor"],
            call.kwargs["height"],
            call.kwargs["element_type"].__name__,
            call.kwargs["ifc_wall"],
            call.kwargs["Name"],
        )
        for call in ifc_mapper_add_door_window.call_args_list
    } == {
        (
            "fake_element_footprint_window_1",
            custom_element_heights[OpeningType.WINDOW][0],
            custom_element_heights[OpeningType.WINDOW][1]
            - custom_element_heights[OpeningType.WINDOW][0],
            "IfcWindow",
            "separator_placeholder",
            "Window",
        ),
        (
            "fake_element_footprint_window_0",
            custom_element_heights[OpeningType.WINDOW][0],
            custom_element_heights[OpeningType.WINDOW][1]
            - custom_element_heights[OpeningType.WINDOW][0],
            "IfcWindow",
            "separator_placeholder",
            "Window",
        ),
        (
            "fake_element_footprint_door_0",
            custom_element_heights[OpeningType.DOOR][0],
            custom_element_heights[OpeningType.DOOR][1]
            - custom_element_heights[OpeningType.DOOR][0],
            "IfcDoor",
            "separator_placeholder",
            "Door",
        ),
        (
            "fake_element_footprint_door_1",
            custom_element_heights[OpeningType.DOOR][0],
            custom_element_heights[OpeningType.DOOR][1]
            - custom_element_heights[OpeningType.DOOR][0],
            "IfcDoor",
            "separator_placeholder",
            "Door",
        ),
    }


def test_ifc_export_handler_add_elements_features(mocker, custom_element_heights):
    from handlers.ifc import IfcExportHandler
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    def _fake_layout(floor_id: int):
        def _make_fake_element(element_type, name, height):
            fake_element = mocker.MagicMock()
            fake_element.footprint = f"fake_element_footprint_{name}_{floor_id}"
            fake_element.type = element_type
            fake_element.axes_scales_translation = mocker.PropertyMock(
                return_value=("a", "s", "t")
            )
            fake_element.height = height

            return fake_element

        areas = [
            _make_fake_element(
                AreaType.NOT_DEFINED,
                f"area_{i}",
                height=custom_element_heights["GENERIC_SPACE_HEIGHT"],
            )
            for i in range(2)
        ]
        for i, area in enumerate(areas):
            area.features = [
                _make_fake_element(
                    feature_type,
                    feature_type,
                    custom_element_heights.get(feature_type, (0, 1)),
                )
                for feature_type in FeatureType
            ]
            area.db_area_id = i

        fake_layout = mocker.MagicMock()
        fake_layout.areas = areas
        return fake_layout

    ifc_mapper_add_add_wall_railing_slab_furniture_mock = mocker.patch.object(
        EntityIfcMapper,
        "add_wall_railing_slab_furniture",
        return_value="furniture_mock",
    )
    ifc_mapper_add_sanitary_terminal_mock = mocker.patch.object(
        EntityIfcMapper,
        "add_sanitary_terminal",
        return_value="sanitary_element",
    )
    ifc_mapper_add_elements_to_floor_mock = mocker.patch.object(
        EntityIfcMapper, "add_elements_to_floor"
    )
    ifc_mapper_add_elements_to_area_mock = mocker.patch.object(
        EntityIfcMapper, "add_elements_to_area"
    )
    mocker.patch.object(
        IfcExportHandler,
        "floor_layouts_relative_by_floor_id",
        mocker.PropertyMock(
            return_value={0: _fake_layout(floor_id=0), 1: _fake_layout(floor_id=1)}
        ),
    )

    IfcExportHandler(site_id=1337).add_elements(
        ifc_floors_by_id={0: "floor_placeholder_0"},
        ifc_areas_by_id_and_floor_id={
            (0, 0): "area_placeholder_0",
            (0, 1): "area_placeholder_1",
        },
    )

    actual_furniture_calls = {
        (
            call.kwargs["polygon"],
            call.kwargs["start_elevation_relative_to_floor"],
            call.kwargs["height"],
            call.kwargs["element_type"].__name__,
            call.kwargs["Name"],
        )
        for call in ifc_mapper_add_add_wall_railing_slab_furniture_mock.call_args_list
    }

    assert actual_furniture_calls == {
        (
            "fake_element_footprint_FeatureType.STAIRS_0",
            custom_element_heights[FeatureType.STAIRS][0],
            custom_element_heights[FeatureType.STAIRS][1]
            - custom_element_heights[FeatureType.STAIRS][0],
            "IfcStair",
            "Stairs",
        ),
        (
            "fake_element_footprint_FeatureType.BATHTUB_0",
            custom_element_heights[FeatureType.BATHTUB][0],
            custom_element_heights[FeatureType.BATHTUB][1]
            - custom_element_heights[FeatureType.BATHTUB][0],
            "IfcSanitaryTerminal",
            "Bathtub",
        ),
        (
            "fake_element_footprint_FeatureType.KITCHEN_0",
            custom_element_heights[FeatureType.KITCHEN][0],
            custom_element_heights[FeatureType.KITCHEN][1]
            - custom_element_heights[FeatureType.KITCHEN][0],
            "IfcFurniture",
            "Kitchen",
        ),
        (
            "fake_element_footprint_FeatureType.SHOWER_0",
            custom_element_heights[FeatureType.SHOWER][0],
            custom_element_heights[FeatureType.SHOWER][1]
            - custom_element_heights[FeatureType.SHOWER][0],
            "IfcSanitaryTerminal",
            "Shower",
        ),
        (
            "fake_element_footprint_FeatureType.TOILET_0",
            custom_element_heights[FeatureType.TOILET][0],
            custom_element_heights[FeatureType.TOILET][1]
            - custom_element_heights[FeatureType.TOILET][0],
            "IfcSanitaryTerminal",
            "Toilet",
        ),
        (
            "fake_element_footprint_FeatureType.SINK_0",
            custom_element_heights[FeatureType.SINK][0],
            custom_element_heights[FeatureType.SINK][1]
            - custom_element_heights[FeatureType.SINK][0],
            "IfcSanitaryTerminal",
            "Sink",
        ),
    }

    assert [
        [
            call.kwargs["ifc_floor"],
            call.kwargs["axes"],
            call.kwargs["scales"],
            call.kwargs["translation"],
            call.kwargs["ifc_element_type"].__name__,
            call.kwargs["surface_model_path"]
            == SURFACE_MODELS.get(FeatureType[call.kwargs["Name"].upper()]),
            np.array_equal(
                call.kwargs["surface_model_matrix"],
                SURFACE_MODEL_MATRICES.get(FeatureType[call.kwargs["Name"].upper()]),
            ),
            call.kwargs["Name"],
        ]
        for call in ifc_mapper_add_sanitary_terminal_mock.call_args_list
    ] == []

    # no elements are assigned to the floor
    assert [
        [call.kwargs["floor"], set(call.kwargs["elements"])]
        for call in ifc_mapper_add_elements_to_floor_mock.call_args_list
    ] == []

    assert [
        [call.kwargs["area"], set(call.kwargs["elements"])]
        for call in ifc_mapper_add_elements_to_area_mock.call_args_list
    ] == [
        ["area_placeholder_0", {"furniture_mock"}],
        ["area_placeholder_1", {"furniture_mock"}],
    ]


def _fake_layout(floor_id: int, default_element_heights=None):
    fake_layout = MagicMock()
    fake_layout.footprint_ex_areas_without_floor.__repr__ = lambda self: (
        f"footprint_ex_areas_without_floor_{floor_id}"
    )
    fake_layout.footprint_ex_areas_without_ceiling.__repr__ = lambda self: (
        f"footprint_ex_areas_without_ceiling_{floor_id}"
    )
    fake_layout.footprint_ex_areas_without_ceiling.exterior = (
        f"footprint_ex_areas_without_ceiling_{floor_id}_exterior"
    )
    fake_layout.footprint_ex_areas_without_floor.exterior = (
        f"footprint_ex_areas_without_floor_{floor_id}_exterior"
    )
    fake_layout.default_element_heights = default_element_heights

    return fake_layout


def _fake_unary_union(geoms):
    mock = MagicMock(exterior="+".join([geom.exterior for geom in geoms]))
    mock.__repr__ = lambda z: "+".join([repr(geom) for geom in geoms])
    return mock


def _fake_polygon(geometry):
    return f"Polygon({repr(geometry)})"


def _fake_as_multipolygon(geom):
    multipolygon = Mock()
    type(multipolygon).geoms = PropertyMock(return_value=[geom])
    return multipolygon


@pytest.fixture
def mocked_polygon(monkeypatch):
    from handlers.ifc.exporter import ifc_export_handler as ifc_export_handler_module

    return monkeypatch.setattr(ifc_export_handler_module, "Polygon", _fake_polygon)


@pytest.fixture
def mocked_unary_union(monkeypatch):
    from handlers.ifc.exporter import ifc_export_handler as ifc_export_handler_module

    return monkeypatch.setattr(
        ifc_export_handler_module, "unary_union", _fake_unary_union
    )


@pytest.fixture
def mocked_as_multipolygon(monkeypatch):
    from handlers.ifc.exporter import ifc_export_handler as ifc_export_handler_module

    return monkeypatch.setattr(
        ifc_export_handler_module, "as_multipolygon", _fake_as_multipolygon
    )


@pytest.fixture
def mocked_add_wall_railing_slab_furniture(mocker):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    return mocker.patch.object(
        EntityIfcMapper,
        "add_wall_railing_slab_furniture",
        return_value="slab_mock",
    )


@pytest.fixture
def mocked_add_elements_to_floor(mocker):
    from handlers.ifc.exporter.mappers import EntityIfcMapper

    return mocker.patch.object(
        EntityIfcMapper,
        "add_elements_to_floor",
    )


class TestIFCExportAddSlabs:
    @staticmethod
    @pytest.mark.parametrize("use_custom_heights", [True, False])
    def test_ifc_export_handler_add_slabs(
        mocker,
        monkeypatch,
        mocked_floor_infos,
        mocked_polygon,
        mocked_unary_union,
        mocked_as_multipolygon,
        mocked_add_elements_to_floor,
        mocked_add_wall_railing_slab_furniture,
        custom_element_heights,
        use_custom_heights,
    ):
        from handlers import FloorHandler
        from handlers.ifc.exporter import (
            ifc_export_handler as ifc_export_handler_module,
        )

        mocker.patch.object(
            FloorHandler, "get_level_baseline", side_effect=[-1, 0, 1, 2, 3]
        )
        mocker.patch.object(
            ifc_export_handler_module.IfcExportHandler,
            "floor_layouts_relative_by_floor_id",
            mocker.PropertyMock(
                return_value={
                    floor_info["id"]: _fake_layout(
                        floor_info["id"],
                        default_element_heights=custom_element_heights
                        if use_custom_heights
                        else None,
                    )
                    for floor_info in mocked_floor_infos
                }
            ),
        )

        ifc_export_handler_module.IfcExportHandler(site_id=1337).add_slabs(
            ifc_floors_by_id={
                floor_info["id"]: f"floor_placeholder_{floor_info['id']}"
                for floor_info in mocked_floor_infos
            },
        )

        actual_slabs = {
            (
                call.kwargs["ifc_floor"],
                repr(call.kwargs["polygon"]),
                call.kwargs["element_type"].__name__,
                call.kwargs["Name"],
            )
            for call in mocked_add_wall_railing_slab_furniture.call_args_list
        }

        actual_slab_heights = {
            (
                repr(call.kwargs["polygon"]),
                call.kwargs["start_elevation_relative_to_floor"],
                call.kwargs["height"],
            )
            for call in mocked_add_wall_railing_slab_furniture.call_args_list
        }

        assert actual_slabs == {
            (
                "floor_placeholder_0",
                "footprint_ex_areas_without_floor_0",
                "IfcSlabStandardCase",
                "Floor",
            ),
            (
                "floor_placeholder_0",
                "footprint_ex_areas_without_ceiling_0+footprint_ex_areas_without_floor_1",
                "IfcSlabStandardCase",
                "Floor",
            ),
            (
                "floor_placeholder_1",
                "footprint_ex_areas_without_ceiling_1+footprint_ex_areas_without_floor_2",
                "IfcSlabStandardCase",
                "Floor",
            ),
            (
                "floor_placeholder_2",
                "footprint_ex_areas_without_ceiling_2",
                "IfcSlabStandardCase",
                "Roof",
            ),
            (
                "floor_placeholder_3",
                "footprint_ex_areas_without_floor_3",
                "IfcSlabStandardCase",
                "Floor",
            ),
            (
                "floor_placeholder_3",
                "footprint_ex_areas_without_ceiling_3+footprint_ex_areas_without_floor_4",
                "IfcSlabStandardCase",
                "Floor",
            ),
            (
                "floor_placeholder_4",
                "footprint_ex_areas_without_ceiling_4",
                "IfcSlabStandardCase",
                "Roof",
            ),
        }

        if not use_custom_heights:
            assert actual_slab_heights == {
                (
                    "footprint_ex_areas_without_ceiling_3+footprint_ex_areas_without_floor_4",
                    2.6,
                    0.3,
                ),
                ("footprint_ex_areas_without_floor_0", 0, -0.3),
                ("footprint_ex_areas_without_ceiling_4", 2.6, 0.3),
                ("footprint_ex_areas_without_floor_3", 0, -0.3),
                (
                    "footprint_ex_areas_without_ceiling_1+footprint_ex_areas_without_floor_2",
                    2.6,
                    0.3,
                ),
                (
                    "footprint_ex_areas_without_ceiling_0+footprint_ex_areas_without_floor_1",
                    2.6,
                    0.3,
                ),
                ("footprint_ex_areas_without_ceiling_2", 2.6, 0.3),
            }
        else:
            assert actual_slab_heights == {
                (
                    "footprint_ex_areas_without_ceiling_3+footprint_ex_areas_without_floor_4",
                    0,
                    702,
                ),
                ("footprint_ex_areas_without_ceiling_2", 0, 702),
                ("footprint_ex_areas_without_floor_3", 0, -756),
                ("footprint_ex_areas_without_floor_0", 0, -756),
                ("footprint_ex_areas_without_ceiling_4", 0, 702),
                (
                    "footprint_ex_areas_without_ceiling_1+footprint_ex_areas_without_floor_2",
                    0,
                    702,
                ),
                (
                    "footprint_ex_areas_without_ceiling_0+footprint_ex_areas_without_floor_1",
                    0,
                    702,
                ),
            }

        actual_floor_assignments = [
            [call.kwargs["floor"], set(call.kwargs["elements"])]
            for call in mocked_add_elements_to_floor.call_args_list
        ]
        assert actual_floor_assignments == [
            ["floor_placeholder_0", {"slab_mock"}],
            ["floor_placeholder_1", {"slab_mock"}],
            ["floor_placeholder_2", {"slab_mock"}],
            ["floor_placeholder_3", {"slab_mock"}],
            ["floor_placeholder_4", {"slab_mock"}],
        ]

    @staticmethod
    def test_ifc_export_handler_add_slabs_only_one_floor(
        mocker,
        monkeypatch,
        mocked_polygon,
        mocked_unary_union,
        mocked_as_multipolygon,
        mocked_add_elements_to_floor,
        mocked_add_wall_railing_slab_furniture,
    ):
        from handlers.ifc.exporter import (
            ifc_export_handler as ifc_export_handler_module,
        )

        floors_info = [
            {
                "id": 1,
                "building_id": "building_id",
                "floor_number": 0,
                "plan_id": "plan_id",
            }
        ]
        mocker.patch.object(
            ifc_export_handler_module.IfcExportHandler,
            "floor_infos",
            mocker.PropertyMock(return_value=floors_info),
        )

        mocker.patch.object(
            ifc_export_handler_module.IfcExportHandler,
            "floor_layouts_relative_by_floor_id",
            mocker.PropertyMock(
                return_value={
                    floor_info["id"]: _fake_layout(floor_info["id"])
                    for floor_info in floors_info
                }
            ),
        )

        ifc_export_handler_module.IfcExportHandler(site_id=1337).add_slabs(
            ifc_floors_by_id={
                floor_info["id"]: f"floor_placeholder_{floor_info['id']}"
                for floor_info in floors_info
            },
        )

        actual_slabs = {
            (
                call.kwargs["ifc_floor"],
                repr(call.kwargs["polygon"]),
                call.kwargs["start_elevation_relative_to_floor"],
                call.kwargs["height"],
                call.kwargs["element_type"].__name__,
                call.kwargs["Name"],
            )
            for call in mocked_add_wall_railing_slab_furniture.call_args_list
        }

        assert actual_slabs == {
            (
                "floor_placeholder_1",
                "footprint_ex_areas_without_ceiling_1",
                2.6,
                0.3,
                "IfcSlabStandardCase",
                "Roof",
            ),
            (
                "floor_placeholder_1",
                "footprint_ex_areas_without_floor_1",
                0,
                -0.3,
                "IfcSlabStandardCase",
                "Floor",
            ),
        }
