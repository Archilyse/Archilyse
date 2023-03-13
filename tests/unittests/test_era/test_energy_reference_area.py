import pytest
from shapely.geometry import box

from brooks.models import SimArea, SimLayout, SimSeparator, SimSpace
from brooks.types import AreaType, SeparatorType
from handlers import PlanLayoutHandler
from handlers.db import BuildingDBHandler, FloorDBHandler, PlanDBHandler
from handlers.energy_reference_area.constants import AREA_TYPE_ERA_MAPPING
from handlers.energy_reference_area.energy_calculation_per_layout import (
    EnergyAreaStatsLayout,
)
from handlers.energy_reference_area.main_report import EnergyAreaReportForSite
from handlers.energy_reference_area.models import EnergyAreasStatsPerFloor


class TestEnergyReferenceArea:
    @pytest.fixture
    def simple_layout(self) -> SimLayout:
        room_area = SimArea(footprint=box(0, 0, 5, 3), area_type=AreaType.ROOM)
        washing_area = SimArea(
            footprint=box(5.3, 0, 10.3, 5), area_type=AreaType.WASH_AND_DRY_ROOM
        )

        wall_between_room_and_washing_area = SimSeparator(
            footprint=box(5, 0, 5.3, 5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        wall_1_washing_area = SimSeparator(
            footprint=box(5, 5, 10.6, 5.3),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        wall_2_washing_area = SimSeparator(
            footprint=box(10.3, 0, 10.6, 5),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        wall_extending_both_rooms = SimSeparator(
            footprint=box(-0.3, -0.6, 10.6, 0),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )

        wall_1_room_area = SimSeparator(
            footprint=box(-0.3, -0.3, 0, 3.3),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )
        wall_2_room_area = SimSeparator(
            footprint=box(0, 3, 5, 3.2),
            separator_type=SeparatorType.WALL,
            height=(0, 2.6),
        )

        room_space = SimSpace(footprint=room_area.footprint)
        room_space.add_area(room_area)
        washing_space = SimSpace(footprint=washing_area.footprint)
        washing_space.add_area(washing_area)
        layout = SimLayout(
            separators={
                wall_1_room_area,
                wall_2_room_area,
                wall_extending_both_rooms,
                wall_2_washing_area,
                wall_1_washing_area,
                wall_between_room_and_washing_area,
            },
            spaces={room_space, washing_space},
        )
        return layout

    @staticmethod
    def test_energy_area_in_layout(simple_layout):
        energy_area_stats = EnergyAreaStatsLayout.energy_area_in_layout(
            layout=simple_layout, area_ids_part_of_units=set()
        )

        assert energy_area_stats.total_era_area == pytest.approx(
            expected=21.28, abs=0.01
        )
        assert energy_area_stats.total_era_volume == pytest.approx(
            expected=55.328, abs=0.01
        )
        assert energy_area_stats.era_wall_area == pytest.approx(expected=6.28, abs=0.01)
        assert energy_area_stats.era_areas == {AreaType.ROOM.name: [15.0]}
        assert energy_area_stats.total_non_era_area == pytest.approx(
            expected=31.93, abs=0.01
        )
        assert energy_area_stats.non_era_areas == {
            AreaType.WASH_AND_DRY_ROOM.name: [25.000000000000004]
        }

    @staticmethod
    def test_energy_void_in_layout(simple_layout):
        from copy import deepcopy

        void_layout = deepcopy(simple_layout)
        void = list(void_layout.areas_by_type[AreaType.ROOM])[0]
        void._type = AreaType.VOID
        void.db_area_id = 1

        energy_area_stats = EnergyAreaStatsLayout.energy_area_in_layout(
            layout=void_layout, area_ids_part_of_units={void.db_area_id}
        )

        # NOTE: Since the only ERA area was a room, when becoming a VOID, the room is only counted to the volume.
        #       Additionally, the walls around the VOID also do only count in the volume.
        #       Thus, the volume does not change while era_area and era_wall_area drop to 0.
        assert energy_area_stats.total_era_area == pytest.approx(expected=0.0, abs=0.01)
        assert energy_area_stats.total_era_volume == pytest.approx(
            expected=55.328, abs=0.01
        )
        assert energy_area_stats.era_wall_area == pytest.approx(expected=0.0, abs=0.01)
        assert energy_area_stats.era_areas == {}
        assert energy_area_stats.era_areas_volume_only == {AreaType.VOID.name: [15.0]}
        assert energy_area_stats.total_non_era_area == pytest.approx(
            expected=38.21, abs=0.01
        )
        assert energy_area_stats.non_era_areas == {
            AreaType.WASH_AND_DRY_ROOM.name: [25.000000000000004]
        }

    @staticmethod
    @pytest.mark.parametrize(
        "bounds,area_type,is_era",
        [
            ([0, 0, 1, 4], AreaType.VOID, True),
            ([0, 0, 2, 4], AreaType.VOID, False),
            ([0, 0, 1, 4], AreaType.SHAFT, True),
            ([0, 0, 2, 4], AreaType.SHAFT, False),
        ],
    )
    def test_is_era_area(bounds, area_type, is_era):
        area = SimArea(footprint=box(*bounds), area_type=area_type)
        assert EnergyAreaStatsLayout._is_era_area(area=area) == is_era

    @staticmethod
    @pytest.mark.parametrize("area_footprint_smaller_than_10", [True, False])
    def test_areas_storerooms(simple_layout, area_footprint_smaller_than_10):
        from shapely.geometry import box

        smallest_area: SimArea = sorted(
            simple_layout.areas, key=lambda area: area.footprint.area
        )[0]
        smallest_area._type = AreaType.STOREROOM
        if area_footprint_smaller_than_10:
            smallest_area.footprint = box(0, 0, 3, 3)
        else:
            smallest_area.footprint = box(0, 0, 3.34, 3.34)
        (
            era_areas_by_type,
            non_era_areas_by_type,
            era_areas_volume_only,
        ) = EnergyAreaStatsLayout._areas_by_era_and_type(
            layout=simple_layout, area_ids_part_of_units=set()
        )
        if area_footprint_smaller_than_10:
            assert len(non_era_areas_by_type[AreaType.STOREROOM]) == 0
            assert len(era_areas_by_type[AreaType.STOREROOM]) == 1
            assert len(era_areas_volume_only) == 0
        else:
            assert len(era_areas_by_type[AreaType.STOREROOM]) == 0
            assert len(non_era_areas_by_type[AreaType.STOREROOM]) == 1
            assert len(era_areas_volume_only) == 0

    @staticmethod
    @pytest.mark.parametrize(
        "in_unit,size,expected_era_area,expected_non_era_heated",
        [
            (False, 4, True, False),  # small voids should be ERA area
            (False, 6, False, False),
            (True, 4, True, False),  # small voids should be ERA area
            (True, 6, False, True),  # large voids only if inside unit
        ],
    )
    def test_areas_voids(
        simple_layout, in_unit, size, expected_era_area, expected_non_era_heated
    ):
        from math import sqrt

        from shapely.geometry import box

        area: SimArea = sorted(
            simple_layout.areas, key=lambda area: area.footprint.area
        )[0]
        area._type = AreaType.VOID
        area.footprint = box(0, 0, sqrt(size), sqrt(size))
        area.db_area_id = 1

        (
            era_areas_by_type,
            non_era_areas_by_type,
            era_areas_volume_only,
        ) = EnergyAreaStatsLayout._areas_by_era_and_type(
            layout=simple_layout,
            area_ids_part_of_units={area.db_area_id} if in_unit else set(),
        )

        assert len(non_era_areas_by_type[AreaType.VOID]) == (
            0 if expected_era_area or expected_non_era_heated else 1
        )
        assert len(era_areas_by_type[AreaType.VOID]) == (1 if expected_era_area else 0)
        assert len(era_areas_volume_only[AreaType.VOID]) == (
            1 if expected_non_era_heated else 0
        )


class TestEnergyAreaReport:
    @staticmethod
    def test_data_per_floor(mocker):
        mocker.patch.object(
            BuildingDBHandler,
            "find",
            return_value=[
                {"id": None, "client_building_id": "1"},
                {"id": None, "client_building_id": "2"},
            ],
        )
        mocker.patch.object(
            PlanDBHandler, "find", side_effect=[[{"id": 1}, {"id": 2}], [{"id": 3}]]
        )
        mocker.patch.object(
            PlanDBHandler, "get_by", return_value={"default_wall_height": 2.6}
        )
        mocked_get_layout = mocker.patch.object(
            PlanLayoutHandler, "get_layout", return_value=None
        )
        mocked_energy_area_in_layout = mocker.patch.object(
            EnergyAreaStatsLayout,
            "energy_area_in_layout",
            return_value=EnergyAreasStatsPerFloor(
                total_era_area=50,
                total_non_era_area=30,
                era_wall_area=10,
                era_areas={},
                non_era_areas={},
                era_areas_volume_only={},
                floor_height=2.6,
            ),
        )
        mocker.patch.object(
            FloorDBHandler,
            "find",
            side_effect=[
                [{"plan_id": 1, "floor_number": 0}, {"plan_id": 2, "floor_number": 1}],
                [{"plan_id": 3, "floor_number": 0}, {"plan_id": 3, "floor_number": 2}],
            ],
        )
        mocker.patch.object(
            EnergyAreaReportForSite,
            "_area_ids_part_of_units",
            return_value=set(),
        )
        data = EnergyAreaReportForSite._data_per_floor(site_id=None)
        assert [
            {
                "floor_number": row.floor_number,
                "building_client_id": row.building_client_id,
            }
            for row in data
        ] == [
            {"floor_number": 0, "building_client_id": "1"},
            {"floor_number": 1, "building_client_id": "1"},
            {"floor_number": 0, "building_client_id": "2"},
            {"floor_number": 2, "building_client_id": "2"},
        ]
        assert len(data) == 4

        assert mocked_get_layout.call_count == 3
        assert mocked_get_layout.call_args[1] == {"scaled": True, "classified": True}
        assert mocked_energy_area_in_layout.call_count == 3

    @staticmethod
    def test_aggregate_and_create_sheet_per_building():
        data_per_floor = [
            EnergyAreasStatsPerFloor(
                total_era_area=10,
                total_era_volume=20,
                total_non_era_area=5,
                era_wall_area=10,
                era_areas={},
                non_era_areas={},
                era_areas_volume_only={},
                building_client_id="1",
                floor_number=0,
                floor_height=2.6,
            ),
            EnergyAreasStatsPerFloor(
                total_era_area=10,
                total_era_volume=20,
                total_non_era_area=5,
                era_wall_area=10,
                era_areas={},
                non_era_areas={},
                era_areas_volume_only={},
                building_client_id="2",
                floor_number=0,
                floor_height=2.6,
            ),
            EnergyAreasStatsPerFloor(
                total_era_area=10,
                total_era_volume=20,
                total_non_era_area=5,
                era_wall_area=10,
                era_areas={},
                non_era_areas={},
                era_areas_volume_only={},
                building_client_id="1",
                floor_number=1,
                floor_height=2.6,
            ),
        ]
        data = EnergyAreaReportForSite._prepare_data_per_building(
            data_per_floor=data_per_floor
        )
        building_1_data = data.loc[["1"]]
        assert building_1_data.loc[:, "total_era_volume"][0] == 40.0
        assert building_1_data.loc[:, "total_non_era_area"][0] == 10.0
        assert building_1_data.loc[:, "era_wall_area"][0] == 20.0

        building_2_data = data.loc[["2"]]
        assert building_2_data.loc[:, "total_era_volume"][0] == 20.0
        assert building_2_data.loc[:, "total_non_era_area"][0] == 5.0
        assert building_2_data.loc[:, "era_wall_area"][0] == 10.0


def test_area_type_era_mapping_complete():
    for area_type in AreaType:
        assert area_type.name in AREA_TYPE_ERA_MAPPING
