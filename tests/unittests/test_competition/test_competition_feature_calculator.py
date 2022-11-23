import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pytest
from deepdiff import DeepDiff
from shapely.geometry import Polygon, box

from brooks import SpaceConnector
from brooks.classifications import CLASSIFICATIONS, UnifiedClassificationScheme
from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType, SIACategory
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.competition_constants import (
    COMPETITION_SIZES_MARGIN,
    SERVICE_ROOM_TYPES,
)
from common_utils.constants import SEASONS, UNIT_USAGE, VIEW_DIMENSION
from common_utils.exceptions import CompetitionFeaturesValueError
from handlers.competition import CompetitionFeaturesCalculator
from simulations.suntimes.suntimes_handler import SuntimesHandler
from tests.constants import CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3, CLIENT_ID_5

dummy_footprint = box(0, 0, 1, 1)


def make_layout_with_2_rooms(
    area_types: List[AreaType] = None,
    areas_share_a_wall: bool = False,
    areas_distance: float = 1,
):
    layout = SimLayout()
    room_1_footprint = box(0, 0, 1, 1)
    room_2_footprint = box(areas_distance + 1, 0, areas_distance + 2, 1)

    if area_types is None:
        area_types = [AreaType.ROOM, AreaType.ROOM]

    for footprint, area_type in zip([room_1_footprint, room_2_footprint], area_types):
        space = SimSpace(footprint=footprint)
        area = SimArea(footprint=footprint, area_type=area_type)
        area.db_area_id = uuid.uuid4()
        space.areas.add(area)
        layout.spaces.add(space)

    if areas_share_a_wall:
        shared_wall_footprint = box(0, 0, areas_distance + 2, 0.1)
        shared_wall = SimSeparator(
            footprint=shared_wall_footprint, separator_type=SeparatorType.WALL
        )
        layout.separators.add(shared_wall)

    return layout


@pytest.mark.parametrize(
    "areas_share_a_wall, areas_distance, expected_result",
    [(True, 5.0, True), (False, 4.9, False), (True, 5.8, False)],
)
def test_area_is_connected_by_wall(areas_share_a_wall, areas_distance, expected_result):
    layout = make_layout_with_2_rooms(
        areas_share_a_wall=areas_share_a_wall, areas_distance=areas_distance
    )
    areas = list(layout.areas)
    result = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).area_is_connected_by_wall(
        area=areas[0], layout=layout, areas_of_interest=[areas[1]], max_distance=5.0
    )
    assert result == expected_result


class TestReduitWithWaterConnection:
    @staticmethod
    def make_layout_with_storeroom(
        area_type_nearby: AreaType = AreaType.ROOM,
        distance_to_area_nearby: float = 1.0,
    ):
        layout = make_layout_with_2_rooms(
            areas_share_a_wall=True, areas_distance=distance_to_area_nearby
        )
        areas = list(layout.areas)

        # washing machine area
        areas[0]._type = AreaType.STOREROOM

        # area type nearby
        areas[1]._type = area_type_nearby

        return layout

    def _get_ratio(self, layouts, max_rectangle_footprint):
        return CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).reduit_with_water_connection(
            apartment_db_area_ids={
                fake_client_id: [area.db_area_id for area in layout.areas]
                for fake_client_id, layout in enumerate(layouts)
            },
            plan_layouts=layouts,
            max_rectangle_by_area_id={
                area.db_area_id: max_rectangle_footprint
                for layout in layouts
                for area in layout.areas
            },
        )

    @pytest.mark.parametrize(
        "distance_to_area_nearby,max_rectangle_footprint,expected_ratio",
        [
            (1.0, box(0, 0, 1.0, 2.0), 1.0),
            (1.0, box(0, 0, 0.9, 2.0), 0.0),
            (1.0, box(0, 0, 1.0, 1.7), 0.0),
            (1.1, box(0, 0, 1, 2), 0.0),
            # buffer of 5% (area and length)
            (1.0, box(0, 0, 1, 1.91), 1.0),
            (1.0, box(0, 0, 0.96, 2), 1.0),
        ],
    )
    def test_distance_to_water_and_min_dimension_requirement(
        self, distance_to_area_nearby, max_rectangle_footprint, expected_ratio
    ):
        # given
        # a layout with a storeroom and kitchen
        layout = self.make_layout_with_storeroom(
            area_type_nearby=AreaType.KITCHEN,
            distance_to_area_nearby=distance_to_area_nearby,
        )

        # when
        ratio = self._get_ratio(
            max_rectangle_footprint=max_rectangle_footprint, layouts=[layout]
        )

        # then
        assert ratio == expected_ratio

    @pytest.mark.parametrize(
        "area_type_nearby,expected_ratio",
        [
            (
                [
                    AreaType.KITCHEN_DINING,
                    AreaType.KITCHEN,
                    AreaType.BATHROOM,
                    AreaType.SHAFT,
                ],
                1.0,
            ),
            (
                set(a for a in AreaType)
                - {
                    AreaType.KITCHEN_DINING,
                    AreaType.KITCHEN,
                    AreaType.BATHROOM,
                    AreaType.SHAFT,
                },
                0.0,
            ),
        ],
    )
    def test_area_types_with_water_connection(self, area_type_nearby, expected_ratio):
        # given
        # a layout with a storeroom and kitchen
        layouts = [
            self.make_layout_with_storeroom(
                area_type_nearby=area_type,
                distance_to_area_nearby=1.0,
            )
            for area_type in area_type_nearby
        ]

        # when
        ratio = self._get_ratio(
            max_rectangle_footprint=box(0, 0, 2, 2), layouts=layouts
        )

        # then
        assert ratio == expected_ratio

    def test_ratio(self):
        # given
        layout_feature_failed = self.make_layout_with_storeroom(
            area_type_nearby=AreaType.ROOM
        )
        layout_feature_fulfilled = self.make_layout_with_storeroom(
            area_type_nearby=AreaType.KITCHEN
        )

        # when
        ratio = self._get_ratio(
            max_rectangle_footprint=box(0, 0, 2, 2),
            layouts=[layout_feature_failed, layout_feature_fulfilled],
        )

        # then
        assert ratio == 0.5

    def test_reduit_with_water_connection_no_data(self):
        with pytest.raises(CompetitionFeaturesValueError):
            CompetitionFeaturesCalculator(
                UnifiedClassificationScheme()
            ).reduit_with_water_connection(
                apartment_db_area_ids={}, plan_layouts=[], max_rectangle_by_area_id={}
            )


@pytest.mark.parametrize(
    "annotation_plan_id, expected_ratio",
    [(863, 0.15897), (2494, 0.18489), (7641, 1)],
)
def test_private_outdoor_areas_ratio(
    layout_scaled_classified_wo_db_conn, annotation_plan_id, expected_ratio
):
    """
    3332 -> Has a loggia and no balcony
    863 -> has balcony, no loggia
    7641 -> has no balcony/loggia
    """
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=annotation_plan_id)

    ratio = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).private_outdoor_areas_percent(units_layouts=[layout])
    assert ratio == pytest.approx(expected_ratio, abs=1e03)


def test_private_outdoor_areas_ratio_no_data():
    with pytest.raises(CompetitionFeaturesValueError):
        CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).private_outdoor_areas_percent(units_layouts=[])


class TestCompetitionApartmentsWithOutdoor:
    @pytest.mark.parametrize(
        "groups, expected",
        [
            ([[2494], [2494]], 0.0),
            ([[3332, 863], [2494]], 0.5),
            ([[3332, 863], [863]], 1.0),
        ],
    )
    def test_grouped(self, layout_scaled_classified_wo_db_conn, groups, expected):
        """Try different combinations of layouts grouped by clients_ids.
        3332 -> Has a loggia and no balcony
        863 -> has balcony, no loggia
        7641 -> has no balcony/loggia
        """
        units_layouts = {
            i: [
                layout_scaled_classified_wo_db_conn(
                    annotation_plan_id=annotation_plan_id
                )
                for annotation_plan_id in group
            ]
            for i, group in enumerate(groups)
        }
        layouts_per_apartment = {
            f"client_{i}": {j: layout for j, layout in enumerate(layouts)}
            for i, layouts in units_layouts.items()
        }

        average = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).apartments_with_outdoor_percentage(
            layouts_per_apartment=layouts_per_apartment
        )

        assert average == expected


class TestCompetitionSumAreaTypesPerApt:
    @pytest.mark.parametrize(
        "area_types, expected",
        [
            ([AreaType.KITCHEN, AreaType.LIVING_DINING], 2.0),
            ([AreaType.STOREROOM, AreaType.LIVING_DINING], 1.0),
            ([AreaType.STOREROOM, AreaType.ROOM], 0.0),
            ([AreaType.KITCHEN, AreaType.ROOM], 1.0),
            ([AreaType.KITCHEN, AreaType.KITCHEN], 2.0),
            ([AreaType.LIVING_DINING, AreaType.KITCHEN], 2.0),
        ],
    )
    def test_sum_area_types_per_apt_type(self, area_types, expected):
        layout = make_layout_with_2_rooms(area_types=area_types)
        result = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).sum_specific_area_sizes_by_apt_type(
            layouts_by_apt_type={"2.5": [[layout]]},
            area_types={
                AreaType.KITCHEN,
                AreaType.KITCHEN_DINING,
                AreaType.DINING,
                AreaType.LIVING_DINING,
            },
        )
        assert result["2.5"][0] == pytest.approx(expected, abs=1e-03)

    @pytest.mark.parametrize(
        "area_types, expected",
        [
            ([AreaType.KITCHEN, AreaType.LIVING_DINING], 0.0),
            ([AreaType.BALCONY, AreaType.LIVING_DINING], 1.0),
            ([AreaType.GARDEN, AreaType.LOGGIA], 2.0),
            ([AreaType.KITCHEN, AreaType.ROOM], 0.0),
        ],
    )
    def test_sum_area_types_per_apt(self, area_types, expected):
        layout = make_layout_with_2_rooms(area_types=area_types)
        result = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).sum_specific_area_sizes_by_apt(
            layouts_per_apartment={"1": {1: layout}},
            area_types=CLASSIFICATIONS.UNIFIED.value().get_children(SIACategory.ANF),
        )
        assert result["1"] == pytest.approx(expected, abs=1e-03)


@pytest.mark.parametrize(
    "annotation_plan_ids, input_data, expected",
    [
        ([332], [2, 4, 6] * 20, 4.0),
        ([2494], [0] * 58, 0.0),
        ([2494, 332], [3, 5, 7] * 20, 5.0),
    ],
)
def test_generosity_open_space_over_largest_square(
    mocker,
    layout_scaled_classified_wo_db_conn,
    annotation_plan_ids,
    expected,
    input_data,
):
    layouts = [
        layout_scaled_classified_wo_db_conn(annotation_plan_id=annotation_plan_id)
        for annotation_plan_id in annotation_plan_ids
    ]

    mocker.patch.object(Polygon, "area", mocker.PropertyMock(side_effect=input_data))
    max_rectangle_by_area_id = {
        area.db_area_id: Polygon() for layout in layouts for area in layout.areas
    }

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).average_largest_rectangle_all_areas(
        units_layouts=layouts, max_rectangle_by_area_id=max_rectangle_by_area_id
    )
    assert value == pytest.approx(expected, abs=0.2)


@pytest.mark.parametrize(
    "annotation_plan_ids, expected",
    [
        (
            [6380],
            13.27,
        ),
        ([2494], 0.0),
        (
            [2494, 6380],
            13.27,
        ),
    ],
)
def test_private_outdoor_spaces_spaciousness(
    layout_scaled_classified_wo_db_conn,
    annotation_plan_ids,
    expected,
):
    layouts = [
        layout_scaled_classified_wo_db_conn(annotation_plan_id=annotation_plan_id)
        for annotation_plan_id in annotation_plan_ids
    ]

    max_rectangle_by_area_id = {}
    for layout in layouts:
        for area in layout.areas:
            max_rectangle_by_area_id[area.db_area_id] = area.footprint

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).private_outdoor_spaces_spaciousness(
        units_layouts=layouts, max_rectangle_by_area_id=max_rectangle_by_area_id
    )
    assert value == pytest.approx(expected, abs=0.2)


class TestDarkestBrightestRoom:
    @staticmethod
    def make_layout(areas_config):
        """Creates a layout db_area_id and area_type as per areas_config"""
        spaces = set()
        for db_area_id, area_type in areas_config.items():
            space = SimSpace(footprint=dummy_footprint)
            area = SimArea(footprint=dummy_footprint, area_type=area_type)
            area.db_area_id = db_area_id
            space.areas.add(area)
            spaces.add(space)
        return SimLayout(spaces=spaces)

    @pytest.fixture
    def layout_with_living_and_bedrooms(self):
        return self.make_layout(
            {
                "dark": AreaType.ROOM,
                "bright": AreaType.BEDROOM,
                "super_bright": AreaType.BATHROOM,
                "super_dark": AreaType.STOREROOM,
            }
        )

    @pytest.fixture
    def layout_no_living_and_bedrooms(self):
        return self.make_layout(
            {
                "dark": AreaType.BATHROOM,
                "bright": AreaType.BATHROOM,
                "super_bright": AreaType.BATHROOM,
                "super_dark": AreaType.STOREROOM,
            }
        )

    @staticmethod
    def make_sim_data(summer_bright, winter_bright, summer_dark, winter_dark):
        summer_key = SuntimesHandler.get_sun_key_from_datetime(
            datetime(2018, 6, 21, tzinfo=timezone.utc)
        )
        winter_key = SuntimesHandler.get_sun_key_from_datetime(
            datetime(2018, 12, 21, tzinfo=timezone.utc)
        )
        return {
            "dark": {
                summer_key: {"median": summer_dark},
                winter_key: {"median": winter_dark},
            },
            "bright": {
                summer_key: {"median": summer_bright},
                winter_key: {"median": winter_bright},
            },
            "super_bright": {
                summer_key: {"median": 10000},
                winter_key: {"median": 5000},
            },
            "super_dark": {
                summer_key: {"median": -10000},
                winter_key: {"median": -5000},
            },
        }

    def test_avg_darkest_brightest_room(self, layout_with_living_and_bedrooms):
        # Given
        layouts_per_apartment = {
            CLIENT_ID_1: {1: layout_with_living_and_bedrooms},
            CLIENT_ID_2: {2: layout_with_living_and_bedrooms},
        }
        sun_v2_area_stats_by_apartment = {
            CLIENT_ID_1: self.make_sim_data(
                summer_bright=100, summer_dark=10, winter_bright=50, winter_dark=5
            ),
            CLIENT_ID_2: self.make_sim_data(
                summer_bright=1000, summer_dark=100, winter_bright=500, winter_dark=50
            ),
        }
        classification_schema = UnifiedClassificationScheme()

        # When
        comp_feature_handler = CompetitionFeaturesCalculator(classification_schema)
        mean_brightest_in_winter = comp_feature_handler.avg_brightest_in_winter(
            layouts_per_apartment=layouts_per_apartment,
            sun_stats_by_apartment_area=sun_v2_area_stats_by_apartment,
        )
        mean_darkest_in_summer = comp_feature_handler.avg_darkest_summer_area(
            layouts_per_apartment=layouts_per_apartment,
            sun_stats_by_apartment_area=sun_v2_area_stats_by_apartment,
        )

        # Then
        assert mean_darkest_in_summer == 55
        assert mean_brightest_in_winter == 275

    def test_avg_darkest_brightest_room_no_living_and_bedrooms(
        self, layout_no_living_and_bedrooms
    ):
        # Given
        layouts_per_apartment = {
            CLIENT_ID_1: {1: layout_no_living_and_bedrooms},
            CLIENT_ID_2: {2: layout_no_living_and_bedrooms},
        }
        sun_v2_area_stats_by_apartment = {
            CLIENT_ID_1: self.make_sim_data(
                summer_bright=100, summer_dark=10, winter_bright=50, winter_dark=5
            ),
            CLIENT_ID_2: self.make_sim_data(
                summer_bright=1000, summer_dark=100, winter_bright=500, winter_dark=50
            ),
        }
        classification_schema = UnifiedClassificationScheme()

        # When
        comp_feature_handler = CompetitionFeaturesCalculator(classification_schema)

        with pytest.raises(CompetitionFeaturesValueError):
            comp_feature_handler.avg_brightest_in_winter(
                layouts_per_apartment=layouts_per_apartment,
                sun_stats_by_apartment_area=sun_v2_area_stats_by_apartment,
            )
        with pytest.raises(CompetitionFeaturesValueError):
            comp_feature_handler.avg_darkest_summer_area(
                layouts_per_apartment=layouts_per_apartment,
                sun_stats_by_apartment_area=sun_v2_area_stats_by_apartment,
            )

    def test_avg_darkest_brightest_room_no_data(
        self,
    ):
        with pytest.raises(CompetitionFeaturesValueError):
            CompetitionFeaturesCalculator(
                UnifiedClassificationScheme()
            ).avg_brightest_in_winter(
                layouts_per_apartment={},
                sun_stats_by_apartment_area={},
            )


@pytest.mark.parametrize(
    "annotation_plan_ids,  expected",
    [
        ([332], {"GS20.00.01": 27.79092}),
        ([2494], {"GS20.00.02": 0.0}),
        ([2494, 332], {"GS20.00.02": 0.0, "GS20.00.01": 27.79092}),
    ],
)
def test_apartment_storeroom_ratio(
    annotation_plan_ids,
    expected,
    layout_scaled_classified_wo_db_conn,
):
    layouts_per_apartment = defaultdict(dict)
    for annotation_plan_id in annotation_plan_ids:
        layout = layout_scaled_classified_wo_db_conn(
            annotation_plan_id=annotation_plan_id
        )
        if annotation_plan_id == 332:
            for area in layout.areas:
                area._type = AreaType.STOREROOM
            layouts_per_apartment[CLIENT_ID_1][1] = layout
        else:
            layouts_per_apartment[CLIENT_ID_2][1] = layout

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).apartment_with_storerooms_sizes(layouts_per_apartment=layouts_per_apartment)
    assert value == pytest.approx(expected)


@pytest.mark.parametrize(
    "annotation_plan_id, expected",
    [(332, 1), (2494, 9)],
)
def test_bike_parking_count(
    annotation_plan_id, expected, layout_scaled_classified_wo_db_conn
):
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=annotation_plan_id)
    for area in layout.areas:
        for feature in area.features:
            if feature.type == FeatureType.SHAFT:
                feature._type = FeatureType.BIKE_PARKING

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).bike_parking_count(layouts=[layout])
    assert value == expected


def test_pram_and_bike_storage_room_exists(layout_scaled_classified_wo_db_conn):
    # Given
    layout = layout_scaled_classified_wo_db_conn(annotation_plan_id=2494)

    # Then
    assert not CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).any_layout_have_area_type(
        layouts=[layout], area_type=AreaType.PRAM_AND_BIKE_STORAGE_ROOM
    )

    # And when
    area = list(layout.areas)[0]
    area._type = AreaType.PRAM_AND_BIKE_STORAGE_ROOM

    # Then
    assert CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).any_layout_have_area_type(
        layouts=[layout], area_type=AreaType.PRAM_AND_BIKE_STORAGE_ROOM
    )


@pytest.mark.parametrize(
    "annotation_plans_id, expected",
    [
        ([332, 2494], {"13.0": 0.5, "9.0": 0.5}),
        ([4976, 6951, 332, 332], {"11.0": 0.25, "13.0": 0.5, "9.0": 0.25}),
    ],
)
def test_apartment_types_percentage(
    annotation_plans_id, expected, layout_scaled_classified_wo_db_conn
):
    layouts_per_apartment = defaultdict(dict)
    for plan_id, client_id in zip(
        annotation_plans_id, (CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3, CLIENT_ID_5)
    ):
        layouts_per_apartment[client_id][1] = layout_scaled_classified_wo_db_conn(
            plan_id
        )

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).apartment_types_percentage(layouts_per_apartment=layouts_per_apartment)

    assert value == pytest.approx(expected)


@pytest.mark.parametrize(
    "annotation_plans_id, expected",
    [
        (
            [332, 2494],
            [
                ("13.0", 447.95500836723437),
                ("9.0", 517.3991689859538),
            ],
        ),
        (
            [4976, 6951, 332, 332],
            [
                ("9.0", 212.54390372377807),
                ("11.0", 302.7446173690233),
                ("13.0", 447.9550083672345),
                ("13.0", 447.9550083672345),
            ],
        ),
    ],
)
def test_apartment_types_area(
    annotation_plans_id, expected, layout_scaled_classified_wo_db_conn
):
    layouts_per_apartment = defaultdict(dict)
    for plan_id, client_id in zip(
        annotation_plans_id, (CLIENT_ID_1, CLIENT_ID_2, CLIENT_ID_3, CLIENT_ID_5)
    ):
        layouts_per_apartment[client_id][1] = layout_scaled_classified_wo_db_conn(
            plan_id
        )
    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).apartment_types_area(layouts_per_apartment=layouts_per_apartment)

    assert not DeepDiff(value, expected, ignore_order=True, significant_digits=4)


class TestBathtubShowerDistribution:
    @staticmethod
    def make_layout(number_of_rooms, bathrooms):
        # add number of rooms
        spaces = set()
        for _ in range(number_of_rooms):
            space = SimSpace(footprint=dummy_footprint)
            area = SimArea(footprint=dummy_footprint)
            area._type = AreaType.ROOM
            space.areas.add(area)
            spaces.add(space)

        # add bathrooms
        bathroom_features = [
            FeatureType.SHOWER,
            FeatureType.TOILET,
            FeatureType.SINK,
            FeatureType.BATHTUB,
        ]
        for bathroom in bathrooms:
            space = SimSpace(footprint=dummy_footprint)
            bathroom_area = SimArea(
                footprint=dummy_footprint, area_type=AreaType.BATHROOM
            )
            for feature_type, number_of_features in zip(bathroom_features, bathroom):
                for _ in range(number_of_features):
                    bathroom_area.features.add(
                        SimFeature(footprint=dummy_footprint, feature_type=feature_type)
                    )

            space.areas.add(bathroom_area)
            spaces.add(space)

        return SimLayout(spaces=spaces)

    def test_shower_bathtub_distribution(self):
        layouts = [
            self.make_layout(number_of_rooms, bathrooms)
            for number_of_rooms, bathrooms in [
                (3, [(1, 1, 1, 0), (0, 1, 1, 1)]),
                (3, [(1, 1, 1, 1), (0, 1, 1, 0)]),
                (1, [(1, 1, 1, 0)]),
                (1, [(1, 1, 1, 0)]),
            ]
        ]

        value = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).bathrooms_features_distribution(
            layouts_per_apartment={str(i): {i: l} for i, l in enumerate(layouts)}
        )

        assert not DeepDiff(
            dict(value),
            {
                "3.0": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                            {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                        ],
                        "percentage": 0.5,
                    },
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                            {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                        ],
                        "percentage": 0.5,
                    },
                ],
                "1.0": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}
                        ],
                        "percentage": 1.0,
                    }
                ],
            },
            ignore_order=True,
        )

    def test_shower_bathtub_distribution_with_duplicated_features_count_1_only(self):
        layouts = [
            self.make_layout(number_of_rooms, bathrooms)
            for number_of_rooms, bathrooms in [
                (3, [(1, 1, 2, 0), (0, 1, 1, 1)]),
                (3, [(1, 2, 1, 2), (0, 1, 1, 0)]),
                (1, [(1, 2, 2, 0)]),
                (1, [(1, 2, 1, 0)]),
            ]
        ]

        value = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).bathrooms_features_distribution(
            layouts_per_apartment={str(i): {i: l} for i, l in enumerate(layouts)}
        )

        assert not DeepDiff(
            dict(value),
            {
                "3.0": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                            {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                        ],
                        "percentage": 0.5,
                    },
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 1},
                            {"SHOWER": 0, "TOILET": 1, "SINK": 1, "BATHTUB": 0},
                        ],
                        "percentage": 0.5,
                    },
                ],
                "1.0": [
                    {
                        "features": [
                            {"SHOWER": 1, "TOILET": 1, "SINK": 1, "BATHTUB": 0}
                        ],
                        "percentage": 1.0,
                    }
                ],
            },
            ignore_order=True,
        )

    @pytest.mark.parametrize(
        "conf, expected",
        [
            ((1, [(1, 0, 0, 0)]), {"1.0": [[SERVICE_ROOM_TYPES.BATHROOM.name]]}),
            ((1, []), {"1.0": [[]]}),
            (
                (3, [(1, 0, 0, 0), (1, 0, 0, 0)]),
                {
                    "3.0": [
                        [
                            SERVICE_ROOM_TYPES.BATHROOM.name,
                            SERVICE_ROOM_TYPES.BATHROOM.name,
                        ]
                    ]
                },
            ),
            (
                (4, [(1, 0, 0, 1), (0, 0, 0, 1), (0, 1, 1, 0)]),
                {
                    "4.0": [
                        [
                            SERVICE_ROOM_TYPES.BATHROOM.name,
                            SERVICE_ROOM_TYPES.BATHROOM.name,
                            SERVICE_ROOM_TYPES.TOILET.name,
                        ],
                    ]
                },
            ),
        ],
    )
    def test_shower_bathroom_distribution(self, conf, expected):
        layout = self.make_layout(*conf)
        value = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).bathrooms_toilets_distribution(
            layouts_per_apartment={"client_id": {1: layout}}
        )
        assert not DeepDiff(value, expected, ignore_order=True)


@pytest.mark.parametrize(
    "layouts_room_configuration, expected",
    [([1], True), ([0], False), ([0, 1], False), ([1, 1], True)],
)
@pytest.mark.parametrize(
    "room_type",
    [AreaType.BATHROOM, AreaType.STOREROOM],
)
def test_have_area(
    layouts_room_configuration, room_type, expected, layout_scaled_classified_wo_db_conn
):
    layouts = []
    for bathroom_count in layouts_room_configuration:
        space = SimSpace(footprint=dummy_footprint)
        area = SimArea(footprint=dummy_footprint)
        area._type = AreaType.ROOM
        space.areas.add(area)
        for _ in range(bathroom_count):
            area = SimArea(footprint=dummy_footprint)
            area._type = room_type
            space.areas.add(area)
        layouts.append(SimLayout(spaces={space}))

    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).all_layout_have_area_type(layouts=layouts, area_type=room_type)
    assert value == expected


@pytest.mark.parametrize(
    "annotation_plans_id, expected",
    [([332, 2494], 38.2476), ([4976, 6951], 28.546)],
)
@pytest.mark.parametrize("area_type", [AreaType.ROOM, AreaType.NOT_DEFINED])
def test_max_area_size(
    annotation_plans_id, area_type, expected, layout_scaled_classified_wo_db_conn
):
    layouts = [
        layout_scaled_classified_wo_db_conn(annotation_plan_id=plan_id)
        for plan_id in annotation_plans_id
    ]

    value = CompetitionFeaturesCalculator(UnifiedClassificationScheme()).max_area_size(
        layouts=layouts, area_types={area_type}
    )
    if area_type == AreaType.NOT_DEFINED:
        expected = None
    assert value == pytest.approx(expected, abs=0.01)


def test_max_area_size_no_layouts_should_return_none():
    value = CompetitionFeaturesCalculator(UnifiedClassificationScheme()).max_area_size(
        layouts=[], area_types={AreaType.ROOM}
    )
    assert value is None


class TestJanitorWCAdjacentOrAdjoining:
    @staticmethod
    def _add_space(
        layout: SimLayout,
        footprint,
        area_type,
        add_opening_type=None,
        features=None,
        opening_separator_index=0,
    ):
        # create space with area
        area = SimArea(footprint=footprint, area_type=area_type)
        for feature in features or []:
            area.features.add(feature)

        space = SimSpace(footprint=footprint)
        space.areas.add(area)

        # add walls and door
        minx, miny, max_x, maxy = footprint.bounds

        walls = [
            SimSeparator(footprint=footprint, separator_type=SeparatorType.WALL)
            for footprint in [
                # left
                box(minx, miny, minx + 0.1, maxy),
                # bottom
                box(minx, miny, max_x, miny + 0.1),
                # right
                box(max_x - 0.1, miny, max_x, maxy),
                # top
                box(minx, maxy - 0.1, max_x, maxy),
            ]
        ]
        if add_opening_type:
            wall = walls[opening_separator_index]
            wall_bounds = wall.footprint.bounds
            wall.openings.add(
                SimOpening(
                    # add door to one side of area with reduced Y coordinates
                    footprint=box(
                        wall_bounds[0] - 0.05,
                        wall_bounds[1] + 0.05,
                        wall_bounds[2] + 0.05,
                        wall_bounds[3] - 0.05,
                    ),
                    opening_type=add_opening_type,
                    height=(0, 2.6),
                    separator=wall,
                    separator_reference_line=get_center_line_from_rectangle(
                        wall.footprint
                    )[0],
                )
            )

        layout.spaces.add(space)
        layout.separators.update(walls)

        return space

    def make_layout(
        self,
        office_in_layout: bool = False,
        bathroom_in_layout: bool = False,
        bathroom_accessible: bool = True,
        bathroom_distance: int = 5,
        bathroom_has_toilet: bool = True,
        position_shift: float = 0.0,
        opening_separator_index: int = 0,
    ):
        layout = SimLayout()
        bathroom_distance += position_shift

        # add the main space
        area_type = AreaType.ROOM
        if office_in_layout:
            area_type = AreaType.OFFICE
        self._add_space(
            layout=layout,
            footprint=box(position_shift, 0, bathroom_distance, 1),
            add_opening_type=OpeningType.ENTRANCE_DOOR,
            opening_separator_index=opening_separator_index,
            area_type=area_type,
        )

        # optionally add a bathroom with toilet to the right of the corridor
        if bathroom_in_layout:
            bathroom_footprint = box(bathroom_distance, 0, bathroom_distance + 1, 1)

            # Optionally add a toilet feature
            features = None
            if bathroom_has_toilet:
                toilet_footprint = box(
                    bathroom_distance + 0.2, 0.2, bathroom_distance + 0.8, 0.8
                )
                features = [
                    SimFeature(
                        footprint=toilet_footprint, feature_type=FeatureType.TOILET
                    )
                ]

            # Optionally add an opening
            opening_type = None
            if bathroom_accessible:
                opening_type = OpeningType.DOOR

            self._add_space(
                layout=layout,
                footprint=bathroom_footprint,
                area_type=AreaType.BATHROOM,
                add_opening_type=opening_type,
                features=features,
                opening_separator_index=opening_separator_index,
            )

        return layout

    def test_find_connected_public_spaces_recursively(self):
        # Given a layout with 2 connected corridors
        layout = SimLayout()
        corridor_1 = self._add_space(
            layout=layout,
            footprint=box(0, 0, 1, 1),
            area_type=AreaType.CORRIDOR,
            add_opening_type=OpeningType.ENTRANCE_DOOR,
        )
        corridor_2 = self._add_space(
            layout=layout,
            footprint=box(1, 0, 2, 1),
            area_type=AreaType.CORRIDOR,
            add_opening_type=OpeningType.DOOR,
        )
        space_connections, _ = SpaceConnector.get_connected_spaces_using_doors(
            doors=layout.openings,
            spaces_or_areas=layout.spaces,
        )
        public_spaces = {corridor_1.id: corridor_1, corridor_2.id: corridor_2}

        for space_id in public_spaces.keys():
            # When
            connected_spaces = set(
                CompetitionFeaturesCalculator(
                    UnifiedClassificationScheme()
                )._find_connected_public_spaces_recursively(
                    space_id=space_id,
                    public_spaces=public_spaces,
                    space_connections=space_connections,
                )
            )
            # Then
            assert connected_spaces == {corridor_1, corridor_2}

    @pytest.mark.parametrize(
        "bathroom_in_layout, bathroom_distance, bathroom_accessible, bathroom_has_toilet, expected_result",
        [
            (
                # the bathroom must be in public space
                True,
                1,
                True,
                True,
                True,
            ),
            (
                # the bathroom must have a toilet
                True,
                1,
                True,
                False,
                False,
            ),
            (
                # the bathroom must be connected
                True,
                1,
                False,
                True,
                False,
            ),
            (
                # the bathroom MUST EXIST!!!
                False,
                1,
                True,
                True,
                False,
            ),
            (
                # the bathroom must not be more distant than 10 meters
                True,
                11,
                True,
                True,
                False,
            ),
        ],
    )
    def test_wc_is_in_public_space(
        self,
        bathroom_in_layout,
        bathroom_distance,
        bathroom_accessible,
        bathroom_has_toilet,
        expected_result,
    ):
        private_layout = self.make_layout(opening_separator_index=2)
        public_layout = self.make_layout(
            position_shift=5.0,
            bathroom_in_layout=bathroom_in_layout,
            bathroom_distance=bathroom_distance,
            bathroom_accessible=bathroom_accessible,
            bathroom_has_toilet=bathroom_has_toilet,
        )
        value = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        )._wc_is_in_public_space(layout=private_layout, public_layout=public_layout)

        assert value is expected_result

    @pytest.mark.parametrize(
        "janitor_layouts_config, public_layout_config, expected_result",
        [
            (
                # the janitor toilet may be enclosed in the janitor office layout
                [{"office_in_layout": True, "bathroom_in_layout": True}],
                {"bathroom_in_layout": False},
                True,
            ),
            (
                # the janitor toilet may be in public space
                [{"office_in_layout": True, "bathroom_in_layout": False}],
                {"bathroom_in_layout": True},
                True,
            ),
            (
                # the janitor toilet MUST EXIST!!!
                [{"office_in_layout": True, "bathroom_in_layout": False}],
                {"bathroom_in_layout": False},
                False,
            ),
            (
                # ALL janitor office layouts have to have a toilet
                [
                    {"office_in_layout": True, "bathroom_in_layout": False},
                    {"office_in_layout": True, "bathroom_in_layout": True},
                ],
                {"bathroom_in_layout": False},
                False,
            ),
            (
                # ONLY janitor office layouts have to have a toilet
                [
                    {"office_in_layout": True, "bathroom_in_layout": True},
                    {"office_in_layout": False, "bathroom_in_layout": False},
                ],
                {"bathroom_in_layout": False},
                True,
            ),
        ],
    )
    def test_janitor_wc_adjacent_or_adjoining(
        self, janitor_layouts_config, public_layout_config, expected_result
    ):
        janitor_layouts = {
            1: [
                self.make_layout(**config, position_shift=6)
                for config in janitor_layouts_config
            ]
        }
        public_layouts = {1: self.make_layout(**public_layout_config)}

        value = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).janitor_wc_adjacent_or_adjoining(
            janitor_layouts=janitor_layouts, public_layouts=public_layouts
        )

        assert value is expected_result


@pytest.mark.parametrize(
    "area_types, areas_share_a_wall, areas_distance, expected",
    [
        ([AreaType.STOREROOM, AreaType.KITCHEN], True, 0.9, True),
        ([AreaType.STOREROOM, AreaType.ROOM], True, 0.9, False),
        ([AreaType.STOREROOM, AreaType.KITCHEN], False, 0.9, False),
        ([AreaType.STOREROOM, AreaType.KITCHEN], True, 1.1, False),
    ],
)
def test_janitor_storerooms_water_connections_available(
    area_types, areas_share_a_wall, areas_distance, expected
):
    layout = make_layout_with_2_rooms(
        areas_share_a_wall=areas_share_a_wall,
        areas_distance=areas_distance,
        area_types=area_types,
    )
    value = CompetitionFeaturesCalculator(
        UnifiedClassificationScheme()
    ).janitor_storerooms_water_connections_available(
        janitor_layouts=[layout], plan_layouts=[layout]
    )
    assert value == expected


class TestSpaceIsNavigable:
    @pytest.mark.parametrize(
        "min_corr, expected", [(1.2, True), (1.5, True), (2.5, False)]
    )
    def test_navigable_room(self, min_corr, expected):
        """
        A 2m x 2m space with a door at the left side:
        +-------+
        |       |
        |       |
        +-------+
        """
        assert (
            CompetitionFeaturesCalculator(UnifiedClassificationScheme()).is_navigable(
                space_footprint=box(0, 0, 2, 2),
                opening_footprints=[box(-0.1, 0.8, 0.1, 1.6)],
                corridor_width=min_corr,
            )
            == expected
        )

    @pytest.mark.parametrize(
        "min_corr, expected", [(1.2, True), (1.5, True), (2.5, True), (4, False)]
    )
    def test_navigable_room_with_extra_area(self, min_corr, expected):
        """
        A 4m x 4m room (door at the left!) with a 1m x 1m extra area:
        +-------+
        |       |
        |       +---+
        |           |
        +-----------+
        """
        assert (
            CompetitionFeaturesCalculator(UnifiedClassificationScheme()).is_navigable(
                space_footprint=box(0, 0, 4, 4).union(box(4, 0, 5, 1)),
                opening_footprints=[box(-0.1, 0.8, 0.1, 1.6)],
                corridor_width=min_corr,
            )
            == expected
        )

    @pytest.mark.parametrize("min_corr, expected", [(1.2, False), (0.5, True)])
    def test_too_small_room(self, min_corr, expected):
        """
        A 1m x 1m space with a door at the left side:
        +-------+
        |       |
        |       |
        +-------+
        """
        assert (
            CompetitionFeaturesCalculator(UnifiedClassificationScheme()).is_navigable(
                space_footprint=box(0, 0, 1, 1),
                opening_footprints=[box(-0.1, 0.2, 0.1, 0.8)],
                corridor_width=min_corr,
            )
            == expected
        )

    @pytest.mark.parametrize(
        "min_corr, expected", [(1.2, False), (1.5, False), (1, True)]
    )
    def test_corridor_navigable(self, min_corr, expected):
        """
        A 4m x 4m room with a 1m x 1m corridor with a door e.g:
        +-------+
        |       |
        |       +---+
        |
        +-----------+
        (space is not navigable because the navigable area is not intersecting with the door)
        """
        assert (
            CompetitionFeaturesCalculator(UnifiedClassificationScheme()).is_navigable(
                space_footprint=box(0, 0, 4, 4).union(box(4, 0, 5, 1)),
                opening_footprints=[box(4.9, 0.2, 5.1, 0.8)],
                corridor_width=min_corr,
            )
            == expected
        )

    @pytest.mark.parametrize(
        "min_corr, expected", [(1.2, False), (1.5, False), (1, True)]
    )
    def test_corridor_not_navigable_case_2(self, min_corr, expected):
        """
        Two 4m x 4m areas connected by a 1m x 1m corridor:
        +-------+   +-------+
        |       |   |       |
        |       +---+       |
        |                   |
        +-------------------+
        (not navigable because the navigable area is split into 2 parts)
        """
        assert (
            CompetitionFeaturesCalculator(UnifiedClassificationScheme()).is_navigable(
                space_footprint=box(0, 0, 4, 4)
                .union(box(4, 0, 5, 1))
                .union(box(5, 0, 9, 4)),
                opening_footprints=[box(-0.1, 0.8, 0.1, 1.6)],
                corridor_width=min_corr,
            )
            == expected
        )


class TestWithFeatures:
    @staticmethod
    def make_layout(
        feature_footprint: Polygon, feature_type: FeatureType = FeatureType.ELEVATOR
    ) -> SimLayout:
        footprint = box(-10, -10, 10, 10)
        space = SimSpace(footprint=footprint)
        area = SimArea(footprint=footprint, area_type=AreaType.ROOM)
        space.areas.add(area)
        if feature_footprint:
            area.features.add(
                SimFeature(footprint=feature_footprint, feature_type=feature_type)
            )
        return SimLayout(spaces={space})

    @pytest.mark.parametrize(
        "elevator_footprint, expected_result",
        [
            (box(0, 0, 1.1, 1.4), True),
            (box(0, 0, 1.1, 1.3), False),
            (box(0, 0, 1.0, 1.4), False),
            # with 5% buffer
            (box(0, 0, 1.1 * 0.95, 1.4 * COMPETITION_SIZES_MARGIN), True),
            (None, False),
        ],
    )
    def test_minimum_elevator_dimensions(
        self, elevator_footprint: Polygon, expected_result
    ):
        layout = self.make_layout(elevator_footprint)
        result = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).minimum_elevator_dimensions(plans=[{"plan_layout": layout}])
        assert result is expected_result

    @pytest.mark.parametrize(
        "features_types, expected",
        [
            ([], 0.0),
            ([FeatureType.WASHING_MACHINE], 1.0),
            ([FeatureType.WASHING_MACHINE, FeatureType.SINK], 0.5),
            ([FeatureType.ELEVATOR, FeatureType.SINK], 0.0),
            (
                [
                    FeatureType.ELEVATOR,
                    FeatureType.SINK,
                    FeatureType.SHOWER,
                    FeatureType.WASHING_MACHINE,
                ],
                0.25,
            ),
        ],
    )
    def test_check_feature_is_present_per_apt_percentage(
        self, features_types, expected
    ):
        layouts = [
            self.make_layout(
                feature_type=feature_type, feature_footprint=box(0, 0, 1, 1)
            )
            for feature_type in features_types
        ]
        layouts_per_apartment = {str(i): {1: layouts[i]} for i in range(len(layouts))}

        result = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        ).check_feature_is_present_per_apt_percentage(
            layouts_per_apartment=layouts_per_apartment,
            targe_feature_type=FeatureType.WASHING_MACHINE,
        )
        assert result == pytest.approx(expected)


class TestRatioOfNavigableSpacesArea:
    @staticmethod
    def make_layout(space_footprint):
        space = SimSpace(footprint=space_footprint)
        space.areas.add(SimArea(footprint=space_footprint, area_type=AreaType.ROOM))
        return SimLayout(spaces={space})

    def test_ratio_of_navigable_spaces_area(self):
        feature_calculator = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        )

        not_navigable = self.make_layout(box(0, 0, 1, 1))
        navigable = self.make_layout(box(0, 0, 2, 2))

        assert feature_calculator.ratio_of_navigable_spaces_area(
            plans=[
                {"plan_layout": navigable, "floor_numbers": [-1]},
                {"plan_layout": navigable, "floor_numbers": [0]},
                {"plan_layout": not_navigable, "floor_numbers": [0, 1, 2, 3]},
            ]
        ) == {"1.2": 0.5, "1.5": 0.5}


class TestAvgTotalHoursOfSunshine:
    feature_calculator = CompetitionFeaturesCalculator(UnifiedClassificationScheme())

    @pytest.mark.parametrize(
        "min_threshold, sun_observations, expected_result",
        [
            # regular case: partially above threshold
            (10, [0, 0, 0, 20, 70, 30, 40, 30, 30, 20, 0, 0], [(5.0, 19.0)]),
            # always above threshold
            (0, [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10], [(0, 22)]),
            # always under threshold
            (10, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [(0, 0)]),
            # several periods above threshold
            (
                10,
                [5, 15, 15, 5, 15, 15, 15, 15, 15, 15, 15, 15],
                [(1.0, 5.0), (7.0, 22.0)],
            ),
            # starting above threshold, dipping below and ending above threshold
            (10, [30, 30, 30, 20, 10, 5, 5, 5, 10, 20, 30, 30], [(0, 8), (16, 22)]),
        ],
    )
    def test_get_periods_of_direct_sunshine(
        self, min_threshold, sun_observations, expected_result
    ):
        result = list(
            self.feature_calculator._get_periods_of_direct_sunshine(
                sun_observations=list(zip(range(0, 23, 2), sun_observations)),
                min_threshold=min_threshold,
            )
        )
        assert result == expected_result

    def test_get_periods_of_direct_sunshine_given_observations_out_of_order(self):
        """
        This test is to ensure that _get_periods_of_direct_sunshine
        accepts observations which are not ordered by time
        """
        result = list(
            self.feature_calculator._get_periods_of_direct_sunshine(
                sun_observations=[(0, 20), (24, 20), (12, 30)],
                min_threshold=25,
            )
        )
        assert result == [(6, 18)]

    @pytest.mark.parametrize(
        "periods, expected_result",
        [
            ([(0, 7), (9, 15)], 13),
            ([(0, 7), (5, 15)], 15),
            ([(5, 15), (0, 7)], 15),
        ],
    )
    def test_aggregate_periods_of_sunshine(self, periods, expected_result):
        assert (
            self.feature_calculator._aggregate_periods_of_sunshine(periods=periods)
            == expected_result
        )

    @pytest.fixture
    def plan_layout(self):
        space = SimSpace(footprint=dummy_footprint)
        for fake_balcony_db_area_id in range(3):
            area = SimArea(footprint=dummy_footprint, area_type=AreaType.BALCONY)
            area.db_area_id = fake_balcony_db_area_id
            space.areas.add(area)

        interior_area = SimArea(footprint=dummy_footprint, area_type=AreaType.ROOM)
        interior_area.db_area_id = 3
        space.areas.add(interior_area)

        return SimLayout(spaces={space})

    @staticmethod
    def make_sun_vector(season: SEASONS, data: List[float]) -> dict:
        sun_obs_dates = [
            datetime(
                season.value.year,
                season.value.month,
                season.value.day,
                hour,
                tzinfo=timezone.utc,
            )
            for hour in range(0, 23, 2)
        ]
        return {
            SuntimesHandler.get_sun_key_from_datetime(dt=obs_date): {"max": sun_value}
            for obs_date, sun_value in zip(sun_obs_dates, data)
        }

    @pytest.fixture
    def sun_v2_stats_by_apartment_area(self):
        # an area with morning sun
        summer_morning_sun = [0, 0, 5, 10, 100.1, 100.1, 100.1, 0, 0, 0, 0, 0]
        winter_morning_sun = [0, 0, 0, 0, 10, 100.1, 100.1, 0, 0, 0, 0, 0]
        vector_morning_sun = {
            **self.make_sun_vector(season=SEASONS.SUMMER, data=summer_morning_sun),
            **self.make_sun_vector(season=SEASONS.WINTER, data=winter_morning_sun),
        }

        # an area with evening sun
        summer_evening_sun = [0, 0, 0, 0, 0, 0, 0, 100.1, 100.1, 100.1, 10, 5]
        winter_evening_sun = [0, 0, 0, 0, 0, 0, 0, 100.1, 10, 5, 0, 0]
        vector_evening_sun = {
            **self.make_sun_vector(season=SEASONS.SUMMER, data=summer_evening_sun),
            **self.make_sun_vector(season=SEASONS.WINTER, data=winter_evening_sun),
        }

        return {
            CLIENT_ID_1: {
                1: vector_morning_sun,
                2: vector_evening_sun,
                3: vector_morning_sun,
            }
        }

    def test_get_apartments_outdoor_areas_sun_values(
        self, plan_layout, sun_v2_stats_by_apartment_area
    ):
        # when
        apartments_outdoor_areas_sun_values = (
            self.feature_calculator._get_apartments_outdoor_areas_sun_values(
                sun_stats_by_apartment_area=sun_v2_stats_by_apartment_area,
                plan_layouts=[plan_layout],
                season=SEASONS.SUMMER,
            )
        )

        # then
        assert apartments_outdoor_areas_sun_values == {
            CLIENT_ID_1: {
                1: [
                    (0, 0),
                    (2, 0),
                    (4, 5),
                    (6, 10),
                    (8, 100.1),
                    (10, 100.1),
                    (12, 100.1),
                    (14, 0),
                    (16, 0),
                    (18, 0),
                    (20, 0),
                    (22, 0),
                ],
                2: [
                    (0, 0),
                    (2, 0),
                    (4, 0),
                    (6, 0),
                    (8, 0),
                    (10, 0),
                    (12, 0),
                    (14, 100.1),
                    (16, 100.1),
                    (18, 100.1),
                    (20, 10),
                    (22, 5),
                ],
            }
        }

    @pytest.mark.parametrize(
        "season, expected_result",
        [(SEASONS.SUMMER, 13.5560), (SEASONS.WINTER, 8.0)],
    )
    def test_avg_total_minutes_of_sunshine_outside_areas(
        self, season, expected_result, plan_layout, sun_v2_stats_by_apartment_area
    ):
        result = self.feature_calculator.avg_total_hours_of_sunshine_outside_areas(
            sun_stats_by_apartment_area=sun_v2_stats_by_apartment_area,
            plan_layouts=[plan_layout],
            season=season,
        )
        assert result == pytest.approx(expected_result, abs=0.001)


class TestAnalysisViewFeatures:
    @staticmethod
    def view_data_example(
        layouts_per_apartment: Dict[str, Dict[int, SimLayout]], classification_schema
    ):
        sim_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for i, (_, unit_info) in enumerate(sorted(layouts_per_apartment.items())):
            for unit_id, layout in unit_info.items():
                for area_type, areas in layout.areas_by_type.items():
                    if area_type in classification_schema.LIVING_AND_BEDROOMS:
                        rooms = list(areas)
                        for room in rooms[: len(rooms) // 2]:
                            sim_data[unit_id][room.db_area_id][
                                VIEW_DIMENSION.VIEW_GREENERY.value
                            ]["mean"] = 2
                        for room in rooms[len(rooms) // 2 :]:
                            sim_data[unit_id][room.db_area_id][
                                VIEW_DIMENSION.VIEW_GREENERY.value
                            ]["mean"] = 4
                    else:
                        for area in areas:
                            # outliers to check we are considering only the right areas
                            sim_data[unit_id][area.db_area_id][
                                VIEW_DIMENSION.VIEW_GREENERY.value
                            ]["mean"] = (-2000 * i)
        return sim_data

    def test_avg_analysis(
        self,
        layout_scaled_classified_wo_db_conn,
    ):
        # Given
        classification_schema = UnifiedClassificationScheme()

        # unit layouts
        layouts_per_apartment = {
            "1": {1: layout_scaled_classified_wo_db_conn(332)},
            "2": {2: layout_scaled_classified_wo_db_conn(2494)},
        }

        # and simulation data (1 value per unit area dimension)
        sim_data = self.view_data_example(
            layouts_per_apartment=layouts_per_apartment,
            classification_schema=classification_schema,
        )

        # When
        comp_feature_handler = CompetitionFeaturesCalculator(classification_schema)
        avg_view_values = comp_feature_handler.avg_analysis_feature(
            layouts_per_apartment=layouts_per_apartment,
            unit_area_stats=sim_data,
            dimension=VIEW_DIMENSION.VIEW_GREENERY,
        )

        # Then
        # Some layouts have an uneven number of rooms, therefore the mean is slightly over 3.0
        assert avg_view_values == pytest.approx(3.055, abs=10**-3)


class TestAptWithAreaMinimumSize:
    @staticmethod
    def make_layout(all_apartment_configs: List[List[Tuple[AreaType, Tuple]]]):
        fake_layouts = {}
        max_rectangle_by_area_id = {}

        total_areas = 0
        for num_apartment, apartment_config in enumerate(all_apartment_configs):
            spaces = set()
            for area_type_polygon in apartment_config:
                area_type = area_type_polygon[0]
                footprint = Polygon(area_type_polygon[1])
                space = SimSpace(footprint=footprint)
                space.areas = {
                    SimArea(
                        footprint=footprint,
                        area_type=area_type,
                        db_area_id=total_areas,
                    )
                }
                max_rectangle_by_area_id[total_areas] = footprint
                spaces.add(space)
                total_areas += 1

            fake_layouts[num_apartment] = SimLayout(spaces=spaces)

        return fake_layouts, max_rectangle_by_area_id

    @pytest.mark.parametrize(
        "bathroom_polygon_apartment, expected_area_info",
        [
            (
                [
                    [
                        [
                            AreaType.BATHROOM,
                            ((0.0, 0.0), (0.0, 2.0), (3.0, 2.0), (3.0, 0.0)),
                        ]
                    ],
                    [
                        [
                            AreaType.BATHROOM,
                            ((0.0, 0.0), (0.0, 2.0), (3.0, 2.0), (3.0, 0.0)),
                        ]
                    ],
                ],
                {"1": [(6.0, 3.0, 2.0)], "2": [(6.0, 3.0, 2.0)]},
            ),
            (
                [
                    [
                        [
                            AreaType.BATHROOM,
                            ((0.0, 0.0), (0.0, 2.0), (3.0, 2.0), (3.0, 0.0)),
                        ]
                    ],
                    [
                        [
                            AreaType.BATHROOM,
                            (
                                (0.0, 0.0),
                                (0.0, 1.7),
                                (1.5, 1.7),
                                (1.5, 0.0),
                            ),
                        ]
                    ],  # This won't make the cut as it should be 3.8m
                ],
                {"1": [(6.0, 3.0, 2.0)], "2": [(2.55, 1.7, 1.5)]},
            ),
        ],
    )
    def test_avg_apt_w_bathroom_sia500_size_bathrooms_passing_check(
        self,
        bathroom_polygon_apartment,
        expected_area_info,
    ):
        fake_layouts, max_rectangle_by_area_id = self.make_layout(
            all_apartment_configs=bathroom_polygon_apartment
        )

        layouts_per_apartment = {
            "1": {1: fake_layouts[0]},
            "2": {2: fake_layouts[1]},
        }

        results = CompetitionFeaturesCalculator(
            classification_schema=UnifiedClassificationScheme()
        ).avg_apt_bathroom_sia500_size(
            layouts_per_apartment=layouts_per_apartment,
            max_rectangle_by_area_id=max_rectangle_by_area_id,
        )

        assert results == expected_area_info

    def test_avg_apt_bedroom_minimum(self):
        polygons_apartment = [
            # 1 room
            [[AreaType.BEDROOM, ((0, 0), (0, 2), (2, 2), (2, 0))]],
            [  # 2 rooms
                [AreaType.BEDROOM, ((0, 0), (0, 2), (2, 2), (2, 0))],
                [AreaType.BEDROOM, ((0, 0), (0, 2), (2, 2), (2, 0))],
            ],
            [[AreaType.ROOM, ((0, 0), (0, 2), (2, 2), (2, 0))]],
            [[AreaType.LIVING_DINING, ((0, 0), (0, 2), (2, 2), (2, 0))]],
            # Not present
            [[AreaType.BATHROOM, ((0, 0), (0, 2), (2, 3.0), (2, 0))]],
        ]
        fake_layouts, max_rectangle_by_area_id = self.make_layout(
            all_apartment_configs=polygons_apartment
        )

        layouts_per_apartment = {
            "1": {1: fake_layouts[0]},
            "2": {2: fake_layouts[1]},
            "3": {3: fake_layouts[2]},
            "4": {4: fake_layouts[3]},
            "5": {5: fake_layouts[4]},
        }
        expected = {
            "1": [(4, 2, 2)],
            "2": [(4, 2, 2), (4, 2, 2)],
            "3": [(4, 2, 2)],
            "4": [(4, 2, 2)],
            "5": [],
        }

        results = CompetitionFeaturesCalculator(
            classification_schema=UnifiedClassificationScheme()
        ).avg_apt_bedroom_minimum(
            layouts_per_apartment=layouts_per_apartment,
            max_rectangle_by_area_id=max_rectangle_by_area_id,
        )
        assert results == pytest.approx(expected)

    def test_dinning_sizes_per_apt(self):
        polygons_apartment = [
            # 1 room
            [[AreaType.BEDROOM, ((0, 0), (0, 2), (2, 2), (2, 0))]],  # No living
            [  # 2 rooms
                [AreaType.BEDROOM, ((0, 0), (0, 2), (2, 2), (2, 0))],
                [AreaType.LIVING_DINING, ((0, 0), (0, 2), (2, 2), (2, 0))],
            ],
            [[AreaType.LIVING_ROOM, ((0, 0), (0, 2), (2, 2), (2, 0))]],
            [
                [AreaType.LIVING_DINING, ((0, 0), (0, 2), (2, 2), (2, 0))],
                [AreaType.LIVING_DINING, ((0, 0), (0, 5), (5, 5), (5, 0))],
            ],
            [[AreaType.BATHROOM, ((0, 0), (0, 2), (2, 3.0), (2, 0))]],  # No living
        ]
        fake_layouts, max_rectangle_by_area_id = self.make_layout(
            all_apartment_configs=polygons_apartment
        )

        layouts_per_apartment = {
            "1": {1: fake_layouts[0]},
            "2": {2: fake_layouts[1]},
            "3": {3: fake_layouts[2]},
            "4": {4: fake_layouts[3]},
            "5": {5: fake_layouts[4]},
        }
        expected = {
            "1": [],
            "2": [(4, 2, 2)],
            "3": [(4, 2, 2)],
            "4": [(4, 2, 2), (25, 5, 5)],
            "5": [],
        }

        results = CompetitionFeaturesCalculator(
            classification_schema=UnifiedClassificationScheme()
        ).dinning_sizes_per_apt(
            layouts_per_apartment=layouts_per_apartment,
            max_rectangle_by_area_id=max_rectangle_by_area_id,
        )
        assert not DeepDiff(
            results, expected, ignore_order=True, ignore_numeric_type_changes=True
        )


class TestTotalLivingArea:
    @pytest.mark.parametrize(
        "plan_id, expected",
        [
            (332, 447.955),
            (863, 245.3683),
            (4976, 212.5439),
        ],
    )
    def test_comp_total_living_area_feature(
        self, layout_scaled_classified_wo_db_conn, plan_id, expected
    ):
        feature_calculator = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        )

        layout = layout_scaled_classified_wo_db_conn(plan_id)

        assert feature_calculator.calculate_total_living_area(
            residential_units_layouts=[layout]
        ) == pytest.approx(expected)


class TestTotalHNFArea:
    @pytest.mark.parametrize(
        "plan_id, expected",
        [
            (332, 447.955),
            (863, 242.93489),
            (4976, 212.5439),
        ],
    )
    def test_comp_total_hnf_area_feature(
        self, layout_scaled_classified_wo_db_conn, plan_id, expected
    ):
        feature_calculator = CompetitionFeaturesCalculator(
            UnifiedClassificationScheme()
        )

        layout = layout_scaled_classified_wo_db_conn(plan_id)

        assert feature_calculator.calculate_total_hnf_area(
            layouts=[layout]
        ) == pytest.approx(expected)


@pytest.mark.parametrize(
    "plans_ids, expected_residential, expected_commercial",
    [
        ((332, 863), 1429.3995, 589.9415),
        ((4976, 863), 652.4675, 589.9415),
    ],
)
def test_m2_by_usage_type(
    layout_scaled_classified_wo_db_conn,
    plans_ids,
    expected_residential,
    expected_commercial,
):
    layouts = [layout_scaled_classified_wo_db_conn(plan_id) for plan_id in plans_ids]
    layouts_by_type = {
        UNIT_USAGE.RESIDENTIAL.name: [layouts[0], layouts[0]],
        UNIT_USAGE.COMMERCIAL.name: [layouts[1], layouts[1]],
    }
    feature_calculator = CompetitionFeaturesCalculator(UnifiedClassificationScheme())
    assert feature_calculator.m2_by_usage_type(
        layouts_by_type=layouts_by_type
    ) == pytest.approx(
        {
            UNIT_USAGE.RESIDENTIAL.name: expected_residential,
            UNIT_USAGE.COMMERCIAL.name: expected_commercial,
        },
        abs=0.01,
    )
