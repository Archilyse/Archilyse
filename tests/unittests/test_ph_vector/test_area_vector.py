import math
from dataclasses import asdict, fields
from typing import Optional

import pytest
from deepdiff import DeepDiff
from shapely.geometry import LineString, Polygon, box

from brooks.models import (
    SimArea,
    SimFeature,
    SimLayout,
    SimOpening,
    SimSeparator,
    SimSpace,
)
from brooks.types import AreaType, FeatureType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from common_utils.constants import TASK_TYPE
from handlers import PlanLayoutHandler, SlamSimulationHandler, StatsHandler
from handlers.db import UnitDBHandler
from handlers.ph_vector.ph2022 import AreaVector, AreaVectorSchema
from handlers.ph_vector.ph2022.area_vector import (
    VECTOR_STATS_DEFAULT_FIELDS,
    AreaVectorStats,
    BiggestRectangles,
    FloorFeatures,
    LayoutFeatures,
)
from handlers.ph_vector.ph2022.area_vector_schema import (
    AreaVectorStatsSchema,
    BiggestRectangleSchema,
    FloorFeaturesSchema,
    LayoutFeaturesSchema,
)

fake_apartment_id = "Fake Apartment ID"
fake_site_id = -999
fake_unit_id = 1000
fake_area_id = 1
fake_floor_id = 77
fake_floor_number = 99
fake_plan_id = 66


def make_layout(
    area_footprint: Polygon,
    area_type: AreaType = AreaType.ROOM,
    opening_type: OpeningType = OpeningType.WINDOW,
    separator_opening_footprint: Optional[Polygon] = None,
    feature_type: FeatureType = FeatureType.BATHTUB,
) -> SimLayout:
    feature = SimFeature(footprint=area_footprint, feature_type=feature_type)
    area = SimArea(
        footprint=area_footprint, db_area_id=fake_area_id, area_type=area_type
    )
    space = SimSpace(footprint=area_footprint, areas={area})
    if separator_opening_footprint is None:
        separator_opening_footprint = area_footprint
    wall = SimSeparator(
        footprint=separator_opening_footprint, separator_type=SeparatorType.WALL
    )
    area.features.add(feature)
    wall.add_opening(
        SimOpening(
            footprint=separator_opening_footprint,
            opening_type=opening_type,
            separator=wall,
            height=(2, 2),
            separator_reference_line=get_center_line_from_rectangle(wall.footprint)[0],
        )
    )
    return SimLayout(spaces={space}, separators={wall})


@pytest.fixture
def mocked_area_stats(mocker):
    def fake_area_stats(desired_dimensions, **kwargs):
        return {
            fake_unit_id: {
                fake_area_id: {
                    dimension: {field: 1.0 for field in VECTOR_STATS_DEFAULT_FIELDS}
                    for dimension in desired_dimensions
                }
            }
        }

    return mocker.patch.object(
        StatsHandler, StatsHandler.get_area_stats.__name__, side_effect=fake_area_stats
    )


@pytest.fixture
def mocked_biggest_rectangles_db(mocker):
    return mocker.patch.object(
        SlamSimulationHandler,
        "get_all_results",
        return_value=[
            {"results": {str(fake_area_id): box(0, 0, 1.2, 2).wkt}},
            {"results": {str(fake_area_id): box(0, 0, 1.2, 2).wkt}},
        ],
    )


class TestAreaVectorStats:
    def test_area_vector_stats(self, mocker, mocked_area_stats):
        expected_result = {
            fake_unit_id: {
                fake_area_id: AreaVectorStatsSchema(
                    **{
                        field.name: (
                            1.0 / (4 * math.pi)
                            if field.name.startswith("view_")
                            else 1.0
                        )
                        for field in fields(AreaVectorStatsSchema)
                    }
                )
            }
        }
        assert AreaVectorStats.get_vector_stats(site_id=mocker.ANY) == expected_result


class TestLayoutFeatures:
    def test_make_layout_features(self, mocked_biggest_rectangles_db):
        layout = make_layout(
            area_footprint=box(0, 0, 2, 2),
            separator_opening_footprint=box(0, 0, 1, 1),
            area_type=AreaType.BATHROOM,
            opening_type=OpeningType.DOOR,
        )
        area = next(iter(layout.areas))
        layout_features = asdict(
            LayoutFeatures(layouts=[layout])._make_layout_features(
                area=area, layout=layout
            )
        )
        assert layout_features == dict(
            layout_area_type="Bathroom",
            layout_area=4.0,
            layout_is_navigable=True,
            layout_compactness=0.7853981633974483,
            layout_mean_walllengths=2.0,
            layout_std_walllengths=0.0,
            layout_has_entrance_door=False,
            layout_number_of_doors=1,
            layout_number_of_windows=0,
            layout_has_shower=False,
            layout_has_sink=False,
            layout_has_bathtub=True,
            layout_has_stairs=False,
            layout_has_toilet=False,
            layout_perimeter=8.0,
            layout_door_perimeter=2.002,
            layout_open_perimeter=0.0,
            layout_window_perimeter=0.0,
            layout_railing_perimeter=0.0,
            layout_connects_to_bathroom=False,
            layout_connects_to_private_outdoor=False,
            layout_net_area=4.0,
            layout_room_count=0.0,
        )

    @pytest.mark.parametrize(
        "opening_type", [OpeningType.DOOR, OpeningType.ENTRANCE_DOOR]
    )
    @pytest.mark.parametrize(
        "space_width, expected_result", [(1.2, True), (1.1, False)]
    )
    def test_area_is_navigable(
        self,
        opening_type,
        space_width,
        expected_result,
    ):
        footprint = box(0, 0, space_width, space_width)
        layout = make_layout(area_footprint=footprint, opening_type=opening_type)
        area = next(iter(layout.areas))
        assert (
            LayoutFeatures(layouts=[layout])._area_is_navigable(
                area=area, layout=layout
            )
            == expected_result
        )

    def test_area_connects_to_area_type(self, mocker):
        pol = Polygon([(0, 0), (0, 1), (1, 1), (1, 0)])
        separator = SimSeparator(pol, SeparatorType.WALL)

        areas = {
            "room": SimArea(pol, area_id="room", area_type=AreaType.ROOM),
            "bath": SimArea(pol, area_id="bath", area_type=AreaType.BATHROOM),
            "balcony": SimArea(pol, area_id="balcony", area_type=AreaType.BALCONY),
            "loggia": SimArea(pol, area_id="loggia", area_type=AreaType.LOGGIA),
            "living": SimArea(pol, area_id="living", area_type=AreaType.LIVING_DINING),
        }
        openings = [
            SimOpening(
                pol,
                (0, 1.90),
                separator,
                opening_type=OpeningType.DOOR,
                separator_reference_line=LineString(),
            ),
            SimOpening(
                pol,
                (0, 1.90),
                separator,
                opening_type=OpeningType.DOOR,
                separator_reference_line=LineString(),
            ),
            SimOpening(
                pol,
                (0, 1.90),
                separator,
                opening_type=OpeningType.DOOR,
                separator_reference_line=LineString(),
            ),
            SimOpening(
                pol,
                (0, 1.90),
                separator,
                opening_type=OpeningType.DOOR,
                separator_reference_line=LineString(),
            ),
        ]
        # Room with a bathroom connected to a living room with a balcony and a loggia
        areas_openings = {
            "room": {openings[0], openings[1]},
            "bath": {openings[0]},
            "balcony": {openings[2]},
            "loggia": {openings[3]},
            "living": {openings[2], openings[3], openings[1]},
        }
        mocker.patch.object(SimLayout, "areas", set(areas.values()))
        mocker.patch.object(SimLayout, "areas_openings", areas_openings)
        layout = SimLayout()

        assert LayoutFeatures._area_connects_to_area_type(
            area=areas["room"], layout=layout, target_types={AreaType.BATHROOM}
        )
        assert not LayoutFeatures._area_connects_to_area_type(
            area=areas["room"], layout=layout, target_types={AreaType.BALCONY}
        )
        assert LayoutFeatures._area_connects_to_area_type(
            area=areas["living"],
            layout=layout,
            target_types={AreaType.BALCONY, AreaType.BATHROOM, AreaType.LOGGIA},
        )
        assert LayoutFeatures._area_connects_to_area_type(
            area=areas["living"], layout=layout, target_types={AreaType.LOGGIA}
        )
        assert not LayoutFeatures._area_connects_to_area_type(
            area=areas["bath"], layout=layout, target_types={AreaType.LIVING_DINING}
        )

    @pytest.mark.parametrize("element_footprint", [box(1, 0.2, 1.1, 0.8)])
    def test_area_perimeter_intersection(self, element_footprint, mocker):
        area_footprint = box(0, 0, 1, 1)
        assert LayoutFeatures(layouts=mocker.ANY)._area_perimeter_intersection(
            area_footprint=area_footprint, sim_element_footprints=[element_footprint]
        ) == pytest.approx(0.6, abs=1e-2)

    def test_area_perimeter_features(self, mocker):
        area = SimArea(footprint=box(0, 0, 1, 1))
        wall = SimSeparator(
            footprint=box(1, 0, 1.1, 1), separator_type=SeparatorType.WALL
        )
        for opening_type in OpeningType:
            wall.add_opening(
                SimOpening(
                    footprint=box(1, 0.4, 1.1, 0.6),
                    opening_type=opening_type,
                    separator=wall,
                    height=(2, 2),
                    separator_reference_line=get_center_line_from_rectangle(
                        polygon=wall.footprint
                    )[0],
                )
            )

        separators = {wall}
        for separator_type in set(SeparatorType) - {SeparatorType.WALL}:
            separators.add(
                SimSeparator(
                    footprint=box(-0.1, 0, 0, 1),
                    separator_type=separator_type,
                    height=(2, 2),
                )
            )

        layout = SimLayout(
            spaces={SimSpace(footprint=box(0, 0, 1, 1), areas={area})},
            separators=separators,
        )

        assert not DeepDiff(
            {
                "layout_window_perimeter": 0.2,
                "layout_door_perimeter": 0.2,
                "layout_open_perimeter": 1.0,
                "layout_railing_perimeter": 1.0,
                "layout_perimeter": 4.0,
            },
            LayoutFeatures(layouts=mocker.ANY)._area_perimeter_features(
                area=area, layout=layout
            ),
            significant_digits=2,
        )

    def test_area_element_counts(self):
        area = SimArea(footprint=box(0, 0, 1, 1))
        for feature_type in FeatureType:
            area.features.add(
                SimFeature(footprint=box(0, 0, 0.1, 0.1), feature_type=feature_type)
            )

        wall = SimSeparator(
            footprint=box(1, 0, 1.1, 1), separator_type=SeparatorType.WALL
        )
        for opening_type in OpeningType:
            wall.add_opening(
                SimOpening(
                    footprint=box(1, 0.4, 1.1, 0.6),
                    opening_type=opening_type,
                    separator=wall,
                    height=(2, 2),
                    separator_reference_line=get_center_line_from_rectangle(
                        wall.footprint
                    )[0],
                )
            )

        layout = SimLayout(
            spaces={SimSpace(footprint=box(0, 0, 2, 1), areas={area})},
            separators={wall},
        )

        assert LayoutFeatures(layouts=[layout])._area_element_counts(
            area=area, layout=layout
        ) == {
            "layout_number_of_windows": 1,
            "layout_number_of_doors": 2,
            "layout_has_bathtub": True,
            "layout_has_shower": True,
            "layout_has_sink": True,
            "layout_has_stairs": True,
            "layout_has_toilet": True,
        }

    @pytest.mark.parametrize(
        "door_types, expected_result",
        [
            ([OpeningType.DOOR], False),
            ([OpeningType.ENTRANCE_DOOR], True),
            ([OpeningType.DOOR, OpeningType.ENTRANCE_DOOR], True),
        ],
    )
    def test_area_has_entrance_door(self, door_types, expected_result):
        area = SimArea(footprint=box(0, 0, 1, 1))
        wall = SimSeparator(
            footprint=box(1, 0, 1.1, 1), separator_type=SeparatorType.WALL
        )
        for opening_type in door_types:
            wall.add_opening(
                SimOpening(
                    footprint=box(1, 0.4, 1.1, 0.6),
                    opening_type=opening_type,
                    separator=wall,
                    height=(2, 2),
                    separator_reference_line=get_center_line_from_rectangle(
                        wall.footprint
                    )[0],
                )
            )

        layout = SimLayout(
            spaces={SimSpace(footprint=box(0, 0, 2, 1), areas={area})},
            separators={wall},
        )
        assert (
            LayoutFeatures._area_has_entrance_door(area=area, layout=layout)
            == expected_result
        )

    @pytest.mark.parametrize(
        "area_type, expected_net_area",
        [(AreaType.ROOM, 1.0), (AreaType.BATHROOM, 0.5), (AreaType.NOT_DEFINED, 0.0)],
    )
    def test_get_net_area(self, mocker, area_type, expected_net_area):
        from handlers.ph_vector.ph2022.area_vector import UnifiedClassificationScheme

        mocker.patch.object(
            UnifiedClassificationScheme,
            "NET_AREA_CONTRIBUTIONS",
            {
                AreaType.ROOM: 1.0,
                AreaType.BATHROOM: 0.5,
            },
        )
        area = SimArea(footprint=box(0, 0, 1, 1), area_type=area_type)
        layout_features = LayoutFeatures(layouts=mocker.ANY)
        assert layout_features._get_net_area(area=area) == expected_net_area

    @pytest.mark.parametrize(
        "area_type, expected_room_count",
        [(AreaType.ROOM, 0.5), (AreaType.BATHROOM, 0.0)],
    )
    def test_get_room_count(self, mocker, area_type, expected_room_count):
        from handlers.ph_vector.ph2022.area_vector import UnifiedClassificationScheme

        mocker.patch.object(
            UnifiedClassificationScheme, "ROOM_COUNTS", {AreaType.ROOM: 0.5}
        )
        area = SimArea(footprint=box(0, 0, 1, 1), area_type=area_type)
        layout_features = LayoutFeatures(layouts=mocker.ANY)
        assert layout_features._get_room_count(area=area) == expected_room_count


class TestBiggestRectangle:
    def test_biggest_rectangle(self, mocked_biggest_rectangles_db):
        biggest_rectangles_by_area = BiggestRectangles.get_biggest_rectangles(
            site_id=fake_site_id
        )
        assert biggest_rectangles_by_area == {
            fake_area_id: BiggestRectangleSchema(
                layout_biggest_rectangle_width=1.2, layout_biggest_rectangle_length=2.0
            )
        }
        mocked_biggest_rectangles_db.assert_called_once_with(
            site_id=fake_site_id, task_type=TASK_TYPE.BIGGEST_RECTANGLE
        )


class TestFloorFeatures:
    @pytest.mark.parametrize(
        "area_type,feature_type,expected_result",
        [
            (AreaType.ELEVATOR, FeatureType.ELEVATOR, True),
            (AreaType.ELEVATOR, FeatureType.BATHTUB, True),
            (AreaType.ROOM, FeatureType.ELEVATOR, True),
            (AreaType.BATHROOM, FeatureType.TOILET, False),
        ],
    )
    def test_area_has_elevator(self, area_type, feature_type, expected_result, mocker):
        footprint = box(0, 0, 1, 1)
        layout = make_layout(
            area_footprint=footprint, area_type=area_type, feature_type=feature_type
        )
        assert (
            FloorFeatures(
                floors_info={fake_floor_id: mocker.ANY},
                floors_public_layout={fake_floor_id: layout},
            )._has_elevator(floor_id=fake_floor_id)
            == expected_result
        )

    def test_get_floor_features(self):
        footprint = box(0, 0, 1, 1)
        layout = make_layout(
            area_footprint=footprint,
            area_type=AreaType.ELEVATOR,
            feature_type=FeatureType.ELEVATOR,
        )
        assert FloorFeatures(
            floors_info={
                fake_floor_id: {
                    "floor_number": fake_floor_number,
                }
            },
            floors_public_layout={fake_floor_id: layout},
        ).get_floor_features() == {
            fake_floor_id: FloorFeaturesSchema(
                floor_number=fake_floor_number,
                floor_has_elevator=True,
            )
        }


class TestAreaVector:
    @pytest.fixture
    def mocked_get_units_info(self, mocker):
        return mocker.patch.object(
            AreaVector,
            "_get_units_info",
            return_value=[
                {
                    "id": fake_unit_id,
                    "client_id": fake_apartment_id,
                    "floor_id": fake_floor_id,
                    "representative_unit_client_id": fake_apartment_id,
                }
            ],
        )

    @pytest.fixture
    def mocked_floors_info(self, mocker):
        return mocker.patch.object(
            AreaVector,
            "_floors_info",
            {
                fake_floor_id: {
                    "floor_number": fake_floor_number,
                    "plan_id": fake_plan_id,
                }
            },
        )

    @pytest.fixture
    def mocked_units_layout(self, mocker):
        return mocker.patch.object(
            AreaVector,
            "_units_layout",
            {
                fake_unit_id: make_layout(
                    area_footprint=box(0, 0, 2, 2),
                    opening_type=OpeningType.DOOR,
                    area_type=AreaType.BATHROOM,
                )
            },
        )

    @pytest.fixture
    def mocked_get_public_layout(self, mocker):
        return mocker.patch.object(
            PlanLayoutHandler,
            "get_public_layout",
            return_value=make_layout(
                area_footprint=box(0, 0, 2, 2),
                opening_type=OpeningType.DOOR,
                area_type=AreaType.ELEVATOR,
            ),
        )

    @pytest.mark.parametrize("representative_units_only", [True, False])
    @pytest.mark.parametrize("unit_is_representative", [True, False])
    def test_get_units_info_excludes_non_representative_units(
        self, representative_units_only, unit_is_representative, mocker
    ):
        fake_unit_info = [
            {
                "id": fake_unit_id,
                "client_id": fake_apartment_id,
                "floor_id": fake_floor_id,
                "representative_unit_client_id": fake_apartment_id
                if unit_is_representative
                else None,
            }
        ]
        mocker.patch.object(UnitDBHandler, "find", return_value=fake_unit_info)

        expected_result = fake_unit_info
        if representative_units_only and not unit_is_representative:
            expected_result = []

        assert (
            list(
                AreaVector(site_id=fake_site_id)._get_units_info(
                    representative_units_only=representative_units_only
                )
            )
            == expected_result
        )

    def test_get_vector(
        self,
        mocked_area_stats,
        mocked_biggest_rectangles_db,
        mocked_get_public_layout,
        mocked_floors_info,
        mocked_units_layout,
        mocked_get_units_info,
    ):
        areas_vector = [
            asdict(area_vector)
            for area_vector in AreaVector(site_id=fake_site_id).get_vector(
                representative_units_only=False
            )
        ]
        assert areas_vector == [
            {
                **{
                    field.name: 1.0 / (4 * math.pi)
                    if field.name.startswith("view_")
                    else 1.0
                    for field in fields(AreaVectorSchema)
                },
                "apartment_id": fake_apartment_id,
                "floor_number": fake_floor_number,
                "floor_has_elevator": True,
                "layout_area_type": "Bathroom",
                "layout_area": 4.0,
                "layout_is_navigable": True,
                "layout_biggest_rectangle_width": 1.2,
                "layout_biggest_rectangle_length": 2.0,
                "layout_compactness": 0.7853981633974483,
                "layout_mean_walllengths": 2.0,
                "layout_std_walllengths": 0.0,
                "layout_has_entrance_door": False,
                "layout_number_of_windows": 0.0,
                "layout_number_of_doors": 0.0,
                "layout_has_shower": False,
                "layout_has_sink": False,
                "layout_has_bathtub": True,
                "layout_has_stairs": False,
                "layout_has_toilet": False,
                "layout_perimeter": 8.0,
                "layout_open_perimeter": 0.0,
                "layout_window_perimeter": 0.0,
                "layout_door_perimeter": 8.0,
                "layout_railing_perimeter": 0.0,
                "layout_connects_to_bathroom": False,
                "layout_connects_to_private_outdoor": False,
                "layout_net_area": 4.0,
                "layout_room_count": 0.0,
            }
        ]

    @pytest.mark.parametrize("fake_vector_stats", [{fake_unit_id: {}}, {}])
    def test_get_vector_missing_optional_simulations(
        self,
        mocker,
        mocked_floors_info,
        mocked_units_layout,
        mocked_get_units_info,
        mocked_get_public_layout,
        fake_vector_stats,
    ):
        mocker.patch.object(
            BiggestRectangles, "get_biggest_rectangles", return_value={}
        )
        mocker.patch.object(
            AreaVectorStats, "get_vector_stats", return_value=fake_vector_stats
        )

        fake_layout_features = LayoutFeaturesSchema(
            **{field.name: "fake" for field in fields(LayoutFeaturesSchema)}
        )
        mocker.patch.object(
            LayoutFeatures,
            "get_area_features",
            return_value={fake_area_id: fake_layout_features},
        )

        areas_vector = AreaVector(site_id=fake_site_id).get_vector(
            representative_units_only=False
        )
        assert areas_vector == [
            AreaVectorSchema(
                **asdict(AreaVectorStatsSchema()),
                **asdict(BiggestRectangleSchema()),
                **asdict(fake_layout_features),
                apartment_id=fake_apartment_id,
                floor_number=fake_floor_number,
                floor_has_elevator=True,
            )
        ]
