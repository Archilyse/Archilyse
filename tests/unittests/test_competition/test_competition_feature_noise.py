import pytest
from shapely.geometry import box

from brooks.classifications import UnifiedClassificationScheme
from brooks.models import SimArea, SimLayout, SimOpening, SimSeparator, SimSpace
from brooks.types import AreaType, OpeningType, SeparatorType
from brooks.util.geometry_ops import get_center_line_from_rectangle
from handlers.competition import CompetitionFeaturesCalculator


class TestNoiseInsulatedRooms:
    @staticmethod
    def make_layout(db_area_id: int = 1, area_type=AreaType.ROOM):
        """Layout with 1 area"""
        footprint = box(0, 0, 1, 1)
        area = SimArea(footprint=footprint, area_type=area_type)
        area.db_area_id = db_area_id

        space = SimSpace(footprint=footprint)
        space.areas.add(area)

        # add walls top / bottom walls with windows, needed to validate the room has windows
        minx, miny, maxx, maxy = footprint.bounds
        separators = set()
        for y in [miny, maxy]:
            wall = SimSeparator(
                footprint=box(minx, y - 0.1, maxx, y + 0.1),
                separator_type=SeparatorType.WALL,
                height=(2, 0),
            )
            wall.add_opening(
                SimOpening(
                    footprint=box(minx + 0.2, y - 0.1, maxx - 0.2, y + 0.1),
                    opening_type=OpeningType.WINDOW,
                    separator=wall,
                    height=(2.8, 0),
                    separator_reference_line=get_center_line_from_rectangle(
                        wall.footprint
                    )[0],
                )
            )
            separators.add(wall)

        return SimLayout(spaces={space}, separators=separators)

    @pytest.mark.parametrize(
        "room_type, noises, expected_result",
        [
            (AreaType.LIVING_ROOM, [[100], [0]], 0.0),
            (AreaType.LIVING_ROOM, [[0], [0]], 1.0),
            (AreaType.LIVING_ROOM, [[20], [20]], 1.0),
            (AreaType.BATHROOM, [[20], [20]], 0.0),
            (AreaType.ROOM, [[100], [0.0]], 0.0),
        ],
    )
    def test_noise_insulated_rooms_simple(
        self, room_type, site, noises, expected_result
    ):
        unit_id, area_id = 1, 1
        layout = self.make_layout(db_area_id=area_id, area_type=room_type)
        noise_window_per_area = {
            unit_id: {
                area_id: {"noise_TRAIN_DAY": noises[0], "noise_TRAFFIC_DAY": noises[1]}
            }
        }

        features_calculator = CompetitionFeaturesCalculator(
            classification_schema=UnifiedClassificationScheme()
        )
        assert (
            features_calculator.noise_insulated_rooms(
                residential_units_layouts_with_id=[(unit_id, layout)],
                noise_window_per_area=noise_window_per_area,
            )
            == expected_result
        )
