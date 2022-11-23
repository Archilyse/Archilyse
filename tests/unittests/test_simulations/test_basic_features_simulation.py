import json
from collections import Counter

import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point, box

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimFeature, SimLayout, SimSpace
from brooks.types import AreaType, FeatureType, get_valid_area_type_from_string
from handlers import PlanLayoutHandler, ReactPlannerHandler, UnitHandler
from handlers.db import UnitAreaDBHandler
from handlers.editor_v2.editor_v2_element_mapper import ReactPlannerToBrooksMapper
from handlers.editor_v2.schema import ReactPlannerData
from simulations.basic_features import CustomValuatorBasicFeatures2
from simulations.basic_features.basic_feature import BaseBasicFeatures
from tests.utils import _generate_dummy_layout


def get_fake_layout(constructors):
    class FakeAreas:
        def __init__(self, area_type):
            self.type = area_type

    class FakeSpaces:
        def __init__(self, area_types):
            self.areas = [FakeAreas(area_type=area_type) for area_type in area_types]

    class FakeLayout:
        def __init__(self, _constructors):
            self.spaces = [
                FakeSpaces(area_types=area_types) for area_types in _constructors
            ]
            self.areas = [a for s in self.spaces for a in s.areas]

    return FakeLayout(_constructors=constructors)


@pytest.fixture
def layout(annotations_plan_3881):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_3881)
    )
    for opening in layout.openings:
        opening.height = [0, 2.6]

    for area in layout.areas:
        area._type = AreaType.ROOM

    return layout


@pytest.fixture
def unit_34850(
    mocker,
    georef_plan_values,
    layout_scaled_classified_wo_db_conn,
):
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=5825)
    unit_info = {"plan_id": 5825, "client_id": -77}

    unit_areas_db = [
        {"unit_id": 34850, "area_id": 472792},
        {"unit_id": 34850, "area_id": 472796},
        {"unit_id": 34850, "area_id": 472797},
        {"unit_id": 34850, "area_id": 472798},
        {"unit_id": 34850, "area_id": 472804},
        {"unit_id": 34850, "area_id": 472807},
        {"unit_id": 34850, "area_id": 472808},
        {"unit_id": 34850, "area_id": 472810},
        {"unit_id": 34850, "area_id": 472811},
        {"unit_id": 34850, "area_id": 472816},
    ]

    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)
    mocker.patch.object(UnitHandler, "_get_unit_info", return_value=unit_info)
    mocker.patch.object(UnitAreaDBHandler, "find", return_value=unit_areas_db)

    return UnitHandler().get_unit_layout(unit_id=34850, postprocessed=False)


@pytest.fixture
def unit_36410(mocker, layout_scaled_classified_wo_db_conn):
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=5826)

    unit_info = {"plan_id": 5826, "client_id": -77}

    unit_areas_db = [
        {"unit_id": 36410, "area_id": 410554},
        {"unit_id": 36410, "area_id": 410557},
        {"unit_id": 36410, "area_id": 410565},
        {"unit_id": 36410, "area_id": 410570},
        {"unit_id": 36410, "area_id": 410575},
        {"unit_id": 36410, "area_id": 410596},
        {"unit_id": 36410, "area_id": 410602},
        {"unit_id": 36410, "area_id": 410603},
    ]
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)
    mocker.patch.object(UnitHandler, "_get_unit_info", return_value=unit_info)
    mocker.patch.object(UnitAreaDBHandler, "find", return_value=unit_areas_db)
    return UnitHandler().get_unit_layout(unit_id=36410, postprocessed=False)


@pytest.fixture
def layout_3_rooms_w_stairs(mocker, annotations_3_rooms_2_w_stairs):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_3_rooms_2_w_stairs),
        scaled=True,
    )
    mocker.patch.object(
        ReactPlannerHandler,
        "project",
        return_value={"data": annotations_3_rooms_2_w_stairs},
    )
    layout_areas_sorted = sorted(
        layout.areas,
        key=lambda x: x.footprint.centroid.x,
    )
    return layout, layout_areas_sorted


@pytest.fixture
def layout_2494(annotations_plan_2494, fixtures_path):
    layout = ReactPlannerToBrooksMapper.get_layout(
        planner_elements=ReactPlannerData(**annotations_plan_2494), scaled=True
    )

    with fixtures_path.joinpath("areas/areas_plan_2494.json").open() as f:
        for area in json.load(f):
            for l_area in layout.areas:
                if Point(area["coord_x"], area["coord_y"]).within(l_area.footprint):
                    l_area._type = get_valid_area_type_from_string(area["area_type"])

    return layout


class TestBasicFeaturesAreasMethods:
    stair_size_area_2 = 2.8335999999999983
    stair_size_area_3 = 1.691999999999999
    area_1_layout = 19.9695051846878
    area_2_layout_w_stairs = 21.975385450497512
    area_2_layout_wo_stairs = area_2_layout_w_stairs - stair_size_area_2
    area_3_layout_w_stairs = 15.797274231803627
    area_3_layout_wo_stairs = area_3_layout_w_stairs - stair_size_area_3
    total_area_layout = area_3_layout_w_stairs + area_1_layout + area_2_layout_w_stairs

    @pytest.mark.parametrize(
        "areas_type, expected_net_area_ph_basic_feature",
        [
            (
                [AreaType.ROOM, AreaType.LIVING_ROOM, AreaType.BEDROOM],
                area_1_layout + area_2_layout_w_stairs + area_3_layout_w_stairs,
            ),
            (
                [AreaType.ROOM, AreaType.DINING, AreaType.STAIRCASE],
                area_1_layout + area_2_layout_w_stairs,
            ),
            (
                [AreaType.ROOM, AreaType.LOGGIA, AreaType.STAIRCASE],
                area_1_layout,
            ),
            ([AreaType.BALCONY, AreaType.STAIRCASE, AreaType.STAIRCASE], 0),
            ([AreaType.BALCONY, AreaType.VOID, AreaType.LIGHTWELL], 0),
        ],
    )
    def test_net_areas(
        self,
        layout_3_rooms_w_stairs,
        areas_type,
        expected_net_area_ph_basic_feature,
    ):
        layout, layout_areas_sorted = layout_3_rooms_w_stairs

        for area, area_type in zip(layout_areas_sorted, areas_type):
            area._type = area_type

        result = CustomValuatorBasicFeatures2().net_area([layout])

        assert result["net-area"] == pytest.approx(
            expected_net_area_ph_basic_feature, abs=0.01
        )

    @pytest.mark.parametrize(
        "areas_type, expected_area_values",
        [
            (
                [AreaType.ROOM, AreaType.LIVING_ROOM, AreaType.BEDROOM],
                {
                    "area-rooms": area_1_layout
                    + area_2_layout_wo_stairs
                    + area_3_layout_wo_stairs
                },
            ),
            (
                [AreaType.ROOM, AreaType.DINING, AreaType.STAIRCASE],
                {
                    "area-rooms": area_1_layout + area_2_layout_wo_stairs,
                    "area-staircases": area_3_layout_w_stairs + stair_size_area_2,
                },
            ),
            (
                [AreaType.ROOM, AreaType.LOGGIA, AreaType.STAIRCASE],
                {
                    "area-rooms": area_1_layout,
                    "area-staircases": area_3_layout_w_stairs + stair_size_area_2,
                    "area-loggias": area_2_layout_wo_stairs,
                },
            ),
            (
                [AreaType.BALCONY, AreaType.STAIRCASE, AreaType.STAIRCASE],
                {
                    "area-staircases": area_2_layout_wo_stairs
                    + area_3_layout_w_stairs
                    + stair_size_area_2,
                    "area-balconies": area_1_layout,
                },
            ),
            (
                [AreaType.KITCHEN, AreaType.KITCHEN_DINING, AreaType.BATHROOM],
                {
                    "area-kitchens": area_1_layout + area_2_layout_wo_stairs,
                    "area-bathrooms": area_3_layout_wo_stairs,
                },
            ),
            (
                [AreaType.CORRIDOR, AreaType.STOREROOM, AreaType.WINTERGARTEN],
                {
                    "area-corridors": area_1_layout,
                    "area-storage_rooms": area_2_layout_wo_stairs,
                    "area-sunrooms": area_3_layout_wo_stairs,
                },
            ),
        ],
    )
    def test_total_area_by_room_type(
        self, layout_3_rooms_w_stairs, areas_type, expected_area_values
    ):
        layout, layout_areas_sorted = layout_3_rooms_w_stairs
        for area, area_type in zip(layout_areas_sorted, areas_type):
            area._type = area_type

        result = dict(
            [
                *CustomValuatorBasicFeatures2().total_area_by_room_type([layout]),
                *CustomValuatorBasicFeatures2().area_of_staircases([layout]),
            ]
        )
        assert sum(result.values()) == pytest.approx(self.total_area_layout, abs=0.01)
        assert not DeepDiff(
            result,
            {
                "area-balconies": 0.0,
                "area-bathrooms": 0.0,
                "area-corridors": 0.0,
                "area-elevators": 0.0,
                "area-kitchens": 0.0,
                "area-loggias": 0.0,
                "area-rooms": 0.0,
                "area-shafts": 0.0,
                "area-staircases": self.stair_size_area_2
                + self.stair_size_area_3,  # default value because of the feature
                "area-storage_rooms": 0.0,
                "area-sunrooms": 0.0,
                **expected_area_values,
            },
            ignore_order=True,
            significant_digits=3,
        )

    @pytest.mark.parametrize(
        "areas_type, expected_ph_basic_feature",
        [
            (
                [AreaType.ROOM, AreaType.BEDROOM, AreaType.LIVING_ROOM],
                {
                    "VF": 0.0,
                    "HNF": area_1_layout
                    + area_2_layout_w_stairs
                    + area_3_layout_w_stairs,
                    "ANF": 0.0,
                    "NNF": 0.0,
                    "FF": 0.0,
                },
            ),
            (
                [AreaType.ROOM, AreaType.ROOM, AreaType.STAIRCASE],
                {
                    "VF": area_3_layout_w_stairs,
                    "HNF": area_1_layout + area_2_layout_w_stairs,
                    "ANF": 0.0,
                    "NNF": 0.0,
                    "FF": 0.0,
                },
            ),
            (
                [AreaType.ROOM, AreaType.LOGGIA, AreaType.STAIRCASE],
                {
                    "VF": area_3_layout_w_stairs,
                    "HNF": area_1_layout,
                    "ANF": area_2_layout_w_stairs,
                    "NNF": 0.0,
                    "FF": 0.0,
                },
            ),
            (
                [AreaType.BALCONY, AreaType.STAIRCASE, AreaType.STAIRCASE],
                {
                    "VF": area_2_layout_w_stairs + area_3_layout_w_stairs,
                    "HNF": 0.0,
                    "ANF": area_1_layout,
                    "NNF": 0.0,
                    "FF": 0.0,
                },
            ),
            (
                [AreaType.STOREROOM, AreaType.CORRIDOR, AreaType.SHAFT],
                {
                    "VF": 0.0,
                    "HNF": area_2_layout_w_stairs,
                    "ANF": 0.0,
                    "NNF": area_1_layout,
                    "FF": area_3_layout_w_stairs,
                },
            ),
            (
                [AreaType.STOREROOM, AreaType.CORRIDOR, AreaType.SHAFT],
                {
                    "VF": 0.0,
                    "HNF": area_2_layout_w_stairs,
                    "ANF": 0.0,
                    "NNF": area_1_layout,
                    "FF": area_3_layout_w_stairs,
                },
            ),
        ],
    )
    def test_sia_dimensions(
        self,
        layout_3_rooms_w_stairs,
        areas_type,
        expected_ph_basic_feature,
    ):
        layout, layout_areas_sorted = layout_3_rooms_w_stairs

        for area, area_type in zip(layout_areas_sorted, areas_type):
            area._type = area_type

        result = CustomValuatorBasicFeatures2().sia_dimensions([layout])

        assert not DeepDiff(
            expected_ph_basic_feature, result, ignore_order=True, significant_digits=2
        )

    def test_stairs_overlap_walls_total_area(self, layout_2494):
        result = dict(
            [
                *CustomValuatorBasicFeatures2().total_area_by_room_type([layout_2494]),
                *CustomValuatorBasicFeatures2().area_of_staircases([layout_2494]),
            ]
        )
        assert not DeepDiff(
            {
                "area-balconies": 0.0,
                "area-loggias": 0.0,
                "area-shafts": 1.1385899828463095,
                "area-kitchens": 0.0,
                "area-corridors": 0.0,
                "area-rooms": 0.0,
                "area-bathrooms": 16.380614101873803,
                "area-sunrooms": 0.0,
                "area-storage_rooms": 0.0,
                "area-elevators": 0.0,
                "area-staircases": 327.557675206531,
            },
            result,
            significant_digits=3,
        )

    def test_stairs_overlap_walls_sia_dimensions(self, layout_2494):
        result = BaseBasicFeatures().sia_dimensions([layout_2494])
        assert not DeepDiff(
            {
                "ANF": 0.0,
                "FF": 1.1385899,
                "HNF": 16.380614101873803,
                "NNF": 0.0,
                "VF": 327.5575758886717,
            },
            result,
            significant_digits=3,
        )

    def test_stairs_overlap_walls_net_area(self, layout_2494):
        result = CustomValuatorBasicFeatures2().net_area([layout_2494])
        assert result["net-area"] == pytest.approx(16.380614101873803)


class TestOldRectangleFeature:
    def test_biggest_rectangle_simple_area(self):
        polygon = box(0, 0, 10, 5)
        area = SimArea(footprint=polygon, area_type=AreaType.KITCHEN_DINING)
        space = SimSpace(footprint=polygon)
        space.areas = {area}
        layout = SimLayout(spaces={space})
        assert CustomValuatorBasicFeatures2().find_biggest_rectangles(
            layouts=[layout], valid_area_types={AreaType.KITCHEN_DINING}
        ) == pytest.approx(expected=43.48, abs=0.01)

    def test_biggest_rectangle_area_with_feature(self):
        feature = SimFeature(footprint=box(0, 0, 2, 5))
        area_polygon = box(0, 0, 10, 5)
        area = SimArea(footprint=area_polygon, area_type=AreaType.KITCHEN_DINING)
        area.features = {feature}
        space = SimSpace(footprint=area_polygon)
        space.areas = {area}
        layout = SimLayout(spaces={space})
        assert CustomValuatorBasicFeatures2().find_biggest_rectangles(
            layouts=[layout], valid_area_types={AreaType.KITCHEN_DINING}
        ) == pytest.approx(expected=34.77, abs=0.01)

    def test_find_biggest_rectangle_area_completely_covered_by_feature(self):
        closed_room = SimArea(footprint=box(0, 0, 5, 5), area_type=AreaType.BALCONY)
        room_feature = SimFeature(
            footprint=box(0, 0, 5, 5), feature_type=FeatureType.SHAFT
        )
        closed_room.features = {room_feature}
        container_space = SimSpace(footprint=closed_room.footprint)
        container_space.areas = {closed_room}
        layout = SimLayout(spaces={container_space})
        biggest_rectangle = CustomValuatorBasicFeatures2().find_biggest_rectangles(
            layouts=[layout], valid_area_types={AreaType.LOGGIA, AreaType.BALCONY}
        )
        assert biggest_rectangle == 0


class TestCounters:
    @pytest.mark.parametrize(
        "constructors, expected_ph_1, expected_ph_2",
        [
            (
                [
                    [AreaType.ROOM],
                    [AreaType.CORRIDOR, AreaType.CORRIDOR],
                    [AreaType.BATHROOM, AreaType.BATHROOM],
                    [AreaType.ELEVATOR, AreaType.ELEVATOR],
                ],
                1,
                1,
            ),
            ([[AreaType.ROOM], [AreaType.DINING, AreaType.KITCHEN]], 2, 2),
            ([[AreaType.ROOM], [AreaType.KITCHEN_DINING]], 2.5, 2.5),
            ([[AreaType.ROOM, AreaType.KITCHEN_DINING]], 1.5, 2.5),
            ([[AreaType.ROOM] * 10], 1, 10),
            ([[AreaType.ROOM, AreaType.CORRIDOR]], 1, 1),
            ([[AreaType.BATHROOM]], 0, 0),
            ([[]], 0, 0),
            ([[AreaType.ROOM]], 1, 1),
            ([[AreaType.BEDROOM]], 1, 1),
            ([[AreaType.LIVING_ROOM]], 1, 1),
            ([[AreaType.LIVING_DINING]], 1.5, 1.5),
            (
                [[area for area in AreaType]],
                1.5,
                sum(UnifiedClassificationScheme.NBR_OF_ROOMS_COUNTER.values()),
            ),
            (
                [[area] for area in AreaType],
                sum(UnifiedClassificationScheme.NBR_OF_ROOMS_COUNTER.values()),
                sum(UnifiedClassificationScheme.NBR_OF_ROOMS_COUNTER.values()),
            ),
        ],
    )
    def test_calculate_number_rooms(self, constructors, expected_ph_1, expected_ph_2):
        fake_layout = get_fake_layout(constructors=constructors)
        assert (
            CustomValuatorBasicFeatures2().number_of_rooms(layouts=[fake_layout])[0][1]
            == expected_ph_2
        ), (constructors, expected_ph_2)

    def test_get_areas_by_parent_area_type(self, unit_34850, unit_36410):
        areas_by_room_category = BaseBasicFeatures().get_areas_by_area_type_groups(
            layouts=[unit_34850, unit_36410],
            groups=BaseBasicFeatures().ROOM_CATEGORIES,
        )

        assert Counter(
            {
                key: len(values)
                for key, values in areas_by_room_category.items()
                if len(values) > 0
            }
        ) == {
            "ROOMS": 5,
            "SHAFTS": 3,
            "CORRIDORS": 3,
            "KITCHENS": 1,
            "BATHROOMS": 3,
        }

    def test_furniture_count_dimensions(self, unit_34850, unit_36410):
        results = CustomValuatorBasicFeatures2().furniture_count_dimensions(
            layouts=[unit_34850, unit_36410]
        )
        assert {result[0]: result[1] for result in results} == {
            "number-of-bathtubs": 1,
            "number-of-showers": 1,
            "number-of-toilets": 3,
        }


def test_full_results_basic_features(unit_34850):
    result = CustomValuatorBasicFeatures2().get_basic_features(
        unit_id_unit_layout={34850: unit_34850}
    )
    expected_basic_features = {
        "number-of-rooms": 4.5,
        "number-of-balconies": 0.0,
        "number-of-loggias": 0.0,
        "number-of-kitchens": 1.0,
        "number-of-corridors": 1.0,
        "number-of-bathrooms": 2.0,
        "number-of-sunrooms": 0.0,
        "number-of-storage-rooms": 0.0,
        "area-balconies": 0.0,
        "area-loggias": 0.0,
        "area-shafts": 0.17104372429342657,
        "area-kitchens": 13.043643000665448,
        "area-corridors": 11.933922342229417,
        "area-rooms": 76.65504716731739,
        "area-bathrooms": 6.35195347601161,
        "area-sunrooms": 0.0,
        "area-storage_rooms": 0.0,
        "area-elevators": 0.0,
        "area-staircases": 0.0,
        "maximum-dining-table": 19.12973585330693,
        "maximum-balcony-area": 0.0,
        "has-kitchen-window": 1,
        "number-of-bathtubs": 1.0,
        "number-of-showers": 0.0,
        "number-of-toilets": 2.0,
        "net-area-reduced-loggias": 107.98456598622386,
        "net-area": 107.98456598622386,
        "net-area-no-corridors": 96.05064364399443,
        "net-area-no-corridors-reduced-loggias": 96.05064364399443,
        "area-sia416-FF": 0.17104372429342657,
        "area-sia416-HNF": 107.98456598622386,
        "area-sia416-NNF": 0.0,
        "area-sia416-VF": 0.0,
        "area-sia416-ANF": 0.0,
    }
    assert not DeepDiff(
        expected_basic_features, result, ignore_order=True, significant_digits=2
    )


class TestCompetitionScheme:
    @staticmethod
    def test_competition_includes_offices_as_net_area():
        fake_layout = _generate_dummy_layout(area_type=AreaType.OFFICE)
        res = CustomValuatorBasicFeatures2().net_area(layouts=[fake_layout])
        expected_area = list(fake_layout.areas)[0].footprint.area

        assert res == {
            "net-area-reduced-loggias": expected_area,
            "net-area": expected_area,
            "net-area-no-corridors": expected_area,
            "net-area-no-corridors-reduced-loggias": expected_area,
        }


def test_basic_feature_unified_classification(
    layout_scaled_classified_wo_db_conn, fixtures_path
):
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=7641)
    basic_features = CustomValuatorBasicFeatures2().get_basic_features(
        unit_id_unit_layout={1: layout}
    )

    expected_basic_features = {
        "area-balconies": 28.42498773942851,
        "area-bathrooms": 0.0,
        "area-corridors": 0.0,
        "area-elevators": 0.0,
        "area-kitchens": 0.0,
        "area-loggias": 0.0,
        "area-rooms": 353.30117584605415,
        "area-shafts": 0.0,
        "area-sia416-ANF": 28.42498773942851,
        "area-sia416-FF": 0.0,
        "area-sia416-HNF": 353.30117584605415,
        "area-sia416-NNF": 0.0,
        "area-sia416-VF": 30.362514546248953,
        "area-staircases": 8.958699999999993,
        "area-storage_rooms": 0.0,
        "area-sunrooms": 0.0,
        "has-kitchen-window": 0,
        "maximum-balcony-area": 7.811564123717329,
        "maximum-dining-table": 0.0,
        "net-area": 353.30117584605415,
        "net-area-no-corridors": 374.70504409751373,
        "net-area-no-corridors-reduced-loggias": 374.70504409751373,
        "net-area-reduced-loggias": 374.70504409751373,
        "number-of-balconies": 4.0,
        "number-of-bathrooms": 0.0,
        "number-of-bathtubs": 0.0,
        "number-of-corridors": 0.0,
        "number-of-kitchens": 0.0,
        "number-of-loggias": 0.0,
        "number-of-rooms": 6.0,
        "number-of-showers": 0.0,
        "number-of-storage-rooms": 0.0,
        "number-of-sunrooms": 0.0,
        "number-of-toilets": 0.0,
    }
    assert not DeepDiff(expected_basic_features, basic_features, significant_digits=3)
