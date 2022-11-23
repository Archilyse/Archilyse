import json
from functools import partial
from typing import List

import numpy as np
import pytest
from deepdiff import DeepDiff
from shapely.affinity import scale, translate
from shapely.geometry import Point, box

from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.constants import NOISE_SURROUNDING_TYPE, NOISE_TIME_TYPE
from handlers import PlanLayoutHandler, UnitHandler
from handlers.db import AreaDBHandler, UnitAreaDBHandler, UnitDBHandler
from simulations.noise.noise_sources_levels_generator import get_noise_sources
from simulations.noise.utils import (
    format_area_window_noises,
    get_surrounding_footprints,
)
from tests.utils import make_layout_square_4_windows


@pytest.fixture
def noise_window_expected_2016(fixtures_path):
    with fixtures_path.joinpath("noise/noise_expected_2016_test.json").open() as f:
        return format_area_window_noises(area_window_noises=json.load(f))


class TestNoiseSimulationHandler:
    @staticmethod
    def _make_layout(windows_conf: List[List[int]], areas_sizes: List[int]):
        spaces = set()
        separators = set()
        for i, (windows, area_size) in enumerate(zip(windows_conf, areas_sizes)):
            trans_pol = partial(translate, xoff=i * 50)
            # Translates each box 50 units * i to the right.
            # No issues as far as the spaces are not too big
            space_footprint = trans_pol(scale(box(0, 0, 1, 1), area_size))
            space = SimSpace(footprint=space_footprint, height=(0, 2.6))
            space.add_area(
                SimArea(footprint=space_footprint, db_area_id=i + 1, height=(0, 2.6))
            )
            spaces.add(space)

            separator = SimSeparator(
                footprint=space_footprint, separator_type=SeparatorType.WALL
            )
            separators.add(separator)

            for window_size in windows:
                window = SimOpening(
                    footprint=trans_pol(scale(box(0, 0, 1, 1), window_size)),
                    opening_type=OpeningType.WINDOW,
                    separator=separator,
                    height=(0.5, 2),
                    separator_reference_line=get_center_line_from_rectangle(
                        separator.footprint
                    )[0],
                )
                separator.add_opening(window)

        return SimLayout(spaces=spaces, separators=separators)

    @pytest.mark.parametrize(
        "noise_sources, surrounding_footprints, expected_noises",
        [
            (
                [
                    (
                        Point(-50, -50),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    )
                ],
                [],
                [0, 0, 74.85, 74.85],
            ),
            (
                [
                    (
                        Point(-50, -50),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    )
                ],
                # (overlapping surrounding footprints are ignored)
                [Point(0, 0).buffer(1000)],
                [0, 0, 74.85, 74.85],
            ),
            (
                [
                    (
                        Point(-50, -50),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    )
                ]
                * 2,
                [],
                [
                    0,
                    0,
                    77.858,
                    77.858,
                ],
            ),
            (
                [
                    (
                        Point(-50, -50),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    ),
                    (
                        Point(30, 30),
                        {NOISE_TIME_TYPE.DAY: 50, NOISE_TIME_TYPE.NIGHT: 50},
                    ),
                ],
                [],
                [30.039, 30.039, 74.85, 74.85],
            ),
            (
                [
                    (
                        Point(-50, -50),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    )
                ],
                [box(-10, -10, 0.75, 0.75)],
                [0, 0, 0, 0],
            ),
            (
                [(Point(3, 3), {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100})],
                [box(2.25, 2.25, 2.75, 2.75)],
                [0, 0, 0, 0],
            ),
            (
                [
                    (
                        Point(0, 0),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    ),
                    (
                        Point(3, 3),
                        {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                    ),
                ],
                [box(-10, -10, 0.75, 0.75), box(2.25, 2.25, 2.75, 2.75)],
                [0, 0, 0, 0],
            ),
        ],
    )
    def test_noise_windows_handler_noise_at_windows_and_outdoor_doors(
        self,
        mocker,
        plan,
        make_floor,
        make_units,
        building,
        site,
        noise_sources,
        surrounding_footprints,
        expected_noises,
    ):
        from simulations.noise import noise_window_simulation_handler as noise_module

        area = AreaDBHandler.add(
            coord_x=1,
            coord_y=2,
            area_type=AreaType.ROOM.value,
            plan_id=plan["id"],
            scaled_polygon="fake",
        )
        layout = make_layout_square_4_windows(db_area_id=area["id"])
        floor = make_floor(building=building, plan=plan, floornumber=0)
        (unit,) = make_units(floor)
        UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area["id"])

        mocker.patch.object(
            PlanLayoutHandler, "get_private_layout", return_value=layout
        )
        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)

        mocker.patch.object(
            noise_module, get_noise_sources.__name__, return_value=noise_sources
        )
        mocker.patch.object(
            noise_module,
            get_surrounding_footprints.__name__,
            return_value=surrounding_footprints,
        )

        sim_handler = noise_module.NoiseWindowSimulationHandler(site_id=site["id"])
        result = sim_handler.get_noise_for_site()

        assert sorted(result[1][1]["noise_TRAFFIC_DAY"]) == pytest.approx(
            expected_noises, abs=2
        )

    def test_noise_window_loggia_with_windows(
        self, mocker, site, plan, building, make_floor, make_units
    ):
        def make_layout():
            """A layout with 1 room and 1 loggia connected by a an opening of type opening_type.
            The Loggia have a window, no railings"""
            spaces = set()
            for fake_db_area_id, (area_type, footprint) in enumerate(
                [
                    (AreaType.ROOM, box(0, 0, 1, 1)),
                    (AreaType.LOGGIA, box(1, 0, 2, 1)),
                ]
            ):
                space = SimSpace(footprint=footprint)
                space.areas.add(
                    SimArea(
                        footprint=footprint,
                        area_type=area_type,
                        db_area_id=fake_db_area_id + 1,
                    )
                )
                spaces.add(space)

            wall1 = SimSeparator(
                footprint=box(0.9, 0, 1.1, 1), separator_type=SeparatorType.WALL
            )
            wall2 = SimSeparator(
                footprint=box(1.9, 0, 2.1, 1), separator_type=SeparatorType.WALL
            )
            wall3 = SimSeparator(
                footprint=box(0, 0, 2.1, 0.1), separator_type=SeparatorType.WALL
            )
            wall4 = SimSeparator(
                footprint=box(0, 1, 2.1, 1.1), separator_type=SeparatorType.WALL
            )
            wall5 = SimSeparator(
                footprint=box(0, 0, 0.1, 1.1), separator_type=SeparatorType.WALL
            )
            opening1 = SimOpening(
                footprint=box(0.9, 0.3, 1.1, 0.7),
                opening_type=OpeningType.WINDOW,
                separator=wall1,
                height=(2, 0),
                separator_reference_line=get_center_line_from_rectangle(
                    wall1.footprint
                )[0],
            )
            opening2 = SimOpening(
                footprint=box(1.9, 0.3, 2.1, 0.7),
                opening_type=OpeningType.WINDOW,
                separator=wall2,
                height=(2, 0),
                separator_reference_line=get_center_line_from_rectangle(
                    wall1.footprint
                )[0],
            )
            wall1.add_opening(opening1)
            wall2.add_opening(opening2)

            return SimLayout(
                separators={wall1, wall2, wall3, wall4, wall5}, spaces=spaces
            )

        from simulations.noise import noise_window_simulation_handler as noise_module

        layout = make_layout()
        noise_sources = [
            (Point(10, 0.5), {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 50})
        ]
        unit_id = 1
        areas_ids = [a.db_area_id for a in layout.areas]
        for area_id in areas_ids:
            AreaDBHandler.add(
                id=area_id,
                coord_x=1,
                coord_y=2,
                area_type=AreaType.ROOM.value,
                plan_id=plan["id"],
                scaled_polygon="fake",
            )

        floor = make_floor(building=building, plan=plan, floornumber=0)
        (unit,) = make_units(floor)
        for area_id in areas_ids:
            UnitAreaDBHandler.add(unit_id=unit["id"], area_id=area_id)

        mocker.patch.object(
            PlanLayoutHandler, "get_private_layout", return_value=layout
        )
        mocker.patch.object(PlanLayoutHandler, "get_layout", return_value=layout)

        mocker.patch.object(
            noise_module, get_noise_sources.__name__, return_value=noise_sources
        )
        mocker.patch.object(
            noise_module, get_surrounding_footprints.__name__, return_value=[]
        )

        sim_handler = noise_module.NoiseWindowSimulationHandler(site_id=site["id"])
        result = sim_handler.get_noise_for_site()

        # 2 total different openings
        opening_noises = {
            n
            for area_id in areas_ids
            for n in result[unit_id][area_id]["noise_TRAFFIC_DAY"]
        }

        assert sorted(opening_noises) == pytest.approx(
            [92.70238774764911, 93.42758849100746]
        )

    def test_noise_window_simulate_no_unit(
        self,
        mocker,
        site,
        plan_classified_scaled,
        make_floor,
        building,
        fake_noise_simulator,
        populate_plan_annotations,
        populate_plan_areas_db,
    ):
        from simulations.noise import noise_window_simulation_handler as noise_module

        make_floor(building=building, plan=plan_classified_scaled, floornumber=0)

        mocker.patch.object(
            noise_module,
            get_noise_sources.__name__,
            return_value=[(Point(-50, -50), 100), (Point(30, 30), 50)],
        )
        mocker.patch.object(
            noise_module, get_surrounding_footprints.__name__, return_value=[]
        )

        sim_handler = noise_module.NoiseWindowSimulationHandler(site_id=site["id"])

        assert sim_handler.get_noise_for_site() == {}

    def test_noise_window_simulate_real_layout(
        self,
        mocker,
        site,
        plan_classified_scaled,
        make_floor,
        building,
        fake_noise_simulator,
        populate_plan_annotations,
        populate_plan_areas_db,
        noise_window_expected_2016,
        fixtures_path,
        update_fixtures=False,
    ):
        from simulations.noise import noise_window_simulation_handler as noise_module

        make_floor(building=building, plan=plan_classified_scaled, floornumber=0)

        all_areas = [a["id"] for a in AreaDBHandler.find()]
        UnitHandler.create_or_extend_units_from_areas(
            plan_id=plan_classified_scaled["id"], apartment_area_ids=[all_areas]
        )
        unit_id = UnitDBHandler.get_by(plan_id=plan_classified_scaled["id"])["id"]

        mocker.patch.object(
            noise_module,
            get_noise_sources.__name__,
            return_value=[
                (
                    Point(-50, -50),
                    {NOISE_TIME_TYPE.DAY: 100, NOISE_TIME_TYPE.NIGHT: 100},
                ),
                (Point(30, 30), {NOISE_TIME_TYPE.DAY: 50, NOISE_TIME_TYPE.NIGHT: 50}),
            ],
        )
        mocker.patch.object(
            noise_module, get_surrounding_footprints.__name__, return_value=[]
        )

        sim_handler = noise_module.NoiseWindowSimulationHandler(site_id=site["id"])
        result = sim_handler.get_noise_for_site()

        # assert all areas have same keys
        keys = {"observation_points"} | {n.value for n in NOISE_SURROUNDING_TYPE}
        for values in result[unit_id].values():
            assert set(values.keys()) == keys

        # assert all areas values
        if update_fixtures:
            with fixtures_path.joinpath("noise/noise_expected_2016_test.json").open(
                "w"
            ) as f:
                json.dump(result, f)

        for area_id, values in result[unit_id].items():
            assert {
                tuple(p)
                for p in np.round(
                    noise_window_expected_2016[1][area_id]["observation_points"],
                    decimals=6,
                )
            } == {
                tuple(p)
                for p in np.round(values["observation_points"], decimals=6).tolist()
            }
            assert not DeepDiff(
                noise_window_expected_2016[1][area_id]["noise_TRAFFIC_DAY"],
                values["noise_TRAFFIC_DAY"],
                ignore_order=True,
                significant_digits=2,
            )
