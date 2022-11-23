import pytest
from shapely.geometry import box

from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.constants import (
    NOISE_SOURCE_TYPE,
    NOISE_SURROUNDING_TYPE,
    NOISE_TIME_TYPE,
)
from handlers import PlanLayoutHandler
from simulations.noise import NoiseWindowSimulationHandler


@pytest.mark.parametrize(
    "floor_height,expected",
    [(0, 13.402), (2.9 * 2, 13.575), (2.9 * 5, 10.37), (3.2 * 10, 7.559)],
)
def test_get_real_floor_noise(floor_height, expected):
    noises_by_location = {
        NOISE_SOURCE_TYPE.TRAFFIC: {
            (1, 1, 1): [
                ({NOISE_TIME_TYPE.DAY: 10, NOISE_TIME_TYPE.NIGHT: 10}, 10),
                ({NOISE_TIME_TYPE.DAY: 20, NOISE_TIME_TYPE.NIGHT: 20}, 10),
                ({NOISE_TIME_TYPE.DAY: 0, NOISE_TIME_TYPE.NIGHT: 0}, 0),
                ({NOISE_TIME_TYPE.DAY: 1, NOISE_TIME_TYPE.NIGHT: 1}, 1),
                ({NOISE_TIME_TYPE.DAY: 2, NOISE_TIME_TYPE.NIGHT: 2}, 2),
            ],
        }
    }
    result = NoiseWindowSimulationHandler.get_real_floor_noise(
        floor_height=floor_height,
        noises_by_location=noises_by_location,
    )
    assert result == {
        NOISE_SURROUNDING_TYPE.TRAFFIC_DAY: {
            (1, 1, 1): pytest.approx(expected, abs=0.001)
        },
        NOISE_SURROUNDING_TYPE.TRAFFIC_NIGHT: {
            (1, 1, 1): pytest.approx(expected, abs=0.001)
        },
    }


@pytest.mark.parametrize("locations_1,locations_2", [([1, 2], [1, 3]), ([3], [])])
def test_get_noise_for_unit(locations_1, locations_2):
    locations = {1: (1, 1, 1), 2: (2, 2, 2), 3: (3, 3, 3), 4: (4, 4, 4)}
    locations_1 = [locations[i] for i in locations_1]
    locations_2 = [locations[i] for i in locations_2]
    locations_by_area = {1: locations_1, 2: locations_2}
    location_noises = {
        (1, 1, 1): 10,
        (2, 2, 2): 20,
        (3, 3, 3): 30,
    }
    real_noise_by_location = {
        noise: location_noises for noise in NOISE_SURROUNDING_TYPE
    }

    result = NoiseWindowSimulationHandler.get_noise_for_unit(
        floor_height=0,
        locations_by_area=locations_by_area,
        real_noise_by_location=real_noise_by_location,
        unit_areas_ids=[1, 2],
    )
    results_expected = {}
    if locations_1:
        results_expected[1] = {
            "observation_points": locations_1,
            **{
                noise.value: [location_noises[location] for location in locations_1]
                for noise in NOISE_SURROUNDING_TYPE
            },
        }
    if locations_2:
        results_expected[2] = {
            "observation_points": locations_2,
            **{
                noise.value: [location_noises[location] for location in locations_2]
                for noise in NOISE_SURROUNDING_TYPE
            },
        }
    assert result == results_expected


def make_layout_with_area_type(
    opening_type: OpeningType, second_area_type: AreaType = AreaType.BALCONY
):
    """A layout with 1 room and 1 balcony connected by an opening of type opening_type"""
    spaces = set()
    for fake_db_area_id, (area_type, footprint) in enumerate(
        [
            (AreaType.ROOM, box(0, 0, 10, 10)),
            (second_area_type, box(10, 0, 20, 10)),
        ]
    ):
        space = SimSpace(footprint=footprint)
        area = SimArea(footprint=footprint, area_type=area_type)
        area.db_area_id = fake_db_area_id + 1
        space.areas.add(area)
        spaces.add(space)

    wall = SimSeparator(
        footprint=box(9.9, 0, 10.2, 10), separator_type=SeparatorType.WALL
    )
    opening = SimOpening(
        footprint=box(9.9, 3, 10.2, 4),
        opening_type=opening_type,
        separator=wall,
        height=(2, 0),
        separator_reference_line=get_center_line_from_rectangle(wall.footprint)[0],
    )
    wall.add_opening(opening)

    return SimLayout(separators={wall}, spaces=spaces)


@pytest.mark.parametrize(
    "opening_type, area_type, opening_type_is_considered",
    [
        (OpeningType.DOOR, AreaType.BALCONY, True),
        (OpeningType.DOOR, AreaType.ROOM, False),
        (OpeningType.WINDOW, AreaType.BALCONY, True),
        (OpeningType.WINDOW, AreaType.ROOM, False),
        (OpeningType.ENTRANCE_DOOR, AreaType.BALCONY, False),
        (OpeningType.WINDOW, AreaType.GARDEN, True),
        (OpeningType.WINDOW, AreaType.LOGGIA, True),
        (OpeningType.WINDOW, AreaType.BIKE_STORAGE, False),
    ],
)
def test_get_locations_by_area_at_windows_and_outdoor_doors_opening_types(
    mocker,
    site,
    opening_type,
    area_type,
    opening_type_is_considered,
):
    from simulations.noise import noise_window_simulation_handler as noise_module

    layout = make_layout_with_area_type(
        opening_type=opening_type, second_area_type=area_type
    )
    mocker.patch.object(PlanLayoutHandler, "get_private_layout", return_value=layout)
    mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)

    sim_handler = noise_module.NoiseWindowSimulationHandler(site_id=site["id"])

    result = sim_handler.get_locations_by_area(
        layout_handler=PlanLayoutHandler(plan_id=-999)
    )

    if opening_type_is_considered:
        assert result
    else:
        assert not result
