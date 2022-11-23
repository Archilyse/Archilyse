from collections import Counter

import pytest
from shapely.geometry import Point

from common_utils.constants import (
    ADMIN_SIM_STATUS,
    REGION,
    SIMULATION_VERSION,
    TASK_TYPE,
    UNIT_USAGE,
)
from common_utils.exceptions import (
    BaseElevationException,
    DBException,
    DBNotFoundException,
)
from handlers import (
    BuildingHandler,
    PlanLayoutHandler,
    SlamSimulationHandler,
    UnitHandler,
)
from handlers.db import (
    BuildingDBHandler,
    PlanDBHandler,
    UnitAreaDBHandler,
    UnitDBHandler,
)
from simulations.view.meshes.triangulation3d import LayoutTriangulatorClabExtrusion
from surroundings.srtm import SrtmFilesHandler
from tests.constants import ELEVATION_BY_POINT
from tests.utils import check_3d_mesh_format, random_simulation_version


def visualize_mesh(meshes):
    from surroundings.visualization.sourroundings_3d_figure import (
        create_3d_surroundings_from_triangles_per_type,
    )

    create_3d_surroundings_from_triangles_per_type(
        filename="salpica",
        triangles_per_layout=meshes,
        triangles_per_surroundings_type=[],
    )


class TestBuildingHandler:
    def test_get_building_by_id(self, building):
        building_id = building["id"]
        building_from_db = BuildingDBHandler.get_by(id=building_id)
        assert building_from_db is not None
        assert building_from_db == building

    def test_find_building(self, building):
        housenumber = "20-22"
        buildings = BuildingDBHandler.find(housenumber=housenumber)
        assert buildings is not None
        assert buildings[0] == building

    @pytest.mark.parametrize(
        "building_values",
        [
            {"housenumber": "-777"},
            {"client_building_id": "3"},
            {"client_building_id": ""},
        ],
    )
    def test_update_building(self, building_values, building):
        updated_building = BuildingDBHandler.update(
            item_pks=dict(id=building["id"]), new_values=building_values
        )
        del building["updated"]
        del updated_building["updated"]
        building.update(building_values)
        assert building == updated_building

    def test_delete_building_by_id(self, building):
        building_id = building["id"]
        BuildingDBHandler.delete({"id": building_id})
        with pytest.raises(DBNotFoundException):
            assert BuildingDBHandler.get_by(id=building_id)

    def test_update_building_raises_db_exception_in_case_of_integrity_errors(
        self, building, other_clients_building
    ):
        with pytest.raises(DBException):
            BuildingDBHandler.update(
                item_pks=dict(id=building["id"]),
                new_values=dict(
                    site_id=other_clients_building["site_id"],
                    street=other_clients_building["street"],
                    housenumber=other_clients_building["housenumber"],
                    zipcode=other_clients_building["zipcode"],
                    city=other_clients_building["city"],
                ),
            )


def test_classify_apartment_types(
    site,
    make_plans,
    make_classified_split_plans,
    plan,
    building,
    client,
    login,
):
    plans = make_plans(building, building)
    for plan, fixture_plan_id in zip(plans, [1478, 2494]):
        make_classified_split_plans(
            plan,
            building=building,
            annotations_plan_id=fixture_plan_id,
            floor_number=plan["id"],
        )
    unit = UnitDBHandler.find(plan_id=plans[0]["id"], apartment_no=1)[0]
    UnitDBHandler.update(
        item_pks={"id": unit["id"]}, new_values={"unit_type": "custom_name"}
    )

    all_units = UnitDBHandler.find()
    assert len(all_units) == 11

    run_id = "my-run-id"
    SlamSimulationHandler.register_simulation(
        run_id=run_id,
        site_id=site["id"],
        task_type=TASK_TYPE.BASIC_FEATURES,
        state=ADMIN_SIM_STATUS.SUCCESS,
    )
    index = {
        (plans[0]["id"], 1): [{"UnitBasics.number-of-rooms": 3}],
        (plans[0]["id"], 2): [{"UnitBasics.number-of-rooms": 4}],
    }
    for i in range(1, 10):
        index[(plans[1]["id"], i)] = [{"UnitBasics.number-of-rooms": i + 1}]
    assert len(index) == 11

    SlamSimulationHandler.store_results(
        run_id=run_id,
        results=dict(
            (u["id"], index[(u["plan_id"], u["apartment_no"])]) for u in all_units
        ),
    )

    basic_feature_results = SlamSimulationHandler.get_all_results(
        site_id=site["id"], task_type=TASK_TYPE.BASIC_FEATURES
    )
    assert len(basic_feature_results) == 11
    assert all([unit["results"] is not None for unit in basic_feature_results])

    BuildingHandler.create_unit_types_per_building(building_id=building["id"])
    unit_types = [unit["unit_type"] for unit in UnitDBHandler.find()]
    assert Counter(unit_types) == {
        "4": 2,
        "custom_name": 1,
        "10": 1,
        "2": 1,
        "3": 1,
        "5": 1,
        "6": 1,
        "7": 1,
        "8": 1,
        "9": 1,
    }


def test_get_building_layout_triangles(
    first_pipeline_complete_db_models, visualize=False
):
    building_id = first_pipeline_complete_db_models["building"]["id"]
    units = first_pipeline_complete_db_models["units"]

    meshes = list(
        BuildingHandler(building_id=building_id).generate_layout_triangles(
            simulation_version=SIMULATION_VERSION.PH_01_2021, by_unit=True
        )
    )
    if visualize:
        visualize_mesh(meshes=meshes)

    check_3d_mesh_format(
        meshes=meshes,
        expected_dimensions={(412, 3, 3), (360, 3, 3), (256, 3, 3)},
        expected_mesh_names={unit["client_id"] for unit in units},
        expected_nbr_of_meshes=len(units),
    )


def test_get_building_layout_triangles_calls_sub_methods(mocker, building):
    floor_triangles_mock = mocker.patch.object(
        BuildingHandler, "get_floor_triangles", return_value=["foo"]
    )
    unit_triangles_mock = mocker.patch.object(
        BuildingHandler, "get_unit_triangles", return_value=["bar"]
    )

    result = list(
        BuildingHandler(building_id=building["id"]).generate_layout_triangles(
            simulation_version=SIMULATION_VERSION.PH_01_2021, by_unit=False
        )
    )
    floor_triangles_mock.assert_called_once_with(
        simulation_version=SIMULATION_VERSION.PH_01_2021, exclude_underground=True
    )
    unit_triangles_mock.assert_called_once_with(
        simulation_version=SIMULATION_VERSION.PH_01_2021, only_underground=True
    )
    assert result == ["foo", "bar"]


def test_get_building_layout_triangles_plans_without_units(
    building, floor, plan_classified_scaled_georeferenced, visualize=False
):
    PlanDBHandler.update(
        item_pks={"id": plan_classified_scaled_georeferenced["id"]},
        new_values={"without_units": True},
    )
    meshes = list(
        BuildingHandler(building_id=building["id"]).generate_layout_triangles(
            simulation_version=SIMULATION_VERSION.PH_01_2021, by_unit=True
        )
    )
    if visualize:
        visualize_mesh(meshes=meshes)

    check_3d_mesh_format(
        meshes=meshes,
        expected_dimensions={(2140, 3, 3)},
        expected_mesh_names={floor["floor_number"]},
        expected_nbr_of_meshes=1,
    )


@pytest.fixture
def building_with_plan_units_and_plan_without_units(
    first_pipeline_complete_db_models, make_plans, make_classified_plans, make_floor
):
    another_plan = make_plans(
        first_pipeline_complete_db_models["building"],
    )[0]
    make_classified_plans(another_plan, db_fixture_ids=False)
    unitless_floornumber = 0
    unitless_floor = make_floor(
        building=first_pipeline_complete_db_models["building"],
        plan=another_plan,
        floornumber=unitless_floornumber,
    )

    plan = first_pipeline_complete_db_models["plan"]
    another_plan = PlanDBHandler.update(
        item_pks=dict(id=another_plan["id"]),
        new_values={
            "without_units": True,
            "annotation_finished": True,
            "georef_x": plan["georef_x"],
            "georef_y": plan["georef_y"],
            "georef_rot_angle": plan["georef_rot_angle"],
            "georef_scale": plan["georef_scale"],
            "georef_rot_x": plan["georef_rot_x"],
            "georef_rot_y": plan["georef_rot_y"],
        },
    )
    return {
        **first_pipeline_complete_db_models,
        "unitless_plan": another_plan,
        "unitless_floor": unitless_floor,
    }


def test_get_building_layout_triangles_mixed(
    mocker, building, building_with_plan_units_and_plan_without_units, visualize=False
):
    building_id = building_with_plan_units_and_plan_without_units["building"]["id"]
    unitless_plan = building_with_plan_units_and_plan_without_units["unitless_plan"]
    unitless_floor = building_with_plan_units_and_plan_without_units["unitless_floor"]

    building_handler = BuildingHandler(building_id=building_id)

    floor_triangles_spy = mocker.spy(building_handler, "get_floor_triangles")
    unit_triangles_spy = mocker.spy(building_handler, "get_unit_triangles")

    simulation_version = SIMULATION_VERSION.PH_01_2021
    meshes = list(
        building_handler.generate_layout_triangles(
            simulation_version=simulation_version, by_unit=True
        )
    )
    if visualize:
        visualize_mesh(meshes=meshes)

    check_3d_mesh_format(
        meshes=meshes,
        expected_dimensions={(3728, 3, 3), (412, 3, 3), (360, 3, 3), (256, 3, 3)},
        expected_mesh_names={
            unitless_floor["floor_number"],
            "GS20.00.01",
            "GS20.01.02",
            "GS20.00.02",
        },
        expected_nbr_of_meshes=5,
    )
    call_args = floor_triangles_spy.call_args[1]
    assert call_args["simulation_version"] == simulation_version
    assert call_args["from_plans"][0]["id"] == unitless_plan["id"]
    unit_triangles_spy.assert_called_once_with(simulation_version=simulation_version)


def test_get_building_layout_triangles_no_elevation(first_pipeline_complete_db_models):
    building_id = first_pipeline_complete_db_models["building"]["id"]
    BuildingDBHandler.update(
        item_pks={"id": building_id}, new_values={"elevation": None}
    )

    with pytest.raises(BaseElevationException):
        list(
            BuildingHandler(building_id=building_id).generate_layout_triangles(
                simulation_version=SIMULATION_VERSION.PH_01_2021, by_unit=False
            )
        )


def test_get_elevation(
    mocker,
    building,
    plan,
    mocked_swisstopo_esri_ascii_grid,
):
    coordinates = list(ELEVATION_BY_POINT.keys())[0]

    class FakeFootprint:
        centroid = Point(coordinates)

    mocker.patch.object(
        PlanLayoutHandler, "get_georeferenced_footprint", return_value=FakeFootprint
    )
    with mocked_swisstopo_esri_ascii_grid("swiss_1188_1", "swiss_1168_3"):
        BuildingHandler.calculate_elevation(
            building_id=building["id"],
            simulation_version=random_simulation_version(),
            region=REGION.CH,
        )
    assert BuildingDBHandler.get_by(id=building["id"])["elevation"] == pytest.approx(
        ELEVATION_BY_POINT[coordinates]
    )


def test_get_elevation_srtm_us(
    mocker, building, plan, mocked_gcp_download, fixtures_srtm_path
):
    mocker.patch.object(
        SrtmFilesHandler,
        SrtmFilesHandler.get_srtm_files.__name__,
        return_value=iter(
            [(fixtures_srtm_path.joinpath("n33_w085_1arc_v3.tif"))],
        ),
    )

    coordinates = (685509, 424279)

    class FakeFootprint:
        centroid = Point(coordinates)

    mocker.patch.object(
        PlanLayoutHandler, "get_georeferenced_footprint", return_value=FakeFootprint
    )
    BuildingHandler.calculate_elevation(
        building_id=building["id"],
        simulation_version=random_simulation_version(),
        region=REGION.US_GEORGIA,
    )
    assert BuildingDBHandler.get_by(id=building["id"])["elevation"] == pytest.approx(
        300.0483
    )


@pytest.mark.parametrize(
    "exclude_underground, expected_floor_numbers",
    [(True, {0, 1, 2}), (False, {-1, 0, 1, 2})],
)
def test_get_floor_triangles(
    mocker,
    building,
    make_plans,
    make_floor,
    exclude_underground,
    expected_floor_numbers,
):
    plan1, plan2 = make_plans(*(building, building))
    make_floor(building=building, plan=plan1, floornumber=-1)
    make_floor(building=building, plan=plan1, floornumber=0)
    make_floor(building=building, plan=plan2, floornumber=1)
    make_floor(building=building, plan=plan2, floornumber=2)

    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value="Placeholder")
    mocked_triangulator = mocker.patch.object(
        LayoutTriangulatorClabExtrusion,
        "create_layout_triangles",
        return_value=["Triangle", "Triangle", "Triangle"],
    )
    triangles_by_floors = list(
        BuildingHandler(building_id=building["id"]).get_floor_triangles(
            simulation_version=SIMULATION_VERSION.EXPERIMENTAL,
            exclude_underground=exclude_underground,
        )
    )
    assert len(triangles_by_floors) == len(expected_floor_numbers)
    assert {triangles[0] for triangles in triangles_by_floors} == expected_floor_numbers

    mocked_calls = []
    if not exclude_underground:
        mocked_calls.append(
            mocker.call(
                layouts_upper_floor=["Placeholder"],
                level_baseline=-2.9,
            )
        )
    mocked_calls.extend(
        [
            mocker.call(
                layouts_upper_floor=["Placeholder"],
                level_baseline=0,
            ),
            mocker.call(
                layouts_upper_floor=["Placeholder"],
                level_baseline=2.9,
            ),
            mocker.call(
                layouts_upper_floor=[],
                level_baseline=5.8,
            ),  # last floor has no upper floor
        ]
    )

    assert mocked_triangulator.call_args_list == mocked_calls


@pytest.mark.parametrize(
    "only_underground",
    [True, False],
)
def test_get_unit_triangles(
    mocker,
    building,
    make_plans,
    make_floor,
    make_units,
    only_underground,
):
    (plan1,) = make_plans(building)
    floor_underground = make_floor(building=building, plan=plan1, floornumber=-1)
    floor_overground = make_floor(building=building, plan=plan1, floornumber=0)
    unit_underground, unit_overground = make_units(floor_underground, floor_overground)

    mocked_unit_triangulation = mocker.patch.object(UnitHandler, "get_layout_triangles")
    mocker.patch.object(UnitHandler, "get_unit_layout")

    list(
        BuildingHandler(building_id=building["id"]).get_unit_triangles(
            simulation_version=SIMULATION_VERSION.EXPERIMENTAL,
            only_underground=only_underground,
        )
    )

    called_unit_ids = [
        call.kwargs["unit_id"] for call in mocked_unit_triangulation.call_args_list
    ]

    if only_underground:
        assert called_unit_ids == [unit_underground["id"]]
    else:
        assert called_unit_ids == [unit_underground["id"], unit_overground["id"]]


def test_building_handler_get_area_usages(site_with_3_units):
    unit_areas = {
        unit["id"]: list(
            UnitAreaDBHandler.find_in(
                unit_id=[unit["id"]],
                output_columns=["area_id"],
            )
        )
        for unit in site_with_3_units["units"]
    }

    num_unit_areas = sum([len(areas) for areas in unit_areas.values()])
    num_areas_unit_0 = len(unit_areas[site_with_3_units["units"][0]["id"]])
    num_public_areas = 5
    area_usages = BuildingHandler(
        building_id=site_with_3_units["building"]["id"]
    )._area_usage_by_floor_number()
    assert Counter(area_usages[1].values())[UNIT_USAGE.RESIDENTIAL] == num_unit_areas
    assert Counter(area_usages[1].values())[None] == num_public_areas

    for unit_usage in {u for u in UNIT_USAGE if u is not UNIT_USAGE.RESIDENTIAL}:
        UnitDBHandler.update(
            item_pks={"id": site_with_3_units["units"][0]["id"]},
            new_values={"unit_usage": unit_usage.name},
        )
        area_usages = BuildingHandler(
            building_id=site_with_3_units["building"]["id"]
        )._area_usage_by_floor_number()
        assert Counter(area_usages[1].values())[unit_usage] == num_areas_unit_0
        assert (
            Counter(area_usages[1].values())[UNIT_USAGE.RESIDENTIAL]
            == num_unit_areas - num_areas_unit_0
        )
        assert Counter(area_usages[1].values())[None] == num_public_areas


@pytest.mark.parametrize(
    "init_args, elevation_expected",
    [
        ({"elevation": 10}, 10),
        ({"elevation_override": 10}, 10),
        ({"elevation": 20, "elevation_override": 10}, 10),
        ({"elevation": 10, "elevation_override": None}, 10),
        ({"elevation": 10, "elevation_override": 0.0}, 0.0),
        ({"elevation": 0.0}, 0.0),
        ({}, BaseElevationException),
    ],
)
def test_building_handler_override_elevation(site, init_args, elevation_expected):
    building = BuildingDBHandler.add(
        site_id=site["id"],
        client_building_id="1",
        housenumber="20-22",
        city="Zurich",
        zipcode="8000",
        street="Technoparkstrasse",
        **init_args
    )
    if elevation_expected == BaseElevationException:
        with pytest.raises(BaseElevationException):
            return BuildingHandler(building_id=building["id"]).elevation
    else:
        assert (
            BuildingHandler(building_id=building["id"]).elevation == elevation_expected
        )
