import pytest
from deepdiff import DeepDiff
from shapely.geometry import MultiPolygon, Point, Polygon, box
from shapely.ops import unary_union

from brooks.types import AreaType
from brooks.util.projections import project_geometry
from common_utils.constants import REGION, SIMULATION_VERSION, PipelineCompletedCriteria
from handlers import GCloudStorageHandler, SiteHandler, UnitHandler
from handlers.db import SiteDBHandler, UnitDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData


@pytest.mark.parametrize(
    "simulation_version",
    [
        SIMULATION_VERSION.PH_01_2021,
        SIMULATION_VERSION.PH_2022_H1,
        SIMULATION_VERSION.EXPERIMENTAL,
    ],
)
@pytest.mark.parametrize("region", [REGION.CH, REGION.CZ])
@pytest.mark.parametrize("sample", [True, False])
def test_generate_view_surroundings_calls_factory_method(
    simulation_version, region, sample, mocker
):
    import surroundings.surrounding_handler

    site_id = -999
    lat, lon = 46.0, 8.0
    plans_footprints = [box(0, 0, 1, 1), box(1, 0, 2, 1)]

    mocked_view_surroundings = mocker.patch.object(
        surroundings.surrounding_handler, "generate_view_surroundings"
    )
    mocker.patch.object(
        SiteHandler, "_plan_footprints_per_building", return_value={1: plans_footprints}
    )

    view_surroundings = SiteHandler.generate_view_surroundings(
        site_info=dict(
            id=site_id,
            georef_region=region.name,
            simulation_version=simulation_version.name,
            lat=lat,
            lon=lon,
        ),
        sample=sample,
    )

    assert view_surroundings == mocked_view_surroundings.return_value
    mocked_view_surroundings.assert_called_once_with(
        site_id=site_id,
        region=region,
        location=project_geometry(
            Point(lon, lat), crs_from=REGION.LAT_LON, crs_to=region
        ),
        building_footprints=[unary_union(plans_footprints)],
        simulation_version=simulation_version,
        sample=sample,
    )


@pytest.mark.parametrize(
    "plan_mock, unit_mock, areas_mock, expected",
    [
        ([], [], [], PipelineCompletedCriteria()),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": 1,
                    "georef_rot_angle": 1,
                    "annotation_finished": True,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [],
            [{"area_type": AreaType.ROOM.name}],
            PipelineCompletedCriteria(
                labelled=True,
                georeferenced=True,
                classified=True,
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": 1,
                    "georef_rot_angle": 1,
                    "annotation_finished": True,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [],
            [{"area_type": AreaType.NOT_DEFINED.name}],
            PipelineCompletedCriteria(
                labelled=True,
                georeferenced=True,
                classified=False,
            ),
        ),
        ([], [{"client_id": None}], [], PipelineCompletedCriteria()),
        (
            [
                {
                    "georef_x": None,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": 1,
                    "georef_rot_angle": 1,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [],
            [{"area_type": AreaType.NOT_DEFINED.name}],
            PipelineCompletedCriteria(classified=False),
        ),
        (
            [],
            [{"client_id": 1}, {"client_id": None}],
            [],
            PipelineCompletedCriteria(),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": None,
                    "georef_rot_angle": 1,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [{"client_id": 1}, {"client_id": 2}],
            [{"area_type": AreaType.NOT_DEFINED.name}],
            PipelineCompletedCriteria(
                splitted=True, units_linked=True, classified=False, georeferenced=True
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": None,
                    "georef_rot_angle": 1,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [{"client_id": 1}, {"client_id": 2}],
            [{"area_type": AreaType.ROOM.name}, {"area_type": AreaType.KITCHEN.name}],
            PipelineCompletedCriteria(
                # classified false as not labelled
                splitted=True,
                units_linked=True,
                classified=False,
                georeferenced=True,
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": None,
                    "georef_rot_angle": 1,
                    "id": 2,
                    "without_units": False,
                }
            ],
            [{"client_id": 1}, {"client_id": 2}],
            [
                {"area_type": AreaType.ROOM.name},
                {"area_type": AreaType.NOT_DEFINED.name},
            ],
            PipelineCompletedCriteria(
                # classified false as not labelled
                splitted=True,
                units_linked=True,
                classified=False,
                georeferenced=True,
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": 1.0,
                    "georef_rot_angle": 1,
                    "id": 1,
                    "without_units": False,
                },
                {
                    "georef_x": None,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": None,
                    "georef_rot_angle": 1,
                    "id": 2,
                    "without_units": False,
                },
            ],
            [{"client_id": 1}, {"client_id": 2}],
            [{"area_type": AreaType.NOT_DEFINED.name}],
            PipelineCompletedCriteria(
                splitted=True, units_linked=True, classified=False, georeferenced=False
            ),
        ),
        # Experimental plan that is labelled will be scaled
        (
            [
                {
                    "georef_x": None,
                    "georef_y": None,
                    "georef_rot_x": None,
                    "georef_rot_y": None,
                    "georef_scale": None,
                    "georef_rot_angle": None,
                    "annotation_finished": True,
                    "id": 1,
                    "without_units": False,
                },
            ],
            [],
            [],
            PipelineCompletedCriteria(
                labelled=True,
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": None,
                    "georef_rot_angle": 1,
                    "annotation_finished": True,
                    "id": 1,
                    "without_units": True,
                },
            ],
            [],
            [{"area_type": AreaType.ROOM.name}],
            PipelineCompletedCriteria(
                labelled=True,
                classified=True,
                splitted=True,
                georeferenced=True,
                units_linked=True,
            ),
        ),
        (
            [
                {
                    "georef_x": 1,
                    "georef_y": 1,
                    "georef_rot_x": 1,
                    "georef_rot_y": 1,
                    "georef_scale": 1.0,
                    "georef_rot_angle": 1,
                    "annotation_finished": True,
                    "id": 1,
                    "without_units": True,
                },
            ],
            [],
            [{"area_type": AreaType.ROOM.name}],
            PipelineCompletedCriteria(
                labelled=True,
                classified=True,
                splitted=True,
                georeferenced=True,
                units_linked=True,
            ),
        ),
    ],
)
def test_site_requirements_for_results(
    mocker, plan_mock, unit_mock, areas_mock, expected
):
    from handlers import plan_handler, site_handler

    site_id = 1
    mocker.patch.object(
        plan_handler.PlanDBHandler,
        "get_by",
        lambda id: {plan["id"]: plan for plan in plan_mock}[id],
    )
    mocker.patch.object(site_handler.PlanDBHandler, "find", return_value=plan_mock)
    mocker.patch.object(plan_handler.UnitDBHandler, "find", return_value=unit_mock)
    mocker.patch.object(plan_handler.AreaDBHandler, "find", return_value=areas_mock)

    assert (
        site_handler.SiteHandler.pipeline_completed_criteria(site_id=site_id)
        == expected
    )


def test_read_building_footprints_slam(
    mocker, building_surroundings_path, site_region_proj_ch
):
    mocker.patch.object(
        SiteDBHandler,
        "get_by",
        return_value={
            "gcs_buildings_link": "fake_link",
            "lon": -19.91799616385958,
            "lat": 32.12448649090249,
            **site_region_proj_ch,
        },
    )

    with building_surroundings_path.open("rb") as f:
        mocker.patch.object(
            GCloudStorageHandler,
            "download_bytes_from_media_link",
            return_value=f.read(),
        )

    buildings_footprints = list(
        SiteHandler.get_surr_buildings_footprints_for_site(site_id=-1, as_lat_lon=True)
    )
    assert len(buildings_footprints) == 26
    assert all(isinstance(b, (Polygon, MultiPolygon)) for b in buildings_footprints)


def test_update_location_based_on_geoereferenced_layouts(mocker):
    mocked_update = mocker.patch.object(SiteDBHandler, "update")
    mocker.patch.object(
        SiteHandler,
        "_plan_footprints_per_building",
        return_value={1: [box(minx=0, miny=0, maxx=10, maxy=10)]},
    )
    site_id = 123

    SiteHandler.update_location_based_on_geoereferenced_layouts(
        site_info={"id": site_id, "georef_region": REGION.CH.name}
    )

    expected_location = project_geometry(
        geometry=Point(5, 5),
        crs_from=REGION.CH,
        crs_to=REGION.LAT_LON,
    )
    assert mocked_update.call_args[1] == {
        "item_pks": {"id": site_id},
        "new_values": {"lon": expected_location.x, "lat": expected_location.y},
    }


def test_basic_features_generation_2_units_1_apartment(
    mocker,
    fixtures_path,
    mock_working_dir,
    brooks_model_json_path,
    mocked_gcp_download,
    annotations_plan_4836,
    annotations_plan_2016,
):
    mocker.patch.object(
        UnitDBHandler,
        "find",
        return_value=[{"id": 1, "client_id": "A"}, {"id": 2, "client_id": "A"}],
    )
    mocker.patch.object(UnitHandler, "validate_unit")
    layout_a = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_4836), scaled=True
    )
    layout_b = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_2016), scaled=True
    )

    mocker.patch.object(
        UnitHandler, "get_unit_layout", side_effect=[layout_a, layout_b]
    )

    basic_features_by_unit_id = SiteHandler.generate_basic_features(site_id=1)

    expected = {
        "UnitBasics.area-balconies": 0.0,
        "UnitBasics.area-bathrooms": 51.217292983603166,
        "UnitBasics.area-corridors": 0.0,
        "UnitBasics.area-elevators": 6.078511326145416,
        "UnitBasics.area-kitchens": 0.0,
        "UnitBasics.area-loggias": 0.0,
        "UnitBasics.area-rooms": 0.0,
        "UnitBasics.area-shafts": 3.9095454105155087,
        "UnitBasics.area-sia416-ANF": 0.0,
        "UnitBasics.area-sia416-FF": 3.9095454105155087,
        "UnitBasics.area-sia416-HNF": 51.217292983603166,
        "UnitBasics.area-sia416-NNF": 0.0,
        "UnitBasics.area-sia416-VF": 70.53129831600727,
        "UnitBasics.area-staircases": 64.45278698986183,
        "UnitBasics.area-storage_rooms": 0.0,
        "UnitBasics.area-sunrooms": 0.0,
        "UnitBasics.has-kitchen-window": 0,
        "UnitBasics.maximum-balcony-area": 0.0,
        "UnitBasics.maximum-dining-table": 0.0,
        "UnitBasics.net-area": 51.217292983603166,
        "UnitBasics.net-area-no-corridors": 51.217292983603166,
        "UnitBasics.net-area-no-corridors-reduced-loggias": 51.217292983603166,
        "UnitBasics.net-area-reduced-loggias": 51.217292983603166,
        "UnitBasics.number-of-balconies": 0.0,
        "UnitBasics.number-of-bathrooms": 11.0,
        "UnitBasics.number-of-bathtubs": 7.0,
        "UnitBasics.number-of-corridors": 0.0,
        "UnitBasics.number-of-kitchens": 0.0,
        "UnitBasics.number-of-loggias": 0.0,
        "UnitBasics.number-of-rooms": 0.0,
        "UnitBasics.number-of-showers": 0.0,
        "UnitBasics.number-of-storage-rooms": 0.0,
        "UnitBasics.number-of-sunrooms": 0.0,
        "UnitBasics.number-of-toilets": 11.0,
    }
    unit_ids = {res[0] for res in basic_features_by_unit_id}
    assert unit_ids == {1, 2}
    results = [res[1][0] for res in basic_features_by_unit_id]
    assert results[0] == results[1]
    assert not DeepDiff(expected, results[0], significant_digits=3)
